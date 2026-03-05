"""
Ensemble infrastructure for combining LightGBM, XGBoost, and CatBoost models.

Provides VotingRegressor and StackingRegressor wrappers for ensemble strategies:
- Simple averaging: Equal weight to all models
- Weighted averaging: Optimal weights via simplex grid search
- Stacking: Meta-learner (Ridge) trained on base model predictions

Supports 2 or 3 model ensembles (any combination of LightGBM, XGBoost, CatBoost).

Key functions:
- create_voting_ensemble: Create VotingRegressor with optional weights
- create_stacking_ensemble: Create StackingRegressor with Ridge meta-learner
- find_optimal_weights: Simplex grid search for optimal model weights
- build_and_save_ensemble: End-to-end ensemble creation from trained models
- save_ensemble: Save ensemble model to disk
- load_ensemble: Load ensemble model from disk
- benchmark_ensemble_strategies: Benchmark all strategies on holdout data
"""

import itertools
import logging
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import StackingRegressor, VotingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from lineupiq.models.persistence import load_model

logger = logging.getLogger(__name__)

# Directory for saved model files
# Located at packages/backend/models/ (not in src/, these are artifacts)
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models"

EnsembleType = Literal["voting_simple", "voting_weighted", "stacking"]


def create_voting_ensemble(
    models: dict[str, Any],
    weights: list[float] | None = None,
) -> VotingRegressor:
    """Create VotingRegressor ensemble for averaging predictions.

    Supports 2 or 3 models (any combination of LightGBM, XGBoost, CatBoost).

    Args:
        models: Dict mapping model names to trained model objects.
            E.g., {"lgbm": m1, "xgb": m2, "catboost": m3}
        weights: Optional weights for weighted averaging, same order as models dict.
            If None, uses simple averaging (equal weights).

    Returns:
        VotingRegressor ensemble ready for fitting or prediction.

    Example:
        >>> ensemble = create_voting_ensemble({"lgbm": m1, "xgb": m2})
        >>> ensemble = create_voting_ensemble(
        ...     {"lgbm": m1, "xgb": m2, "catboost": m3},
        ...     weights=[0.5, 0.3, 0.2]
        ... )
    """
    estimators = list(models.items())

    if weights is None:
        logger.info(f"Creating simple voting ensemble ({len(estimators)} models, equal weights)")
        voting_reg = VotingRegressor(estimators=estimators)
    else:
        logger.info(f"Creating weighted voting ensemble with weights={weights}")
        voting_reg = VotingRegressor(estimators=estimators, weights=weights)

    return voting_reg


def create_stacking_ensemble(
    models: dict[str, Any],
    cv: int = 5,
) -> StackingRegressor:
    """Create StackingRegressor ensemble with Ridge meta-learner.

    Uses cross-validation to generate out-of-fold predictions for meta-learner training,
    preventing overfitting. Ridge regularization handles correlated base predictions.

    Args:
        models: Dict mapping model names to trained model objects.
        cv: Number of cross-validation folds for meta-learner training (default: 5).

    Returns:
        StackingRegressor ensemble ready for fitting or prediction.

    Example:
        >>> ensemble = create_stacking_ensemble({"lgbm": m1, "xgb": m2, "catboost": m3})
        >>> ensemble.fit(X_train, y_train)
        >>> predictions = ensemble.predict(X_test)
    """
    estimators = list(models.items())

    # Ridge with alpha=1.0 prevents overfitting on correlated base predictions
    meta_learner = Ridge(alpha=1.0)

    logger.info(f"Creating stacking ensemble ({len(estimators)} models, cv={cv}, meta-learner=Ridge)")
    stacking_reg = StackingRegressor(
        estimators=estimators,
        final_estimator=meta_learner,
        cv=cv,
        passthrough=False,  # Use only base predictions, not original features
    )

    return stacking_reg


