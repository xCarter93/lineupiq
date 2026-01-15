"""
Data processing pipeline for ML-ready weekly player stats.

Combines cleaning, normalization, and schedule joining to produce
clean, normalized, weekly player stats with game context.

This is the main entry point for getting ML-ready data for feature engineering.
"""

import logging
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)


def add_game_context(player_df: pl.DataFrame, schedule_df: pl.DataFrame) -> pl.DataFrame:
    """Join player stats with schedule data to add game context.

    Joins on season + week to determine:
    - Whether player is home or away
    - Who the opponent is
    - Game ID for reference

    Args:
        player_df: Player stats DataFrame with season, week, recent_team columns.
        schedule_df: Schedule DataFrame with season, week, home_team, away_team, game_id.

    Returns:
        Player DataFrame with added columns:
        - is_home: bool (True if player's team == home_team)
        - opponent: str (away_team if home, home_team if away)
        - game_id: str (from schedule)

    Example:
        >>> player_df = pl.DataFrame({
        ...     "player_id": ["001"],
        ...     "recent_team": ["KC"],
        ...     "season": [2024],
        ...     "week": [1]
        ... })
        >>> schedule_df = pl.DataFrame({
        ...     "game_id": ["2024_01_KC_BUF"],
        ...     "season": [2024],
        ...     "week": [1],
        ...     "home_team": ["KC"],
        ...     "away_team": ["BUF"]
        ... })
        >>> result = add_game_context(player_df, schedule_df)
        >>> result["is_home"][0]
        True
        >>> result["opponent"][0]
        'BUF'
    """
    initial_count = len(player_df)
    logger.info(f"Adding game context to {initial_count} player rows")

    # Verify required columns exist
    required_player_cols = ["season", "week", "recent_team"]
    required_schedule_cols = ["season", "week", "home_team", "away_team", "game_id"]

    for col in required_player_cols:
        if col not in player_df.columns:
            raise ValueError(f"Player DataFrame missing required column: {col}")

    for col in required_schedule_cols:
        if col not in schedule_df.columns:
            raise ValueError(f"Schedule DataFrame missing required column: {col}")

    # Select only needed columns from schedule for the join
    schedule_cols = ["season", "week", "home_team", "away_team", "game_id"]
    # Add weather columns if they exist
    if "temp" in schedule_df.columns:
        schedule_cols.append("temp")
    if "wind" in schedule_df.columns:
        schedule_cols.append("wind")
    if "is_dome" in schedule_df.columns:
        schedule_cols.append("is_dome")

    schedule_subset = schedule_df.select([col for col in schedule_cols if col in schedule_df.columns])

    # Join player stats with schedules on season and week
    # For each player row, we need to find the game their team played in
    # A team can be either home_team or away_team in the schedule

    # First, join where player's team is home_team
    home_games = schedule_subset.with_columns(
        pl.col("home_team").alias("_join_team")
    )

    # Then, join where player's team is away_team
    away_games = schedule_subset.with_columns(
        pl.col("away_team").alias("_join_team")
    )

    # Combine both possibilities
    all_games = pl.concat([home_games, away_games])

    # Join on season, week, and team
    result = player_df.join(
        all_games,
        left_on=["season", "week", "recent_team"],
        right_on=["season", "week", "_join_team"],
        how="left",
    )

    # Determine is_home and opponent based on team
    result = result.with_columns([
        (pl.col("recent_team") == pl.col("home_team")).alias("is_home"),
        pl.when(pl.col("recent_team") == pl.col("home_team"))
        .then(pl.col("away_team"))
        .otherwise(pl.col("home_team"))
        .alias("opponent"),
    ])

    # Count how many players got matched
    matched_count = result.filter(pl.col("game_id").is_not_null()).shape[0]
    unmatched_count = result.filter(pl.col("game_id").is_null()).shape[0]

    logger.info(
        f"Game context join: {matched_count} matched, {unmatched_count} unmatched "
        f"(bye weeks, mismatched teams)"
    )

    return result


