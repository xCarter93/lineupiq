"""
RB (Running Back) model training module.

Provides position-specific model training for RB stat predictions:
- rushing_yards, rushing_tds, carries (rushing stats)
- receiving_yards, receptions, receiving_tds (pass-catching stats)
- fumbles_lost (combined rushing + receiving fumbles)

Uses the training infrastructure from training.py with Optuna hyperparameter
tuning and TimeSeriesSplit validation. Supports both XGBoost and LightGBM
(LightGBM default for 7x faster training).

Key functions:
- prepare_rb_data: Filter and prepare data for RB model training
- train_rb_models: Train all 7 RB models with hyperparameter tuning
"""

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray

from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.persistence import save_model
from lineupiq.models.training import ModelType, train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

# All RB prediction targets (7 targets for complete fantasy scoring)
RB_TARGETS = [
    "rushing_yards",
    "rushing_tds",
    "carries",
    "receiving_yards",
    "receptions",
    "receiving_tds",
    "fumbles_lost",
]


def prepare_rb_data(
    df: pl.DataFrame,
) -> tuple[NDArray[np.floating[Any]], dict[str, NDArray[np.floating[Any]]]]:
    """Filter and prepare data for RB model training.

    Filters to RB position only and extracts features and all 7 targets:
    - rushing_yards, rushing_tds, carries (rushing stats)
    - receiving_yards, receptions, receiving_tds (pass-catching stats)
    - fumbles_lost (combined rushing + receiving fumbles)

    Note: FB (Fullback) is already grouped with RB per 03-02 decision.

    Args:
        df: Feature DataFrame from build_features().

    Returns:
        Tuple of (X, y_dict) where:
        - X: Feature matrix of shape (n_samples, n_features)
        - y_dict: Dict mapping target name to target array

    Example:
        >>> df = build_features([2024])
        >>> X, y = prepare_rb_data(df)
        >>> X.shape[1] == len(get_feature_columns())
        True
        >>> "rushing_yards" in y
        True
        >>> "fumbles_lost" in y
        True
    """
    feature_cols = get_feature_columns()

    # Filter to RB position only
    rb_df = df.filter(pl.col("position") == "RB")
    logger.info(f"Filtered to {len(rb_df)} RB rows from {len(df)} total")

    # Compute fumbles_lost as sum of rushing and receiving fumbles lost
    # Both columns have nulls filled with 0 by cleaning.py
    rb_df = rb_df.with_columns(
        (
            pl.col("rushing_fumbles_lost").fill_null(0)
            + pl.col("receiving_fumbles_lost").fill_null(0)
        ).alias("fumbles_lost")
    )

    # Build list of columns to check for nulls: features + targets
    columns_to_check = feature_cols + RB_TARGETS

    # Drop rows with null values in features or targets
    rb_df = rb_df.drop_nulls(subset=[c for c in columns_to_check if c in rb_df.columns])
    logger.info(f"After dropping nulls: {len(rb_df)} rows")

    # Extract features as numpy array
    X = rb_df.select(feature_cols).to_numpy().astype(np.float64)

    # Extract targets as dict of arrays
    y_dict = {}
    for target in RB_TARGETS:
        y_dict[target] = rb_df.select(target).to_numpy().flatten().astype(np.float64)

    logger.info(f"Prepared RB data: X shape {X.shape}, {len(RB_TARGETS)} targets")

    return X, y_dict


