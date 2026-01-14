"""
LineupIQ Data Module - NFL data fetching utilities.

This module provides typed functions for fetching NFL data from nflreadpy
with consistent interfaces and Polars DataFrame returns.

Public API:
    fetch_player_stats: Weekly/seasonal player statistics
    fetch_schedules: Game schedules with weather/venue data
    fetch_snap_counts: Snap participation data
    filter_skill_positions: Filter to QB/RB/WR/TE only
    SKILL_POSITIONS: Frozenset of skill position codes
"""

from lineupiq.data.fetchers import (
    SKILL_POSITIONS,
    fetch_player_stats,
    fetch_schedules,
    fetch_snap_counts,
    filter_skill_positions,
)

__all__ = [
    "SKILL_POSITIONS",
    "fetch_player_stats",
    "fetch_schedules",
    "fetch_snap_counts",
    "filter_skill_positions",
]
