"""
Model loading utilities for the prediction API.

Loads all trained models at startup and provides utilities for
filtering models by position.
"""

import logging
from typing import Any

from lineupiq.models import list_models, load_model

logger = logging.getLogger(__name__)


def load_models() -> dict[str, Any]:
    """Load all trained models from disk.

    Uses lineupiq.models.list_models() to discover all saved models,
    then loads each one using lineupiq.models.load_model().

    Returns:
        Dict mapping model names (e.g., "QB_passing_yards") to loaded
        XGBoost model objects.

    Example:
        >>> models = load_models()
        >>> len(models)
        13
        >>> "QB_passing_yards" in models
        True
    """
    models: dict[str, Any] = {}

    model_list = list_models()
    logger.info(f"Found {len(model_list)} models to load")

    for position, target in model_list:
        model_name = f"{position}_{target}"
        model, _metadata = load_model(position, target)
        models[model_name] = model
        logger.debug(f"Loaded model: {model_name}")

    logger.info(f"Successfully loaded {len(models)} models")
    return models


def get_position_models(models: dict[str, Any], position: str) -> dict[str, Any]:
    """Filter models dict to only those for a specific position.

    Args:
        models: Dict of all loaded models (from load_models()).
        position: Position prefix to filter by (e.g., "QB", "RB", "WR", "TE").

    Returns:
        Dict mapping target names (without position prefix) to model objects.
        For example, if position="QB", returns {"passing_yards": model, "passing_tds": model}.

    Example:
        >>> models = load_models()
        >>> qb_models = get_position_models(models, "QB")
        >>> "passing_yards" in qb_models
        True
        >>> "QB_passing_yards" in qb_models
        False
    """
    position_models: dict[str, Any] = {}
    prefix = f"{position}_"

    for model_name, model in models.items():
        if model_name.startswith(prefix):
            # Strip position prefix from key
            target = model_name[len(prefix) :]
            position_models[target] = model

    return position_models
