"""
In-memory caching for prediction responses.

Provides LRU cache with TTL expiration to reduce redundant model inference.
"""

import hashlib
import json
import time
from typing import Any


class PredictionCache:
    """In-memory cache for prediction responses.

    Features:
    - LRU eviction when max_size exceeded
    - TTL-based expiration
    - Hit/miss statistics for observability

    Thread safety: Not required (single-threaded uvicorn default).
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        """Initialize cache with size and TTL limits.

        Args:
            max_size: Maximum number of entries before LRU eviction.
            ttl_seconds: Time-to-live for entries in seconds.
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []  # Track access order for LRU
        self._hits = 0
        self._misses = 0

    def _make_key(self, position: str, features: dict[str, Any]) -> str:
        """Create deterministic hash from position and features.

        Args:
            position: Position type (QB, RB, WR, TE).
            features: Feature dict from request.

        Returns:
            SHA-256 hex digest of position + sorted features.
        """
        # Sort features for deterministic ordering
        sorted_features = json.dumps(features, sort_keys=True)
        key_data = f"{position}:{sorted_features}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, position: str, features: dict[str, Any]) -> Any | None:
        """Get cached response if exists and not expired.

        Args:
            position: Position type (QB, RB, WR, TE).
            features: Feature dict from request.

        Returns:
            Cached response if valid, None on miss or expiration.
        """
        key = self._make_key(position, features)

        if key not in self._cache:
            self._misses += 1
            return None

        response, timestamp = self._cache[key]
        current_time = time.time()

        # Check TTL expiration
        if current_time - timestamp > self.ttl_seconds:
            # Expired - remove and return None
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._misses += 1
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        self._hits += 1
        return response

    def set(self, position: str, features: dict[str, Any], response: Any) -> None:
        """Store response in cache.

        Evicts oldest entries (LRU) if over max_size.

        Args:
            position: Position type (QB, RB, WR, TE).
            features: Feature dict from request.
            response: Response to cache.
        """
        key = self._make_key(position, features)
        current_time = time.time()

        # Evict oldest entries if at capacity
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]

        # Store response with timestamp
        self._cache[key] = (response, current_time)

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def clear(self) -> None:
        """Empty the cache and reset statistics."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with size, max_size, hits, and misses.
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
        }
