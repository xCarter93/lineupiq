"""
Pydantic schemas for model explainability API.

Provides schemas for SHAP-based feature contribution explanations that help
users understand why a prediction is what it is.
"""

from pydantic import BaseModel, Field


# Feature display names for human-readable explanations
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    # Rolling stats
    "passing_yards_roll5": "Recent Passing Yards",
    "passing_tds_roll5": "Recent Passing TDs",
    "rushing_yards_roll5": "Recent Rushing Yards",
    "rushing_tds_roll5": "Recent Rushing TDs",
    "carries_roll5": "Recent Carries",
    "receiving_yards_roll5": "Recent Receiving Yards",
    "receiving_tds_roll5": "Recent Receiving TDs",
    "receptions_roll5": "Recent Receptions",
    # Opponent features
    "opp_pass_defense_strength": "Opponent Pass Defense",
    "opp_rush_defense_strength": "Opponent Rush Defense",
    "opp_pass_yards_allowed_rank": "Opponent Pass Defense Rank",
    "opp_rush_yards_allowed_rank": "Opponent Rush Defense Rank",
    "opp_total_yards_allowed_rank": "Opponent Total Defense Rank",
    # Weather features
    "temp_normalized": "Game Temperature",
    "wind_normalized": "Wind Conditions",
    # Team strength features
    "team_points_roll5": "Team Recent Scoring",
    "team_yards_roll5": "Team Recent Yardage",
    "team_plays_roll5": "Team Pace",
    # Volatility features
    "passing_yards_std5": "Passing Volatility",
    "passing_yards_cv5": "Passing Consistency",
    "rushing_yards_std5": "Rushing Volatility",
    "rushing_yards_cv5": "Rushing Consistency",
    "receiving_yards_std5": "Receiving Volatility",
    "receiving_yards_cv5": "Receiving Consistency",
    "receptions_std5": "Receptions Volatility",
    "receptions_cv5": "Receptions Consistency",
    # Context features
    "is_home": "Home Field Advantage",
    "is_dome": "Indoor Stadium",
}

# Target display names for natural language summaries
TARGET_DISPLAY_NAMES: dict[str, str] = {
    "passing_yards": "passing yards",
    "passing_tds": "passing TDs",
    "interceptions": "interceptions",
    "rushing_yards": "rushing yards",
    "rushing_tds": "rushing TDs",
    "carries": "carries",
    "receiving_yards": "receiving yards",
    "receiving_tds": "receiving TDs",
    "receptions": "receptions",
    "fumbles_lost": "fumbles lost",
}

# Valid targets by position
VALID_TARGETS: dict[str, list[str]] = {
    "QB": ["passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "fumbles_lost"],
    "RB": ["rushing_yards", "rushing_tds", "carries", "receiving_yards", "receptions", "receiving_tds", "fumbles_lost"],
    "WR": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
    "TE": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
}


class FeatureContribution(BaseModel):
    """A single feature's contribution to the prediction."""

    feature: str = Field(..., description="Raw feature name")
    display_name: str = Field(..., description="Human-readable feature name")
    value: float = Field(..., description="The feature value used in prediction")
    contribution: float = Field(..., description="SHAP value (positive or negative)")
    direction: str = Field(..., description="Impact direction: 'up' or 'down'")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "feature": "passing_yards_roll5",
                    "display_name": "Recent Passing Yards",
                    "value": 280.5,
                    "contribution": 15.3,
                    "direction": "up",
                }
            ]
        }
    }


