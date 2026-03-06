"""
Simulation API routes for season backtesting.

Provides endpoints to initialize, advance, and query simulation state.
These endpoints trigger the simulation CLI operations and return status.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from lineupiq.models.over_under import compute_over_under_edge
from lineupiq.models.regression_mean import compute_regression_signal
from lineupiq.simulation.monte_carlo import simulate_player_outcomes
from lineupiq.simulation.state import (
    SimulationState,
    load_state,
    save_state,
    initialize_state,
    reset_state,
)
from lineupiq.simulation.batch_predict import load_predictions

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to simulation CLI script
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "scripts"


class SimulationInitRequest(BaseModel):
    """Request to initialize a simulation."""

    target_season: int = 2025
    quick: bool = False


class SimulationAdvanceRequest(BaseModel):
    """Request to advance simulation to a specific week."""

    to_week: int
    quick: bool = False


class SimulationStateResponse(BaseModel):
    """Response with simulation state."""

    name: str
    target_season: int
    training_seasons: list[int]
    current_week: int
    status: str
    last_trained_at: str | None
    created_at: str | None
    updated_at: str | None


class SimulationStatusResponse(BaseModel):
    """Response with full simulation status including prediction counts."""

    state: SimulationStateResponse | None
    predictions: dict[str, int] | None  # week -> count
    message: str


class MonteCarloRequest(BaseModel):
    mean: float
    lower_bound: float
    upper_bound: float
    line: float | None = None
    n_simulations: int = 10_000


class OverUnderRequest(BaseModel):
    prediction_mean: float
    lower_bound: float
    upper_bound: float
    line: float
    market_over_probability: float = 0.5


class RegressionMeanRequest(BaseModel):
    actual_fp_recent: float
    xfp_recent: float


def run_simulation_command(command: list[str]) -> None:
    """Run simulation CLI command in background.

    Args:
        command: Command arguments for simulate_season.py
    """
    script_path = SCRIPTS_DIR / "simulate_season.py"
    full_command = [sys.executable, str(script_path)] + command

    logger.info(f"Running simulation command: {' '.join(full_command)}")

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=SCRIPTS_DIR.parent,
        )
        if result.returncode != 0:
            logger.error(f"Simulation command failed: {result.stderr}")
        else:
            logger.info(f"Simulation command completed successfully")
    except Exception as e:
        logger.error(f"Error running simulation command: {e}")


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status() -> SimulationStatusResponse:
    """Get current simulation status.

    Returns:
        SimulationStatusResponse with state and prediction counts.
    """
    state = load_state()

    if state is None:
        return SimulationStatusResponse(
            state=None,
            predictions=None,
            message="No simulation found. Use POST /simulation/init to create one.",
        )

    # Get prediction counts by week
    predictions = load_predictions(state.target_season)
    prediction_counts: dict[str, int] | None = None

    if predictions is not None:
        by_week = predictions.group_by("week").count()
        prediction_counts = {
            str(row["week"]): row["count"]
            for row in by_week.to_dicts()
        }

    return SimulationStatusResponse(
        state=SimulationStateResponse(
            name=state.name,
            target_season=state.target_season,
            training_seasons=state.training_seasons,
            current_week=state.current_week,
            status=state.status,
            last_trained_at=state.last_trained_at,
            created_at=state.created_at,
            updated_at=state.updated_at,
        ),
        predictions=prediction_counts,
        message=f"Simulation at week {state.current_week}, status: {state.status}",
    )


@router.post("/init")
async def initialize_simulation(
    request: SimulationInitRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Initialize a new season simulation.

    This creates the simulation state and triggers background training.
    Training runs asynchronously - check /status for progress.

    Args:
        request: SimulationInitRequest with target_season and quick flag.
        background_tasks: FastAPI background tasks for async execution.

    Returns:
        Dict with simulation ID and status message.
    """
    # Check if simulation already exists
    existing = load_state()
    if existing and existing.status != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Simulation already in progress (status: {existing.status}). "
            f"Wait for completion or reset first.",
        )

    # Create initial state
    state = initialize_state(
        target_season=request.target_season,
        training_seasons=list(range(2022, request.target_season)),
    )
    state.status = "training"
    save_state(state)

    # Build command
    command = ["init", f"--target-season={request.target_season}"]
    if request.quick:
        command.append("--quick")

    # Run in background
    background_tasks.add_task(run_simulation_command, command)

    return {
        "status": "started",
        "message": f"Simulation initialization started for {request.target_season}. "
        f"Check /simulation/status for progress.",
        "target_season": request.target_season,
    }


