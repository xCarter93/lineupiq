"""
LineupIQ Data Module - NFL data fetching, storage, and cleaning utilities.

This module provides typed functions for fetching NFL data from nflreadpy
with consistent interfaces and Polars DataFrame returns, plus cache-aware
storage with Parquet persistence and data cleaning for ML consumption.

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
]
