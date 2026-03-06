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
from lineupiq.models.persistence import get_save_target, save_model
from lineupiq.models.training import ModelType, fit_conformal, train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# Default training seasons (excluding 2025 holdout)
DEFAULT_TRAINING_SEASONS = [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]

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
    target_season: int | None = None,
    include_weeks: list[int] | None = None,
) -> dict[str, Tuple[Any, dict[str, Any]]]:
    """Train all team defense prediction models.

    Args:
        seasons: List of seasons to train on (default: 2022-2025).
        n_trials: Number of Optuna trials per model.
        model_type: "lightgbm" or "xgboost".
        target_season: Season to filter for partial week training (simulation mode).
        include_weeks: Weeks to include from target_season (simulation mode).

    Returns:
        Dict mapping target names to (model, metrics) tuples.
    """
    if seasons is None:
        seasons = DEFAULT_TRAINING_SEASONS

    logger.info("Training defense models")

    # Load and process defense data
    df = process_defense_data(
        seasons,
        target_season=target_season,
        include_weeks=include_weeks,
    )

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
        season_array = df.select("season").to_numpy().flatten().astype(np.int64)

        # Remove rows with null targets
        valid_mask = ~np.isnan(y)
        X_valid = X[valid_mask]
        y_valid = y[valid_mask]
        season_valid = season_array[valid_mask]

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
            season_array=season_valid,
        )

        # Train final model
        model, scores = train_model(
            X_valid,
            y_valid,
            params=best_params,
            model_type=model_type,
            season_array=season_valid,
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

        # Fit conformal prediction intervals (MAPIE) - only for LightGBM (expensive 5-fold CV)
        mapie_model = fit_conformal(model, X_valid, y_valid) if model_type == "lightgbm" else None

        # Save model with correct suffix for model type
        save_target = get_save_target(target, model_type)
        model_path = save_model(model, "DEF", save_target, metadata, mapie_model=mapie_model)
        trained_models[target] = (model, metadata)

        logger.info(f"Saved DEF_{target} model: CV RMSE = {cv_rmse.mean():.4f}")

    return trained_models


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_defense_models()
