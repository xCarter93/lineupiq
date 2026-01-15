"""
Kicker model training for fantasy football predictions.

Trains models to predict:
- fg_att: Total FG attempts
- fg_att_0_39: Short FG attempts (high value, high accuracy)
- fg_att_40_49: Medium FG attempts (medium value)
- fg_att_50_plus: Long FG attempts (high value, lower accuracy)
- pat_att: Extra point attempts
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from lightgbm import LGBMRegressor
from numpy.typing import NDArray

from lineupiq.data.kicker_processing import (
    get_kicker_feature_columns,
    get_kicker_target_columns,
    process_kicker_data,
)
from lineupiq.models.persistence import save_model
from lineupiq.models.training import ModelType, train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# Training seasons (excluding 2025 holdout)
TRAINING_SEASONS = [2021, 2022, 2023, 2024]

# Target columns for kicker models
KICKER_TARGETS = get_kicker_target_columns()


def train_kicker_models(
    n_trials: int = 30,
    model_type: ModelType = "lightgbm",
) -> dict[str, Path]:
    """Train all kicker prediction models.

    Args:
        n_trials: Number of Optuna trials per model.
        model_type: "lightgbm" or "xgboost".

    Returns:
        Dict mapping target names to saved model paths.
    """
    logger.info("Training kicker models")

    # Load and process kicker data
    df = process_kicker_data(TRAINING_SEASONS)

    feature_cols = get_kicker_feature_columns()
    target_cols = get_kicker_target_columns()

    # Verify feature columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    # Prepare feature matrix
    X: NDArray[np.floating[Any]] = df.select(feature_cols).to_numpy().astype(np.float64)

    saved_models: dict[str, Path] = {}

    for target in target_cols:
        if target not in df.columns:
            logger.warning(f"Target column {target} not found, skipping")
            continue

        logger.info(f"Training K_{target} model")

        y: NDArray[np.floating[Any]] = (
            df.select(target).to_numpy().flatten().astype(np.float64)
        )

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

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -scores
        metadata: dict[str, Any] = {
            "position": "K",
            "target": target,
            "model_type": model_type,
            "n_samples": len(y_valid),
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "feature_columns": feature_cols,
            "seasons": TRAINING_SEASONS,
        }

        # save_model expects XGBRegressor but we're passing LGBMRegressor
        # The persistence module handles both since they have compatible interfaces
        model_path = save_model(model, "K", target, metadata)  # type: ignore[arg-type]
        saved_models[target] = model_path

        logger.info(f"Saved K_{target} model: CV RMSE = {cv_rmse.mean():.4f}")

    return saved_models


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_kicker_models()
