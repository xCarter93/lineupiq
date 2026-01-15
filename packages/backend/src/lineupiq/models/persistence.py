"""
Model persistence utilities for saving and loading trained ML models.

Uses joblib for efficient serialization of XGBoost models with numpy arrays.
Models are saved with metadata for version tracking and reproducibility.

Key functions:
- save_model: Save model with metadata to disk
- load_model: Load model and metadata from disk
- list_models: List all saved models
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from xgboost import XGBRegressor

logger = logging.getLogger(__name__)

# Directory for saved model files
# Located at packages/backend/models/ (not in src/, these are artifacts)
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models"


def save_model(
    model: XGBRegressor,
    position: str,
    target: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Save trained model with metadata to disk.

    Creates artifact dict containing model, metadata, and feature names.
    Saves to MODELS_DIR/{position}_{target}.joblib.

    Args:
        model: Trained XGBRegressor model.
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        metadata: Optional metadata dict. Should include:
            - trained_at: ISO timestamp
            - n_samples: Number of training samples
            - best_params: Hyperparameters used
            - cv_scores: Cross-validation scores

    Returns:
        Path to the saved model file.

    Example:
        >>> model = XGBRegressor()
        >>> model.fit(X, y)
        >>> path = save_model(model, "QB", "passing_yards", {"n_samples": 1000})
        >>> path.exists()
        True
    """
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Build metadata with defaults
    if metadata is None:
        metadata = {}

    if "trained_at" not in metadata:
        metadata["trained_at"] = datetime.now(timezone.utc).isoformat()

    # Get feature names if available
    feature_names = None
    if hasattr(model, "feature_names_in_"):
        feature_names = list(model.feature_names_in_)

    # Create artifact
    artifact = {
        "model": model,
        "metadata": metadata,
        "feature_names": feature_names,
        "position": position,
        "target": target,
    }

    # Save to disk
    filename = f"{position}_{target}.joblib"
    filepath = MODELS_DIR / filename
    joblib.dump(artifact, filepath)

    logger.info(f"Saved model to {filepath}")
    return filepath


def load_model(position: str, target: str) -> tuple[XGBRegressor, dict[str, Any]]:
    """Load model and metadata from disk.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").

    Returns:
        Tuple of (trained model, metadata dict).

    Raises:
        FileNotFoundError: If model file doesn't exist.

    Example:
        >>> model, metadata = load_model("QB", "passing_yards")
        >>> model.predict(X_test)
    """
    filename = f"{position}_{target}.joblib"
    filepath = MODELS_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Model not found: {filepath}")

    artifact = joblib.load(filepath)

    model = artifact["model"]
    metadata = artifact.get("metadata", {})

    # Add artifact info to metadata for convenience
    metadata["position"] = artifact.get("position", position)
    metadata["target"] = artifact.get("target", target)
    metadata["feature_names"] = artifact.get("feature_names")

    logger.info(f"Loaded model from {filepath}")
    return model, metadata


def list_models() -> list[tuple[str, str]]:
    """List all saved models.

    Scans MODELS_DIR for .joblib files and extracts position/target from filenames.

    Returns:
        List of (position, target) tuples for all saved models.

    Example:
        >>> models = list_models()
        >>> ("QB", "passing_yards") in models
        True
    """
    if not MODELS_DIR.exists():
        return []

    models = []
    for filepath in MODELS_DIR.glob("*.joblib"):
        # Parse filename: {position}_{target}.joblib
        name = filepath.stem  # Remove .joblib extension
        parts = name.split("_", 1)  # Split on first underscore only
        if len(parts) == 2:
            position, target = parts
            models.append((position, target))

    logger.info(f"Found {len(models)} saved models")
    return models
