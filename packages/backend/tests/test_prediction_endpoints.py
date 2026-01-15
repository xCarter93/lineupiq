"""
Tests for prediction API endpoints.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from lineupiq.api.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the API with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_features() -> dict:
    """Sample feature values for testing predictions."""
    return {
        "passing_yards_roll3": 250.0,
        "passing_tds_roll3": 1.8,
        "rushing_yards_roll3": 15.0,
        "rushing_tds_roll3": 0.2,
        "carries_roll3": 3.0,
        "receiving_yards_roll3": 45.0,
        "receiving_tds_roll3": 0.3,
        "receptions_roll3": 4.5,
        "opp_pass_defense_strength": 0.95,
        "opp_rush_defense_strength": 1.05,
        "opp_pass_yards_allowed_rank": 15.0,
        "opp_rush_yards_allowed_rank": 20.0,
        "opp_total_yards_allowed_rank": 18.0,
        "temp_normalized": 0.6,
        "wind_normalized": 0.2,
        "is_home": True,
        "is_dome": False,
    }


def test_qb_prediction(client: TestClient, sample_features: dict) -> None:
    """Test QB prediction endpoint returns valid response."""
    response = client.post("/predict/qb", json=sample_features)

    assert response.status_code == 200
    data = response.json()

    # Verify response has expected keys
    assert "passing_yards" in data
    assert "passing_tds" in data

    # Verify values are reasonable (not NaN or extreme)
    assert 0 <= data["passing_yards"] <= 500
    assert 0 <= data["passing_tds"] <= 8


def test_rb_prediction(client: TestClient, sample_features: dict) -> None:
    """Test RB prediction endpoint returns valid response."""
    response = client.post("/predict/rb", json=sample_features)

    assert response.status_code == 200
    data = response.json()

    # Verify response has all 5 RB stat keys
    assert "rushing_yards" in data
    assert "rushing_tds" in data
    assert "carries" in data
    assert "receiving_yards" in data
    assert "receptions" in data

    # Verify values are reasonable
    assert 0 <= data["rushing_yards"] <= 250
    assert 0 <= data["rushing_tds"] <= 5
    assert 0 <= data["carries"] <= 40
    assert 0 <= data["receiving_yards"] <= 150
    assert 0 <= data["receptions"] <= 15


def test_wr_prediction(client: TestClient, sample_features: dict) -> None:
    """Test WR prediction endpoint returns valid response."""
    response = client.post("/predict/wr", json=sample_features)

    assert response.status_code == 200
    data = response.json()

    # Verify response has 3 receiver stat keys
    assert "receiving_yards" in data
    assert "receiving_tds" in data
    assert "receptions" in data

    # Verify values are reasonable
    assert 0 <= data["receiving_yards"] <= 250
    assert 0 <= data["receiving_tds"] <= 4
    assert 0 <= data["receptions"] <= 20


def test_te_prediction(client: TestClient, sample_features: dict) -> None:
    """Test TE prediction endpoint returns valid response."""
    response = client.post("/predict/te", json=sample_features)

    assert response.status_code == 200
    data = response.json()

    # Verify response has 3 receiver stat keys
    assert "receiving_yards" in data
    assert "receiving_tds" in data
    assert "receptions" in data

    # Verify values are reasonable
    assert 0 <= data["receiving_yards"] <= 200
    assert 0 <= data["receiving_tds"] <= 3
    assert 0 <= data["receptions"] <= 15


def test_invalid_request(client: TestClient) -> None:
    """Test that missing fields return 422 validation error."""
    # Missing required fields
    incomplete_request = {
        "passing_yards_roll3": 250.0,
        "passing_tds_roll3": 1.8,
        # Missing all other fields
    }

    response = client.post("/predict/qb", json=incomplete_request)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
