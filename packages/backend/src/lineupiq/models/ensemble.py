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
"""

import logging
from pathlib import Path
from typing import Any, Literal

import joblib
from sklearn.ensemble import StackingRegressor, VotingRegressor
from sklearn.linear_model import Ridge

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
