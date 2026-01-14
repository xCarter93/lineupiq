"""
LineupIQ Data Module - NFL data fetching and storage utilities.

This module provides typed functions for fetching NFL data from nflreadpy
with consistent interfaces and Polars DataFrame returns, plus cache-aware
storage with Parquet persistence.

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
"""

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
]
