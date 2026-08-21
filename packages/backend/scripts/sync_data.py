#!/usr/bin/env python3
"""
Sync the latest NFL data into the local parquet cache.

Entry point for the Weekly Data Sync workflow. Resolves seasons from nflreadpy
rather than the calendar year: player stats lag the season rollover (nflverse only
publishes a season's parquet after Week 1 finishes) while schedules and rosters
are available for the new season months earlier.

Usage:
    uv run python scripts/sync_data.py
"""

import logging
import sys
from pathlib import Path

import polars as pl

from lineupiq.data.fetchers import (
    fetch_player_stats,
    fetch_schedules,
    latest_stats_season,
)
from lineupiq.data.storage import get_cache_path, save_parquet

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sync_data")


def cache(df: pl.DataFrame, data_type: str, season: int) -> Path:
    """Write a season's DataFrame to the cache and verify it landed non-empty."""
    if df.is_empty():
        raise RuntimeError(f"{data_type} for {season} came back empty")

    path = get_cache_path(data_type, str(season))
    save_parquet(df, path)

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"Failed to write {path}")

    logger.info(f"Cached {len(df)} {data_type} rows for {season} -> {path}")
    return path


def latest_schedule_season() -> int:
    """Return the newest season with a published schedule.

    The schedule for a new season is released well before its stats, so this tracks
    the roster season and only falls back if the release has not happened yet.
    """
    import nflreadpy as nfl

    current = int(nfl.get_current_season(roster=True))
    for season in (current, current - 1):
        try:
            if not nfl.load_schedules(seasons=[season]).is_empty():
                return season
        except Exception as e:
            logger.info(f"Schedule for {season} not published yet: {e}")

    raise RuntimeError(f"No published schedule for {current} or {current - 1}")


def main() -> int:
    stats_season = latest_stats_season()
    schedule_season = latest_schedule_season()
    logger.info(f"Syncing stats for {stats_season}, schedules for {schedule_season}")

    cache(fetch_player_stats([stats_season]), "player_stats", stats_season)
    cache(fetch_schedules([schedule_season]), "schedules", schedule_season)

    logger.info("Data sync complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Data sync failed: {e}")
        sys.exit(1)
