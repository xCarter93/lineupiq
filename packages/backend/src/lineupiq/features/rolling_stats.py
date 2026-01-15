"""
Rolling window statistics for player performance features.

Computes rolling averages over a configurable window to capture recent form,
which is more predictive than career averages or single-game stats.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def compute_rolling_stats(df: pl.DataFrame, window: int = 3) -> pl.DataFrame:
    """Compute rolling window statistics for player performance.

    Calculates rolling averages for passing, rushing, and receiving stats
    over a configurable number of games. Uses min_samples=1 to handle players
    with fewer than `window` games (early season or new players).

    Args:
        df: Processed player stats from process_player_stats(). Must contain:
            - player_id: Unique player identifier
            - season: NFL season year
            - week: Week number
            - Stat columns: passing_yards, rushing_yards, receiving_yards, etc.
        window: Number of games for rolling window (default: 3).

    Returns:
        DataFrame with original columns plus rolling average columns:
            - passing_yards_roll{window}
            - passing_tds_roll{window}
            - interceptions_roll{window}
            - rushing_yards_roll{window}
            - rushing_tds_roll{window}
            - carries_roll{window}
            - receiving_yards_roll{window}
            - receiving_tds_roll{window}
            - receptions_roll{window}

    Example:
        >>> from lineupiq.data import process_player_stats
        >>> df = process_player_stats([2024])
        >>> result = compute_rolling_stats(df, window=3)
        >>> "passing_yards_roll3" in result.columns
        True
    """
    logger.info(f"Computing rolling stats with window={window} for {len(df)} rows")

    # Verify required columns exist
    required_cols = ["player_id", "season", "week"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"DataFrame missing required column: {col}")

    # Sort by player_id, season, week to ensure correct ordering for rolling
    df = df.sort(["player_id", "season", "week"])

    # Define stats to compute rolling averages for
    # Only compute for columns that exist in the DataFrame
    stat_columns = {
        # Passing stats
        "passing_yards": f"passing_yards_roll{window}",
        "passing_tds": f"passing_tds_roll{window}",
        "interceptions": f"interceptions_roll{window}",
        # Rushing stats
        "rushing_yards": f"rushing_yards_roll{window}",
        "rushing_tds": f"rushing_tds_roll{window}",
        "carries": f"carries_roll{window}",
        # Receiving stats
        "receiving_yards": f"receiving_yards_roll{window}",
        "receiving_tds": f"receiving_tds_roll{window}",
        "receptions": f"receptions_roll{window}",
    }

    # Build list of rolling expressions for columns that exist
    rolling_exprs = []
    for stat_col, roll_col in stat_columns.items():
        if stat_col in df.columns:
            rolling_exprs.append(
                pl.col(stat_col)
                .rolling_mean(window_size=window, min_samples=1)
                .over("player_id")
                .alias(roll_col)
            )
            logger.debug(f"Adding rolling stat: {stat_col} -> {roll_col}")
        else:
            logger.debug(f"Skipping {stat_col} (not in DataFrame)")

    if not rolling_exprs:
        logger.warning("No stat columns found for rolling computation")
        return df

    # Apply all rolling expressions
    df = df.with_columns(rolling_exprs)

    new_cols = [col for col in df.columns if f"_roll{window}" in col]
    logger.info(f"Rolling stats computed. Added {len(new_cols)} columns: {new_cols}")

    return df
