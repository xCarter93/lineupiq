"""
Data cleaning and validation functions for NFL data.

Provides Polars-based cleaning functions to prepare raw nflreadpy data
for ML consumption. Handles null values, validates data types, caps outliers,
and selects ML-relevant columns.
"""

import logging

import polars as pl

from lineupiq.data.fetchers import SKILL_POSITIONS

logger = logging.getLogger(__name__)

# Stat columns to fill nulls with 0
NUMERIC_STAT_COLUMNS = [
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "carries",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "targets",
]

# ML-relevant columns to select
ML_IDENTIFIER_COLUMNS = [
    "player_id",
    "player_name",
    "player_display_name",
    "position",
    "recent_team",
    "season",
    "week",
]

ML_PASSING_COLUMNS = [
    "passing_yards",
    "passing_tds",
    "interceptions",
    "attempts",
    "completions",
]

ML_RUSHING_COLUMNS = [
    "rushing_yards",
    "rushing_tds",
    "carries",
]

ML_RECEIVING_COLUMNS = [
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "targets",
]

ML_FANTASY_COLUMNS = [
    "fantasy_points",
    "fantasy_points_ppr",
]

ML_COLUMNS = (
    ML_IDENTIFIER_COLUMNS
    + ML_PASSING_COLUMNS
    + ML_RUSHING_COLUMNS
    + ML_RECEIVING_COLUMNS
    + ML_FANTASY_COLUMNS
)

# Outlier caps (based on NFL single-game records)
MAX_YARDS_PER_GAME = 600  # Single game record ~550 yards
MAX_TDS_PER_GAME = 8  # Conservative cap for TDs


def validate_player_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Validate player stats DataFrame by removing invalid rows.

    Removes rows where:
    - player_id is null (required identifier)
    - position is null or not a skill position (QB, RB, WR, TE)
    - season is null
    - week is null or <= 0

    Args:
        df: Raw player stats DataFrame from nflreadpy.

    Returns:
        Validated DataFrame with invalid rows removed.

    Example:
        >>> df = pl.DataFrame({
        ...     "player_id": ["001", None, "003"],
        ...     "position": ["QB", "RB", "WR"],
        ...     "season": [2024, 2024, 2024],
        ...     "week": [1, 2, 3]
        ... })
        >>> result = validate_player_stats(df)
        >>> len(result)
        2
    """
    initial_count = len(df)

    # Remove null player_id
    df = df.filter(pl.col("player_id").is_not_null())
    after_player_id = len(df)
    removed_player_id = initial_count - after_player_id
    if removed_player_id > 0:
        logger.info(f"Removed {removed_player_id} rows with null player_id")

    # Remove null or invalid position
    df = df.filter(
        pl.col("position").is_not_null() & pl.col("position").is_in(SKILL_POSITIONS)
    )
    after_position = len(df)
    removed_position = after_player_id - after_position
    if removed_position > 0:
        logger.info(f"Removed {removed_position} rows with invalid/null position")

    # Remove null season
    df = df.filter(pl.col("season").is_not_null())
    after_season = len(df)
    removed_season = after_position - after_season
    if removed_season > 0:
        logger.info(f"Removed {removed_season} rows with null season")

    # Remove null or invalid week
    df = df.filter(pl.col("week").is_not_null() & (pl.col("week") > 0))
    after_week = len(df)
    removed_week = after_season - after_week
    if removed_week > 0:
        logger.info(f"Removed {removed_week} rows with null/invalid week")

    total_removed = initial_count - after_week
    logger.info(
        f"Validation complete: {initial_count} -> {after_week} rows "
        f"({total_removed} removed)"
    )

    return df


def clean_numeric_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Clean numeric stat columns by filling nulls and capping outliers.

    - Fills null values in stat columns with 0
    - Caps obvious outliers (yards > 600, TDs > 8 per game)

    Args:
        df: Player stats DataFrame.

    Returns:
        DataFrame with cleaned numeric stats.

    Example:
        >>> df = pl.DataFrame({
        ...     "passing_yards": [None, 300, 700],
        ...     "passing_tds": [2, None, 10]
        ... })
        >>> result = clean_numeric_stats(df)
        >>> result["passing_yards"].to_list()
        [0, 300, 600]
    """
    # Fill nulls with 0 for stat columns that exist in the DataFrame
    existing_stat_columns = [col for col in NUMERIC_STAT_COLUMNS if col in df.columns]

    for col in existing_stat_columns:
        df = df.with_columns(pl.col(col).fill_null(0))

    # Cap yard columns at MAX_YARDS_PER_GAME
    yard_columns = [col for col in existing_stat_columns if "yards" in col]
    for col in yard_columns:
        over_cap = df.filter(pl.col(col) > MAX_YARDS_PER_GAME)
        if len(over_cap) > 0:
            logger.info(f"Capping {len(over_cap)} values in {col} to {MAX_YARDS_PER_GAME}")
        df = df.with_columns(
            pl.when(pl.col(col) > MAX_YARDS_PER_GAME)
            .then(MAX_YARDS_PER_GAME)
            .otherwise(pl.col(col))
            .alias(col)
        )

    # Cap TD columns at MAX_TDS_PER_GAME
    td_columns = [col for col in existing_stat_columns if "tds" in col]
    for col in td_columns:
        over_cap = df.filter(pl.col(col) > MAX_TDS_PER_GAME)
        if len(over_cap) > 0:
            logger.info(f"Capping {len(over_cap)} values in {col} to {MAX_TDS_PER_GAME}")
        df = df.with_columns(
            pl.when(pl.col(col) > MAX_TDS_PER_GAME)
            .then(MAX_TDS_PER_GAME)
            .otherwise(pl.col(col))
            .alias(col)
        )

    logger.info(f"Cleaned numeric stats for {len(df)} rows")
    return df


