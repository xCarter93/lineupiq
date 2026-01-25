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
from typing import Any, Tuple

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

# Default training seasons (excluding 2025 holdout)
DEFAULT_TRAINING_SEASONS = [2022, 2023, 2024, 2025]

# Target columns for defense models
DEF_TARGETS = [
    "points_allowed",
    "def_sacks",
    "def_interceptions",
    "def_fumbles",
    "total_def_tds",
]


def train_defense_models(
    seasons: list[int] | None = None,
    n_trials: int = 30,
    model_type: ModelType = "lightgbm",
) -> dict[str, Tuple[Any, dict[str, Any]]]:
    """Train all team defense prediction models.

    Args:
        seasons: List of seasons to train on (default: 2022-2025).
        n_trials: Number of Optuna trials per model.
        model_type: "lightgbm" or "xgboost".

    Returns:
        Dict mapping target names to (model, metrics) tuples.
    """
    if seasons is None:
        seasons = DEFAULT_TRAINING_SEASONS

    logger.info("Training defense models")

    # Load and process defense data
    df = process_defense_data(seasons)

    feature_cols = get_defense_feature_columns()
    target_cols = get_defense_target_columns()

    # Verify feature columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    # Prepare feature matrix
    X: NDArray[np.floating] = df.select(feature_cols).to_numpy()

    trained_models: dict[str, Tuple[Any, dict[str, Any]]] = {}

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

        # Tune hyperparameters (uses Poisson for count targets)
        best_params, _ = tune_hyperparameters(
            X_valid,
            y_valid,
            n_trials=n_trials,
            model_type=model_type,
            target=target,
        )

        # Train final model
        model, scores = train_model(
            X_valid,
            y_valid,
            params=best_params,
            model_type=model_type,
        )

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -scores

        # Save model
        metadata = {
            "position": "DEF",
            "target": target,
            "model_type": model_type,
            "n_samples": len(y_valid),
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "feature_columns": feature_cols,
            "seasons": seasons,
        }

        model_path = save_model(model, "DEF", target, metadata)
        trained_models[target] = (model, metadata)

        logger.info(f"Saved DEF_{target} model: CV RMSE = {cv_rmse.mean():.4f}")

    return trained_models


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_defense_models()
