"""
Tests for prediction cache functionality.

Includes unit tests for PredictionCache class and integration tests
for cache behavior in prediction endpoints.
"""

import time

import pytest
from fastapi.testclient import TestClient

from lineupiq.api.cache import PredictionCache
from lineupiq.api.main import app


# =============================================================================
# Unit tests for PredictionCache
# =============================================================================


@pytest.fixture
def cache() -> PredictionCache:
    """Create a fresh cache instance for testing."""
    return PredictionCache(max_size=10, ttl_seconds=60)


def test_cache_set_get(cache: PredictionCache) -> None:
    """Test that set values can be retrieved with get."""
    features = {"feature_a": 1.0, "feature_b": 2.0}
    response = {"prediction": 100.5}

    cache.set("QB", features, response)
    result = cache.get("QB", features)

    assert result == response


def test_cache_miss(cache: PredictionCache) -> None:
    """Test that get returns None for non-existent keys."""
    features = {"feature_a": 1.0}

    result = cache.get("QB", features)

    assert result is None


def test_cache_expiration() -> None:
    """Test that expired entries return None."""
    cache = PredictionCache(max_size=10, ttl_seconds=0.1)
    features = {"feature_a": 1.0}
    response = {"prediction": 100.5}

    cache.set("QB", features, response)

    # Verify it's there initially
    assert cache.get("QB", features) == response

    # Wait for expiration
    time.sleep(0.2)

    # Should be expired now
    assert cache.get("QB", features) is None


def test_cache_max_size() -> None:
    """Test that old entries are evicted when max_size is exceeded."""
    cache = PredictionCache(max_size=3, ttl_seconds=60)

    # Add 3 entries (at capacity)
    cache.set("QB", {"id": 1}, {"result": 1})
    cache.set("QB", {"id": 2}, {"result": 2})
    cache.set("QB", {"id": 3}, {"result": 3})

    # All 3 should be present
    assert cache.get("QB", {"id": 1}) is not None
    assert cache.get("QB", {"id": 2}) is not None
    assert cache.get("QB", {"id": 3}) is not None

    # Add 4th entry - should evict oldest (id=1)
    cache.set("QB", {"id": 4}, {"result": 4})

    # id=1 should be evicted
    assert cache.get("QB", {"id": 1}) is None
    # Others should remain
    assert cache.get("QB", {"id": 2}) is not None
    assert cache.get("QB", {"id": 3}) is not None
    assert cache.get("QB", {"id": 4}) is not None


def test_cache_stats(cache: PredictionCache) -> None:
    """Test that hits and misses are tracked correctly."""
    features = {"feature_a": 1.0}
    response = {"prediction": 100.5}

    # Initial stats
    stats = cache.stats()
    assert stats["size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0

    # Miss
    cache.get("QB", features)
    assert cache.stats()["misses"] == 1

    # Set and hit
    cache.set("QB", features, response)
    assert cache.stats()["size"] == 1

    cache.get("QB", features)
    assert cache.stats()["hits"] == 1

    # Another miss with different features
    cache.get("QB", {"different": "features"})
    assert cache.stats()["misses"] == 2


def test_cache_clear(cache: PredictionCache) -> None:
    """Test that clear empties the cache and resets stats."""
    features = {"feature_a": 1.0}
    response = {"prediction": 100.5}

    cache.set("QB", features, response)
    cache.get("QB", features)  # Hit
    cache.get("QB", {"different": "features"})  # Miss

    # Verify non-empty
    assert cache.stats()["size"] > 0
    assert cache.stats()["hits"] > 0

    # Clear
    cache.clear()

    stats = cache.stats()
    assert stats["size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0


def test_cache_different_positions(cache: PredictionCache) -> None:
    """Test that same features with different positions are cached separately."""
    features = {"feature_a": 1.0}
    qb_response = {"passing_yards": 250}
    rb_response = {"rushing_yards": 80}

    cache.set("QB", features, qb_response)
    cache.set("RB", features, rb_response)

    assert cache.get("QB", features) == qb_response
    assert cache.get("RB", features) == rb_response


# =============================================================================
# Integration tests with TestClient
# =============================================================================


@pytest.fixture
def client():
    """Create test client with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# Sample prediction request data
SAMPLE_REQUEST = {
    "passing_yards_roll3": 250.5,
    "passing_tds_roll3": 1.8,
    "rushing_yards_roll3": 15.0,
    "rushing_tds_roll3": 0.2,
    "carries_roll3": 3.0,
    "receiving_yards_roll3": 0.0,
    "receiving_tds_roll3": 0.0,
    "receptions_roll3": 0.0,
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


def test_prediction_caching(client: TestClient) -> None:
    """Test that duplicate predictions return cached responses with HIT header."""
    # Clear cache before test
    client.delete("/cache")

    # First request - should be MISS
    response1 = client.post("/predict/qb", json=SAMPLE_REQUEST)
    assert response1.status_code == 200
    assert response1.headers.get("X-Cache") == "MISS"

    # Second request with same data - should be HIT
    response2 = client.post("/predict/qb", json=SAMPLE_REQUEST)
    assert response2.status_code == 200
    assert response2.headers.get("X-Cache") == "HIT"

    # Responses should be identical
    assert response1.json() == response2.json()


def test_cache_stats_endpoint(client: TestClient) -> None:
    """Test that GET /cache/stats returns expected keys."""
    response = client.get("/cache/stats")
    assert response.status_code == 200

    data = response.json()
    assert "size" in data
    assert "max_size" in data
    assert "hits" in data
    assert "misses" in data


def test_cache_clear_endpoint(client: TestClient) -> None:
    """Test that DELETE /cache clears the cache."""
    # Make a prediction to populate cache
    client.post("/predict/qb", json=SAMPLE_REQUEST)

    # Check stats before clear
    stats_before = client.get("/cache/stats").json()
    assert stats_before["size"] > 0 or stats_before["hits"] > 0 or stats_before["misses"] > 0

    # Clear cache
    response = client.delete("/cache")
    assert response.status_code == 200
    assert response.json() == {"cleared": True}

    # Check stats after clear
    stats_after = client.get("/cache/stats").json()
    assert stats_after["size"] == 0
    assert stats_after["hits"] == 0
    assert stats_after["misses"] == 0


def test_all_positions_use_cache(client: TestClient) -> None:
    """Test that all position endpoints support caching."""
    # Clear cache
    client.delete("/cache")

    for position in ["qb", "rb", "wr", "te"]:
        # First call - MISS
        r1 = client.post(f"/predict/{position}", json=SAMPLE_REQUEST)
        assert r1.status_code == 200
        assert r1.headers.get("X-Cache") == "MISS", f"{position} should return MISS first time"

        # Second call - HIT
        r2 = client.post(f"/predict/{position}", json=SAMPLE_REQUEST)
        assert r2.status_code == 200
        assert r2.headers.get("X-Cache") == "HIT", f"{position} should return HIT second time"