@router.post("/advance")
async def advance_simulation(
    request: SimulationAdvanceRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Advance simulation to incorporate new week's data.

    Triggers model retraining with the new week's actual data and
    regenerates predictions for remaining weeks.

    Args:
        request: SimulationAdvanceRequest with target week and quick flag.
        background_tasks: FastAPI background tasks for async execution.

    Returns:
        Dict with status message.

    Raises:
        HTTPException: If no simulation exists or invalid week.
    """
    state = load_state()

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="No simulation found. Use POST /simulation/init first.",
        )

    if state.status != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Simulation is busy (status: {state.status}). Wait for completion.",
        )

    if request.to_week <= state.current_week:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance to week {request.to_week}. "
            f"Current week is {state.current_week}.",
        )

    if request.to_week > 18:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid week {request.to_week}. Max is 18.",
        )

    # Update state to show advancing
    state.status = "advancing"
    save_state(state)

    # Build command
    command = ["advance", f"--week={request.to_week}"]
    if request.quick:
        command.append("--quick")

    # Run in background
    background_tasks.add_task(run_simulation_command, command)

    return {
        "status": "started",
        "message": f"Advancing to week {request.to_week}. Check /simulation/status for progress.",
        "from_week": state.current_week,
        "to_week": request.to_week,
    }


@router.post("/reset")
async def reset_simulation() -> dict[str, Any]:
    """Reset simulation to week 0.

    Clears current week progress but keeps prediction files.

    Returns:
        Dict with status message.

    Raises:
        HTTPException: If no simulation exists.
    """
    state = load_state()

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="No simulation found.",
        )

    state = reset_state(state)
    save_state(state)

    return {
        "status": "reset",
        "message": "Simulation reset to week 0.",
        "current_week": 0,
    }


@router.get("/predictions/{week}")
async def get_week_predictions(week: int, position: str | None = None) -> dict[str, Any]:
    """Get predictions for a specific week.

    Args:
        week: Week number (1-18).
        position: Optional position filter (QB, RB, WR, TE).

    Returns:
        Dict with predictions for the week.

    Raises:
        HTTPException: If no simulation or predictions found.
    """
    state = load_state()

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="No simulation found.",
        )

    predictions = load_predictions(state.target_season)

    if predictions is None:
        raise HTTPException(
            status_code=404,
            detail="No predictions found. Run simulation init first.",
        )

    # Filter to requested week
    week_preds = predictions.filter(predictions["week"] == week)

    if week_preds.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for week {week}.",
        )

    # Optionally filter by position
    if position:
        week_preds = week_preds.filter(week_preds["position"] == position.upper())

    return {
        "week": week,
        "season": state.target_season,
        "count": len(week_preds),
        "predictions": week_preds.to_dicts(),
    }


def _calculate_defense_points_allowed_score(points_allowed: int) -> float:
    """Calculate fantasy points from defense points allowed (bracket-based)."""
    if points_allowed <= 0:
        return 10.0
    if points_allowed <= 6:
        return 7.0
    if points_allowed <= 13:
        return 4.0
    if points_allowed <= 20:
        return 1.0
    if points_allowed <= 27:
        return 0.0
    if points_allowed <= 34:
        return -1.0
    return -4.0


@router.get("/actuals/{week}")
async def get_week_actuals(week: int, position: str | None = None) -> dict[str, Any]:
    """Get actual stats for a completed week.

    Args:
        week: Week number (1-18).
        position: Optional position filter (QB, RB, WR, TE, K, DEF).

    Returns:
        Dict with actual stats for the week.

    Raises:
        HTTPException: If no simulation found or week not completed.
    """
    from lineupiq.data.fetchers import fetch_player_stats, fetch_schedules
    from lineupiq.data.defense_processing import process_defense_data
    from lineupiq.data.kicker_processing import process_kicker_data

    state = load_state()

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="No simulation found.",
        )

    # Check if week is completed (has actuals)
    completed_weeks = state.current_week - 1  # current_week is what we're predicting
    if week > completed_weeks:
        raise HTTPException(
            status_code=400,
            detail=f"Week {week} is not completed yet. Current completed weeks: {completed_weeks}",
        )

    actuals = []
    positions_to_fetch = [position.upper()] if position else ["QB", "RB", "WR", "TE", "K", "DEF"]

    try:
        # Fetch skill position stats (QB, RB, WR, TE)
        skill_positions = [p for p in positions_to_fetch if p in ["QB", "RB", "WR", "TE"]]
        if skill_positions:
            all_stats = fetch_player_stats([state.target_season], summary_level="week")
            stats = all_stats.filter(all_stats["week"] == week)
            if skill_positions != ["QB", "RB", "WR", "TE"]:
                stats = stats.filter(stats["position"].is_in(skill_positions))

            for row in stats.to_dicts():
                fantasy_pts = 0.0
                fantasy_pts += (row.get("passing_yards") or 0) * 0.04
                fantasy_pts += (row.get("passing_tds") or 0) * 4
                fantasy_pts += (row.get("passing_interceptions") or 0) * -2
                fantasy_pts += (row.get("rushing_yards") or 0) * 0.1
                fantasy_pts += (row.get("rushing_tds") or 0) * 6
                fantasy_pts += (row.get("receiving_yards") or 0) * 0.1
                fantasy_pts += (row.get("receiving_tds") or 0) * 6
                fantasy_pts += (row.get("receptions") or 0) * 1
                fantasy_pts += (row.get("fumbles_lost") or 0) * -2

                actuals.append({
                    "player_id": row.get("player_id") or row.get("gsis_id"),
                    "player_name": row.get("player_display_name") or row.get("player_name"),
                    "position": row.get("position"),
                    "team": row.get("recent_team") or row.get("team"),
                    "week": week,
                    "season": state.target_season,
                    "fantasy_points": round(fantasy_pts, 2),
                    "passing_yards": row.get("passing_yards"),
                    "passing_tds": row.get("passing_tds"),
                    "interceptions": row.get("passing_interceptions"),
                    "rushing_yards": row.get("rushing_yards"),
                    "rushing_tds": row.get("rushing_tds"),
                    "receiving_yards": row.get("receiving_yards"),
                    "receiving_tds": row.get("receiving_tds"),
                    "receptions": row.get("receptions"),
                })

        # Fetch kicker stats (use process_kicker_data for computed distance buckets)
        if "K" in positions_to_fetch:
            kicker_data = process_kicker_data([state.target_season])
            kicker_week = kicker_data.filter(kicker_data["week"] == week)

            for row in kicker_week.to_dicts():
                fg_made = row.get("fg_made") or 0
                pat_made = row.get("pat_made") or 0
                # Get FG attempts by distance bucket
                fg_att_0_39 = row.get("fg_att_0_39") or 0
                fg_att_40_49 = row.get("fg_att_40_49") or 0
                fg_att_50_plus = row.get("fg_att_50_plus") or 0
                # Kicker scoring by distance: 3 pts (0-39), 4 pts (40-49), 5 pts (50+), 1 pt PAT
                # Use made counts for scoring, attempts for comparison
                fg_made_short = (row.get("fg_made_0_19") or 0) + (row.get("fg_made_20_29") or 0) + (row.get("fg_made_30_39") or 0)
                fg_made_med = row.get("fg_made_40_49") or 0
                fg_made_long = (row.get("fg_made_50_59") or 0) + (row.get("fg_made_60_") or 0)
                fantasy_pts = (fg_made_short * 3.0) + (fg_made_med * 4.0) + (fg_made_long * 5.0) + (pat_made * 1.0)

                actuals.append({
                    "player_id": row.get("player_id"),
                    "player_name": row.get("player_name"),
                    "position": "K",
                    "team": row.get("recent_team"),
                    "week": week,
                    "season": state.target_season,
                    "fantasy_points": round(fantasy_pts, 2),
                    "fg_made": fg_made,
                    "fg_att": row.get("fg_att") or 0,
                    "fg_att_0_39": fg_att_0_39,
                    "fg_att_40_49": fg_att_40_49,
                    "fg_att_50_plus": fg_att_50_plus,
                    "pat_made": pat_made,
                    "pat_att": row.get("pat_att") or 0,
                })

        # Fetch defense stats
        if "DEF" in positions_to_fetch:
            def_data = process_defense_data([state.target_season])
            def_week = def_data.filter(def_data["week"] == week)

            for row in def_week.to_dicts():
                points_allowed = int(row.get("points_allowed") or 0)
                def_sacks = row.get("def_sacks") or 0
                def_ints = row.get("def_interceptions") or 0
                def_fumbles = row.get("def_fumbles") or 0
                total_def_tds = row.get("total_def_tds") or 0

                fantasy_pts = _calculate_defense_points_allowed_score(points_allowed)
                fantasy_pts += def_sacks * 1.0
                fantasy_pts += def_ints * 2.0
                fantasy_pts += def_fumbles * 2.0
                fantasy_pts += total_def_tds * 6.0

                team = row.get("team")
                actuals.append({
                    "player_id": f"DEF_{team}",
                    "player_name": f"{team} Defense",
                    "position": "DEF",
                    "team": team,
                    "week": week,
                    "season": state.target_season,
                    "fantasy_points": round(fantasy_pts, 2),
                    "points_allowed": points_allowed,
                    "def_sacks": def_sacks,
                    "def_interceptions": def_ints,
                    "def_fumbles": def_fumbles,
                    "total_def_tds": total_def_tds,
                })

    except Exception as e:
        logger.error(f"Error fetching actuals for week {week}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching actuals: {str(e)}",
        )

    return {
        "week": week,
        "season": state.target_season,
        "count": len(actuals),
        "actuals": actuals,
    }


@router.post("/monte-carlo")
async def run_monte_carlo(request: MonteCarloRequest) -> dict[str, Any]:
    """Generate distribution-based outcome summary for a player stat."""
    summary = simulate_player_outcomes(
        mean=request.mean,
        lower_bound=request.lower_bound,
        upper_bound=request.upper_bound,
        n_simulations=request.n_simulations,
        line=request.line,
    )
    return {
        "mean": summary.mean,
        "median": summary.median,
        "floor_p10": summary.floor_p10,
        "ceiling_p90": summary.ceiling_p90,
        "p25": summary.p25,
        "p75": summary.p75,
        "std_dev": summary.std_dev,
        "hit_rate_over_line": summary.hit_rate_over_line,
    }


@router.post("/over-under")
async def run_over_under(request: OverUnderRequest) -> dict[str, Any]:
    """Compare model distribution to market line and return edge."""
    edge = compute_over_under_edge(
        prediction_mean=request.prediction_mean,
        lower_bound=request.lower_bound,
        upper_bound=request.upper_bound,
        line=request.line,
        market_over_probability=request.market_over_probability,
    )
    return {
        "line": edge.line,
        "model_over_probability": edge.model_over_probability,
        "market_over_probability": edge.market_over_probability,
        "edge": edge.edge,
        "recommendation": edge.recommendation,
    }


@router.post("/regression-mean")
async def run_regression_mean(request: RegressionMeanRequest) -> dict[str, Any]:
    """Compute buy-low / sell-high signal from actual-vs-expected FP."""
    signal = compute_regression_signal(
        actual_fp_recent=request.actual_fp_recent,
        xfp_recent=request.xfp_recent,
    )
    return {
        "luck_factor": signal.luck_factor,
        "label": signal.label,
        "confidence": signal.confidence,
    }
