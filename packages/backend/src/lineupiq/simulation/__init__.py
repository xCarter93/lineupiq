"""
Season simulation module for backtesting predictions.

Provides tools to simulate an NFL season week-by-week, generating predictions
with incrementally trained models to validate the prediction system.

Main components:
- state: Simulation state management (file-based and Convex sync)
- features: Feature generation for future weeks using partial data
- batch_predict: Batch prediction generation for all players
"""

from lineupiq.simulation.state import SimulationState, load_state, save_state
from lineupiq.simulation.features import generate_week_features
from lineupiq.simulation.batch_predict import generate_batch_predictions

__all__ = [
    "SimulationState",
    "load_state",
    "save_state",
    "generate_week_features",
    "generate_batch_predictions",
]
