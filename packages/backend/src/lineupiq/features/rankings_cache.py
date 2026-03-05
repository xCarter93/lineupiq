"""
Cached current-season rankings for inference-time feature parity.

Solves the critical training/inference gap where opponent strength and team
strength features were hardcoded to neutral defaults at inference time, while
models were trained on actual computed values.

Computes and caches defensive rankings and team offensive strength from
current-season data, using the same logic as the training pipeline
(opponent_features.py and team_strength.py).

Cache refreshes every 6 hours or on-demand to balance freshness with
API performance.
"""

import logging
import time
from functools import lru_cache

import nflreadpy as nfl
import polars as pl

from lineupiq.features.opponent_features import (
    compute_defensive_rankings,
    compute_defensive_stats,
)

logger = logging.getLogger(__name__)

# Cache TTL in seconds (6 hours)
_CACHE_TTL = 6 * 60 * 60

# Cached data and timestamps
_defensive_rankings: pl.DataFrame | None = None
_team_strength: pl.DataFrame | None = None
_last_refresh: float = 0.0


def _get_current_seasons() -> list[int]:
    """Get current and previous season for ranking computation."""
    current = nfl.get_current_season()
    return [current - 1, current]


def refresh_rankings(force: bool = False) -> None:
    """Refresh cached defensive rankings and team strength data.

    Uses the same computation logic as the training pipeline to ensure
    feature parity between training and inference.

    Args:
        force: If True, refresh regardless of TTL.
    """
    global _defensive_rankings, _team_strength, _last_refresh

    now = time.time()
    if not force and _last_refresh > 0 and (now - _last_refresh) < _CACHE_TTL:
        return  # Cache still fresh

    logger.info("Refreshing rankings cache for inference feature parity...")

    seasons = _get_current_seasons()

    try:
        # --- Defensive Rankings ---
        # Load player stats (same source as training pipeline)
        from lineupiq.data import process_player_stats

        player_df = process_player_stats(seasons)

        # Compute defensive stats (what each defense allowed)
        def_stats = compute_defensive_stats(player_df)

        # Compute rankings (using prior-week logic, same as training)
        _defensive_rankings = compute_defensive_rankings(def_stats)

        logger.info(
            f"Computed defensive rankings: {len(_defensive_rankings)} team-week entries"
        )

        # --- Team Strength ---
        # Load team-level stats and schedules (same as pipeline.py Step 4)
        from lineupiq.data.fetchers import fetch_schedules

        team_stats_df = nfl.load_team_stats(seasons)
        schedules_df = fetch_schedules(seasons)

        from lineupiq.features.team_strength import compute_team_strength

        _team_strength = compute_team_strength(team_stats_df, schedules_df, window=5)

        logger.info(
            f"Computed team strength: {len(_team_strength)} team-week entries"
        )

        _last_refresh = now
        # Clear the LRU caches so they pick up fresh data
        get_latest_opponent_strength.cache_clear()
        get_latest_team_strength.cache_clear()

    except Exception:
        logger.exception("Failed to refresh rankings cache")
        # Keep stale data if refresh fails
        if _defensive_rankings is None:
            _defensive_rankings = pl.DataFrame()
        if _team_strength is None:
            _team_strength = pl.DataFrame()


@lru_cache(maxsize=64)
def get_latest_opponent_strength(opponent_team: str) -> dict[str, float]:
    """Get the most recent opponent defensive strength for a team.

    Returns the latest available rankings for the given team, using the
    same computation as the training pipeline. Falls back to neutral
    defaults only if no data is available.

    Args:
        opponent_team: NFL team abbreviation (e.g., "KC", "PHI").

    Returns:
        Dict with 5 opponent strength features.
    """
    refresh_rankings()

    neutral = {
        "opp_pass_defense_strength": 0.5,
        "opp_rush_defense_strength": 0.5,
        "opp_pass_yards_allowed_rank": 16.0,
        "opp_rush_yards_allowed_rank": 16.0,
        "opp_total_yards_allowed_rank": 16.0,
    }

    if _defensive_rankings is None or _defensive_rankings.is_empty():
        logger.warning(f"No defensive rankings available for {opponent_team}, using neutral defaults")
        return neutral

    # Filter to the opponent team and get the most recent week
    team_data = _defensive_rankings.filter(pl.col("team") == opponent_team)

    if team_data.is_empty():
        logger.warning(f"No rankings found for team {opponent_team}, using neutral defaults")
        return neutral

    # Get the most recent entry (latest season + week)
    latest = team_data.sort(["season", "week"], descending=True).row(0, named=True)

    return {
        "opp_pass_defense_strength": float(latest.get("opp_pass_defense_strength", 0.5)),
        "opp_rush_defense_strength": float(latest.get("opp_rush_defense_strength", 0.5)),
        "opp_pass_yards_allowed_rank": float(latest.get("opp_pass_yards_allowed_rank", 16.0)),
        "opp_rush_yards_allowed_rank": float(latest.get("opp_rush_yards_allowed_rank", 16.0)),
        "opp_total_yards_allowed_rank": float(latest.get("opp_total_yards_allowed_rank", 16.0)),
    }


@lru_cache(maxsize=64)
def get_latest_team_strength(team: str) -> dict[str, float]:
    """Get the most recent team offensive strength for a team.

    Returns the latest available team strength metrics, using the
    same computation as the training pipeline. Falls back to league
    average defaults only if no data is available.

    Args:
        team: NFL team abbreviation (e.g., "KC", "PHI").

    Returns:
        Dict with 3 team strength features.
    """
    refresh_rankings()

    neutral = {
        "team_points_roll5": 22.0,
        "team_yards_roll5": 340.0,
        "team_plays_roll5": 65.0,
    }

    if _team_strength is None or _team_strength.is_empty():
        logger.warning(f"No team strength data available for {team}, using neutral defaults")
        return neutral

    # Filter to the team and get the most recent week
    team_data = _team_strength.filter(pl.col("team") == team)

    if team_data.is_empty():
        logger.warning(f"No strength data found for team {team}, using neutral defaults")
        return neutral

    # Get the most recent entry (latest season + week)
    latest = team_data.sort(["season", "week"], descending=True).row(0, named=True)

    return {
        "team_points_roll5": float(latest.get("team_points_roll5", 22.0)),
        "team_yards_roll5": float(latest.get("team_yards_roll5", 340.0)),
        "team_plays_roll5": float(latest.get("team_plays_roll5", 65.0)),
    }
