"""
LineupIQ Features Module - Feature engineering for ML model consumption.

This module provides feature computation utilities for building ML-ready
datasets from processed player stats.

Public API:
    Rolling Statistics:
        compute_rolling_stats: Compute rolling window averages for player stats
"""

from lineupiq.features.rolling_stats import compute_rolling_stats

__all__ = [
    "compute_rolling_stats",
]
