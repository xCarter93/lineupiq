"""
ML model training, tuning, and persistence utilities.

This module provides the training infrastructure for XGBoost models with:
- Optuna hyperparameter tuning
- TimeSeriesSplit validation (avoids temporal data leakage)
- Model persistence with joblib
- Position-specific training modules (QB, RB, WR, TE)

Submodules:
- training: Model training and hyperparameter tuning
- persistence: Model save/load utilities
- qb: QB-specific model training

Example:
    >>> from lineupiq.models import train_model, tune_hyperparameters
    >>> from lineupiq.models import save_model, load_model, list_models
    >>> from lineupiq.models import train_qb_models, QB_TARGETS
"""

from lineupiq.models.persistence import (
    list_models,
    load_model,
    save_model,
)
from lineupiq.models.qb import (
    QB_TARGETS,
    prepare_qb_data,
    train_qb_models,
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
    # QB Models
    "QB_TARGETS",
    "prepare_qb_data",
    "train_qb_models",
]
