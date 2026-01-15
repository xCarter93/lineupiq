"""
ML model training, tuning, and persistence utilities.

This module provides the training infrastructure for XGBoost models with:
- Optuna hyperparameter tuning
- TimeSeriesSplit validation (avoids temporal data leakage)
- Model persistence with joblib

Submodules:
- training: Model training and hyperparameter tuning
- persistence: Model save/load utilities

Example:
    >>> from lineupiq.models import train_model, tune_hyperparameters
    >>> from lineupiq.models import save_model, load_model, list_models
"""

from lineupiq.models.persistence import (
    list_models,
    load_model,
    save_model,
)
from lineupiq.models.training import (
    create_study,
    get_xgb_params,
    train_model,
    tune_hyperparameters,
)

__all__ = [
    # Training
    "create_study",
    "get_xgb_params",
    "train_model",
    "tune_hyperparameters",
    # Persistence
    "save_model",
    "load_model",
    "list_models",
]
