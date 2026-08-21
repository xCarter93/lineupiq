"""
Tests for API setup and model loading infrastructure.

Tests FastAPI app initialization, health endpoint, and model loader utilities.
"""

from fastapi.testclient import TestClient

from lineupiq.api import app
from lineupiq.api.models_loader import get_position_models, load_models
from lineupiq.models import QB_TARGETS, RB_TARGETS, RECEIVER_TARGETS
from lineupiq.models.defense import DEF_TARGETS
from lineupiq.models.kicker import KICKER_TARGETS

# Derived from the src target constants so adding a target doesn't rot these tests
EXPECTED_TARGETS_BY_POSITION = {
    "QB": QB_TARGETS,
    "RB": RB_TARGETS,
    "WR": RECEIVER_TARGETS,
    "TE": RECEIVER_TARGETS,
    "K": KICKER_TARGETS,
    "DEF": DEF_TARGETS,
}
EXPECTED_MODEL_COUNT = sum(len(t) for t in EXPECTED_TARGETS_BY_POSITION.values())


def test_app_exists() -> None:
    """Verify FastAPI app imports correctly with expected title."""
    assert app is not None
    assert app.title == "LineupIQ API"
    assert app.version == "0.1.0"


def test_health_endpoint() -> None:
    """Verify /health returns 200 with models_loaded count."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] == EXPECTED_MODEL_COUNT


def test_load_models() -> None:
    """Verify load_models() returns dict with expected model count."""
    models = load_models()

    assert isinstance(models, dict)
    assert len(models) == EXPECTED_MODEL_COUNT

    for position, targets in EXPECTED_TARGETS_BY_POSITION.items():
        for target in targets:
            model_name = f"{position}_{target}"
            assert model_name in models, f"Missing model: {model_name}"


def test_get_position_models() -> None:
    """Verify get_position_models() filters correctly for each position."""
    models = load_models()

    for position, targets in EXPECTED_TARGETS_BY_POSITION.items():
        position_models = get_position_models(models, position)

        assert len(position_models) == len(targets)
        for target in targets:
            assert target in position_models
            # Keys should NOT have position prefix
            assert f"{position}_{target}" not in position_models
