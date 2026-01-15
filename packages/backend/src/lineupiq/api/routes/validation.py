"""
Validation routes for model accuracy metrics.

Provides endpoints to fetch model validation results from backtesting.
"""

from fastapi import APIRouter, HTTPException

from lineupiq.api.schemas.validation import ValidationResponse, ModelMetrics, OverallMetrics
from lineupiq.models import (
    load_holdout_data,
    run_all_backtests,
    summarize_backtest_results,
)

router = APIRouter()


@router.get("/metrics", response_model=ValidationResponse)
async def get_validation_metrics(season: int = 2025) -> ValidationResponse:
    """Get model validation metrics from backtesting.

    Runs backtest on holdout season data if not cached,
    returns accuracy metrics for all models.

    Args:
        season: Season to validate against (default 2025).

    Returns:
        ValidationResponse with overall and per-model metrics.
    """
    try:
        # Load holdout data
        holdout_df = load_holdout_data(season=season)

        if len(holdout_df) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No holdout data available for season {season}"
            )

        # Run backtests
        backtest_results = run_all_backtests(holdout_df)

        if not backtest_results:
            raise HTTPException(
                status_code=500,
                detail="Backtesting failed - no results returned"
            )

        # Summarize results
        summary = summarize_backtest_results(backtest_results)

        # Convert to response schema
        overall = OverallMetrics(
            overall_accuracy_pct=summary["overall_accuracy_pct"],
            overall_confidence=summary["overall_confidence"],
            model_count=len(summary["by_model"]),
        )

        by_model = [
            ModelMetrics(
                position=m["position"],
                target=m["target"],
                accuracy_pct=m["accuracy_pct"],
                confidence=m["confidence"],
                mae=m["mae"],
                rmse=m["rmse"],
                r2=m["r2"],
                sample_count=m["sample_count"],
            )
            for m in summary["by_model"]
        ]

        return ValidationResponse(
            overall=overall,
            by_model=by_model,
            validation_season=season,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {e}")


@router.get("/metrics/{position}", response_model=list[ModelMetrics])
async def get_position_metrics(position: str, season: int = 2025) -> list[ModelMetrics]:
    """Get validation metrics for a specific position.

    Args:
        position: Player position (QB, RB, WR, TE).
        season: Validation season.

    Returns:
        List of ModelMetrics for all targets of that position.
    """
    # Reuse the full metrics endpoint and filter
    full_response = await get_validation_metrics(season=season)
    return [m for m in full_response.by_model if m.position.upper() == position.upper()]
