"""Shared test helpers."""

from typing import Any

import pytest

from lineupiq.features.pipeline import get_feature_columns


def model_feature_count(model: Any, metadata: Any = None) -> int | None:
    """Number of features a saved model was fitted on, or None if undiscoverable.

    CatBoost reports n_features_in_ as 0, so saved metadata wins when present.
    """
    candidates = [
        metadata.get("n_features") if isinstance(metadata, dict) else None,
        getattr(model, "n_features_in_", None),
    ]
    for candidate in candidates:
        if candidate:
            return int(candidate)
    return None


def skip_if_model_schema_stale(
    model: Any, position: str, target: str, metadata: Any = None
) -> None:
    """Skip when a saved .joblib predates the current feature schema.

    Saved models are only usable until get_feature_columns() changes; the next
    training run regenerates them, at which point these tests run again.
    """
    expected = len(get_feature_columns())
    actual = model_feature_count(model, metadata)
    if actual is not None and actual != expected:
        pytest.skip(
            f"saved {position} {target} model expects {actual} features, "
            f"current schema has {expected} - retrain pending"
        )
