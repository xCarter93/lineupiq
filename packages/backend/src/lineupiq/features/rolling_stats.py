"""
Rolling window statistics for player performance features.

Computes rolling averages over a configurable window to capture recent form,
which is more predictive than career averages or single-game stats.

Also provides volatility metrics (rolling std, coefficient of variation)
to identify boom/bust players who may need different prediction approaches.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def compute_rolling_stats(df: pl.DataFrame, window: int = 5) -> pl.DataFrame:
    """Compute rolling window statistics for player performance.

    Calculates rolling averages for passing, rushing, and receiving stats
    over a configurable number of games. Uses min_samples=1 to handle players
    with fewer than `window` games (early season or new players).

    Uses shift(1) to prevent data leakage - only prior games are included,
    never the current game being predicted. This ensures rolling features
    represent "what we knew before this game" rather than including the
    current game's outcome.

    Rolling window expanded from 3 to 5 games (Phase 19.1) to better capture
    recent performance trends, especially for volatile stats like touchdowns.

    Args:
        df: Processed player stats from process_player_stats(). Must contain:
            - player_id: Unique player identifier
            - season: NFL season year
            - week: Week number
            - Stat columns: passing_yards, rushing_yards, receiving_yards, etc.
        window: Number of games for rolling window (default: 5).

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
        >>> result = compute_rolling_stats(df, window=5)
        >>> "passing_yards_roll5" in result.columns
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
    # Use shift(1) to prevent data leakage - only prior games used, never current
    rolling_exprs = []
    for stat_col, roll_col in stat_columns.items():
        if stat_col in df.columns:
            rolling_exprs.append(
                pl.col(stat_col)
                .shift(1)
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


def compute_volatility_features(
    df: pl.DataFrame,
    stat_columns: list[str],
    window: int = 5,
) -> pl.DataFrame:
    """Compute player volatility metrics for boom/bust identification.

    Volatility metrics help models distinguish between consistent players
    and high-variance performers who may need different prediction approaches.

    Args:
        df: DataFrame with player stats, must have player_id, season, week columns.
        stat_columns: Which stat columns to compute volatility for.
        window: Rolling window size (default: 5 games).

    Returns:
        DataFrame with original columns plus:
        - {stat}_std{window}: Rolling standard deviation
        - {stat}_cv{window}: Coefficient of variation (std/mean)
    """
    logger.info(f"Computing volatility features for {len(stat_columns)} stats")

    # Filter to columns that exist
    existing = [c for c in stat_columns if c in df.columns]
    if not existing:
        logger.warning("No matching stat columns found for volatility")
        return df

    # Sort for rolling calculations
    result = df.sort(["player_id", "season", "week"])

    # Compute rolling std and CV for each stat
    new_cols = []
    for col in existing:
        # Rolling std with shift to avoid leakage
        std_col = (
            pl.col(col)
            .shift(1)
            .rolling_std(window_size=window, min_samples=2)
            .over("player_id")
            .alias(f"{col}_std{window}")
        )

        # Rolling mean for CV calculation (also shifted)
        mean_expr = (
            pl.col(col)
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
        )

        # CV = std / mean (handle division by zero)
        cv_col = (
            pl.when(mean_expr > 0)
            .then(
                pl.col(col)
                .shift(1)
                .rolling_std(window_size=window, min_samples=2)
                .over("player_id")
                / mean_expr
            )
            .otherwise(0.0)
            .alias(f"{col}_cv{window}")
        )

        new_cols.extend([std_col, cv_col])

    result = result.with_columns(new_cols)

    # Fill nulls with 0 (no variance for new players)
    volatility_cols = [f"{c}_std{window}" for c in existing] + [f"{c}_cv{window}" for c in existing]
    for col_name in volatility_cols:
        if col_name in result.columns:
            result = result.with_columns(pl.col(col_name).fill_null(0.0))

    logger.info(f"Added {len(volatility_cols)} volatility features")

    return result


def get_volatility_columns(stat_columns: list[str], window: int = 5) -> list[str]:
    """Return list of volatility feature column names.

    Args:
        stat_columns: Base stat columns used for volatility.
        window: Rolling window size (default: 5).

    Returns:
        List of volatility column names (std and cv for each stat).
    """
    cols = []
    for col in stat_columns:
        cols.append(f"{col}_std{window}")
        cols.append(f"{col}_cv{window}")
    return cols


def add_lagged_rolling(
    df: pl.DataFrame,
    columns: list[str],
    window: int = 5,
) -> pl.DataFrame:
    """Replace same-week stat columns with lagged rolling averages.

    Same shift(1)-then-roll idiom as compute_rolling_stats, for stats joined in
    from external sources (NGS, PFR, xFP) whose current-week values are outcomes
    of the game being predicted. Raw columns are dropped so no unlagged value
    can reach a model. Sorting happens here because callers join first and
    Polars joins do not guarantee row order.

    Args:
        df: Frame with player_id, season, week and the raw stat columns.
        columns: Raw stat columns to lag (missing ones are ignored).
        window: Number of prior games to average (default: 5).

    Returns:
        DataFrame with each raw column replaced by {col}_roll{window}.
    """
    existing = [c for c in columns if c in df.columns]
    if not existing:
        return df

    result = df.sort(["player_id", "season", "week"]).with_columns(
        [
            pl.col(col)
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias(f"{col}_roll{window}")
            for col in existing
        ]
    )

    logger.info(f"Lagged {len(existing)} columns into {window}-game rolling means")
    return result.drop(existing)
