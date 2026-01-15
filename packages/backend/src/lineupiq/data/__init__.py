"""
LineupIQ Data Module - NFL data fetching, storage, cleaning, normalization, and processing.

This module provides typed functions for fetching NFL data from nflreadpy
with consistent interfaces and Polars DataFrame returns, plus cache-aware
storage with Parquet persistence, data cleaning for ML consumption,
normalization utilities for consistent identifiers, and a full processing
pipeline for ML-ready data.

Public API:
    Fetchers:
        fetch_player_stats: Weekly/seasonal player statistics
        fetch_schedules: Game schedules with weather/venue data
        fetch_snap_counts: Snap participation data
        filter_skill_positions: Filter to QB/RB/WR/TE only
        SKILL_POSITIONS: Frozenset of skill position codes

    Storage:
        load_with_cache: Cache-aware data loading
        get_cache_path: Get path for cached data file
        DATA_DIR: Default data directory path

    Cleaning:
        clean_player_stats: Full pipeline for player stats cleaning
        clean_schedules: Clean schedule data for ML consumption
        validate_player_stats: Remove invalid rows from player stats
        clean_numeric_stats: Fill nulls and cap outliers
        select_ml_columns: Select only ML-relevant columns

    Normalization:
        TEAM_MAPPING: Historical to current team abbreviation mapping
        CURRENT_TEAMS: Frozenset of 32 current NFL team abbreviations
        normalize_team: Normalize single team abbreviation
        normalize_team_columns: Normalize team columns in DataFrame
        standardize_player_id: Standardize player IDs with player_key
        normalize_position: Normalize position values (FB -> RB)
        normalize_player_data: Full player data normalization pipeline

    Processing:
        process_player_stats: Full data processing pipeline for ML-ready stats
        save_processed_data: Save processed data to Parquet file
        add_game_context: Join player stats with schedule for home/away/opponent
        add_weather_context: Normalize weather features for ML
"""

from lineupiq.data.cleaning import (
    clean_numeric_stats,
    clean_player_stats,
    clean_schedules,
    select_ml_columns,
    validate_player_stats,
)
from lineupiq.data.fetchers import (
    SKILL_POSITIONS,
    fetch_player_stats,
    fetch_schedules,
    fetch_snap_counts,
    filter_skill_positions,
)
from lineupiq.data.normalization import (
    CURRENT_TEAMS,
    TEAM_MAPPING,
    normalize_player_data,
    normalize_position,
    normalize_team,
    normalize_team_columns,
    standardize_player_id,
)
from lineupiq.data.processing import (
    add_game_context,
    add_weather_context,
    process_player_stats,
    save_processed_data,
)
from lineupiq.data.storage import (
    DATA_DIR,
    get_cache_path,
    load_player_stats_cached,
    load_schedules_cached,
    load_with_cache,
)

__all__ = [
    # Fetchers
    "SKILL_POSITIONS",
    "fetch_player_stats",
    "fetch_schedules",
    "fetch_snap_counts",
    "filter_skill_positions",
    # Storage
    "DATA_DIR",
    "get_cache_path",
    "load_with_cache",
    # Convenience functions (cached loading)
    "load_player_stats_cached",
    "load_schedules_cached",
    # Cleaning
    "clean_player_stats",
    "clean_schedules",
    "validate_player_stats",
    "clean_numeric_stats",
    "select_ml_columns",
    # Normalization
    "TEAM_MAPPING",
    "CURRENT_TEAMS",
    "normalize_team",
    "normalize_team_columns",
    "standardize_player_id",
    "normalize_position",
    "normalize_player_data",
    # Processing
    "process_player_stats",
    "save_processed_data",
    "add_game_context",
    "add_weather_context",
]
