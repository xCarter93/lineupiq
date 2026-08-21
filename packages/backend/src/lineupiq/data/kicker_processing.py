"""
Kicker data processing for ML model training.

Processes raw kicker stats into features suitable for predicting:
- FG attempts by distance bucket
- XP (PAT) attempts
- FG/XP success rates (as context features)
"""

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_kicker_stats, fetch_schedules
from lineupiq.data.team_context import TEAM_CONTEXT_COLUMNS, attach_team_vegas_context

logger = logging.getLogger(__name__)

# Kicker stat columns for cleaning
KICKER_STAT_COLUMNS = [
    "fg_made",
    "fg_att",
    "fg_missed",
    "fg_made_0_19",
    "fg_made_20_29",
    "fg_made_30_39",
    "fg_made_40_49",
    "fg_made_50_59",
    "fg_made_60_",
    "fg_missed_0_19",
    "fg_missed_20_29",
    "fg_missed_30_39",
    "fg_missed_40_49",
    "fg_missed_50_59",
    "fg_missed_60_",
    "pat_made",
    "pat_att",
    "pat_missed",
]

# Target columns for kicker models
KICKER_TARGETS = [
    "fg_att",  # Total FG attempts
    "fg_att_0_39",  # Short FG attempts (0-39 yards)
    "fg_att_40_49",  # Medium FG attempts
    "fg_att_50_plus",  # Long FG attempts (50+)
    "pat_att",  # Extra point attempts
]


def process_kicker_data(
    seasons: list[int],
    target_season: int | None = None,
    include_weeks: list[int] | None = None,
    future_rows: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Process kicker data for model training.

    Args:
        seasons: List of seasons to process.
        target_season: If provided, filter this season to only include specific weeks.
        include_weeks: Weeks to include from target_season (required if target_season set).
        future_rows: Identity-only rows (player_id, player_name, team, season, week)
            for an upcoming week. Stats stay null so rolling features lag onto them
            from prior games and Vegas context is joined from the schedule.

    Returns:
        DataFrame with kicker features and targets, one row per kicker-game.

    Example:
        >>> df = process_kicker_data([2024])
        >>> "fg_att_roll5" in df.columns
        True
    """
    logger.info(f"Processing kicker data for seasons: {seasons}")

    # Fetch raw kicker stats
    df = fetch_kicker_stats(seasons)

    # Select relevant columns; nflreadpy renamed recent_team -> team
    team_col = "recent_team" if "recent_team" in df.columns else "team"
    id_cols = ["player_id", "player_name", "season", "week"]
    available_id = [c for c in id_cols if c in df.columns]
    available_stats = [c for c in KICKER_STAT_COLUMNS if c in df.columns]

    df = df.select(
        [pl.col(c) for c in available_id]
        + [pl.col(team_col).alias("team")]
        + [pl.col(c) for c in available_stats]
    )

    # Fill nulls with 0 for stat columns
    for col in available_stats:
        df = df.with_columns(pl.col(col).fill_null(0))

    # Create distance bucket aggregates for attempts
    df = df.with_columns(
        [
            # Short FG attempts (0-39)
            (
                pl.col("fg_made_0_19").fill_null(0)
                + pl.col("fg_missed_0_19").fill_null(0)
                + pl.col("fg_made_20_29").fill_null(0)
                + pl.col("fg_missed_20_29").fill_null(0)
                + pl.col("fg_made_30_39").fill_null(0)
                + pl.col("fg_missed_30_39").fill_null(0)
            ).alias("fg_att_0_39"),
            # Medium FG attempts (40-49)
            (
                pl.col("fg_made_40_49").fill_null(0)
                + pl.col("fg_missed_40_49").fill_null(0)
            ).alias("fg_att_40_49"),
            # Long FG attempts (50+)
            (
                pl.col("fg_made_50_59").fill_null(0)
                + pl.col("fg_missed_50_59").fill_null(0)
                + pl.col("fg_made_60_").fill_null(0)
                + pl.col("fg_missed_60_").fill_null(0)
            ).alias("fg_att_50_plus"),
        ]
    )

    # Append upcoming-week rows before the rolling block so their windows lag onto
    # prior games; their stat columns stay null and never enter a feature.
    if future_rows is not None:
        df = pl.concat([df, future_rows], how="diagonal_relaxed")

    schedule_seasons = sorted(set(df.select("season").to_series().to_list()))
    df = attach_team_vegas_context(df, fetch_schedules(schedule_seasons), "team")

    # Add rolling features for kicker consistency
    df = df.sort(["player_id", "season", "week"])

    df = df.with_columns(
        [
            pl.col("fg_att")
            .shift(1)
            .rolling_mean(window_size=3, min_samples=1)
            .over("player_id")
            .alias("fg_att_roll5"),
            pl.col("pat_att")
            .shift(1)
            .rolling_mean(window_size=3, min_samples=1)
            .over("player_id")
            .alias("pat_att_roll5"),
            # Success rate as context
            pl.when(pl.col("fg_att") > 0)
            .then(pl.col("fg_made") / pl.col("fg_att"))
            .otherwise(0.0)
            .shift(1)
            .rolling_mean(window_size=3, min_samples=1)
            .over("player_id")
            .alias("fg_pct_roll5"),
        ]
    )

    # Fill rolling nulls
    for col in ["fg_att_roll5", "pat_att_roll5", "fg_pct_roll5"]:
        mean_val = df.select(pl.col(col).mean()).item() or 0.0
        df = df.with_columns(pl.col(col).fill_null(mean_val))

    # Filter target season to only include specified weeks (simulation mode)
    if target_season is not None and include_weeks is not None:
        logger.info(f"Filtering season {target_season} to weeks {include_weeks}")
        df = df.filter(
            (pl.col("season") != target_season) |
            ((pl.col("season") == target_season) & (pl.col("week").is_in(include_weeks)))
        )
        logger.info(f"After filtering: {len(df)} rows")

    logger.info(f"Processed kicker data: {df.shape[0]} rows, {df.shape[1]} columns")

    return df


def get_kicker_feature_columns() -> list[str]:
    """Return feature columns for kicker models."""
    return [
        "fg_att_roll5",
        "pat_att_roll5",
        "fg_pct_roll5",
    ] + TEAM_CONTEXT_COLUMNS


def get_kicker_target_columns() -> list[str]:
    """Return target columns for kicker models."""
    return KICKER_TARGETS
