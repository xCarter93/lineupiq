"""
Tests for API setup and model loading infrastructure.

Tests FastAPI app initialization, health endpoint, and model loader utilities.
"""

from fastapi.testclient import TestClient

from lineupiq.api import app
from lineupiq.api.models_loader import get_position_models, load_models


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
        assert data["models_loaded"] > 0
        # Should have all 13 models: QB (2) + RB (5) + WR (3) + TE (3)
        assert data["models_loaded"] == 13


def test_load_models() -> None:
    """Verify load_models() returns dict with expected model count."""
    models = load_models()

    assert isinstance(models, dict)
    assert len(models) == 13

    # Verify expected model names exist
    expected_models = [
        "QB_passing_yards",
        "QB_passing_tds",
        "RB_rushing_yards",
        "RB_rushing_tds",
        "RB_carries",
        "RB_receiving_yards",
        "RB_receptions",
        "WR_receiving_yards",
        "WR_receiving_tds",
        "WR_receptions",
        "TE_receiving_yards",
        "TE_receiving_tds",
        "TE_receptions",
    ]

    for model_name in expected_models:
        assert model_name in models, f"Missing model: {model_name}"


def test_get_position_models() -> None:
    """Verify get_position_models() filters correctly for each position."""
    models = load_models()

    # Test QB models (should have 2)
    qb_models = get_position_models(models, "QB")
    assert len(qb_models) == 2
    assert "passing_yards" in qb_models
    assert "passing_tds" in qb_models
    # Keys should NOT have position prefix
    assert "QB_passing_yards" not in qb_models

    # Test RB models (should have 5)
    rb_models = get_position_models(models, "RB")
    assert len(rb_models) == 5
    assert "rushing_yards" in rb_models
    assert "rushing_tds" in rb_models
    assert "carries" in rb_models
    assert "receiving_yards" in rb_models
    assert "receptions" in rb_models

    # Test WR models (should have 3)
    wr_models = get_position_models(models, "WR")
    assert len(wr_models) == 3
    assert "receiving_yards" in wr_models
    assert "receiving_tds" in wr_models
    assert "receptions" in wr_models

    # Test TE models (should have 3)
    te_models = get_position_models(models, "TE")
    assert len(te_models) == 3
    assert "receiving_yards" in te_models
    assert "receiving_tds" in te_models
    assert "receptions" in te_models
