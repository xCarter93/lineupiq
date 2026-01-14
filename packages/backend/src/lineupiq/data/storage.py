"""
Data storage layer with Parquet persistence and file-based caching.

Provides cache-aware loading functions to avoid repeated network calls
when fetching NFL data from nflreadpy.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import polars as pl

logger = logging.getLogger(__name__)

# Default data directory relative to package
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


def get_cache_path(data_type: str, key: str) -> Path:
    """Get path for cached data file.

    Args:
        data_type: Category (player_stats, schedules, snap_counts).
        key: Unique identifier (e.g., season year or "all").

    Returns:
        Path to parquet file.

    Example:
        >>> path = get_cache_path("player_stats", "2024")
        >>> path.name
        '2024.parquet'
    """
    return DATA_DIR / data_type / f"{key}.parquet"


def is_cache_valid(path: Path, max_age_days: int = 7) -> bool:
    """Check if cached file exists and is fresh.

    Args:
        path: Path to cache file.
        max_age_days: Maximum age before considered stale.

    Returns:
        True if cache exists and is within max_age.

    Example:
        >>> from pathlib import Path
        >>> is_cache_valid(Path("/nonexistent/file.parquet"))
        False
    """
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(days=max_age_days)


def save_parquet(df: pl.DataFrame, path: Path) -> None:
    """Save DataFrame to Parquet file.

    Creates parent directories if they don't exist.

    Args:
        df: Polars DataFrame to save.
        path: Destination path.

    Example:
        >>> import polars as pl
        >>> from pathlib import Path
        >>> df = pl.DataFrame({"a": [1, 2, 3]})
        >>> # save_parquet(df, Path("/tmp/test.parquet"))
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    logger.info(f"Saved {len(df)} rows to {path}")


def load_parquet(path: Path) -> pl.DataFrame:
    """Load DataFrame from Parquet file.

    Args:
        path: Path to parquet file.

    Returns:
        Polars DataFrame.

    Raises:
        FileNotFoundError: If path doesn't exist.

    Example:
        >>> from pathlib import Path
        >>> # df = load_parquet(Path("/tmp/test.parquet"))
    """
    df = pl.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def load_with_cache(
    data_type: str,
    key: str,
    fetcher: Callable[[], pl.DataFrame],
    max_age_days: int = 7,
    force_refresh: bool = False,
) -> pl.DataFrame:
    """Load data from cache or fetch if stale/missing.

    This is the main interface for cache-aware data loading. It checks
    for a valid cache file first, and only calls the fetcher function
    if the cache is missing or stale.

    Args:
        data_type: Category for cache organization (player_stats, schedules, etc.).
        key: Unique identifier for this data (e.g., season year).
        fetcher: Function to call if cache miss.
        max_age_days: Cache staleness threshold in days.
        force_refresh: If True, always fetch fresh data regardless of cache.

    Returns:
        Polars DataFrame from cache or fresh fetch.

    Example:
        >>> from lineupiq.data.fetchers import fetch_player_stats
        >>> # df = load_with_cache("player_stats", "2024", lambda: fetch_player_stats([2024]))
    """
    cache_path = get_cache_path(data_type, key)

    if not force_refresh and is_cache_valid(cache_path, max_age_days):
        logger.info(f"Cache hit for {data_type}/{key}")
        return load_parquet(cache_path)

    logger.info(f"Cache miss for {data_type}/{key}, fetching...")
    df = fetcher()
    save_parquet(df, cache_path)
    return df


# =============================================================================
# High-level convenience functions combining fetchers with caching
# =============================================================================


def load_player_stats_cached(
    seasons: list[int],
    max_age_days: int = 7,
    force_refresh: bool = False,
) -> pl.DataFrame:
    """Load player stats with per-season caching.

    Each season is cached independently, so requesting [2023, 2024] after
    having cached 2024 will only fetch 2023.

    Args:
        seasons: List of seasons to load (e.g., [2023, 2024]).
        max_age_days: Cache freshness threshold.
        force_refresh: Force re-fetch from nflreadpy.

    Returns:
        Combined DataFrame for all requested seasons.

    Example:
        >>> df = load_player_stats_cached([2024])
        >>> df.shape[0] > 0
        True
    """
    from lineupiq.data.fetchers import fetch_player_stats

    dfs = []
    for season in seasons:
        df = load_with_cache(
            data_type="player_stats",
            key=str(season),
            fetcher=lambda s=season: fetch_player_stats([s]),
            max_age_days=max_age_days,
            force_refresh=force_refresh,
        )
        dfs.append(df)
    return pl.concat(dfs) if dfs else pl.DataFrame()


def load_schedules_cached(
    seasons: list[int] | None = None,
    max_age_days: int = 7,
    force_refresh: bool = False,
) -> pl.DataFrame:
    """Load schedules with caching.

    Args:
        seasons: Seasons to load (None = all available).
        max_age_days: Cache freshness threshold.
        force_refresh: Force re-fetch.

    Returns:
        Schedules DataFrame.

    Example:
        >>> df = load_schedules_cached([2024])
        >>> "temp" in df.columns
        True
    """
    from lineupiq.data.fetchers import fetch_schedules

    key = "all" if seasons is None else "_".join(map(str, sorted(seasons)))
    return load_with_cache(
        data_type="schedules",
        key=key,
        fetcher=lambda: fetch_schedules(seasons),
        max_age_days=max_age_days,
        force_refresh=force_refresh,
    )
