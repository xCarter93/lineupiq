"""
Pydantic schemas for model explainability API.

Provides schemas for SHAP-based feature contribution explanations that help
users understand why a prediction is what it is.
"""

from pydantic import BaseModel, Field


# Feature display names for human-readable explanations (40 features - Phase 20+21)
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
    # Weather features (Phase 20)
    "temp_normalized": "Game Temperature",
    "wind_normalized": "Wind Conditions",
    "extreme_cold": "Extreme Cold (<25°F)",
    "freezing": "Freezing Temps (<32°F)",
    "extreme_heat": "Extreme Heat (>85°F)",
    "high_wind": "High Wind (≥15mph)",
    "very_high_wind": "Very High Wind (≥20mph)",
    "has_precip": "Precipitation",
    "precip_amount": "Precipitation Amount",
    # Matchup features (Phase 20)
    "home_spread": "Vegas Spread",
    "total_points": "Vegas Over/Under",
    "vegas_strength_diff": "Vegas Strength Differential",
    "home_favored": "Home Team Favored",
    "is_divisional": "Divisional Matchup",
    # Context features
    "is_home": "Home Field Advantage",
    "is_dome": "Indoor Stadium",
    # Game context features
    "days_since_last_game": "Rest Days",
    "is_post_bye": "Post-Bye Week",
    "implied_team_total": "Implied Team Total",
    "game_script_lean": "Game Script Lean",
    # Usage features
    "snap_pct_roll5": "Snap Percentage",
    "snap_pct_trend": "Snap % Trend",
    "target_share_roll5": "Target Share",
    "carry_share_roll5": "Carry Share",
    # EPA features
    "team_epa_roll5": "Team EPA/Play",
    "opp_def_epa_roll5": "Opponent Def EPA/Play",
    "player_epa_roll5": "Player EPA/Play",
    "team_pass_epa_vs_rush_epa": "Pass vs Rush EPA",
    # Multi-window rolling features
    "passing_yards_roll3": "Recent Passing Yards (3G)",
    "rushing_yards_roll3": "Recent Rushing Yards (3G)",
    "receiving_yards_roll3": "Recent Receiving Yards (3G)",
    "receptions_roll3": "Recent Receptions (3G)",
    "passing_yards_momentum": "Passing Momentum",
    "rushing_yards_momentum": "Rushing Momentum",
    "receiving_yards_momentum": "Receiving Momentum",
    "receptions_momentum": "Receptions Momentum",
    # Interaction features
    "rush_yards_x_opp_rush_def": "Rush Yards × Opp Rush Def",
    "pass_yards_x_opp_pass_def": "Pass Yards × Opp Pass Def",
    "recv_yards_x_opp_pass_def": "Recv Yards × Opp Pass Def",
    "player_volume_x_team_pace": "Volume × Team Pace",
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

    Contains all 40 features required for model inference (Phase 20+21), matching PredictionRequest.
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

    # Weather features (9 features - Phase 20)
    temp_normalized: float = Field(
        ..., description="Normalized temperature (0-1 scale)"
    )
    wind_normalized: float = Field(
        ..., description="Normalized wind speed (0-1 scale)"
    )
    extreme_cold: bool = Field(
        ..., description="Temperature below 25°F"
    )
    freezing: bool = Field(
        ..., description="Temperature below 32°F"
    )
    extreme_heat: bool = Field(
        ..., description="Temperature above 85°F"
    )
    high_wind: bool = Field(
        ..., description="Wind speed >= 15 mph"
    )
    very_high_wind: bool = Field(
        ..., description="Wind speed >= 20 mph"
    )
    has_precip: bool = Field(
        ..., description="Precipitation present"
    )
    precip_amount: float = Field(
        ..., description="Precipitation amount in inches"
    )

    # Matchup features (5 features - Phase 20)
    home_spread: float = Field(
        ..., description="Vegas spread (positive = home favored)"
    )
    total_points: float = Field(
        ..., description="Vegas over/under total"
    )
    vegas_strength_diff: float = Field(
        ..., description="Home implied total - opponent implied total"
    )
    home_favored: bool = Field(
        ..., description="Home team favored by Vegas"
    )
    is_divisional: bool = Field(
        ..., description="Divisional matchup"
    )

    # Context features (2 features)
    is_home: bool = Field(
        ..., description="Whether the player is playing at home"
    )
    is_dome: bool = Field(
        ..., description="Whether the game is in a dome/indoor stadium"
    )

    # Game context features (4 features)
    days_since_last_game: float = Field(
        ..., description="Days since team's last game"
    )
    is_post_bye: bool = Field(
        ..., description="Post-bye week game"
    )
    implied_team_total: float = Field(
        ..., description="Vegas-derived expected team scoring"
    )
    game_script_lean: float = Field(
        ..., description="Expected pass/rush lean from spread"
    )

    # Usage features (4 features)
    snap_pct_roll5: float = Field(
        ..., description="5-game rolling snap percentage"
    )
    snap_pct_trend: float = Field(
        ..., description="Snap percentage trend (roll3 - roll5)"
    )
    target_share_roll5: float = Field(
        ..., description="5-game rolling target share (WR/TE)"
    )
    carry_share_roll5: float = Field(
        ..., description="5-game rolling carry share (RB)"
    )

    # EPA features (4 features)
    team_epa_roll5: float = Field(
        ..., description="5-game rolling team offensive EPA per play"
    )
    opp_def_epa_roll5: float = Field(
        ..., description="5-game rolling opponent defensive EPA per play"
    )
    player_epa_roll5: float = Field(
        ..., description="5-game rolling player EPA per play"
    )
    team_pass_epa_vs_rush_epa: float = Field(
        ..., description="Team pass EPA minus rush EPA (pass lean)"
    )

    # Multi-window rolling features (8 features)
    passing_yards_roll3: float = Field(
        ..., description="3-game rolling average of passing yards"
    )
    rushing_yards_roll3: float = Field(
        ..., description="3-game rolling average of rushing yards"
    )
    receiving_yards_roll3: float = Field(
        ..., description="3-game rolling average of receiving yards"
    )
    receptions_roll3: float = Field(
        ..., description="3-game rolling average of receptions"
    )
    passing_yards_momentum: float = Field(
        ..., description="Passing yards momentum (roll3 - roll5)"
    )
    rushing_yards_momentum: float = Field(
        ..., description="Rushing yards momentum (roll3 - roll5)"
    )
    receiving_yards_momentum: float = Field(
        ..., description="Receiving yards momentum (roll3 - roll5)"
    )
    receptions_momentum: float = Field(
        ..., description="Receptions momentum (roll3 - roll5)"
    )

    # Interaction features (4 features)
    rush_yards_x_opp_rush_def: float = Field(
        ..., description="Rushing yards × opponent rush defense"
    )
    pass_yards_x_opp_pass_def: float = Field(
        ..., description="Passing yards × opponent pass defense"
    )
    recv_yards_x_opp_pass_def: float = Field(
        ..., description="Receiving yards × opponent pass defense"
    )
    player_volume_x_team_pace: float = Field(
        ..., description="Player volume × team pace"
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
                    "temp_normalized": 0.5,
                    "wind_normalized": 0.2,
                    "extreme_cold": False,
                    "freezing": False,
                    "extreme_heat": False,
                    "high_wind": False,
                    "very_high_wind": False,
                    "has_precip": False,
                    "precip_amount": 0.0,
                    "home_spread": 3.5,
                    "total_points": 47.5,
                    "vegas_strength_diff": 3.5,
                    "home_favored": True,
                    "is_divisional": False,
                    "is_home": True,
                    "is_dome": False,
                    "days_since_last_game": 7.0,
                    "is_post_bye": False,
                    "implied_team_total": 24.0,
                    "game_script_lean": 0.0,
                    "snap_pct_roll5": 0.95,
                    "snap_pct_trend": 0.0,
                    "target_share_roll5": 0.0,
                    "carry_share_roll5": 0.0,
                    "team_epa_roll5": 0.05,
                    "opp_def_epa_roll5": 0.0,
                    "player_epa_roll5": 0.1,
                    "team_pass_epa_vs_rush_epa": 0.05,
                    "passing_yards_roll3": 285.0,
                    "rushing_yards_roll3": 22.0,
                    "receiving_yards_roll3": 0.0,
                    "receptions_roll3": 0.0,
                    "passing_yards_momentum": 5.0,
                    "rushing_yards_momentum": 2.0,
                    "receiving_yards_momentum": 0.0,
                    "receptions_momentum": 0.0,
                    "rush_yards_x_opp_rush_def": 10.0,
                    "pass_yards_x_opp_pass_def": 140.0,
                    "recv_yards_x_opp_pass_def": 0.0,
                    "player_volume_x_team_pace": 195.0,
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
