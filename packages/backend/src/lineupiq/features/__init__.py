"""
LineupIQ Features Module - Feature engineering for ML model consumption.

This module provides feature computation utilities for building ML-ready
datasets from processed player stats.

Public API:
    Pipeline (Main Entry Point):
        build_features: Build complete ML-ready feature dataset
        get_feature_columns: Get list of feature column names
        get_target_columns: Get position-specific target columns
        save_features: Save features to Parquet file

    Rolling Statistics:
        compute_rolling_stats: Compute rolling window averages for player stats
        compute_volatility_features: Compute std/CV for boom/bust identification
        get_volatility_columns: Get volatility column names

    Opponent Features:
        add_opponent_strength: Add opponent defensive strength features to player data
        compute_defensive_stats: Aggregate stats allowed by each defense
        compute_defensive_rankings: Compute season-to-date defensive rankings

    Team Strength Features:
        compute_team_strength: Compute team offensive strength metrics
        get_team_strength_columns: Get team strength column names
"""

from lineupiq.features.opponent_features import (
    add_opponent_strength,
    compute_defensive_rankings,
    compute_defensive_stats,
)
from lineupiq.features.pipeline import (
    build_features,
    get_feature_columns,
    get_target_columns,
    save_features,
)
from lineupiq.features.rolling_stats import (
    compute_rolling_stats,
    compute_volatility_features,
    get_volatility_columns,
)
from lineupiq.features.team_strength import (
    compute_team_strength,
    get_team_strength_columns,
)

__all__ = [
    # Pipeline (Main Entry Point)
    "build_features",
    "get_feature_columns",
    "get_target_columns",
    "save_features",
    # Rolling Statistics
    "compute_rolling_stats",
    "compute_volatility_features",
    "get_volatility_columns",
    # Opponent Features
    "add_opponent_strength",
    "compute_defensive_stats",
    "compute_defensive_rankings",
    # Team Strength Features
    "compute_team_strength",
    "get_team_strength_columns",
]
