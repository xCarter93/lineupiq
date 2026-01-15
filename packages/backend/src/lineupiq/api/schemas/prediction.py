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
                    "is_home": True,
                    "is_dome": False,
                }
            ]
        }
    }


class QBPredictionResponse(BaseModel):
    """Response schema for QB predictions."""

    passing_yards: float = Field(..., description="Predicted passing yards")
    passing_tds: float = Field(..., description="Predicted passing TDs")

    model_config = {
        "json_schema_extra": {
            "examples": [{"passing_yards": 267.3, "passing_tds": 1.9}]
        }
    }


class RBPredictionResponse(BaseModel):
    """Response schema for RB predictions."""

    rushing_yards: float = Field(..., description="Predicted rushing yards")
    rushing_tds: float = Field(..., description="Predicted rushing TDs")
    carries: float = Field(..., description="Predicted carries")
    receiving_yards: float = Field(..., description="Predicted receiving yards")
    receptions: float = Field(..., description="Predicted receptions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rushing_yards": 72.5,
                    "rushing_tds": 0.6,
                    "carries": 16.2,
                    "receiving_yards": 22.1,
                    "receptions": 2.8,
                }
            ]
        }
    }


class ReceiverPredictionResponse(BaseModel):
    """Response schema for WR and TE predictions."""

    receiving_yards: float = Field(..., description="Predicted receiving yards")
    receiving_tds: float = Field(..., description="Predicted receiving TDs")
    receptions: float = Field(..., description="Predicted receptions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"receiving_yards": 68.4, "receiving_tds": 0.5, "receptions": 5.2}
            ]
        }
    }
