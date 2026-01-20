"""
Model loading utilities for the prediction API.

Loads all trained models at startup and provides utilities for
filtering models by position.
"""

import logging
from pathlib import Path
from typing import Any

from lineupiq.models import list_models, load_model
from lineupiq.models.ensemble import load_ensemble

logger = logging.getLogger(__name__)


def load_models() -> dict[str, Any]:
    """Load all trained models from disk.

    Prefers ensemble models (voting_weighted) over single models when available.

    NOTE: Ensemble Models Decision - UPDATED (Phase 19, 2026-01-20)
    ================================================================
    This API uses ENSEMBLE models (weighted voting) for production predictions.

    Initial benchmarking (Phase 19-03, 2024 holdout):
    - Trained on 2022-2023 (2 years)
    - Ensembles beat single models on only 1/21 stats (4.8%)
    - Decision: Keep single models

    Validation benchmarking (2025 holdout):
    - Trained on 2020-2024 (5 years)
    - Ensembles beat single models on 20/21 stats (95.2%)!
    - 2-4% improvement across most stats
    - Decision REVERSED: Adopt weighted voting ensembles

    Key insight: Ensembles require sufficient training data (5+ years) to outperform
    single models. With production-realistic training windows, ensembles consistently
    improve predictions.

    See:
    - .planning/phases/19-ensemble-models/BENCHMARK_RESULTS.md (2024 holdout)
    - .planning/phases/19-ensemble-models/BENCHMARK_RESULTS_2025.md (2025 holdout)

    Returns:
        Dict mapping model names (e.g., "QB_passing_yards") to loaded
        model objects (VotingRegressor ensembles or single LightGBM/XGBoost).

    Example:
        >>> models = load_models()
        >>> len(models)
        21
        >>> "QB_passing_yards" in models
        True
    """
    models: dict[str, Any] = {}

    model_list = list_models()
    logger.info(f"Found {len(model_list)} models to load")

    for position, target in model_list:
        model_name = f"{position}_{target}"

        # Try to load ensemble model first (preferred)
        try:
            model = load_ensemble(position, target, "voting_weighted")
            models[model_name] = model
            logger.debug(f"Loaded ensemble model: {model_name}")
        except FileNotFoundError:
            # Fall back to single model if ensemble not available
            model, _metadata = load_model(position, target)
            models[model_name] = model
            logger.debug(f"Loaded single model: {model_name} (ensemble not available)")

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
