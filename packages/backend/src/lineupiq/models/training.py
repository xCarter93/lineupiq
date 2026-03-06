"""
ML training utilities with Optuna hyperparameter tuning and TimeSeriesSplit validation.

Provides training infrastructure for XGBoost and LightGBM models with proper temporal
validation to avoid data leakage in time-series sports data.

Key functions:
- create_study: Create Optuna study for hyperparameter search
- get_xgb_params: Generate XGBoost params from Optuna trial
- get_lgb_params: Generate LightGBM params from Optuna trial
- train_model: Train model with TimeSeriesSplit CV (supports both XGBoost/LightGBM)
- tune_hyperparameters: Run full Optuna optimization (supports both XGBoost/LightGBM)
"""

import logging
import os
from typing import Any, Literal

import numpy as np
import optuna
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor, early_stopping, log_evaluation
from mapie.regression import CrossConformalRegressor
from numpy.typing import NDArray
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

ModelType = Literal["xgboost", "lightgbm", "catboost"]

logger = logging.getLogger(__name__)

# Count targets that benefit from Poisson regression
# These are discrete, non-negative counts (TDs, INTs, receptions, fumbles)
# Using Poisson objective can improve predictions by 5-10%
COUNT_TARGETS = frozenset({
    "passing_tds",
    "rushing_tds",
    "receiving_tds",
    "interceptions",
    "fumbles_lost",
    "receptions",
    "carries",
    "targets",
    "fg_att",
    "pat_att",
    "def_sacks",
    "def_interceptions",
    "def_fumbles",
    "total_def_tds",
})
TD_TARGETS = frozenset({"passing_tds", "rushing_tds", "receiving_tds", "total_def_tds"})


def create_study(direction: str = "minimize") -> optuna.Study:
    """Create Optuna study for hyperparameter search.

    Uses MedianPruner to stop unpromising trials early (20-35% speedup) and
    multivariate TPE sampler for better hyperparameter exploration.

    Args:
        direction: Optimization direction - "minimize" for RMSE, "maximize" for R2.

    Returns:
        Optuna Study object configured for the optimization.

    Example:
        >>> study = create_study(direction="minimize")
        >>> study.direction.name
        'MINIMIZE'
    """
    # MedianPruner stops unpromising trials early based on intermediate values
    # n_startup_trials: Allow 5 trials before pruning starts
    # n_warmup_steps: Allow 2 CV folds before considering pruning
    pruner = optuna.pruners.MedianPruner(
        n_startup_trials=5,
        n_warmup_steps=2,
    )

    # Multivariate TPE considers correlations between hyperparameters
    # n_startup_trials: Use random sampling for first 10 trials
    sampler = optuna.samplers.TPESampler(
        multivariate=True,
        n_startup_trials=10,
    )

    study = optuna.create_study(
        direction=direction,
        sampler=sampler,
        pruner=pruner,
    )
    logger.info(f"Created Optuna study with direction={direction}, TPE sampler, MedianPruner")
    return study


def get_xgb_params(trial: optuna.Trial) -> dict[str, Any]:
    """Generate XGBoost parameters from Optuna trial.

    Defines the hyperparameter search space for XGBoost regression:
    - max_depth: 3-9 (tree complexity)
    - learning_rate: 0.01-0.3 (log scale, step size)
    - n_estimators: 100-500 (number of trees)
    - min_child_weight: 1-20 (minimum samples per leaf)
    - subsample: 0.6-1.0 (row sampling ratio)
    - colsample_bytree: 0.6-1.0 (column sampling ratio)
    - reg_alpha: 1e-8 to 10.0 (log scale, L1 regularization)
    - reg_lambda: 1e-8 to 10.0 (log scale, L2 regularization)

    Args:
        trial: Optuna trial object for suggesting parameters.

    Returns:
        Dictionary of XGBoost hyperparameters.

    Example:
        >>> import optuna
        >>> study = optuna.create_study()
        >>> trial = study.ask()
        >>> params = get_xgb_params(trial)
        >>> "max_depth" in params
        True
    """
    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 9),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
    }
    return params


def get_lgb_params(trial: optuna.Trial, target: str | None = None) -> dict[str, Any]:
    """Generate LightGBM parameters from Optuna trial.

    Defines the hyperparameter search space for LightGBM regression:
    - num_leaves: 20-100 (tree complexity, replaces max_depth)
    - learning_rate: 0.01-0.3 (log scale)
    - n_estimators: 100-500 (number of trees)
    - min_child_samples: 5-50 (minimum samples per leaf)
    - subsample: 0.6-1.0 (row sampling)
    - colsample_bytree: 0.6-1.0 (column sampling)
    - reg_alpha: 1e-8 to 10.0 (L1 regularization)
    - reg_lambda: 1e-8 to 10.0 (L2 regularization)
    - num_threads: Uses all available CPU cores (10-20% speedup)
    - objective: "poisson" for count data (TDs, INTs, etc.), "regression" otherwise

    Args:
        trial: Optuna trial object for suggesting parameters.
        target: Optional target name for objective selection.

    Returns:
        Dictionary of LightGBM hyperparameters.
    """
    params = {
        "num_leaves": trial.suggest_int("num_leaves", 20, 100),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "max_bin": trial.suggest_int("max_bin", 127, 511),
        "min_data_in_bin": trial.suggest_int("min_data_in_bin", 3, 20),
        "verbosity": -1,  # Suppress warnings
        "num_threads": os.cpu_count() or 4,  # Use all CPU cores for 10-20% speedup
    }

    # Use Poisson objective for count targets (TDs, INTs, receptions, etc.)
    # Poisson regression is more appropriate for discrete, non-negative counts
    if target and target in COUNT_TARGETS:
        if target in TD_TARGETS:
            # TD counts are highly zero-inflated; Tweedie is typically more stable.
            params["objective"] = "tweedie"
            params["tweedie_variance_power"] = trial.suggest_float(
                "tweedie_variance_power", 1.1, 1.7
            )
            logger.debug("Using Tweedie objective for TD target: %s", target)
        else:
            params["objective"] = "poisson"
            logger.debug(f"Using Poisson objective for count target: {target}")

    return params


