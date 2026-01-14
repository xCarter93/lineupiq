"""
NFL data fetching functions using nflreadpy.

All functions return Polars DataFrames. Callers can convert to pandas
with .to_pandas() if needed.
"""

import logging
from typing import Literal

import polars as pl

logger = logging.getLogger(__name__)

# Type alias for seasons parameter used across nflreadpy functions
# None=current season, True=all history, int=specific year, list[int]=multiple years
SeasonList = int | list[int] | bool | None

# Skill positions for fantasy football (per PROJECT.md)
SKILL_POSITIONS: frozenset[str] = frozenset({"QB", "RB", "WR", "TE"})


def fetch_player_stats(
    seasons: SeasonList = None,
    summary_level: Literal["week", "reg", "post", "reg+post"] = "week",
) -> pl.DataFrame:
    """Fetch player statistics from nflreadpy.

    Args:
        seasons: Year(s) to fetch.
            - None: Current season
            - True: All available history (1999+)
            - int: Specific season (e.g., 2024)
            - list[int]: Multiple seasons (e.g., [2022, 2023, 2024])
        summary_level: Aggregation level for stats.
            - "week": Weekly stats (default)
            - "reg": Regular season totals
            - "post": Postseason totals
            - "reg+post": Combined totals

    Returns:
        Polars DataFrame with 114 columns of player stats including:
        - Identifiers: player_id, player_name, position, team, week
        - Passing: passing_yards, passing_tds, passing_interceptions
        - Rushing: rushing_yards, rushing_tds, carries
        - Receiving: receiving_yards, receiving_tds, receptions, targets
        - Fantasy: fantasy_points, fantasy_points_ppr

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_player_stats([2024])
        >>> df.shape
        (18981, 114)
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    logger.info(f"Fetching player stats: seasons={seasons}, summary_level={summary_level}")

    try:
        df = nfl.load_player_stats(seasons=seasons, summary_level=summary_level)
        logger.info(f"Fetched {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch player stats: {e}")
        raise RuntimeError(f"Failed to fetch player stats: {e}") from e


def fetch_schedules(seasons: SeasonList = True) -> pl.DataFrame:
    """Fetch game schedules with weather and venue data.

    Args:
        seasons: Year(s) to fetch (default: all available history).
            - None: Current season
            - True: All available history
            - int: Specific season
            - list[int]: Multiple seasons

    Returns:
        Polars DataFrame with ~46 columns including:
        - Game info: game_id, season, week, game_type
        - Teams: home_team, away_team, home_score, away_score
        - Weather: temp, wind, roof
        - Venue: stadium, stadium_id, surface

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_schedules([2024])
        >>> "temp" in df.columns
        True
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    logger.info(f"Fetching schedules: seasons={seasons}")

    try:
        df = nfl.load_schedules(seasons=seasons)
        logger.info(f"Fetched {df.shape[0]} games, {df.shape[1]} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch schedules: {e}")
        raise RuntimeError(f"Failed to fetch schedules: {e}") from e


def fetch_snap_counts(seasons: SeasonList = None) -> pl.DataFrame:
    """Fetch snap participation data.

    Note: Snap count data is only available from 2012 onwards.

    Args:
        seasons: Year(s) to fetch (default: current season).
            - None: Current season
            - True: All available history (2012+)
            - int: Specific season (must be 2012+)
            - list[int]: Multiple seasons (all must be 2012+)

    Returns:
        Polars DataFrame with snap participation data including:
        - Player info: player, team, position
        - Snap counts: offense_snaps, defense_snaps, st_snaps
        - Percentages: offense_pct, defense_pct, st_pct

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_snap_counts([2024])
        >>> "offense_snaps" in df.columns
        True
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    logger.info(f"Fetching snap counts: seasons={seasons}")

    try:
        df = nfl.load_snap_counts(seasons=seasons)
        logger.info(f"Fetched {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch snap counts: {e}")
        raise RuntimeError(f"Failed to fetch snap counts: {e}") from e


def filter_skill_positions(df: pl.DataFrame) -> pl.DataFrame:
    """Filter DataFrame to skill positions only (QB, RB, WR, TE).

    This supports PROJECT.md requirement: "Position priority: Skill positions
    (QB, RB, WR, TE) before K/DEF"

    Args:
        df: DataFrame with 'position' column.

    Returns:
        Filtered DataFrame containing only rows where position is
        QB, RB, WR, or TE.

    Raises:
        ValueError: If 'position' column is not present.

    Example:
        >>> df = fetch_player_stats([2024])
        >>> filtered = filter_skill_positions(df)
        >>> set(filtered["position"].unique().to_list())
        {'QB', 'RB', 'WR', 'TE'}
    """
    if "position" not in df.columns:
        raise ValueError("DataFrame must have 'position' column")

    filtered = df.filter(pl.col("position").is_in(SKILL_POSITIONS))
    logger.debug(f"Filtered from {df.shape[0]} to {filtered.shape[0]} skill position rows")
    return filtered
