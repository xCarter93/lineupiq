"""
ML training utilities with Optuna hyperparameter tuning and TimeSeriesSplit validation.

Provides training infrastructure for XGBoost models with proper temporal validation
to avoid data leakage in time-series sports data.

Key functions:
- create_study: Create Optuna study for hyperparameter search
- get_xgb_params: Generate XGBoost params from Optuna trial
- train_model: Train XGBRegressor with TimeSeriesSplit CV
- tune_hyperparameters: Run full Optuna optimization
"""

import logging
from typing import Any

import numpy as np
import optuna
from numpy.typing import NDArray
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from xgboost import XGBRegressor

logger = logging.getLogger(__name__)


def create_study(direction: str = "minimize") -> optuna.Study:
    """Create Optuna study for hyperparameter search.

    Args:
        direction: Optimization direction - "minimize" for RMSE, "maximize" for R2.

    Returns:
        Optuna Study object configured for the optimization.

    Example:
        >>> study = create_study(direction="minimize")
        >>> study.direction.name
        'MINIMIZE'
    """
    study = optuna.create_study(direction=direction)
    logger.info(f"Created Optuna study with direction={direction}")
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


def train_model(
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    params: dict[str, Any] | None = None,
    n_splits: int = 5,
) -> tuple[XGBRegressor, NDArray[np.floating[Any]]]:
    """Train XGBRegressor with TimeSeriesSplit cross-validation.

    Uses TimeSeriesSplit to maintain temporal integrity - training data always
    comes before validation data, preventing future data leakage.

    Args:
        X: Feature matrix of shape (n_samples, n_features).
        y: Target array of shape (n_samples,).
        params: XGBoost parameters. If None, uses defaults.
        n_splits: Number of CV splits (default: 5).

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

    # Add random_state for reproducibility
    model_params = {**params, "random_state": 42}
    model = XGBRegressor(**model_params)

    # TimeSeriesSplit respects temporal ordering - no shuffle
    tscv = TimeSeriesSplit(n_splits=n_splits)

    # cross_val_score with neg_root_mean_squared_error
    # Returns negative RMSE (so higher is better)
    scores = cross_val_score(
        model, X, y, cv=tscv, scoring="neg_root_mean_squared_error"
    )

    # Fit on full data after CV for final model
    model.fit(X, y)

    logger.info(f"Trained model with mean CV score: {scores.mean():.4f} (+/- {scores.std():.4f})")

    return model, scores


def tune_hyperparameters(
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    n_trials: int = 50,
    n_splits: int = 5,
) -> tuple[dict[str, Any], optuna.Study]:
    """Run Optuna hyperparameter optimization.

    Creates objective function using get_xgb_params + train_model,
    minimizes negative RMSE to find best hyperparameters.

    Args:
        X: Feature matrix of shape (n_samples, n_features).
        y: Target array of shape (n_samples,).
        n_trials: Number of Optuna trials to run (default: 50).
        n_splits: Number of CV splits per trial (default: 5).

    Returns:
        Tuple of (best parameters dict, Optuna study object).

    Example:
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> best_params, study = tune_hyperparameters(X, y, n_trials=5, n_splits=3)
        >>> "max_depth" in best_params
        True
    """
    def objective(trial: optuna.Trial) -> float:
        """Objective function for Optuna optimization."""
        params = get_xgb_params(trial)
        _, scores = train_model(X, y, params=params, n_splits=n_splits)
        # Return mean negative RMSE (minimize this)
        return -scores.mean()

    # Create study and optimize
    study = create_study(direction="minimize")

    # Suppress Optuna logging during optimization
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best_params = study.best_params
    logger.info(f"Best trial value (negative RMSE): {study.best_value:.4f}")
    logger.info(f"Best parameters: {best_params}")

    return best_params, study
