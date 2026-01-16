"""Roster and player history API routes."""

import nflreadpy as nfl
from fastapi import APIRouter, HTTPException, Query

from lineupiq.api.schemas.roster import (
    PlayerHistoryResponse,
    PlayerRoster,
    RosterResponse,
    WeeklyStats,
)
from lineupiq.data.fetchers import fetch_player_history, fetch_rosters

router = APIRouter()


@router.get("/roster", response_model=RosterResponse)
async def get_roster(
    season: int | None = Query(default=None, description="NFL season year (default: current)")
) -> RosterResponse:
    """Get current NFL roster for fantasy-relevant positions.

    Returns all players in QB, RB, WR, TE, K positions for the specified season.
    Use this to populate player dropdowns and search interfaces.

    Args:
        season: NFL season year. Defaults to current season.

    Returns:
        RosterResponse with list of PlayerRoster entries.
    """
    if season is None:
        season = nfl.get_current_season()

    df = fetch_rosters([season])

    players = [
        PlayerRoster(
            player_id=row["gsis_id"],
            name=row["full_name"],
            position=row["position"],
            team=row["team"],
            jersey_number=row.get("jersey_number"),
            height=row.get("height"),
            weight=row.get("weight"),
            college=row.get("college"),
            years_exp=row.get("years_exp"),
            headshot_url=row.get("headshot_url"),
        )
        for row in df.to_dicts()
    ]

    return RosterResponse(season=season, players=players, count=len(players))


@router.get("/player/{player_id}/history", response_model=PlayerHistoryResponse)
async def get_player_history(
    player_id: str,
    seasons: int = Query(default=3, ge=1, le=5, description="Number of seasons to fetch"),
) -> PlayerHistoryResponse:
    """Get player's historical weekly stats for the last N seasons.

    Returns game-by-game stats sorted by most recent first. Use this to
    display player performance history and recent trends.

    Args:
        player_id: Player's gsis_id (e.g., "00-0033873" for Mahomes).
        seasons: Number of seasons to fetch (1-5, default 3).

    Returns:
        PlayerHistoryResponse with list of WeeklyStats.

    Raises:
        HTTPException: 404 if player not found in any season.
    """
    current = nfl.get_current_season()
    season_list = list(range(current - seasons + 1, current + 1))

    df = fetch_player_history(player_id, season_list)

    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"No stats found for player {player_id}")

    # Get player info from first row
    first = df.row(0, named=True)

    games = [
        WeeklyStats(
            season=row["season"],
            week=row["week"],
            opponent_team=row.get("opponent_team"),
            passing_yards=row.get("passing_yards"),
            passing_tds=row.get("passing_tds"),
            interceptions=row.get("passing_interceptions"),
            rushing_yards=row.get("rushing_yards"),
            rushing_tds=row.get("rushing_tds"),
            carries=row.get("carries"),
            receiving_yards=row.get("receiving_yards"),
            receiving_tds=row.get("receiving_tds"),
            receptions=row.get("receptions"),
            fantasy_points=row.get("fantasy_points"),
        )
        for row in df.to_dicts()
    ]

    return PlayerHistoryResponse(
        player_id=player_id,
        player_name=first.get("player_display_name") or first.get("player_name") or "Unknown",
        position=first.get("position") or "Unknown",
        seasons=season_list,
        games=games,
        total_games=len(games),
    )
