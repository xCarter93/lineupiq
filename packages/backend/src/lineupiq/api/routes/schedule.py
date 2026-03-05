"""
Schedule API routes for game information.

Provides endpoints to get schedule data including game time, location, weather, and Vegas lines.
"""

import logging
from typing import Any

import nflreadpy as nfl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache the schedule data to avoid repeated loads
_schedule_cache: dict[int, Any] = {}


def get_schedule(season: int):
    """Get schedule data for a season, with caching."""
    if season not in _schedule_cache:
        try:
            _schedule_cache[season] = nfl.load_schedules([season])
            logger.info(f"Loaded schedule for {season}")
        except Exception as e:
            logger.error(f"Failed to load schedule for {season}: {e}")
            return None
    return _schedule_cache[season]


class GameInfo(BaseModel):
    """Game information for a specific team/week."""
    season: int
    week: int
    team: str
    opponent: str
    is_home: bool
    gameday: str
    weekday: str
    gametime: str
    stadium: str
    roof: str
    surface: str
    temp: int | None
    wind: int | None
    spread_line: float | None
    total_line: float | None
    team_implied_total: float | None


@router.get("/game/{season}/{week}/{team}", response_model=GameInfo)
async def get_game_info(season: int, week: int, team: str) -> GameInfo:
    """Get game information for a team in a specific week.

    Args:
        season: NFL season year.
        week: Week number (1-18).
        team: Team abbreviation (e.g., NE, DAL).

    Returns:
        GameInfo with schedule details.
    """
    schedule = get_schedule(season)

    if schedule is None:
        raise HTTPException(status_code=500, detail=f"Failed to load schedule for {season}")

    team = team.upper()

    # Filter to the team's game for this week
    game = schedule.filter(
        ((schedule['home_team'] == team) | (schedule['away_team'] == team)) &
        (schedule['week'] == week)
    )

    if game.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No game found for {team} in week {week} of {season}"
        )

    row = game.to_dicts()[0]

    is_home = row['home_team'] == team
    opponent = row['away_team'] if is_home else row['home_team']

    # Calculate implied team total from spread and over/under
    total_line = row.get('total_line')
    spread_line = row.get('spread_line')
    team_implied_total = None

    if total_line is not None and spread_line is not None:
        # Spread is from home team perspective
        # Team implied total = (total - spread) / 2 for home, (total + spread) / 2 for away
        if is_home:
            team_implied_total = (total_line - spread_line) / 2
        else:
            team_implied_total = (total_line + spread_line) / 2

    return GameInfo(
        season=season,
        week=week,
        team=team,
        opponent=opponent,
        is_home=is_home,
        gameday=row.get('gameday', ''),
        weekday=row.get('weekday', ''),
        gametime=row.get('gametime', ''),
        stadium=row.get('stadium', ''),
        roof=row.get('roof', ''),
        surface=row.get('surface', ''),
        temp=row.get('temp'),
        wind=row.get('wind'),
        spread_line=spread_line if is_home else -spread_line if spread_line else None,
        total_line=total_line,
        team_implied_total=round(team_implied_total, 1) if team_implied_total else None,
    )
