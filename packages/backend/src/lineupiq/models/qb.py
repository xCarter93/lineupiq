"""
QB-specific model training module.

Provides functions for training XGBoost models on quarterback stats:
- passing_yards: Total passing yards per game
- passing_tds: Number of passing touchdowns per game

Uses Optuna hyperparameter tuning and TimeSeriesSplit validation
to create accurate prediction models.

Key functions:
- prepare_qb_data: Filter and prepare QB-specific features/targets
- train_qb_models: Train and persist models for all QB targets
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray
from xgboost import XGBRegressor

from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.persistence import save_model
from lineupiq.models.training import train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# Target columns for QB predictions
QB_TARGETS = ["passing_yards", "passing_tds"]


def prepare_qb_data(
    df: pl.DataFrame,
) -> tuple[NDArray[np.floating[Any]], dict[str, NDArray[np.floating[Any]]]]:
    """Filter and prepare QB-specific data for model training.

    Filters the feature DataFrame to only QB rows, drops rows with missing
    values in features or targets, and returns numpy arrays ready for training.

    Args:
        df: Feature DataFrame from build_features().

    Returns:
        Tuple of (X, y_dict) where:
        - X: Feature matrix of shape (n_samples, n_features)
        - y_dict: Dict mapping target name to target array

    Example:
        >>> df = build_features([2024])
        >>> X, y_dict = prepare_qb_data(df)
        >>> "passing_yards" in y_dict
        True
    """
    # Filter to QB position only
    qb_df = df.filter(pl.col("position") == "QB")
    logger.info(f"Filtered to {len(qb_df)} QB rows from {len(df)} total")

    # Get feature columns
    feature_cols = get_feature_columns()

    # Verify all required columns exist
    missing_features = [c for c in feature_cols if c not in qb_df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    missing_targets = [c for c in QB_TARGETS if c not in qb_df.columns]
    if missing_targets:
        raise ValueError(f"Missing target columns: {missing_targets}")

    # Drop rows with any null values in features or targets
    all_required_cols = feature_cols + QB_TARGETS
    qb_df = qb_df.drop_nulls(subset=all_required_cols)
    logger.info(f"After dropping nulls: {len(qb_df)} rows")

    # Extract features as numpy array
    X = qb_df.select(feature_cols).to_numpy().astype(np.float64)

    # Extract targets as dict of numpy arrays
    y_dict = {}
    for target in QB_TARGETS:
        y_dict[target] = qb_df.select(target).to_numpy().flatten().astype(np.float64)

    logger.info(f"Prepared data: X shape {X.shape}, targets: {list(y_dict.keys())}")

    return X, y_dict


def train_qb_models(
    seasons: list[int],
    n_trials: int = 50,
) -> dict[str, tuple[XGBRegressor, dict[str, Any]]]:
    """Train and persist QB models for all target stats.

    Loads features for specified seasons, prepares QB data, then for each
    target stat:
    1. Runs Optuna hyperparameter tuning
    2. Trains final model with best parameters
    3. Saves model with metadata

    Args:
        seasons: List of seasons to train on (e.g., [2021, 2022, 2023, 2024]).
        n_trials: Number of Optuna trials for hyperparameter tuning (default: 50).

    Returns:
        Dict mapping target name to (model, metrics) tuple where metrics contains:
        - cv_rmse_mean: Mean cross-validation RMSE
        - cv_rmse_std: Standard deviation of CV RMSE
        - best_params: Best hyperparameters from Optuna
        - n_samples: Number of training samples

    Example:
        >>> results = train_qb_models([2023, 2024], n_trials=10)
        >>> "passing_yards" in results
        True
        >>> model, metrics = results["passing_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    logger.info(f"Training QB models for seasons {seasons} with {n_trials} trials")

    # Load features
    df = build_features(seasons)

    # Prepare QB-specific data
    X, y_dict = prepare_qb_data(df)

    results: dict[str, tuple[XGBRegressor, dict[str, Any]]] = {}

    for target in QB_TARGETS:
        logger.info(f"Training model for QB {target}...")
        y = y_dict[target]

        # Run hyperparameter tuning
        best_params, study = tune_hyperparameters(X, y, n_trials=n_trials)

        # Train final model with best parameters
        model, cv_scores = train_model(X, y, params=best_params)

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -cv_scores
        metrics = {
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
            "seasons": seasons,
        }

        # Save model
        save_model(model, "QB", target, metadata=metrics)

        results[target] = (model, metrics)
        logger.info(
            f"QB {target}: CV RMSE = {metrics['cv_rmse_mean']:.2f} +/- {metrics['cv_rmse_std']:.2f}"
        )

    logger.info(f"Completed training {len(results)} QB models")
    return results
