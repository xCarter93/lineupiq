"""
Team defense model training for fantasy football predictions.

Trains models to predict team-level defensive stats:
- points_allowed: Points given up to opponent
- sacks: Quarterback sacks
- interceptions: Interceptions
- fumbles_forced: Fumble recoveries
- total_def_tds: Defensive + special teams touchdowns
"""

import logging
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from lineupiq.data.defense_processing import (
    get_defense_feature_columns,
    get_defense_target_columns,
    process_defense_data,
)
from lineupiq.models.persistence import save_model
from lineupiq.models.training import ModelType, train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# Training seasons (excluding 2025 holdout)
TRAINING_SEASONS = [2021, 2022, 2023, 2024]

# Target columns for defense models
DEF_TARGETS = [
    "points_allowed",
    "sacks",
    "interceptions",
    "fumbles_forced",
    "total_def_tds",
]


def train_defense_models(
    n_trials: int = 30,
    model_type: ModelType = "lightgbm",
) -> dict[str, Path]:
    """Train all team defense prediction models.

    Args:
        n_trials: Number of Optuna trials per model.
        model_type: "lightgbm" or "xgboost".

    Returns:
        Dict mapping target names to saved model paths.
    """
    logger.info("Training defense models")

    # Load and process defense data
    df = process_defense_data(TRAINING_SEASONS)

    feature_cols = get_defense_feature_columns()
    target_cols = get_defense_target_columns()

    # Verify feature columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    # Prepare feature matrix
    X: NDArray[np.floating] = df.select(feature_cols).to_numpy()

    saved_models: dict[str, Path] = {}

    for target in target_cols:
        if target not in df.columns:
            logger.warning(f"Target column {target} not found, skipping")
            continue

        logger.info(f"Training DEF_{target} model")

        y: NDArray[np.floating] = df.select(target).to_numpy().flatten()

        # Remove rows with null targets
        valid_mask = ~np.isnan(y)
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]

        if len(y_valid) < 100:
            logger.warning(f"Insufficient data for {target}: {len(y_valid)} samples")
            continue

        # Tune hyperparameters
        best_params, _ = tune_hyperparameters(
            X_valid,
            y_valid,
            n_trials=n_trials,
            model_type=model_type,
        )

        # Train final model
        model, scores = train_model(
            X_valid,
            y_valid,
            params=best_params,
            model_type=model_type,
        )

        # Save model
        metadata = {
            "position": "DEF",
            "target": target,
            "model_type": model_type,
            "n_samples": len(y_valid),
            "cv_score": float(scores.mean()),
            "feature_columns": feature_cols,
        }

        model_path = save_model(model, "DEF", target, metadata)
        saved_models[target] = model_path

        logger.info(f"Saved DEF_{target} model: CV score = {scores.mean():.4f}")

    return saved_models


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_defense_models()