def get_catboost_params(trial: optuna.Trial, target: str | None = None) -> dict[str, Any]:
    """Generate CatBoost parameters from Optuna trial.

    Defines the hyperparameter search space for CatBoost regression:
    - depth: 4-10 (tree depth)
    - learning_rate: 0.01-0.3 (log scale)
    - iterations: 100-500 (number of trees)
    - l2_leaf_reg: 1.0-10.0 (L2 regularization)
    - subsample: 0.6-1.0 (row sampling, requires bootstrap_type=Bernoulli)
    - colsample_bylevel: 0.6-1.0 (column sampling per level)
    - min_data_in_leaf: 5-50 (minimum samples per leaf)
    - random_strength: 0.1-10.0 (randomization for scoring splits)

    Args:
        trial: Optuna trial object for suggesting parameters.
        target: Optional target name for objective selection.

    Returns:
        Dictionary of CatBoost hyperparameters.
    """
    params: dict[str, Any] = {
        "depth": trial.suggest_int("depth", 4, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "iterations": trial.suggest_int("iterations", 100, 500),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.6, 1.0),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 50),
        "random_strength": trial.suggest_float("random_strength", 0.1, 10.0, log=True),
        "bootstrap_type": "Bernoulli",
        "verbose": 0,
        "thread_count": os.cpu_count() or 4,
        "allow_writing_files": False,
    }

    # Use Poisson loss for count targets
    if target and target in COUNT_TARGETS:
        params["loss_function"] = "Poisson"
        logger.debug(f"Using Poisson loss for count target: {target}")
    else:
        params["loss_function"] = "RMSE"

    return params


def train_model(
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    params: dict[str, Any] | None = None,
    n_splits: int = 5,
    model_type: ModelType = "lightgbm",
    early_stopping_rounds: int = 50,
    trial: optuna.Trial | None = None,
    season_array: NDArray[np.integer[Any]] | None = None,
    decay_rate: float = 0.15,
) -> tuple[XGBRegressor | LGBMRegressor | CatBoostRegressor, NDArray[np.floating[Any]]]:
    """Train model with TimeSeriesSplit cross-validation and early stopping.

    Uses TimeSeriesSplit to maintain temporal integrity - training data always
    comes before validation data, preventing future data leakage.

    Supports LightGBM, XGBoost, and CatBoost with early stopping callbacks
    to prevent overfitting. Reports intermediate values to Optuna for trial
    pruning when trial object is provided.

    Args:
        X: Feature matrix of shape (n_samples, n_features).
        y: Target array of shape (n_samples,).
        params: Model parameters. If None, uses defaults.
        n_splits: Number of CV splits (default: 5).
        model_type: "xgboost", "lightgbm", or "catboost" (default: "lightgbm").
        early_stopping_rounds: Rounds without improvement before stopping (default: 50).
        trial: Optional Optuna trial for reporting intermediate values and pruning.

    Returns:
        Tuple of (trained model, array of CV scores).
        CV scores are negative RMSE values (higher is better).

    Example:
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> model, scores = train_model(X, y, n_splits=3)
        >>> len(scores) == 3
        True
    """
    if params is None:
        params = {}

    # TimeSeriesSplit respects temporal ordering - no shuffle
    tscv = TimeSeriesSplit(n_splits=n_splits)

    scores = []
    sample_weights: NDArray[np.floating[Any]] | None = None
    if season_array is not None:
        max_season = int(np.max(season_array))
        sample_weights = np.exp(-decay_rate * (max_season - season_array))
        logger.info("Using exponential recency sample weighting (decay_rate=%.3f)", decay_rate)

    for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        w_train = sample_weights[train_idx] if sample_weights is not None else None

        # Create fresh model for each fold
        fold_model: XGBRegressor | LGBMRegressor | CatBoostRegressor
        if model_type == "lightgbm":
            model_params = {**params, "random_state": 42, "verbosity": -1}
            fold_model = LGBMRegressor(**model_params)

            # Fit with early stopping callbacks
            fold_model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                sample_weight=w_train,
                callbacks=[
                    early_stopping(stopping_rounds=early_stopping_rounds),
                    log_evaluation(period=0),  # Suppress per-iteration logs
                ],
            )
        elif model_type == "catboost":
            model_params = {**params, "random_seed": 42, "verbose": 0}
            fold_model = CatBoostRegressor(**model_params)
            fold_model.fit(
                X_train,
                y_train,
                eval_set=(X_val, y_val),
                sample_weight=w_train,
                early_stopping_rounds=early_stopping_rounds,
            )
        else:
            model_params = {**params, "random_state": 42}
            fold_model = XGBRegressor(
                **model_params,
                early_stopping_rounds=early_stopping_rounds,
            )
            fold_model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                sample_weight=w_train,
                verbose=False,
            )

        # Calculate validation RMSE
        y_pred = fold_model.predict(X_val)
        rmse = root_mean_squared_error(y_val, y_pred)
        scores.append(-rmse)  # Negative RMSE for consistency (higher is better)

        # Report intermediate value to Optuna for pruning
        if trial is not None:
            trial.report(-np.mean(scores), fold_idx)
            if trial.should_prune():
                raise optuna.TrialPruned()

    scores_array = np.array(scores)

    # Fit final model on full data with early stopping disabled
    model: XGBRegressor | LGBMRegressor | CatBoostRegressor
    if model_type == "lightgbm":
        model_params = {**params, "random_state": 42, "verbosity": -1}
        model = LGBMRegressor(**model_params)
    elif model_type == "catboost":
        model_params = {**params, "random_seed": 42, "verbose": 0}
        model = CatBoostRegressor(**model_params)
    else:
        model_params = {**params, "random_state": 42}
        model = XGBRegressor(**model_params)

    model.fit(X, y, sample_weight=sample_weights)

    logger.info(
        f"Trained {model_type} model with mean CV score: {scores_array.mean():.4f} (+/- {scores_array.std():.4f})"
    )

    return model, scores_array


