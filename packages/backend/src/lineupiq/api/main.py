"""
FastAPI application for LineupIQ predictions.

Uses lifespan context manager to load all trained models at startup.
Models are stored in app.state.models for fast inference.
Prediction cache is stored in app.state.cache for response caching.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from lineupiq.api.cache import PredictionCache
from lineupiq.api.models_loader import load_models
from lineupiq.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load models and initialize cache at startup."""
    logger.info("Starting LineupIQ API - loading models...")
    app.state.models: dict[str, Any] = load_models()
    app.state.cache = PredictionCache()
    logger.info(f"Loaded {len(app.state.models)} models")
    yield
    # Cleanup on shutdown if needed
    logger.info("Shutting down LineupIQ API")


app = FastAPI(
    title="LineupIQ API",
    version="0.1.0",
    description="Fantasy football player stat predictions",
    lifespan=lifespan,
)


app.include_router(router, prefix="/predict", tags=["predictions"])


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict with status and count of loaded models.
    """
    return {
        "status": "healthy",
        "models_loaded": len(app.state.models),
    }


@app.get("/cache/stats")
async def cache_stats() -> dict[str, int]:
    """Get cache statistics.

    Returns:
        Dict with size, max_size, hits, and misses.
    """
    return app.state.cache.stats()


@app.delete("/cache")
async def clear_cache() -> dict[str, bool]:
    """Clear the prediction cache.

    Returns:
        Dict confirming cache was cleared.
    """
    app.state.cache.clear()
    return {"cleared": True}