def add_weather_context(df: pl.DataFrame) -> pl.DataFrame:
    """Add normalized weather features for ML consumption.

    Expects schedule columns already joined (temp, wind, is_dome).

    Adds:
    - temp_normalized: (temp - 65) / 20 (center around comfortable, scale to ~[-2, 2])
    - wind_normalized: wind / 15 (scale to ~[0, 2])

    Null weather values are filled with 0 (neutral conditions).

    Args:
        df: DataFrame with temp and wind columns from schedule join.

    Returns:
        DataFrame with temp_normalized and wind_normalized columns.

    Example:
        >>> df = pl.DataFrame({
        ...     "temp": [85.0, 45.0, None],
        ...     "wind": [30.0, 5.0, None],
        ...     "is_dome": [False, False, True]
        ... })
        >>> result = add_weather_context(df)
        >>> result["temp_normalized"][0]
        1.0
        >>> result["wind_normalized"][0]
        2.0
    """
    logger.info(f"Adding weather context to {len(df)} rows")

    # Add temp_normalized: (temp - 65) / 20
    if "temp" in df.columns:
        df = df.with_columns(
            ((pl.col("temp").fill_null(65) - 65) / 20).alias("temp_normalized")
        )
    else:
        # Default to 0 if no temp column
        df = df.with_columns(pl.lit(0.0).alias("temp_normalized"))
        logger.warning("No temp column found, defaulting temp_normalized to 0")

    # Add wind_normalized: wind / 15
    if "wind" in df.columns:
        df = df.with_columns(
            (pl.col("wind").fill_null(0) / 15).alias("wind_normalized")
        )
    else:
        # Default to 0 if no wind column
        df = df.with_columns(pl.lit(0.0).alias("wind_normalized"))
        logger.warning("No wind column found, defaulting wind_normalized to 0")

    # Fill any remaining nulls in normalized columns with 0
    df = df.with_columns([
        pl.col("temp_normalized").fill_null(0.0),
        pl.col("wind_normalized").fill_null(0.0),
    ])

    logger.info("Weather normalization complete")
    return df


# =============================================================================
# Main processing pipeline
# =============================================================================

# Data directory for processed output
PROCESSED_DIR = Path(__file__).parent.parent.parent.parent / "data" / "processed"


def process_player_stats(
    seasons: list[int],
    force_refresh: bool = False,
) -> pl.DataFrame:
    """Main data processing pipeline for ML-ready player stats.

    This is THE main entry point for getting ML-ready data. It:
    1. Loads raw player stats and schedules (cached)
    2. Cleans both datasets
    3. Normalizes (team abbreviations, player IDs, positions)
    4. Adds game context (home/away, opponent)
    5. Adds weather normalization

    Args:
        seasons: List of seasons to process (e.g., [2023, 2024]).
        force_refresh: If True, force re-fetch from nflreadpy.

    Returns:
        Fully processed DataFrame ready for feature engineering, with columns:
        - Player identifiers: player_id, player_name, position, recent_team, etc.
        - Stats: passing_yards, rushing_yards, receiving_yards, etc.
        - Game context: is_home, opponent, game_id
        - Weather: temp_normalized, wind_normalized

    Example:
        >>> df = process_player_stats([2024])
        >>> "is_home" in df.columns
        True
        >>> "opponent" in df.columns
        True
    """
    from lineupiq.data.cleaning import clean_player_stats, clean_schedules
    from lineupiq.data.normalization import normalize_player_data, normalize_team_columns
    from lineupiq.data.storage import load_player_stats_cached, load_schedules_cached

    logger.info(f"Starting data processing pipeline for seasons {seasons}")

    # Step 1: Load raw data (with caching)
    logger.info("Step 1: Loading raw data...")
    player_stats = load_player_stats_cached(seasons, force_refresh=force_refresh)
    schedules = load_schedules_cached(seasons, force_refresh=force_refresh)

    initial_rows = len(player_stats)
    logger.info(f"Loaded {initial_rows} player rows, {len(schedules)} schedule rows")

    # Step 2: Clean data
    logger.info("Step 2: Cleaning data...")
    player_stats = clean_player_stats(player_stats)
    schedules = clean_schedules(schedules)

    after_clean_rows = len(player_stats)
    logger.info(f"After cleaning: {after_clean_rows} player rows")

    # Step 3: Normalize
    logger.info("Step 3: Normalizing data...")
    player_stats = normalize_player_data(player_stats)
    schedules = normalize_team_columns(schedules)

    # Step 4: Add game context
    logger.info("Step 4: Adding game context...")
    player_stats = add_game_context(player_stats, schedules)

    # Step 5: Add weather normalization
    logger.info("Step 5: Normalizing weather data...")
    player_stats = add_weather_context(player_stats)

    # Step 6: Sort for consistent ordering
    player_stats = player_stats.sort(["season", "week", "player_id"])

    final_rows = len(player_stats)
    final_cols = len(player_stats.columns)

    logger.info(
        f"Pipeline complete: {initial_rows} -> {final_rows} rows, {final_cols} columns"
    )
    logger.info(f"Output columns: {player_stats.columns[:15]}...")

    return player_stats


def save_processed_data(
    df: pl.DataFrame,
    name: str = "processed_stats",
) -> Path:
    """Save processed data to Parquet file.

    Args:
        df: Processed DataFrame to save.
        name: File name (without extension).

    Returns:
        Path to the saved file.

    Example:
        >>> df = process_player_stats([2024])
        >>> path = save_processed_data(df, "player_stats_2024")
        >>> path.exists()
        True
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"{name}.parquet"

    df.write_parquet(output_path)
    logger.info(f"Saved {len(df)} rows to {output_path}")

    return output_path