def tune_hyperparameters(
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    n_trials: int = 50,
    n_splits: int = 5,
    model_type: ModelType = "lightgbm",
    target: str | None = None,
    season_array: NDArray[np.integer[Any]] | None = None,
    decay_rate: float = 0.15,
) -> tuple[dict[str, Any], optuna.Study]:
    """Run Optuna hyperparameter optimization with pruning support.

    Uses MedianPruner to stop unpromising trials early, reducing total
    tuning time by 20-35%. Reports intermediate CV scores after each fold.

    For count targets (TDs, INTs, receptions, etc.), uses Poisson objective
    which is more appropriate for discrete, non-negative data.

    Args:
        X: Feature matrix of shape (n_samples, n_features).
        y: Target array of shape (n_samples,).
        n_trials: Number of Optuna trials to run (default: 50).
        n_splits: Number of CV splits per trial (default: 5).
        model_type: "xgboost" or "lightgbm" (default: "lightgbm").
        target: Optional target name for objective selection (Poisson for counts).

    Returns:
        Tuple of (best parameters dict, Optuna study object).

    Example:
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> best_params, study = tune_hyperparameters(X, y, n_trials=5, n_splits=3)
        >>> "num_leaves" in best_params  # LightGBM param
        True
    """
    def objective(trial: optuna.Trial) -> float:
        """Objective function for Optuna optimization with pruning."""
        if model_type == "lightgbm":
            params = get_lgb_params(trial, target=target)
        elif model_type == "catboost":
            params = get_catboost_params(trial, target=target)
        else:
            params = get_xgb_params(trial)
        # Pass trial to enable intermediate reporting and pruning
        _, scores = train_model(
            X,
            y,
            params=params,
            n_splits=n_splits,
            model_type=model_type,
            trial=trial,
            season_array=season_array,
            decay_rate=decay_rate,
        )
        # Return mean negative RMSE (minimize this)
        return float(-scores.mean())

    # Create study and optimize
    study = create_study(direction="minimize")

    # Suppress Optuna logging during optimization
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best_params = study.best_params
    logger.info(f"Best {model_type} trial value: {study.best_value:.4f}")
    logger.info(f"Best parameters: {best_params}")

    return best_params, study


def fit_conformal(
    model: XGBRegressor | LGBMRegressor | CatBoostRegressor,
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    confidence_level: float = 0.9,
) -> CrossConformalRegressor:
    """Wrap a trained model with MAPIE for conformal prediction intervals.

    Uses CrossConformalRegressor with the "plus" method (jackknife+) which
    provides valid coverage guarantees without requiring a separate calibration set.

    Args:
        model: Already-trained base model (LightGBM, XGBoost, or CatBoost).
        X: Training feature matrix.
        y: Training target array.
        confidence_level: Confidence level (default 0.9 = 90% intervals).

    Returns:
        CrossConformalRegressor wrapping the base model, ready for interval predictions.
    """
    ccr = CrossConformalRegressor(
        estimator=model, confidence_level=confidence_level, method="plus", cv=5,
    )
    ccr.fit_conformalize(X, y)
    logger.info(
        f"Fit MAPIE conformal model (method=plus, cv=5, confidence_level={confidence_level})"
    )
    return ccr
