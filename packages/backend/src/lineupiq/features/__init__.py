"""
LineupIQ Features Module - Feature engineering for ML model consumption.

This module provides feature computation utilities for building ML-ready
datasets from processed player stats.

Public API:
    Rolling Statistics:
        compute_rolling_stats: Compute rolling window averages for player stats

    Opponent Features:
        add_opponent_strength: Add opponent defensive strength features to player data
        compute_defensive_stats: Aggregate stats allowed by each defense
        compute_defensive_rankings: Compute season-to-date defensive rankings
"""

from lineupiq.features.opponent_features import (
    add_opponent_strength,
    compute_defensive_rankings,
    compute_defensive_stats,
)
from lineupiq.features.rolling_stats import compute_rolling_stats

__all__ = [
    # Rolling Statistics
    "compute_rolling_stats",
    # Opponent Features
    "add_opponent_strength",
    "compute_defensive_stats",
    "compute_defensive_rankings",
]
