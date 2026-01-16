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

# Fantasy-relevant positions for roster display (includes K)
FANTASY_POSITIONS: frozenset[str] = frozenset({"QB", "RB", "WR", "TE", "K"})


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


def fetch_kicker_stats(seasons: SeasonList = None) -> pl.DataFrame:
    """Fetch kicker statistics from nflreadpy.

    Args:
        seasons: Year(s) to fetch.
            - None: Current season
            - True: All available history (1999+)
            - int: Specific season (e.g., 2024)
            - list[int]: Multiple seasons (e.g., [2022, 2023, 2024])

    Returns:
        Polars DataFrame filtered to K position with kicking stats:
        - Identifiers: player_id, player_name, team, week, season
        - FG stats: fg_made, fg_att, fg_made_0_19 through fg_made_60_
        - PAT stats: pat_made, pat_att, pat_missed

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_kicker_stats([2024])
        >>> df.shape[0]  # Number of kicker game records
        569
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    logger.info(f"Fetching kicker stats: seasons={seasons}")

    try:
        df = nfl.load_player_stats(seasons=seasons, summary_level="week")

        # Filter to kickers only
        kickers = df.filter(pl.col("position") == "K")

        logger.info(f"Fetched {kickers.shape[0]} kicker game records")

        return kickers
    except Exception as e:
        logger.error(f"Failed to fetch kicker stats: {e}")
        raise RuntimeError(f"Failed to fetch kicker stats: {e}") from e


def fetch_team_defense_stats(seasons: SeasonList = None) -> pl.DataFrame:
    """Fetch team defensive statistics from nflreadpy.

    Args:
        seasons: Year(s) to fetch.
            - None: Current season
            - True: All available history
            - int: Specific season (e.g., 2024)
            - list[int]: Multiple seasons (e.g., [2022, 2023, 2024])

    Returns:
        Polars DataFrame with team-level defensive stats:
        - Identifiers: team, week, season
        - Defensive: sacks, interceptions, fumbles_forced, def_tds
        - Special teams: special_teams_tds

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_team_defense_stats([2024])
        >>> df.shape[0]  # Number of team-week records
        544
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    logger.info(f"Fetching team defense stats: seasons={seasons}")

    try:
        df = nfl.load_team_stats(seasons=seasons)
        logger.info(f"Fetched {df.shape[0]} team-week records")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch team defense stats: {e}")
        raise RuntimeError(f"Failed to fetch team defense stats: {e}") from e


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


def fetch_rosters(seasons: list[int] | None = None) -> pl.DataFrame:
    """Fetch NFL roster data from nflreadpy.

    Returns fantasy-relevant position players (QB, RB, WR, TE, K) with
    biographical and team information suitable for roster display.

    Args:
        seasons: Year(s) to fetch.
            - None: Current season (via nfl.get_current_season())
            - list[int]: Specific seasons (e.g., [2025])

    Returns:
        Polars DataFrame with columns:
        - gsis_id: Player unique identifier
        - full_name: Player's full name
        - position: Position (QB, RB, WR, TE, K)
        - team: NFL team abbreviation
        - jersey_number: Jersey number (may be null)
        - height: Height string (e.g., "6-2")
        - weight: Weight in pounds
        - college: College attended
        - years_exp: Years of NFL experience
        - headshot_url: URL to player headshot image

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_rosters([2025])
        >>> df.shape[0]  # Fantasy-relevant players
        563
        >>> set(df["position"].unique().to_list())
        {'QB', 'RB', 'WR', 'TE', 'K'}
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    # Default to current season if not specified
    if seasons is None:
        current = nfl.get_current_season()
        seasons = [current]

    logger.info(f"Fetching rosters: seasons={seasons}")

    try:
        df = nfl.load_rosters(seasons=seasons)

        # Filter to fantasy-relevant positions
        df = df.filter(pl.col("position").is_in(FANTASY_POSITIONS))

        # Select relevant columns for roster display
        roster_cols = [
            "gsis_id",
            "full_name",
            "position",
            "team",
            "jersey_number",
            "height",
            "weight",
            "college",
            "years_exp",
            "headshot_url",
        ]

        df = df.select([c for c in roster_cols if c in df.columns])

        logger.info(f"Fetched {df.shape[0]} fantasy-relevant players")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch rosters: {e}")
        raise RuntimeError(f"Failed to fetch rosters: {e}") from e


def fetch_player_history(
    player_id: str,
    seasons: list[int] | None = None,
) -> pl.DataFrame:
    """Fetch historical weekly stats for a specific player.

    Retrieves game-by-game statistics for a player across multiple seasons,
    suitable for displaying player history and recent performance trends.

    Args:
        player_id: Player's gsis_id (e.g., "00-0033873" for Mahomes).
        seasons: Years to fetch.
            - None: Last 3 seasons (current, current-1, current-2)
            - list[int]: Specific seasons (e.g., [2023, 2024, 2025])

    Returns:
        Polars DataFrame with weekly stats sorted by season desc, week desc:
        - Identifiers: player_id, player_name, player_display_name, position, season, week
        - Game context: opponent_team
        - Passing: passing_yards, passing_tds, passing_interceptions
        - Rushing: rushing_yards, rushing_tds, carries
        - Receiving: receiving_yards, receiving_tds, receptions
        - Fantasy: fantasy_points, fantasy_points_ppr

        Returns empty DataFrame if player not found.

    Raises:
        ImportError: If nflreadpy is not installed.
        RuntimeError: If data fetch fails.

    Example:
        >>> df = fetch_player_history("00-0033873", [2024])  # Mahomes
        >>> df.shape[0]  # Number of games
        17
        >>> df["passing_yards"].mean()
        281.2
    """
    try:
        import nflreadpy as nfl
    except ImportError as e:
        logger.error("nflreadpy not installed. Run: uv add nflreadpy")
        raise ImportError("nflreadpy is required but not installed") from e

    # Default to last 3 seasons if not specified
    if seasons is None:
        current = nfl.get_current_season()
        seasons = list(range(current - 2, current + 1))

    logger.info(f"Fetching player history: player_id={player_id}, seasons={seasons}")

    try:
        df = nfl.load_player_stats(seasons=seasons, summary_level="week")

        # Filter to specific player
        df = df.filter(pl.col("player_id") == player_id)

        if df.is_empty():
            logger.warning(f"No stats found for player_id={player_id}")
            return df

        # Select relevant columns for history display
        history_cols = [
            "player_id",
            "player_name",
            "player_display_name",
            "position",
            "season",
            "week",
            "opponent_team",
            "passing_yards",
            "passing_tds",
            "passing_interceptions",
            "rushing_yards",
            "rushing_tds",
            "carries",
            "receiving_yards",
            "receiving_tds",
            "receptions",
            "fantasy_points",
            "fantasy_points_ppr",
        ]

        df = df.select([c for c in history_cols if c in df.columns])

        # Sort by season desc, week desc for most recent first
        df = df.sort(["season", "week"], descending=True)

        logger.info(f"Fetched {df.shape[0]} game records for player {player_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch player history: {e}")
        raise RuntimeError(f"Failed to fetch player history: {e}") from e
