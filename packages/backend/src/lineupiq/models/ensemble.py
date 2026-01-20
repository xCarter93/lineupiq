"""
Ensemble infrastructure for combining LightGBM and XGBoost models.

Provides VotingRegressor and StackingRegressor wrappers for three ensemble strategies:
- Simple averaging: Equal weight to both models
- Weighted averaging: Custom weights based on validation performance
- Stacking: Meta-learner (Ridge) trained on base model predictions

Key functions:
- create_voting_ensemble: Create VotingRegressor with optional weights
- create_stacking_ensemble: Create StackingRegressor with Ridge meta-learner
- save_ensemble: Save ensemble model to disk
- load_ensemble: Load ensemble model from disk
- benchmark_ensemble_strategies: Benchmark all strategies on holdout data
"""

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
    lgbm_model: Any,
    xgb_model: Any,
    weights: list[float] | None = None,
) -> VotingRegressor:
    """Create VotingRegressor ensemble for averaging predictions.

    Args:
        lgbm_model: Trained LightGBM model.
        xgb_model: Trained XGBoost model.
        weights: Optional weights for weighted averaging [lgbm_weight, xgb_weight].
            If None, uses simple averaging (equal weights).

    Returns:
        VotingRegressor ensemble ready for fitting or prediction.

    Example:
        >>> from lineupiq.models import load_model, create_voting_ensemble
        >>> lgbm, _ = load_model("QB", "passing_yards_lgbm")
        >>> xgb, _ = load_model("QB", "passing_yards_xgb")
        >>> # Simple averaging
        >>> ensemble = create_voting_ensemble(lgbm, xgb)
        >>> # Weighted averaging (60% LightGBM, 40% XGBoost)
        >>> ensemble = create_voting_ensemble(lgbm, xgb, weights=[0.6, 0.4])
    """
    estimators = [
        ("lgbm", lgbm_model),
        ("xgb", xgb_model),
    ]

    if weights is None:
        logger.info("Creating simple voting ensemble (equal weights)")
        voting_reg = VotingRegressor(estimators=estimators)
    else:
        logger.info(f"Creating weighted voting ensemble with weights={weights}")
        voting_reg = VotingRegressor(estimators=estimators, weights=weights)

    return voting_reg


