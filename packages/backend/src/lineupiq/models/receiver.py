"""
Receiver (WR/TE) model training module.

Provides training functions for Wide Receiver and Tight End receiving stat predictions.
WR and TE share the same targets (receiving_yards, receiving_tds, receptions) but have
different stat distributions - TEs typically have lower volume and fewer TDs.

Key functions:
- prepare_receiver_data: Filter and prepare data for WR or TE position
- train_wr_models: Train models for all WR receiving targets
- train_te_models: Train models for all TE receiving targets
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

# Receiving stats to predict for both WR and TE
RECEIVER_TARGETS = ["receiving_yards", "receiving_tds", "receptions"]


def prepare_receiver_data(
    df: pl.DataFrame, position: str
) -> tuple[NDArray[np.floating[Any]], dict[str, NDArray[np.floating[Any]]]]:
    """Filter and prepare data for WR or TE position.

    Filters the DataFrame to the specified position, drops rows with null values
    in features or targets, and returns numpy arrays ready for training.

    Args:
        df: Feature DataFrame from build_features().
        position: Position to filter ("WR" or "TE").

    Returns:
        Tuple of (X features array, dict of target arrays by target name).

    Raises:
        ValueError: If position is not WR or TE.

    Example:
        >>> df = build_features([2024])
        >>> X, y_dict = prepare_receiver_data(df, "WR")
        >>> X.shape[1] == len(get_feature_columns())
        True
        >>> "receiving_yards" in y_dict
        True
    """
    if position not in ("WR", "TE"):
        raise ValueError(f"Position must be 'WR' or 'TE', got '{position}'")

    # Filter to position
    df_pos = df.filter(pl.col("position") == position)
    logger.info(f"Filtered to {len(df_pos)} {position} rows")

    # Get feature and target columns
    feature_cols = get_feature_columns()

    # Drop rows with null values in features or targets
    required_cols = feature_cols + RECEIVER_TARGETS
    df_clean = df_pos.drop_nulls(subset=required_cols)
    logger.info(f"After dropping nulls: {len(df_clean)} rows")

    # Extract feature matrix
    X = df_clean.select(feature_cols).to_numpy().astype(np.float64)

    # Extract target arrays
    y_dict = {}
    for target in RECEIVER_TARGETS:
        y_dict[target] = df_clean.select(target).to_numpy().flatten().astype(np.float64)

    logger.info(f"Prepared {position} data: X shape {X.shape}, targets {list(y_dict.keys())}")

    return X, y_dict


def train_wr_models(
    seasons: list[int], n_trials: int = 50
) -> dict[str, tuple[XGBRegressor, dict[str, Any]]]:
    """Train XGBoost models for all WR receiving targets.

    Loads feature data, prepares WR-specific training data, and trains a model
    for each receiving target using Optuna hyperparameter tuning.

    Args:
        seasons: List of seasons to train on (e.g., [2019, 2020, 2021, 2022, 2023, 2024]).
        n_trials: Number of Optuna trials per target (default: 50).

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples.

    Example:
        >>> results = train_wr_models([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    logger.info(f"Training WR models for seasons {seasons}")

    # Load features
    df = build_features(seasons)

    # Prepare WR data
    X, y_dict = prepare_receiver_data(df, "WR")

    results: dict[str, tuple[XGBRegressor, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training WR {target} model...")
        y = y_dict[target]

        # Tune hyperparameters
        best_params, study = tune_hyperparameters(X, y, n_trials=n_trials)

        # Train final model with best params
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
        save_model(model, position="WR", target=target, metadata=metrics)

        results[target] = (model, metrics)
        logger.info(
            f"WR {target}: CV RMSE = {metrics['cv_rmse_mean']:.2f} +/- {metrics['cv_rmse_std']:.2f}"
        )

    logger.info(f"Completed training {len(results)} WR models")
    return results


def train_te_models(
    seasons: list[int], n_trials: int = 50
) -> dict[str, tuple[XGBRegressor, dict[str, Any]]]:
    """Train XGBoost models for all TE receiving targets.

    Loads feature data, prepares TE-specific training data, and trains a model
    for each receiving target using Optuna hyperparameter tuning.

    TEs typically have lower stat distributions than WRs (fewer targets, shorter
    routes, more blocking assignments), so separate models provide better accuracy.

    Args:
        seasons: List of seasons to train on (e.g., [2019, 2020, 2021, 2022, 2023, 2024]).
        n_trials: Number of Optuna trials per target (default: 50).

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples.

    Example:
        >>> results = train_te_models([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    logger.info(f"Training TE models for seasons {seasons}")

    # Load features
    df = build_features(seasons)

    # Prepare TE data
    X, y_dict = prepare_receiver_data(df, "TE")

    results: dict[str, tuple[XGBRegressor, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training TE {target} model...")
        y = y_dict[target]

        # Tune hyperparameters
        best_params, study = tune_hyperparameters(X, y, n_trials=n_trials)

        # Train final model with best params
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
        save_model(model, position="TE", target=target, metadata=metrics)

        results[target] = (model, metrics)
        logger.info(
            f"TE {target}: CV RMSE = {metrics['cv_rmse_mean']:.2f} +/- {metrics['cv_rmse_std']:.2f}"
        )

    logger.info(f"Completed training {len(results)} TE models")
    return results
