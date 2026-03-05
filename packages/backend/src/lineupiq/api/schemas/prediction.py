"""
Pydantic schemas for prediction requests and responses.

All feature fields match the output of lineupiq.features.get_feature_columns()
to ensure consistency between training and inference.
"""

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Base request schema for all position predictions.

    Contains all 40 feature fields required for model inference (Phase 20+21).
    Features are organized into rolling stats, opponent strength,
    team strength, volatility, weather, matchup, and context categories.
    """

    # Rolling stats (8 features)
    passing_yards_roll5: float = Field(
        ..., description="5-week rolling average of passing yards"
    )
    passing_tds_roll5: float = Field(
        ..., description="5-week rolling average of passing TDs"
    )
    rushing_yards_roll5: float = Field(
        ..., description="5-week rolling average of rushing yards"
    )
    rushing_tds_roll5: float = Field(
        ..., description="5-week rolling average of rushing TDs"
    )
    carries_roll5: float = Field(
        ..., description="5-week rolling average of carries"
    )
    receiving_yards_roll5: float = Field(
        ..., description="5-week rolling average of receiving yards"
    )
    receiving_tds_roll5: float = Field(
        ..., description="5-week rolling average of receiving TDs"
    )
    receptions_roll5: float = Field(
        ..., description="5-week rolling average of receptions"
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
        ..., description="5-week rolling average of team points scored"
    )
    team_yards_roll5: float = Field(
        ..., description="5-week rolling average of team total yards"
    )
    team_plays_roll5: float = Field(
        ..., description="5-week rolling average of team plays (pace)"
    )

    # Volatility features (8 features)
    passing_yards_std5: float = Field(
        ..., description="5-week standard deviation of passing yards"
    )
    passing_yards_cv5: float = Field(
        ..., description="5-week coefficient of variation of passing yards"
    )
    rushing_yards_std5: float = Field(
        ..., description="5-week standard deviation of rushing yards"
    )
    rushing_yards_cv5: float = Field(
        ..., description="5-week coefficient of variation of rushing yards"
    )
    receiving_yards_std5: float = Field(
        ..., description="5-week standard deviation of receiving yards"
    )
    receiving_yards_cv5: float = Field(
        ..., description="5-week coefficient of variation of receiving yards"
    )
    receptions_std5: float = Field(
        ..., description="5-week standard deviation of receptions"
    )
    receptions_cv5: float = Field(
        ..., description="5-week coefficient of variation of receptions"
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
                    "passing_yards_roll5": 250.5,
                    "passing_tds_roll5": 1.8,
                    "rushing_yards_roll5": 15.0,
                    "rushing_tds_roll5": 0.2,
                    "carries_roll5": 3.0,
                    "receiving_yards_roll5": 0.0,
                    "receiving_tds_roll5": 0.0,
                    "receptions_roll5": 0.0,
                    "opp_pass_defense_strength": 0.95,
                    "opp_rush_defense_strength": 1.05,
                    "opp_pass_yards_allowed_rank": 15.0,
                    "opp_rush_yards_allowed_rank": 20.0,
                    "opp_total_yards_allowed_rank": 18.0,
                    "team_points_roll5": 24.5,
                    "team_yards_roll5": 350.0,
                    "team_plays_roll5": 65.0,
                    "passing_yards_std5": 50.0,
                    "passing_yards_cv5": 0.2,
                    "rushing_yards_std5": 25.0,
                    "rushing_yards_cv5": 0.3,
                    "receiving_yards_std5": 0.0,
                    "receiving_yards_cv5": 0.0,
                    "receptions_std5": 0.0,
                    "receptions_cv5": 0.0,
                    "temp_normalized": 0.6,
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
                    "passing_yards_roll3": 260.0,
                    "rushing_yards_roll3": 18.0,
                    "receiving_yards_roll3": 0.0,
                    "receptions_roll3": 0.0,
                    "passing_yards_momentum": 9.5,
                    "rushing_yards_momentum": 3.0,
                    "receiving_yards_momentum": 0.0,
                    "receptions_momentum": 0.0,
                    "rush_yards_x_opp_rush_def": 7.5,
                    "pass_yards_x_opp_pass_def": 125.0,
                    "recv_yards_x_opp_pass_def": 0.0,
                    "player_volume_x_team_pace": 195.0,
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

    fg_att_roll5: float = Field(
        ..., description="5-week rolling average of FG attempts"
    )
    pat_att_roll5: float = Field(
        ..., description="5-week rolling average of PAT attempts"
    )
    fg_pct_roll5: float = Field(
        ..., description="5-week rolling average of FG percentage"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fg_att_roll5": 2.5,
                    "pat_att_roll5": 3.2,
                    "fg_pct_roll5": 0.85,
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

    points_allowed_roll5: float = Field(
        ..., description="5-week rolling average of points allowed"
    )
    def_sacks_roll5: float = Field(
        ..., description="5-week rolling average of sacks"
    )
    def_ints_roll5: float = Field(
        ..., description="5-week rolling average of interceptions"
    )
    def_fumbles_roll5: float = Field(
        ..., description="5-week rolling average of fumble recoveries"
    )
    def_tds_roll5: float = Field(
        ..., description="5-week rolling average of defensive/ST touchdowns"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "points_allowed_roll5": 21.3,
                    "def_sacks_roll5": 2.5,
                    "def_ints_roll5": 1.2,
                    "def_fumbles_roll5": 0.8,
                    "def_tds_roll5": 0.3,
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


class PlayerFeaturesResponse(BaseModel):
    """Player-specific features for prediction.

    Returns computed feature values based on a player's historical performance,
    ready to be used as input to the prediction models.
    """

    player_id: str = Field(..., description="Player's gsis_id")
    player_name: str = Field(..., description="Player's full name")
    position: str = Field(..., description="Player position (QB, RB, WR, TE)")
    team: str = Field(..., description="Player's current team abbreviation")
    games_available: int = Field(
        ..., description="Number of recent games used for rolling stats"
    )
    features: dict[str, float | bool] = Field(
        ..., description="The 28 feature values for model input"
    )
    has_sufficient_data: bool = Field(
        ..., description="True if player has >= 5 games for reliable rolling stats"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "player_id": "00-0036389",
                    "player_name": "Jalen Hurts",
                    "position": "QB",
                    "team": "PHI",
                    "games_available": 17,
                    "has_sufficient_data": True,
                    "features": {
                        "passing_yards_roll5": 245.7,
                        "passing_tds_roll5": 1.7,
                        "rushing_yards_roll5": 42.3,
                        "rushing_tds_roll5": 0.7,
                        "carries_roll5": 8.3,
                        "receiving_yards_roll5": 0.0,
                        "receiving_tds_roll5": 0.0,
                        "receptions_roll5": 0.0,
                        "opp_pass_defense_strength": 0.5,
                        "opp_rush_defense_strength": 0.6,
                        "opp_pass_yards_allowed_rank": 16.0,
                        "opp_rush_yards_allowed_rank": 18.0,
                        "opp_total_yards_allowed_rank": 17.0,
                        "team_points_roll5": 28.5,
                        "team_yards_roll5": 365.0,
                        "team_plays_roll5": 68.0,
                        "passing_yards_std5": 45.2,
                        "passing_yards_cv5": 0.18,
                        "rushing_yards_std5": 22.1,
                        "rushing_yards_cv5": 0.52,
                        "receiving_yards_std5": 0.0,
                        "receiving_yards_cv5": 0.0,
                        "receptions_std5": 0.0,
                        "receptions_cv5": 0.0,
                        "temp_normalized": 0.5,
                        "wind_normalized": 0.2,
                        "is_home": True,
                        "is_dome": False,
                    },
                }
            ]
        }
    }