def find_optimal_weights(
    models: dict[str, Any],
    X: NDArray[np.floating[Any]],
    y: NDArray[np.floating[Any]],
    step: float = 0.05,
) -> list[float]:
    """Find optimal model weights via simplex grid search.

    Searches over all weight combinations that sum to 1.0 at the given step size.
    For 3 models at step=0.05, this is 231 combinations (fast).
    Computes weighted predictions directly (no VotingRegressor fit per combo) for speed.

    Args:
        models: Dict mapping model names to trained model objects.
        X: Validation feature matrix.
        y: Validation target array.
        step: Step size for weight grid (default: 0.05).

    Returns:
        List of optimal weights in the same order as the models dict.

    Example:
        >>> weights = find_optimal_weights({"lgbm": m1, "xgb": m2, "catboost": m3}, X, y)
        >>> weights
        [0.5, 0.3, 0.2]
    """
    n_models = len(models)
    model_names = list(models.keys())

    # Pre-compute predictions for each model
    predictions = {}
    for name, model in models.items():
        predictions[name] = model.predict(X)

    # Generate simplex grid: all weight combinations summing to 1.0
    n_steps = int(round(1.0 / step))
    best_mae = float("inf")
    best_weights = [1.0 / n_models] * n_models  # default: equal weights

    # Generate all combos of n_models non-negative integers summing to n_steps
    for combo in itertools.combinations_with_replacement(range(n_steps + 1), n_models - 1):
        # Convert dividers to weights
        dividers = [0] + list(combo) + [n_steps]
        weights_int = [dividers[i + 1] - dividers[i] for i in range(n_models)]
        weights = [w / n_steps for w in weights_int]

        # Try all permutations of this weight combo
        seen = set()
        for perm in itertools.permutations(weights):
            if perm in seen:
                continue
            seen.add(perm)

            # Compute weighted prediction directly
            weighted_pred = sum(
                w * predictions[name] for w, name in zip(perm, model_names)
            )
            mae = mean_absolute_error(y, weighted_pred)

            if mae < best_mae:
                best_mae = mae
                best_weights = list(perm)

    logger.info(
        f"Optimal weights for {model_names}: {[f'{w:.2f}' for w in best_weights]} (MAE: {best_mae:.4f})"
    )
    return best_weights


def build_and_save_ensemble(
    models: dict[str, Any],
    position: str,
    target: str,
    X_train: NDArray[np.floating[Any]],
    y_train: NDArray[np.floating[Any]],
    X_val: NDArray[np.floating[Any]],
    y_val: NDArray[np.floating[Any]],
) -> Path:
    """Build a weighted voting ensemble, find optimal weights, fit, and save.

    Convenience function that:
    1. Finds optimal weights via simplex grid search on validation data
    2. Builds VotingRegressor with those weights
    3. Fits the ensemble on full data (train + val) so base models see all data
    4. Saves to disk

    Args:
        models: Dict mapping model names to trained model objects.
            E.g., {"lgbm": m1, "xgb": m2, "catboost": m3}
        position: Player position (e.g., "QB", "RB").
        target: Base target stat name (e.g., "passing_yards").
        X_train: Training features for fitting the ensemble.
        y_train: Training target for fitting the ensemble.
        X_val: Validation features for weight optimization.
        y_val: Validation target for weight optimization.

    Returns:
        Path to the saved ensemble file.
    """
    logger.info(f"Building {len(models)}-model ensemble for {position}_{target}")

    # Find optimal weights on validation data
    optimal_weights = find_optimal_weights(models, X_val, y_val)

    # Create and fit the ensemble on FULL data (train + val)
    # VotingRegressor.fit() refits base models, so we must use all data
    # to match the standalone models which were trained on 100% of data
    X_full = np.vstack([X_train, X_val])
    y_full = np.concatenate([y_train, y_val])
    ensemble = create_voting_ensemble(models, weights=optimal_weights)
    ensemble.fit(X_full, y_full)

    # Save
    filepath = save_ensemble(ensemble, position, target, "voting_weighted")
    logger.info(
        f"Saved {len(models)}-model ensemble for {position}_{target} "
        f"with weights={[f'{w:.2f}' for w in optimal_weights]}"
    )

    return filepath


def save_ensemble(
    ensemble: VotingRegressor | StackingRegressor,
    position: str,
    target: str,
    ensemble_type: EnsembleType,
) -> Path:
    """Save ensemble model to disk.

    Saves ensemble with naming convention: {position}_{target}_{ensemble_type}.joblib

    Args:
        ensemble: Trained ensemble model (VotingRegressor or StackingRegressor).
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        ensemble_type: Type of ensemble ("voting_simple", "voting_weighted", "stacking").

    Returns:
        Path to the saved ensemble file.

    Example:
        >>> path = save_ensemble(ensemble, "QB", "passing_yards", "voting_simple")
        >>> path.name
        'QB_passing_yards_voting_simple.joblib'
    """
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save ensemble
    filename = f"{position}_{target}_{ensemble_type}.joblib"
    filepath = MODELS_DIR / filename
    joblib.dump(ensemble, filepath)

    logger.info(f"Saved {ensemble_type} ensemble to {filepath}")
    return filepath


