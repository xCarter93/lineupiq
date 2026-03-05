"""
Snap count and usage rate features for ML models.

Snap percentage is one of the strongest predictors of player production.
A player taking 90% of snaps will produce more than one taking 50%.

Features:
- snap_pct_roll5: 5-game rolling snap percentage
- snap_pct_trend: Change in snap% (emerging/declining role)
- target_share_roll5: Rolling % of team targets (WR/TE)
- carry_share_roll5: Rolling % of team carries (RB)
"""

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_snap_counts

logger = logging.getLogger(__name__)


def compute_usage_features(
    df: pl.DataFrame,
    seasons: list[int],
    window: int = 5,
) -> pl.DataFrame:
    """Add snap count and usage share features to player data.

    Args:
        df: Player stats DataFrame with player_id, season, week, team, position.
        seasons: Seasons to fetch snap count data for.
        window: Rolling window size (default: 5).

    Returns:
        DataFrame with added snap and usage columns.
    """
    logger.info(f"Computing usage features for seasons {seasons}")

    # Fetch snap count data
    try:
        snaps_df = fetch_snap_counts(seasons)
    except Exception:
        logger.warning("Failed to fetch snap counts, adding default usage features")
        return _add_default_usage_features(df, window)

    if snaps_df.is_empty():
        logger.warning("Empty snap count data, adding defaults")
        return _add_default_usage_features(df, window)

    # Ensure player_id column exists in snap counts (may be named differently)
    player_id_col = None
    for col_name in ["player_id", "pfr_player_id", "gsis_id", "pfr_id"]:
        if col_name in snaps_df.columns:
            player_id_col = col_name
            break

    if player_id_col is None:
        logger.warning("No player_id column found in snap counts, using defaults")
        return _add_default_usage_features(df, window)

    # Rename to player_id if needed
    if player_id_col != "player_id":
        snaps_df = snaps_df.rename({player_id_col: "player_id"})

    # Extract offense snap percentage
    snap_pct_col = "offense_pct" if "offense_pct" in snaps_df.columns else None
    if snap_pct_col is None:
        # Try to compute from snaps
        if "offense_snaps" in snaps_df.columns:
            # We'd need team total snaps to compute percentage
            logger.warning("No offense_pct column, using defaults")
            return _add_default_usage_features(df, window)
        logger.warning("No snap percentage data available, using defaults")
        return _add_default_usage_features(df, window)

    # Select relevant snap data
    snap_data = snaps_df.select([
        "player_id", "season", "week",
        pl.col(snap_pct_col).alias("snap_pct"),
    ])

    # Join snap data to player data
    df = df.join(snap_data, on=["player_id", "season", "week"], how="left")

    # Fill missing snap percentages with position defaults
    df = df.with_columns(
        pl.col("snap_pct").fill_null(0.5)
    )

    # Sort for rolling calculations
    df = df.sort(["player_id", "season", "week"])

    # Compute rolling snap percentage with shift to avoid leakage
    df = df.with_columns([
        pl.col("snap_pct")
        .shift(1)
        .rolling_mean(window_size=window, min_samples=1)
        .over("player_id")
        .fill_null(0.5)
        .alias(f"snap_pct_roll{window}"),
    ])

    # Compute snap percentage trend (current roll3 vs roll5)
    df = df.with_columns(
        (
            pl.col("snap_pct")
            .shift(1)
            .rolling_mean(window_size=3, min_samples=1)
            .over("player_id")
            .fill_null(0.5)
            - pl.col(f"snap_pct_roll{window}")
        )
        .fill_null(0.0)
        .alias("snap_pct_trend")
    )

    # Compute target share (WR/TE: targets / team_targets)
    if "targets" in df.columns:
        # Compute team targets per game
        team_targets = df.group_by(["team", "season", "week"]).agg(
            pl.col("targets").sum().alias("team_targets")
        )
        df = df.join(team_targets, on=["team", "season", "week"], how="left")

        df = df.with_columns(
            pl.when(pl.col("team_targets") > 0)
            .then(pl.col("targets") / pl.col("team_targets"))
            .otherwise(0.0)
            .alias("target_share")
        )

        df = df.with_columns(
            pl.col("target_share")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias(f"target_share_roll{window}")
        )

        # Clean up intermediate columns
        df = df.drop(["team_targets", "target_share"])
    else:
        df = df.with_columns(pl.lit(0.0).alias(f"target_share_roll{window}"))

    # Compute carry share (RB: carries / team_carries)
    if "carries" in df.columns:
        team_carries = df.group_by(["team", "season", "week"]).agg(
            pl.col("carries").sum().alias("team_carries")
        )
        df = df.join(team_carries, on=["team", "season", "week"], how="left")

        df = df.with_columns(
            pl.when(pl.col("team_carries") > 0)
            .then(pl.col("carries") / pl.col("team_carries"))
            .otherwise(0.0)
            .alias("carry_share")
        )

        df = df.with_columns(
            pl.col("carry_share")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias(f"carry_share_roll{window}")
        )

        # Clean up intermediate columns
        df = df.drop(["team_carries", "carry_share"])
    else:
        df = df.with_columns(pl.lit(0.0).alias(f"carry_share_roll{window}"))

    # Drop the raw snap_pct column (we only want the rolling version)
    if "snap_pct" in df.columns:
        df = df.drop("snap_pct")

    logger.info("Added usage features: snap_pct_roll5, snap_pct_trend, target_share_roll5, carry_share_roll5")

    return df


def _add_default_usage_features(df: pl.DataFrame, window: int = 5) -> pl.DataFrame:
    """Add default usage features when snap data is unavailable."""
    return df.with_columns([
        pl.lit(0.5).alias(f"snap_pct_roll{window}"),
        pl.lit(0.0).alias("snap_pct_trend"),
        pl.lit(0.0).alias(f"target_share_roll{window}"),
        pl.lit(0.0).alias(f"carry_share_roll{window}"),
    ])


def get_usage_columns(window: int = 5) -> list[str]:
    """Return list of usage feature column names."""
    return [
        f"snap_pct_roll{window}",
        "snap_pct_trend",
        f"target_share_roll{window}",
        f"carry_share_roll{window}",
    ]