def create_stacking_ensemble(
    lgbm_model: Any,
    xgb_model: Any,
    cv: int = 5,
) -> StackingRegressor:
    """Create StackingRegressor ensemble with Ridge meta-learner.

    Uses cross-validation to generate out-of-fold predictions for meta-learner training,
    preventing overfitting. Ridge regularization handles correlated base predictions.

    Args:
        lgbm_model: Trained LightGBM model.
        xgb_model: Trained XGBoost model.
        cv: Number of cross-validation folds for meta-learner training (default: 5).

    Returns:
        StackingRegressor ensemble ready for fitting or prediction.

    Example:
        >>> from lineupiq.models import load_model, create_stacking_ensemble
        >>> lgbm, _ = load_model("QB", "passing_yards_lgbm")
        >>> xgb, _ = load_model("QB", "passing_yards_xgb")
        >>> ensemble = create_stacking_ensemble(lgbm, xgb, cv=5)
        >>> ensemble.fit(X_train, y_train)
        >>> predictions = ensemble.predict(X_test)
    """
    estimators = [
        ("lgbm", lgbm_model),
        ("xgb", xgb_model),
    ]

    # Ridge with alpha=1.0 prevents overfitting on correlated base predictions
    meta_learner = Ridge(alpha=1.0)

    logger.info(f"Creating stacking ensemble with cv={cv}, meta-learner=Ridge(alpha=1.0)")
    stacking_reg = StackingRegressor(
        estimators=estimators,
        final_estimator=meta_learner,
        cv=cv,
        passthrough=False,  # Use only base predictions, not original features
    )

    return stacking_reg


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
        >>> from lineupiq.models import save_ensemble
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
        >>> from lineupiq.models import load_ensemble
        >>> ensemble = load_ensemble("QB", "passing_yards", "voting_simple")
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

    Loads LightGBM and XGBoost models for position/stat, evaluates 5 strategies
    on holdout data (lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking),
    and identifies the best performer by lowest MAE.

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
        - correlation: Correlation between LightGBM and XGBoost predictions (diversity metric)
        - optimal_weights: [lgbm_weight, xgb_weight] from grid search

    Raises:
        FileNotFoundError: If LightGBM or XGBoost model files don't exist.

    Example:
        >>> results = benchmark_ensemble_strategies(
        ...     "QB", "passing_yards", X_train, y_train, X_holdout, y_holdout
        ... )
        >>> results["best_strategy"]
        'stacking'
        >>> results["results"]["stacking"]["mae"]
        45.2
    """
    logger.info(f"Benchmarking ensemble strategies for {position}_{stat}")

    # Load pre-trained models
    # LightGBM models use base name (e.g., "passing_yards")
    # XGBoost models use _xgb suffix (e.g., "passing_yards_xgb")
    try:
        lgbm_model, _ = load_model(position, stat)
        xgb_model, _ = load_model(position, f"{stat}_xgb")
    except FileNotFoundError as e:
        logger.error(f"Models not found for {position}_{stat}: {e}")
        raise

    # Strategy 1: LightGBM solo
    logger.info(f"Evaluating lgbm_solo for {position}_{stat}")
    lgbm_pred_holdout = lgbm_model.predict(X_holdout)
    lgbm_mae = mean_absolute_error(y_holdout, lgbm_pred_holdout)
    lgbm_r2 = r2_score(y_holdout, lgbm_pred_holdout)

    # Strategy 2: XGBoost solo
    logger.info(f"Evaluating xgb_solo for {position}_{stat}")
    xgb_pred_holdout = xgb_model.predict(X_holdout)
    xgb_mae = mean_absolute_error(y_holdout, xgb_pred_holdout)
    xgb_r2 = r2_score(y_holdout, xgb_pred_holdout)

    # Check prediction diversity (correlation)
    correlation = np.corrcoef(lgbm_pred_holdout, xgb_pred_holdout)[0, 1]
    logger.info(f"Base model correlation: {correlation:.3f}")

    # Strategy 3: Simple voting (equal weights)
    logger.info(f"Evaluating voting_simple for {position}_{stat}")
    voting_simple = create_voting_ensemble(lgbm_model, xgb_model)
    voting_simple.fit(X_train, y_train)
    voting_simple_pred = voting_simple.predict(X_holdout)
    voting_simple_mae = mean_absolute_error(y_holdout, voting_simple_pred)
    voting_simple_r2 = r2_score(y_holdout, voting_simple_pred)

    # Strategy 4: Weighted voting (grid search for optimal weights)
    logger.info(f"Grid searching optimal weights for {position}_{stat}")
    best_mae = float("inf")
    best_weights = [0.5, 0.5]

    # Grid search: 0.0, 0.05, 0.10, ..., 1.0 for lgbm weight
    for lgbm_weight in np.linspace(0, 1, 21):
        xgb_weight = 1 - lgbm_weight
        weights = [lgbm_weight, xgb_weight]

        # Create weighted ensemble
        voting_weighted = create_voting_ensemble(lgbm_model, xgb_model, weights=weights)
        voting_weighted.fit(X_train, y_train)
        weighted_pred = voting_weighted.predict(X_holdout)
        weighted_mae = mean_absolute_error(y_holdout, weighted_pred)

        if weighted_mae < best_mae:
            best_mae = weighted_mae
            best_weights = weights

    logger.info(f"Optimal weights: {best_weights} (MAE: {best_mae:.2f})")

    # Evaluate with optimal weights
    voting_weighted = create_voting_ensemble(lgbm_model, xgb_model, weights=best_weights)
    voting_weighted.fit(X_train, y_train)
    voting_weighted_pred = voting_weighted.predict(X_holdout)
    voting_weighted_mae = mean_absolute_error(y_holdout, voting_weighted_pred)
    voting_weighted_r2 = r2_score(y_holdout, voting_weighted_pred)

    # Strategy 5: Stacking with Ridge meta-learner
    logger.info(f"Evaluating stacking for {position}_{stat}")
    stacking = create_stacking_ensemble(lgbm_model, xgb_model, cv=5)
    stacking.fit(X_train, y_train)
    stacking_pred = stacking.predict(X_holdout)
    stacking_mae = mean_absolute_error(y_holdout, stacking_pred)
    stacking_r2 = r2_score(y_holdout, stacking_pred)

    # Compile results
    results = {
        "lgbm_solo": {"mae": lgbm_mae, "r2": lgbm_r2},
        "xgb_solo": {"mae": xgb_mae, "r2": xgb_r2},
        "voting_simple": {"mae": voting_simple_mae, "r2": voting_simple_r2},
        "voting_weighted": {"mae": voting_weighted_mae, "r2": voting_weighted_r2},
        "stacking": {"mae": stacking_mae, "r2": stacking_r2},
    }

    # Identify best strategy
    best_strategy = min(results, key=lambda k: results[k]["mae"])

    logger.info(f"Best strategy for {position}_{stat}: {best_strategy} (MAE: {results[best_strategy]['mae']:.2f})")

    return {
        "results": results,
        "best_strategy": best_strategy,
        "correlation": correlation,
        "optimal_weights": best_weights,
    }
