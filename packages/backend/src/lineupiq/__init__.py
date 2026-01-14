"""
LineupIQ - Fantasy Football Prediction ML Backend

This package provides machine learning models and data pipelines for predicting
individual NFL player statistics (passing yards, rushing yards, TDs, etc.) which
feed into configurable fantasy point calculations.

Core functionality:
- Data pipeline using nflreadpy for historical NFL data (1999-2025)
- Feature engineering for ML models (opponent strength, weather, rolling stats)
- ML models for skill position stat prediction (QB, RB, WR, TE)
- FastAPI endpoints for inference
"""

__version__ = "0.1.0"
