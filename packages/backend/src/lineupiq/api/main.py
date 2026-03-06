"""
FastAPI application for LineupIQ predictions.

Uses lifespan context manager to load all trained models at startup.
Models are stored in app.state.models for fast inference.
Prediction cache is stored in app.state.cache for response caching.
"""

import logging
from threading import Lock
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lineupiq.api.cache import PredictionCache
from lineupiq.api.models_loader import load_mapie_models, load_models
from lineupiq.api.training import router as training_router
from lineupiq.api.routes import (
    explainability_router,
    roster_router,
    router,
    schedule_router,
    simulation_router,
    validation_router,
)

logger = logging.getLogger(__name__)
_models_reload_lock = Lock()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load models and initialize cache at startup."""
    logger.info("Starting LineupIQ API - loading models...")
    app.state.models: dict[str, Any] = load_models()
    app.state.mapie_models: dict[str, Any] = load_mapie_models()
    app.state.cache = PredictionCache()
    logger.info(f"Loaded {len(app.state.models)} models, {len(app.state.mapie_models)} MAPIE models")
    yield
    # Cleanup on shutdown if needed
    logger.info("Shutting down LineupIQ API")


app = FastAPI(
    title="LineupIQ API",
    version="0.1.0",
    description="Fantasy football player stat predictions",
    lifespan=lifespan,
)

# Configure CORS for frontend access
# Note: allow_origins=["*"] cannot be used with allow_credentials=True
# So we use allow_origin_regex to match localhost on any port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/predict", tags=["predictions"])
app.include_router(validation_router, prefix="/api/validation", tags=["validation"])
app.include_router(roster_router, prefix="/api", tags=["roster"])
app.include_router(explainability_router, prefix="/api/explain", tags=["explainability"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"])
app.include_router(schedule_router, prefix="/api/schedule", tags=["schedule"])
app.include_router(training_router, prefix="/api", tags=["training"])


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


@app.post("/api/models/reload")
async def reload_models() -> dict[str, Any]:
    """Reload model artifacts in-place without restarting the API process."""
    if not _models_reload_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Model reload already in progress")
    try:
        old_models = len(app.state.models)
        old_mapie = len(app.state.mapie_models)
        new_models = load_models()
        new_mapie_models = load_mapie_models()

        if not new_models:
            raise HTTPException(status_code=500, detail="No models found during reload")

        # Atomic replacement to avoid partial state.
        app.state.models = new_models
        app.state.mapie_models = new_mapie_models
        app.state.cache.clear()
        return {
            "status": "reloaded",
            "models_before": old_models,
            "models_after": len(new_models),
            "mapie_before": old_mapie,
            "mapie_after": len(new_mapie_models),
        }
    finally:
        _models_reload_lock.release()