class ExplainabilityRequest(BaseModel):
    """Request schema for explainability endpoint.

    Contains all 28 features required for model inference, matching PredictionRequest.
    """

    # Rolling stats (8 features)
    passing_yards_roll5: float = Field(
        ..., description="3-week rolling average of passing yards"
    )
    passing_tds_roll5: float = Field(
        ..., description="3-week rolling average of passing TDs"
    )
    rushing_yards_roll5: float = Field(
        ..., description="3-week rolling average of rushing yards"
    )
    rushing_tds_roll5: float = Field(
        ..., description="3-week rolling average of rushing TDs"
    )
    carries_roll5: float = Field(
        ..., description="3-week rolling average of carries"
    )
    receiving_yards_roll5: float = Field(
        ..., description="3-week rolling average of receiving yards"
    )
    receiving_tds_roll5: float = Field(
        ..., description="3-week rolling average of receiving TDs"
    )
    receptions_roll5: float = Field(
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
    team_points_roll5: float = Field(
        ..., description="3-week rolling average of team points scored"
    )
    team_yards_roll5: float = Field(
        ..., description="3-week rolling average of team total yards"
    )
    team_plays_roll5: float = Field(
        ..., description="3-week rolling average of team plays (pace)"
    )

    # Volatility features (8 features)
    passing_yards_std5: float = Field(
        ..., description="3-week standard deviation of passing yards"
    )
    passing_yards_cv5: float = Field(
        ..., description="3-week coefficient of variation of passing yards"
    )
    rushing_yards_std5: float = Field(
        ..., description="3-week standard deviation of rushing yards"
    )
    rushing_yards_cv5: float = Field(
        ..., description="3-week coefficient of variation of rushing yards"
    )
    receiving_yards_std5: float = Field(
        ..., description="3-week standard deviation of receiving yards"
    )
    receiving_yards_cv5: float = Field(
        ..., description="3-week coefficient of variation of receiving yards"
    )
    receptions_std5: float = Field(
        ..., description="3-week standard deviation of receptions"
    )
    receptions_cv5: float = Field(
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
                    "passing_yards_roll5": 280.0,
                    "passing_tds_roll5": 2.0,
                    "rushing_yards_roll5": 20.0,
                    "rushing_tds_roll5": 0.3,
                    "carries_roll5": 3.0,
                    "receiving_yards_roll5": 0.0,
                    "receiving_tds_roll5": 0.0,
                    "receptions_roll5": 0.0,
                    "opp_pass_defense_strength": 0.5,
                    "opp_rush_defense_strength": 0.5,
                    "opp_pass_yards_allowed_rank": 16.0,
                    "opp_rush_yards_allowed_rank": 16.0,
                    "opp_total_yards_allowed_rank": 16.0,
                    "temp_normalized": 0.5,
                    "wind_normalized": 0.2,
                    "team_points_roll5": 24.0,
                    "team_yards_roll5": 350.0,
                    "team_plays_roll5": 65.0,
                    "passing_yards_std5": 40.0,
                    "passing_yards_cv5": 0.15,
                    "rushing_yards_std5": 10.0,
                    "rushing_yards_cv5": 0.3,
                    "receiving_yards_std5": 0.0,
                    "receiving_yards_cv5": 0.0,
                    "receptions_std5": 0.0,
                    "receptions_cv5": 0.0,
                    "is_home": True,
                    "is_dome": False,
                }
            ]
        }
    }


class ExplainabilityResponse(BaseModel):
    """Response schema for explainability endpoint.

    Contains the prediction, base value, feature contributions, and a
    natural language summary explaining the prediction.
    """

    position: str = Field(..., description="Player position (QB, RB, WR, TE)")
    target: str = Field(..., description="Target stat being predicted")
    prediction: float = Field(..., description="The predicted value")
    base_value: float = Field(..., description="Expected value without features (SHAP base)")
    contributions: list[FeatureContribution] = Field(
        ..., description="Feature contributions sorted by absolute impact"
    )
    summary: str = Field(..., description="Natural language explanation of prediction")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "position": "QB",
                    "target": "passing_yards",
                    "prediction": 298.5,
                    "base_value": 245.2,
                    "contributions": [
                        {
                            "feature": "passing_yards_roll5",
                            "display_name": "Recent Passing Yards",
                            "value": 280.0,
                            "contribution": 25.3,
                            "direction": "up",
                        },
                        {
                            "feature": "opp_pass_defense_strength",
                            "display_name": "Opponent Pass Defense",
                            "value": 0.4,
                            "contribution": 18.5,
                            "direction": "up",
                        },
                        {
                            "feature": "is_home",
                            "display_name": "Home Field Advantage",
                            "value": 1.0,
                            "contribution": 8.2,
                            "direction": "up",
                        },
                    ],
                    "summary": "Projected 299 passing yards - boosted by recent strong performances and weak opponent pass defense.",
                }
            ]
        }
    }
