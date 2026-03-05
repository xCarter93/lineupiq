"""
Kicker data processing for ML model training.

Processes raw kicker stats into features suitable for predicting:
- FG attempts by distance bucket
- XP (PAT) attempts
- FG/XP success rates (as context features)
"""

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_kicker_stats

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
) -> pl.DataFrame:
    """Process kicker data for model training.

    Args:
        seasons: List of seasons to process.
        target_season: If provided, filter this season to only include specific weeks.
        include_weeks: Weeks to include from target_season (required if target_season set).

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

    # Select relevant columns
    id_cols = ["player_id", "player_name", "recent_team", "season", "week"]
    available_id = [c for c in id_cols if c in df.columns]
    available_stats = [c for c in KICKER_STAT_COLUMNS if c in df.columns]

    df = df.select(available_id + available_stats)

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
    ]


def get_kicker_target_columns() -> list[str]:
    """Return target columns for kicker models."""
    return KICKER_TARGETS