def load_ensemble(
    position: str,
    target: str,
    ensemble_type: EnsembleType,
) -> VotingRegressor | StackingRegressor:
    """Load ensemble model from disk.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        ensemble_type: Type of ensemble ("voting_simple", "voting_weighted", "stacking").

    Returns:
        Loaded ensemble model ready for prediction.

    Raises:
        FileNotFoundError: If ensemble file doesn't exist.

    Example:
        >>> ensemble = load_ensemble("QB", "passing_yards", "voting_weighted")
        >>> predictions = ensemble.predict(X_test)
    """
    filename = f"{position}_{target}_{ensemble_type}.joblib"
    filepath = MODELS_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Ensemble not found: {filepath}")

    ensemble = joblib.load(filepath)
    logger.info(f"Loaded {ensemble_type} ensemble from {filepath}")

    return ensemble


def benchmark_ensemble_strategies(
    position: str,
    stat: str,
    X_train: NDArray[np.floating[Any]],
    y_train: NDArray[np.floating[Any]],
    X_holdout: NDArray[np.floating[Any]],
    y_holdout: NDArray[np.floating[Any]],
) -> dict[str, Any]:
    """Benchmark all ensemble strategies against single models on holdout data.

    Loads available models (LightGBM, XGBoost, optionally CatBoost) for position/stat,
    evaluates ensemble strategies on holdout data, and identifies the best performer.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        stat: Target stat (e.g., "passing_yards", "rushing_tds").
        X_train: Training features for fitting ensembles.
        y_train: Training target for fitting ensembles.
        X_holdout: Holdout features for evaluation.
        y_holdout: Holdout target for evaluation.

    Returns:
        Dict with keys:
        - results: Dict mapping strategy name to {"mae": float, "r2": float}
        - best_strategy: Name of strategy with lowest MAE
        - optimal_weights: Optimal weights from simplex search
        - n_models: Number of models used in ensemble

    Raises:
        FileNotFoundError: If LightGBM or XGBoost model files don't exist.
    """
    logger.info(f"Benchmarking ensemble strategies for {position}_{stat}")

    # Load pre-trained models (LightGBM + XGBoost required, CatBoost optional)
    try:
        lgbm_model, _ = load_model(position, stat)
        xgb_model, _ = load_model(position, f"{stat}_xgb")
    except FileNotFoundError as e:
        logger.error(f"Required models not found for {position}_{stat}: {e}")
        raise

    base_models: dict[str, Any] = {"lgbm": lgbm_model, "xgb": xgb_model}

    # Try loading CatBoost model (optional)
    try:
        catboost_model, _ = load_model(position, f"{stat}_catboost")
        base_models["catboost"] = catboost_model
        logger.info(f"Loaded CatBoost model for {position}_{stat}")
    except FileNotFoundError:
        logger.info(f"No CatBoost model for {position}_{stat}, using 2-model ensemble")

    # Evaluate each single model
    results: dict[str, dict[str, float]] = {}
    predictions: dict[str, NDArray[np.floating[Any]]] = {}

    for name, model in base_models.items():
        pred = model.predict(X_holdout)
        predictions[name] = pred
        results[f"{name}_solo"] = {
            "mae": mean_absolute_error(y_holdout, pred),
            "r2": r2_score(y_holdout, pred),
        }

    # Simple voting (equal weights)
    voting_simple = create_voting_ensemble(base_models)
    voting_simple.fit(X_train, y_train)
    simple_pred = voting_simple.predict(X_holdout)
    results["voting_simple"] = {
        "mae": mean_absolute_error(y_holdout, simple_pred),
        "r2": r2_score(y_holdout, simple_pred),
    }

    # Weighted voting (optimal weights via simplex search)
    optimal_weights = find_optimal_weights(base_models, X_holdout, y_holdout)
    voting_weighted = create_voting_ensemble(base_models, weights=optimal_weights)
    voting_weighted.fit(X_train, y_train)
    weighted_pred = voting_weighted.predict(X_holdout)
    results["voting_weighted"] = {
        "mae": mean_absolute_error(y_holdout, weighted_pred),
        "r2": r2_score(y_holdout, weighted_pred),
    }

    # Stacking with Ridge meta-learner
    stacking = create_stacking_ensemble(base_models, cv=5)
    stacking.fit(X_train, y_train)
    stacking_pred = stacking.predict(X_holdout)
    results["stacking"] = {
        "mae": mean_absolute_error(y_holdout, stacking_pred),
        "r2": r2_score(y_holdout, stacking_pred),
    }

    # Identify best strategy
    best_strategy = min(results, key=lambda k: results[k]["mae"])

    logger.info(
        f"Best strategy for {position}_{stat}: {best_strategy} "
        f"(MAE: {results[best_strategy]['mae']:.2f})"
    )

    return {
        "results": results,
        "best_strategy": best_strategy,
        "optimal_weights": optimal_weights,
        "n_models": len(base_models),
    }