def select_ml_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Select only ML-relevant columns from the DataFrame.

    Selects columns needed for ML:
    - Identifiers: player_id, player_name, player_display_name, position, recent_team, season, week
    - Passing: passing_yards, passing_tds, interceptions, attempts, completions
    - Rushing: rushing_yards, rushing_tds, carries
    - Receiving: receptions, receiving_yards, receiving_tds, targets
    - Fantasy: fantasy_points, fantasy_points_ppr (for validation)

    Missing columns are gracefully ignored.

    Args:
        df: Player stats DataFrame.

    Returns:
        DataFrame with only ML-relevant columns.

    Example:
        >>> df = pl.DataFrame({
        ...     "player_id": ["001"],
        ...     "position": ["QB"],
        ...     "passing_yards": [300],
        ...     "some_other_column": ["value"]
        ... })
        >>> result = select_ml_columns(df)
        >>> "some_other_column" in result.columns
        False
    """
    # Select only columns that exist in the DataFrame
    existing_columns = [col for col in ML_COLUMNS if col in df.columns]
    missing_columns = [col for col in ML_COLUMNS if col not in df.columns]

    if missing_columns:
        logger.debug(f"ML columns not found (ignored): {missing_columns}")

    result = df.select(existing_columns)
    logger.info(
        f"Selected {len(existing_columns)} ML columns from {len(df.columns)} total"
    )

    return result


def clean_player_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Orchestrator function that runs the full cleaning pipeline.

    Pipeline:
    1. validate_player_stats - Remove invalid rows
    2. clean_numeric_stats - Fill nulls and cap outliers
    3. select_ml_columns - Select only ML-relevant columns

    Args:
        df: Raw player stats DataFrame from nflreadpy.

    Returns:
        Fully cleaned DataFrame ready for ML feature engineering.

    Example:
        >>> from lineupiq.data import load_player_stats_cached
        >>> df = load_player_stats_cached([2024])
        >>> cleaned = clean_player_stats(df)
        >>> cleaned.columns  # Only ML columns
    """
    logger.info(f"Starting player stats cleaning pipeline ({len(df)} rows)")

    df = validate_player_stats(df)
    df = clean_numeric_stats(df)
    df = select_ml_columns(df)

    logger.info(f"Cleaning pipeline complete: {df.shape}")
    return df
