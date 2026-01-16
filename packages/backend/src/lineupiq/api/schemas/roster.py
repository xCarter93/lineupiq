"""
Pydantic schemas for roster and player history API endpoints.
"""

from pydantic import BaseModel, Field


class PlayerRoster(BaseModel):
    """Player roster entry from nflreadpy."""

    player_id: str = Field(..., description="Player's gsis_id")
    name: str = Field(..., description="Player's full name")
    position: str = Field(..., description="Position (QB, RB, WR, TE, K)")
    team: str = Field(..., description="NFL team abbreviation")
    jersey_number: int | None = Field(None, description="Jersey number")
    height: int | None = Field(None, description="Height in inches")
    weight: int | None = Field(None, description="Weight in pounds")
    college: str | None = Field(None, description="College attended")
    years_exp: int | None = Field(None, description="Years of NFL experience")
    headshot_url: str | None = Field(None, description="URL to player headshot image")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "player_id": "00-0033873",
                    "name": "Patrick Mahomes",
                    "position": "QB",
                    "team": "KC",
                    "jersey_number": 15,
                    "height": 74,
                    "weight": 225,
                    "college": "Texas Tech",
                    "years_exp": 8,
                    "headshot_url": "https://static.www.nfl.com/image/...",
                }
            ]
        }
    }


class RosterResponse(BaseModel):
    """Full roster response."""

    season: int = Field(..., description="NFL season year")
    players: list[PlayerRoster] = Field(..., description="List of players")
    count: int = Field(..., description="Number of players in response")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "season": 2025,
                    "players": [
                        {
                            "player_id": "00-0033873",
                            "name": "Patrick Mahomes",
                            "position": "QB",
                            "team": "KC",
                            "jersey_number": 15,
                            "height": 74,
                            "weight": 225,
                            "college": "Texas Tech",
                            "years_exp": 8,
                            "headshot_url": "https://static.www.nfl.com/image/...",
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }


class WeeklyStats(BaseModel):
    """Single week of player stats."""

    season: int = Field(..., description="NFL season year")
    week: int = Field(..., description="NFL week number")
    opponent_team: str | None = Field(None, description="Opponent team abbreviation")
    passing_yards: float | None = Field(None, description="Passing yards")
    passing_tds: float | None = Field(None, description="Passing touchdowns")
    interceptions: float | None = Field(None, description="Interceptions thrown")
    rushing_yards: float | None = Field(None, description="Rushing yards")
    rushing_tds: float | None = Field(None, description="Rushing touchdowns")
    carries: float | None = Field(None, description="Rush attempts")
    receiving_yards: float | None = Field(None, description="Receiving yards")
    receiving_tds: float | None = Field(None, description="Receiving touchdowns")
    receptions: float | None = Field(None, description="Receptions")
    fantasy_points: float | None = Field(None, description="Fantasy points (standard)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "season": 2024,
                    "week": 17,
                    "opponent_team": "PIT",
                    "passing_yards": 320.0,
                    "passing_tds": 3.0,
                    "interceptions": 0.0,
                    "rushing_yards": 22.0,
                    "rushing_tds": 0.0,
                    "carries": 4.0,
                    "receiving_yards": 0.0,
                    "receiving_tds": 0.0,
                    "receptions": 0.0,
                    "fantasy_points": 23.8,
                }
            ]
        }
    }


class PlayerHistoryResponse(BaseModel):
    """Player historical stats response."""

    player_id: str = Field(..., description="Player's gsis_id")
    player_name: str = Field(..., description="Player's display name")
    position: str = Field(..., description="Position (QB, RB, WR, TE)")
    seasons: list[int] = Field(..., description="Seasons included in history")
    games: list[WeeklyStats] = Field(..., description="List of game stats")
    total_games: int = Field(..., description="Total number of games")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "player_id": "00-0033873",
                    "player_name": "Patrick Mahomes",
                    "position": "QB",
                    "seasons": [2023, 2024, 2025],
                    "games": [
                        {
                            "season": 2024,
                            "week": 17,
                            "opponent_team": "PIT",
                            "passing_yards": 320.0,
                            "passing_tds": 3.0,
                            "interceptions": 0.0,
                            "rushing_yards": 22.0,
                            "rushing_tds": 0.0,
                            "carries": 4.0,
                            "receiving_yards": 0.0,
                            "receiving_tds": 0.0,
                            "receptions": 0.0,
                            "fantasy_points": 23.8,
                        }
                    ],
                    "total_games": 1,
                }
            ]
        }
    }
