"""
FastAPI application for LineupIQ predictions.

Uses lifespan context manager to load all trained models at startup.
Models are stored in app.state.models for fast inference.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from lineupiq.api.models_loader import load_models

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load models at startup and clean up at shutdown."""
    logger.info("Starting LineupIQ API - loading models...")
    app.state.models: dict[str, Any] = load_models()
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
