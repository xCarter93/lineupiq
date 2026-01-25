"""
Receiver (WR/TE) model training module.

Provides training functions for Wide Receiver and Tight End receiving stat predictions.
WR and TE share the same targets (receiving_yards, receiving_tds, receptions, fumbles_lost)
but have different stat distributions - TEs typically have lower volume and fewer TDs.

Supports both XGBoost and LightGBM (LightGBM default for 7x faster training).

Key functions:
- prepare_receiver_data: Filter and prepare data for WR or TE position
- train_wr_models: Train models for all WR receiving targets
- train_te_models: Train models for all TE receiving targets
- train_receiver_models: Train models for both WR and TE positions
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray

from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.persistence import save_model
from lineupiq.models.training import ModelType, train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# Receiving stats to predict for both WR and TE
RECEIVER_TARGETS = ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"]


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
        Targets: receiving_yards, receiving_tds, receptions, fumbles_lost.

    Raises:
        ValueError: If position is not WR or TE.

    Example:
        >>> df = build_features([2024])
        >>> X, y_dict = prepare_receiver_data(df, "WR")
        >>> X.shape[1] == len(get_feature_columns())
        True
        >>> "receiving_yards" in y_dict
        True
        >>> "fumbles_lost" in y_dict
        True
    """
    if position not in ("WR", "TE"):
        raise ValueError(f"Position must be 'WR' or 'TE', got '{position}'")

    # Filter to position
    df_pos = df.filter(pl.col("position") == position)
    logger.info(f"Filtered to {len(df_pos)} {position} rows")

    # Map receiving_fumbles_lost to fumbles_lost for model target
    df_pos = df_pos.with_columns(
        pl.col("receiving_fumbles_lost").fill_null(0).alias("fumbles_lost")
    )

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
    seasons: list[int] | None = None,
    n_trials: int = 50,
    model_type: ModelType = "lightgbm",
    df: pl.DataFrame | None = None,
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train ML models for all WR receiving targets.

    Loads feature data, prepares WR-specific training data, and trains a model
    for each receiving target using Optuna hyperparameter tuning.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 50).
        model_type: Model type - "lightgbm" (default, 7x faster) or "xgboost".
        df: Optional pre-computed feature DataFrame. If None, features will be
            computed from seasons. Use for feature caching across positions.

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_wr_models([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training WR models for seasons {seasons} using {model_type}")

    # Load features if not provided (enables feature caching)
    if df is None:
        df = build_features(seasons)

    # Prepare WR data
    X, y_dict = prepare_receiver_data(df, "WR")

    results: dict[str, tuple[Any, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training WR {target} model...")
        y = y_dict[target]

        # Tune hyperparameters (uses Poisson for count targets like TDs)
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type=model_type, target=target
        )

        # Train final model with best params
        model, cv_scores = train_model(X, y, params=best_params, model_type=model_type)

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -cv_scores
        metrics = {
            "position": "WR",
            "target": target,
            "model_type": model_type,
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
    seasons: list[int] | None = None,
    n_trials: int = 50,
    model_type: ModelType = "lightgbm",
    df: pl.DataFrame | None = None,
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train ML models for all TE receiving targets.

    Loads feature data, prepares TE-specific training data, and trains a model
    for each receiving target using Optuna hyperparameter tuning.

    TEs typically have lower stat distributions than WRs (fewer targets, shorter
    routes, more blocking assignments), so separate models provide better accuracy.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 50).
        model_type: Model type - "lightgbm" (default, 7x faster) or "xgboost".
        df: Optional pre-computed feature DataFrame. If None, features will be
            computed from seasons. Use for feature caching across positions.

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_te_models([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training TE models for seasons {seasons} using {model_type}")

    # Load features if not provided (enables feature caching)
    if df is None:
        df = build_features(seasons)

    # Prepare TE data
    X, y_dict = prepare_receiver_data(df, "TE")

    results: dict[str, tuple[Any, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training TE {target} model...")
        y = y_dict[target]

        # Tune hyperparameters (uses Poisson for count targets like TDs)
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type=model_type, target=target
        )

        # Train final model with best params
        model, cv_scores = train_model(X, y, params=best_params, model_type=model_type)

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -cv_scores
        metrics = {
            "position": "TE",
            "target": target,
            "model_type": model_type,
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


def train_receiver_models(
    seasons: list[int] | None = None,
    n_trials: int = 50,
    model_type: ModelType = "lightgbm",
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train ML models for both WR and TE receiving targets.

    Convenience function that trains all receiver models (WR + TE) in one call.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 50).
        model_type: Model type - "lightgbm" (default, 7x faster) or "xgboost".

    Returns:
        Dict mapping "{position}_{target}" to (model, metrics) tuple.
        Example keys: "WR_receiving_yards", "TE_receptions".

    Example:
        >>> results = train_receiver_models([2023, 2024], n_trials=10)
        >>> "WR_receiving_yards" in results
        True
        >>> "TE_receiving_yards" in results
        True
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training all receiver models (WR + TE) for seasons {seasons}")

    results: dict[str, tuple[Any, dict[str, Any]]] = {}

    # Train WR models
    wr_results = train_wr_models(seasons, n_trials=n_trials, model_type=model_type)
    for target, (model, metrics) in wr_results.items():
        results[f"WR_{target}"] = (model, metrics)

    # Train TE models
    te_results = train_te_models(seasons, n_trials=n_trials, model_type=model_type)
    for target, (model, metrics) in te_results.items():
        results[f"TE_{target}"] = (model, metrics)

    logger.info(f"Completed training {len(results)} receiver models (WR + TE)")
    return results


def train_wr_models_xgboost(
    seasons: list[int] | None = None,
    n_trials: int = 30,
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train XGBoost models for all WR receiving targets.

    Trains XGBoost models (level-wise tree growth) to complement existing
    LightGBM models (leaf-wise tree growth) for ensemble methods. Uses same
    Optuna tuning and validation approach as train_wr_models().

    Models saved with _xgb.joblib suffix for distinction from LightGBM models.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 30).

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_wr_models_xgboost([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> metrics["model_type"]
        'xgboost'
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training WR XGBoost models for seasons {seasons}")

    # Load features
    df = build_features(seasons)

    # Prepare WR data
    X, y_dict = prepare_receiver_data(df, "WR")

    results: dict[str, tuple[Any, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training WR {target} XGBoost model...")
        y = y_dict[target]

        # Tune hyperparameters with XGBoost
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type="xgboost"
        )

        # Train final model with best params
        model, cv_scores = train_model(X, y, params=best_params, model_type="xgboost")

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -cv_scores
        metrics = {
            "position": "WR",
            "target": target,
            "model_type": "xgboost",
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
            "seasons": seasons,
        }

        # Save model with _xgb suffix
        save_model(model, position="WR", target=f"{target}_xgb", metadata=metrics)

        results[target] = (model, metrics)
        logger.info(
            f"WR {target} XGBoost: CV RMSE = {metrics['cv_rmse_mean']:.2f} +/- {metrics['cv_rmse_std']:.2f}"
        )

    logger.info(f"Completed training {len(results)} WR XGBoost models")
    return results


def train_te_models_xgboost(
    seasons: list[int] | None = None,
    n_trials: int = 30,
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train XGBoost models for all TE receiving targets.

    Trains XGBoost models (level-wise tree growth) to complement existing
    LightGBM models (leaf-wise tree growth) for ensemble methods. Uses same
    Optuna tuning and validation approach as train_te_models().

    TEs typically have lower stat distributions than WRs (fewer targets, shorter
    routes, more blocking assignments), so separate models provide better accuracy.

    Models saved with _xgb.joblib suffix for distinction from LightGBM models.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 30).

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_te_models_xgboost([2023, 2024], n_trials=10)
        >>> "receiving_yards" in results
        True
        >>> model, metrics = results["receiving_yards"]
        >>> metrics["model_type"]
        'xgboost'
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training TE XGBoost models for seasons {seasons}")

    # Load features
    df = build_features(seasons)

    # Prepare TE data
    X, y_dict = prepare_receiver_data(df, "TE")

    results: dict[str, tuple[Any, dict[str, Any]]] = {}

    for target in RECEIVER_TARGETS:
        logger.info(f"Training TE {target} XGBoost model...")
        y = y_dict[target]

        # Tune hyperparameters with XGBoost
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type="xgboost"
        )

        # Train final model with best params
        model, cv_scores = train_model(X, y, params=best_params, model_type="xgboost")

        # Calculate metrics (scores are negative RMSE, so negate)
        cv_rmse = -cv_scores
        metrics = {
            "position": "TE",
            "target": target,
            "model_type": "xgboost",
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
            "seasons": seasons,
        }

        # Save model with _xgb suffix
        save_model(model, position="TE", target=f"{target}_xgb", metadata=metrics)

        results[target] = (model, metrics)
        logger.info(
            f"TE {target} XGBoost: CV RMSE = {metrics['cv_rmse_mean']:.2f} +/- {metrics['cv_rmse_std']:.2f}"
        )

    logger.info(f"Completed training {len(results)} TE XGBoost models")
    return results
