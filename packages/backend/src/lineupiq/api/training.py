"""
Training API endpoints for triggering model retraining.

This module provides endpoints to trigger async model training from the API.
Useful for weekly automated retraining as new game data comes in.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ProcessPoolExecutor

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router for training endpoints
router = APIRouter(prefix="/training", tags=["training"])

# Global state for tracking training (in production, use Redis or DB)
_training_status = {
    "is_running": False,
    "started_at": None,
    "completed_at": None,
    "progress": {"completed": 0, "total": 0},
    "error": None,
    "results": None
}


class TrainingStatus(str, Enum):
    """Training job status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingRequest(BaseModel):
    """Request body for starting a training job."""
    positions: Optional[List[str]] = Field(
        default=None,
        description="Positions to train (default: all)",
        example=["QB", "RB", "WR", "TE"]
    )
    seasons: Optional[List[int]] = Field(
        default=None,
        description="Seasons to train on (default: 2016-2025 excluding 2020)",
        example=[2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]
    )
    n_trials: int = Field(
        default=30,
        description="Number of Optuna trials for hyperparameter tuning",
        ge=1,
        le=100
    )
    rolling_window: int = Field(
        default=5,
        description="Rolling window size for feature engineering",
        ge=3,
        le=10
    )


class TrainingStatusResponse(BaseModel):
    """Response for training status."""
    status: TrainingStatus
    is_running: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, int] = Field(default_factory=lambda: {"completed": 0, "total": 0})
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


def _run_training_sync(
    positions: List[str],
    seasons: List[int],
    n_trials: int,
    rolling_window: int
) -> Dict[str, Any]:
    """
    Run training synchronously (called in background process).

    This runs in a separate process to avoid blocking the API.
    """
    try:
        # Import here to avoid loading heavy ML libs at API startup
        import sys
        from pathlib import Path

        # Add backend to path so we can import the training module
        backend_path = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(backend_path))

        from scripts.train_all import train_all_models

        logger.info(f"Starting training: positions={positions}, seasons={seasons}")
        results = train_all_models(
            positions=positions,
            seasons=seasons,
            n_trials=n_trials,
            rolling_window=rolling_window
        )

        logger.info(f"Training complete: {len(results) if results else 0} models trained")
        return results

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


async def _run_training_background(
    positions: List[str],
    seasons: List[int],
    n_trials: int,
    rolling_window: int
):
    """Run training in background process."""
    global _training_status

    try:
        _training_status["is_running"] = True
        _training_status["started_at"] = datetime.now()
        _training_status["completed_at"] = None
        _training_status["error"] = None
        _training_status["results"] = None
        _training_status["progress"] = {"completed": 0, "total": len(positions) * 5}  # rough estimate

        # Run in separate process to avoid blocking event loop
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=1) as executor:
            results = await loop.run_in_executor(
                executor,
                _run_training_sync,
                positions,
                seasons,
                n_trials,
                rolling_window
            )

        _training_status["is_running"] = False
        _training_status["completed_at"] = datetime.now()
        _training_status["results"] = {
            "models_trained": len(results) if results else 0,
            "positions": positions
        }

        logger.info(f"Training job completed successfully")

    except Exception as e:
        _training_status["is_running"] = False
        _training_status["completed_at"] = datetime.now()
        _training_status["error"] = str(e)
        logger.error(f"Training job failed: {e}", exc_info=True)


@router.post("/start", response_model=dict, summary="Start model training")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a background training job.

    This endpoint triggers async model training without blocking the API.
    Use GET /training/status to check progress.

    Example:
        POST /api/training/start
        {
            "positions": ["QB", "RB"],
            "seasons": [2022, 2023, 2024, 2025],
            "n_trials": 30
        }
    """
    global _training_status

    # Check if training is already running
    if _training_status["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Training is already in progress. Check /training/status for details."
        )

    # Use defaults if not provided
    positions = request.positions or ["QB", "RB", "WR", "TE", "K", "DEF"]
    seasons = request.seasons or [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]

    # Schedule background task
    background_tasks.add_task(
        _run_training_background,
        positions=positions,
        seasons=seasons,
        n_trials=request.n_trials,
        rolling_window=request.rolling_window
    )

    logger.info(f"Training job scheduled: {positions} positions, {len(seasons)} seasons")

    return {
        "status": "accepted",
        "message": "Training job started in background",
        "positions": positions,
        "seasons": seasons,
        "n_trials": request.n_trials
    }


@router.get("/status", response_model=TrainingStatusResponse, summary="Get training status")
async def get_training_status():
    """
    Get current training job status.

    Returns information about the currently running or last completed training job.
    """
    global _training_status

    if _training_status["is_running"]:
        status = TrainingStatus.RUNNING
    elif _training_status["error"]:
        status = TrainingStatus.FAILED
    elif _training_status["completed_at"]:
        status = TrainingStatus.COMPLETED
    else:
        status = TrainingStatus.IDLE

    return TrainingStatusResponse(
        status=status,
        is_running=_training_status["is_running"],
        started_at=_training_status["started_at"],
        completed_at=_training_status["completed_at"],
        progress=_training_status["progress"],
        error=_training_status["error"],
        results=_training_status["results"]
    )


@router.post("/cancel", summary="Cancel running training")
async def cancel_training():
    """
    Cancel the currently running training job.

    Note: This is best-effort cancellation. The training process may not stop immediately.
    """
    global _training_status

    if not _training_status["is_running"]:
        raise HTTPException(
            status_code=400,
            detail="No training job is currently running"
        )

    # In a production system, you'd send a signal to the background process
    # For now, we just mark it as cancelled
    _training_status["is_running"] = False
    _training_status["completed_at"] = datetime.now()
    _training_status["error"] = "Training cancelled by user"

    return {"status": "cancelled", "message": "Training job cancelled"}