def train_rb_models(
    seasons: list[int] | None = None,
    n_trials: int = 50,
    rolling_window: int = 3,
    model_type: ModelType = "lightgbm",
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train ML models for all 7 RB targets.

    Runs full hyperparameter tuning for each RB target stat:
    - rushing_yards: Primary rushing stat
    - rushing_tds: Rushing touchdowns
    - carries: Number of carries
    - receiving_yards: Pass-catching yards
    - receptions: Number of receptions
    - receiving_tds: Receiving touchdowns (6 pts each, ~0.05/game)
    - fumbles_lost: Combined rushing + receiving fumbles (-2 pts each, ~0.04/game)

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 50).
        rolling_window: Rolling window for feature computation (default: 3).
        model_type: Model type - "lightgbm" (default, 7x faster) or "xgboost".

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include: cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_rb_models([2023, 2024], n_trials=10)
        >>> "rushing_yards" in results
        True
        >>> "fumbles_lost" in results
        True
        >>> model, metrics = results["rushing_yards"]
        >>> "cv_rmse_mean" in metrics
        True
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(f"Training RB models for seasons {seasons} with {n_trials} trials using {model_type}")

    # Load and prepare data
    logger.info("Loading feature data...")
    df = build_features(seasons, rolling_window=rolling_window)
    X, y_dict = prepare_rb_data(df)

    results = {}

    for i, target in enumerate(RB_TARGETS, 1):
        logger.info(f"[{i}/{len(RB_TARGETS)}] Training model for {target}...")

        y = y_dict[target]

        # Run hyperparameter tuning
        logger.info(f"  Running {n_trials} Optuna trials...")
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, n_splits=5, model_type=model_type
        )

        # Train final model with best params
        logger.info(f"  Training final model with best params...")
        model, cv_scores = train_model(
            X, y, params=best_params, n_splits=5, model_type=model_type
        )

        # Compute metrics (cv_scores are negative RMSE)
        cv_rmse_mean = float(-cv_scores.mean())
        cv_rmse_std = float(cv_scores.std())

        # Prepare metadata
        metadata = {
            "position": "RB",
            "target": target,
            "model_type": model_type,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_samples": len(y),
            "n_features": X.shape[1],
            "seasons": seasons,
            "best_params": best_params,
            "cv_rmse_mean": cv_rmse_mean,
            "cv_rmse_std": cv_rmse_std,
            "n_trials": n_trials,
            "best_trial_value": study.best_value,
        }

        # Save model
        save_model(model, "RB", target, metadata)

        logger.info(f"  CV RMSE: {cv_rmse_mean:.2f} +/- {cv_rmse_std:.2f}")

        results[target] = (model, metadata)

    logger.info(f"Completed training all {len(RB_TARGETS)} RB models")
    return results


def train_rb_models_xgboost(
    seasons: list[int] | None = None,
    n_trials: int = 30,
    rolling_window: int = 3,
) -> dict[str, tuple[Any, dict[str, Any]]]:
    """Train XGBoost models for all 7 RB targets.

    Trains XGBoost models (level-wise tree growth) to complement existing
    LightGBM models (leaf-wise tree growth) for ensemble methods. Uses same
    Optuna tuning and validation approach as train_rb_models().

    Models saved with _xgb.joblib suffix for distinction from LightGBM models.

    Args:
        seasons: List of seasons to train on. Defaults to [2021-2024] if None.
        n_trials: Number of Optuna trials per target (default: 30).
        rolling_window: Rolling window for feature computation (default: 3).

    Returns:
        Dict mapping target name to (model, metrics) tuple.
        Metrics include: cv_rmse_mean, cv_rmse_std, best_params, n_samples, model_type.

    Example:
        >>> results = train_rb_models_xgboost([2023, 2024], n_trials=10)
        >>> "rushing_yards" in results
        True
        >>> "fumbles_lost" in results
        True
        >>> model, metrics = results["rushing_yards"]
        >>> metrics["model_type"]
        'xgboost'
    """
    if seasons is None:
        seasons = [2021, 2022, 2023, 2024]

    logger.info(
        f"Training RB XGBoost models for seasons {seasons} with {n_trials} trials"
    )

    # Load and prepare data
    logger.info("Loading feature data...")
    df = build_features(seasons, rolling_window=rolling_window)
    X, y_dict = prepare_rb_data(df)

    results = {}

    for i, target in enumerate(RB_TARGETS, 1):
        logger.info(f"[{i}/{len(RB_TARGETS)}] Training XGBoost model for {target}...")

        y = y_dict[target]

        # Run hyperparameter tuning with XGBoost
        logger.info(f"  Running {n_trials} Optuna trials...")
        best_params, study = tune_hyperparameters(
            X, y, n_trials=n_trials, n_splits=5, model_type="xgboost"
        )

        # Train final model with best params
        logger.info(f"  Training final model with best params...")
        model, cv_scores = train_model(
            X, y, params=best_params, n_splits=5, model_type="xgboost"
        )

        # Compute metrics (cv_scores are negative RMSE)
        cv_rmse_mean = float(-cv_scores.mean())
        cv_rmse_std = float(cv_scores.std())

        # Prepare metadata
        metadata = {
            "position": "RB",
            "target": target,
            "model_type": "xgboost",
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_samples": len(y),
            "n_features": X.shape[1],
            "seasons": seasons,
            "best_params": best_params,
            "cv_rmse_mean": cv_rmse_mean,
            "cv_rmse_std": cv_rmse_std,
            "n_trials": n_trials,
            "best_trial_value": study.best_value,
        }

        # Save model with _xgb suffix
        save_model(model, "RB", f"{target}_xgb", metadata)

        logger.info(f"  CV RMSE: {cv_rmse_mean:.2f} +/- {cv_rmse_std:.2f}")

        results[target] = (model, metadata)

    logger.info(f"Completed training all {len(RB_TARGETS)} RB XGBoost models")
    return results
