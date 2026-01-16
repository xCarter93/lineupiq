"""
Pydantic schemas for prediction requests and responses.

All feature fields match the output of lineupiq.features.get_feature_columns()
to ensure consistency between training and inference.
"""

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Base request schema for all position predictions.

    Contains all 17 feature fields required for model inference.
    Features are organized into rolling stats, opponent strength,
    weather, and context categories.
    """

    # Rolling stats (8 features)
    passing_yards_roll3: float = Field(
        ..., description="3-week rolling average of passing yards"
    )
    passing_tds_roll3: float = Field(
        ..., description="3-week rolling average of passing TDs"
    )
    rushing_yards_roll3: float = Field(
        ..., description="3-week rolling average of rushing yards"
    )
    rushing_tds_roll3: float = Field(
        ..., description="3-week rolling average of rushing TDs"
    )
    carries_roll3: float = Field(
        ..., description="3-week rolling average of carries"
    )
    receiving_yards_roll3: float = Field(
        ..., description="3-week rolling average of receiving yards"
    )
    receiving_tds_roll3: float = Field(
        ..., description="3-week rolling average of receiving TDs"
    )
    receptions_roll3: float = Field(
        ..., description="3-week rolling average of receptions"
    )

    # Opponent features (5 features)
    opp_pass_defense_strength: float = Field(
        ..., description="Opponent pass defense strength rating"
    )
    opp_rush_defense_strength: float = Field(
        ..., description="Opponent rush defense strength rating"
    )
    opp_pass_yards_allowed_rank: float = Field(
        ..., description="Opponent rank in pass yards allowed (1-32)"
    )
    opp_rush_yards_allowed_rank: float = Field(
        ..., description="Opponent rank in rush yards allowed (1-32)"
    )
    opp_total_yards_allowed_rank: float = Field(
        ..., description="Opponent rank in total yards allowed (1-32)"
    )

    # Weather features (2 features)
    temp_normalized: float = Field(
        ..., description="Normalized temperature (0-1 scale)"
    )
    wind_normalized: float = Field(
        ..., description="Normalized wind speed (0-1 scale)"
    )

    # Team strength features (3 features)
    team_points_roll3: float = Field(
        ..., description="3-week rolling average of team points scored"
    )
    team_yards_roll3: float = Field(
        ..., description="3-week rolling average of team total yards"
    )
    team_plays_roll3: float = Field(
        ..., description="3-week rolling average of team plays (pace)"
    )

    # Volatility features (8 features)
    passing_yards_std3: float = Field(
        ..., description="3-week standard deviation of passing yards"
    )
    passing_yards_cv3: float = Field(
        ..., description="3-week coefficient of variation of passing yards"
    )
    rushing_yards_std3: float = Field(
        ..., description="3-week standard deviation of rushing yards"
    )
    rushing_yards_cv3: float = Field(
        ..., description="3-week coefficient of variation of rushing yards"
    )
    receiving_yards_std3: float = Field(
        ..., description="3-week standard deviation of receiving yards"
    )
    receiving_yards_cv3: float = Field(
        ..., description="3-week coefficient of variation of receiving yards"
    )
    receptions_std3: float = Field(
        ..., description="3-week standard deviation of receptions"
    )
    receptions_cv3: float = Field(
        ..., description="3-week coefficient of variation of receptions"
    )

    # Context features (2 features)
    is_home: bool = Field(
        ..., description="Whether the player is playing at home"
    )
    is_dome: bool = Field(
        ..., description="Whether the game is in a dome/indoor stadium"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "passing_yards_roll3": 250.5,
                    "passing_tds_roll3": 1.8,
                    "rushing_yards_roll3": 15.0,
                    "rushing_tds_roll3": 0.2,
                    "carries_roll3": 3.0,
                    "receiving_yards_roll3": 0.0,
                    "receiving_tds_roll3": 0.0,
                    "receptions_roll3": 0.0,
                    "opp_pass_defense_strength": 0.95,
                    "opp_rush_defense_strength": 1.05,
                    "opp_pass_yards_allowed_rank": 15.0,
                    "opp_rush_yards_allowed_rank": 20.0,
                    "opp_total_yards_allowed_rank": 18.0,
                    "temp_normalized": 0.6,
                    "wind_normalized": 0.2,
                    "team_points_roll3": 24.5,
                    "team_yards_roll3": 350.0,
                    "team_plays_roll3": 65.0,
                    "passing_yards_std3": 50.0,
                    "passing_yards_cv3": 0.2,
                    "rushing_yards_std3": 25.0,
                    "rushing_yards_cv3": 0.3,
                    "receiving_yards_std3": 0.0,
                    "receiving_yards_cv3": 0.0,
                    "receptions_std3": 0.0,
                    "receptions_cv3": 0.0,
                    "is_home": True,
                    "is_dome": False,
                }
            ]
        }
    }


class QBPredictionResponse(BaseModel):
    """Response schema for QB predictions.

    Includes all fantasy-relevant QB stats for complete scoring calculations.
    """

    passing_yards: float = Field(..., description="Predicted passing yards")
    passing_tds: float = Field(..., description="Predicted passing TDs")
    interceptions: float = Field(..., description="Predicted interceptions")
    rushing_yards: float = Field(..., description="Predicted rushing yards")
    rushing_tds: float = Field(..., description="Predicted rushing TDs")
    fumbles_lost: float = Field(..., description="Predicted fumbles lost")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "passing_yards": 267.3,
                    "passing_tds": 1.9,
                    "interceptions": 0.8,
                    "rushing_yards": 25.5,
                    "rushing_tds": 0.2,
                    "fumbles_lost": 0.2,
                }
            ]
        }
    }


class RBPredictionResponse(BaseModel):
    """Response schema for RB predictions.

    Includes all 7 fantasy-relevant stats:
    - Rushing: rushing_yards, rushing_tds, carries
    - Receiving: receiving_yards, receptions, receiving_tds
    - Turnovers: fumbles_lost (combined rushing + receiving)
    """

    rushing_yards: float = Field(..., description="Predicted rushing yards")
    rushing_tds: float = Field(..., description="Predicted rushing TDs")
    carries: float = Field(..., description="Predicted carries")
    receiving_yards: float = Field(..., description="Predicted receiving yards")
    receptions: float = Field(..., description="Predicted receptions")
    receiving_tds: float = Field(..., description="Predicted receiving TDs")
    fumbles_lost: float = Field(..., description="Predicted fumbles lost")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rushing_yards": 72.5,
                    "rushing_tds": 0.6,
                    "carries": 16.2,
                    "receiving_yards": 22.1,
                    "receptions": 2.8,
                    "receiving_tds": 0.1,
                    "fumbles_lost": 0.05,
                }
            ]
        }
    }


class ReceiverPredictionResponse(BaseModel):
    """Response schema for WR and TE predictions."""

    receiving_yards: float = Field(..., description="Predicted receiving yards")
    receiving_tds: float = Field(..., description="Predicted receiving TDs")
    receptions: float = Field(..., description="Predicted receptions")
    fumbles_lost: float = Field(..., description="Predicted fumbles lost")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "receiving_yards": 68.4,
                    "receiving_tds": 0.5,
                    "receptions": 5.2,
                    "fumbles_lost": 0.02,
                }
            ]
        }
    }


class KickerPredictionRequest(BaseModel):
    """Request schema for kicker predictions.

    Contains rolling stat features for kicker model inference.
    """

    fg_att_roll3: float = Field(
        ..., description="3-week rolling average of FG attempts"
    )
    pat_att_roll3: float = Field(
        ..., description="3-week rolling average of PAT attempts"
    )
    fg_pct_roll3: float = Field(
        ..., description="3-week rolling average of FG percentage"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fg_att_roll3": 2.5,
                    "pat_att_roll3": 3.2,
                    "fg_pct_roll3": 0.85,
                }
            ]
        }
    }


class KickerPrediction(BaseModel):
    """Kicker stat predictions."""

    fg_att: float = Field(..., description="Predicted total FG attempts")
    fg_att_0_39: float = Field(..., description="Predicted short FG attempts (0-39 yards)")
    fg_att_40_49: float = Field(..., description="Predicted medium FG attempts (40-49 yards)")
    fg_att_50_plus: float = Field(..., description="Predicted long FG attempts (50+ yards)")
    pat_att: float = Field(..., description="Predicted extra point attempts")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fg_att": 2.3,
                    "fg_att_0_39": 1.2,
                    "fg_att_40_49": 0.7,
                    "fg_att_50_plus": 0.4,
                    "pat_att": 3.5,
                }
            ]
        }
    }


class KickerPredictionResponse(BaseModel):
    """API response for kicker prediction."""

    predictions: KickerPrediction = Field(..., description="Kicker stat predictions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "predictions": {
                        "fg_att": 2.3,
                        "fg_att_0_39": 1.2,
                        "fg_att_40_49": 0.7,
                        "fg_att_50_plus": 0.4,
                        "pat_att": 3.5,
                    }
                }
            ]
        }
    }


class DefensePredictionRequest(BaseModel):
    """Request schema for team defense predictions.

    Contains rolling stat features for defense model inference.
    """

    points_allowed_roll3: float = Field(
        ..., description="3-week rolling average of points allowed"
    )
    def_sacks_roll3: float = Field(
        ..., description="3-week rolling average of sacks"
    )
    def_ints_roll3: float = Field(
        ..., description="3-week rolling average of interceptions"
    )
    def_fumbles_roll3: float = Field(
        ..., description="3-week rolling average of fumble recoveries"
    )
    def_tds_roll3: float = Field(
        ..., description="3-week rolling average of defensive/ST touchdowns"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "points_allowed_roll3": 21.3,
                    "def_sacks_roll3": 2.5,
                    "def_ints_roll3": 1.2,
                    "def_fumbles_roll3": 0.8,
                    "def_tds_roll3": 0.3,
                }
            ]
        }
    }


class DefensePrediction(BaseModel):
    """Team defense stat predictions."""

    points_allowed: float = Field(..., description="Predicted points allowed")
    def_sacks: float = Field(..., description="Predicted sacks")
    def_interceptions: float = Field(..., description="Predicted interceptions")
    def_fumbles: float = Field(..., description="Predicted fumble recoveries")
    total_def_tds: float = Field(..., description="Predicted defensive/ST touchdowns")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "points_allowed": 21.5,
                    "def_sacks": 2.3,
                    "def_interceptions": 1.1,
                    "def_fumbles": 0.7,
                    "total_def_tds": 0.2,
                }
            ]
        }
    }


class DefensePredictionResponse(BaseModel):
    """API response for team defense prediction."""

    team: str = Field(..., description="NFL team abbreviation")
    opponent: str = Field(..., description="Opponent team abbreviation")
    week: int = Field(..., description="NFL week number")
    predictions: DefensePrediction = Field(..., description="Defense stat predictions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "team": "PHI",
                    "opponent": "DAL",
                    "week": 10,
                    "predictions": {
                        "points_allowed": 21.5,
                        "def_sacks": 2.3,
                        "def_interceptions": 1.1,
                        "def_fumbles": 0.7,
                        "total_def_tds": 0.2,
                    },
                }
            ]
        }
    }
