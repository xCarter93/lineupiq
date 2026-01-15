"""
ML model training, tuning, persistence, and evaluation utilities.

This module provides the training infrastructure for XGBoost models with:
- Optuna hyperparameter tuning
- TimeSeriesSplit validation (avoids temporal data leakage)
- Model persistence with joblib
- Position-specific training modules (QB, RB, WR, TE)
- Model evaluation with standard regression metrics
- Model diagnostics and overfitting detection

Submodules:
- training: Model training and hyperparameter tuning
- persistence: Model save/load utilities
- evaluation: Model evaluation metrics and holdout validation
- qb: QB-specific model training
- rb: RB-specific model training
- receiver: WR and TE model training

Example:
    >>> from lineupiq.models import train_model, tune_hyperparameters
    >>> from lineupiq.models import save_model, load_model, list_models
    >>> from lineupiq.models import train_qb_models, QB_TARGETS
    >>> from lineupiq.models import train_rb_models, RB_TARGETS
    >>> from lineupiq.models import train_wr_models, train_te_models, RECEIVER_TARGETS
    >>> from lineupiq.models import evaluate_model, evaluate_all_models
"""

from lineupiq.models.evaluation import (
    calculate_metrics,
    create_holdout_split,
    evaluate_all_models,
    evaluate_model,
)
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
from lineupiq.models.rb import (
    RB_TARGETS,
    prepare_rb_data,
    train_rb_models,
)
from lineupiq.models.receiver import (
    RECEIVER_TARGETS,
    prepare_receiver_data,
    train_te_models,
    train_wr_models,
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
    # Evaluation
    "calculate_metrics",
    "create_holdout_split",
    "evaluate_model",
    "evaluate_all_models",
    # QB Models
    "QB_TARGETS",
    "prepare_qb_data",
    "train_qb_models",
    # RB Models
    "RB_TARGETS",
    "prepare_rb_data",
    "train_rb_models",
    # Receiver Models (WR/TE)
    "RECEIVER_TARGETS",
    "prepare_receiver_data",
    "train_wr_models",
    "train_te_models",
]
