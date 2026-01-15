"""
LineupIQ Prediction API.

FastAPI application for serving NFL player stat predictions.
All 13 trained ML models are loaded at startup and kept in memory for fast inference.

Endpoints:
- GET /health - Health check with model count

Example:
    >>> from lineupiq.api import app
    >>> app.title
    'LineupIQ API'
"""

from lineupiq.api.main import app

__all__ = ["app"]
