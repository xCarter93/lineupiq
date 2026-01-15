"""
Prediction routes for all positions (QB, RB, WR, TE).

Each endpoint accepts feature values and returns predicted stats
for the specified position.
"""

import numpy as np
from fastapi import APIRouter, Request

from lineupiq.api.models_loader import get_position_models
from lineupiq.api.schemas import (
    PredictionRequest,
    QBPredictionResponse,
    RBPredictionResponse,
    ReceiverPredictionResponse,
)
from lineupiq.features import get_feature_columns

router = APIRouter()


def prepare_features(request: PredictionRequest) -> np.ndarray:
    """Convert prediction request to numpy array for model inference.

    Extracts feature values in the exact order expected by the model,
    converting boolean fields to floats.

    Args:
        request: PredictionRequest with all feature fields.

    Returns:
        2D numpy array of shape (1, 17) for single prediction.
    """
    feature_columns = get_feature_columns()
    feature_values = []

    for col in feature_columns:
        value = getattr(request, col)
        # Convert booleans to float
        if isinstance(value, bool):
            value = float(value)
        feature_values.append(value)

    return np.array([feature_values], dtype=np.float32)


@router.post("/qb", response_model=QBPredictionResponse)
async def predict_qb(request: PredictionRequest, req: Request) -> QBPredictionResponse:
    """Predict QB passing stats.

    Takes feature values and returns predicted passing yards and TDs.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        QBPredictionResponse with passing_yards and passing_tds.
    """
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, "QB")

    passing_yards = round(float(models["passing_yards"].predict(features)[0]), 1)
    passing_tds = round(float(models["passing_tds"].predict(features)[0]), 1)

    return QBPredictionResponse(
        passing_yards=passing_yards,
        passing_tds=passing_tds,
    )


@router.post("/rb", response_model=RBPredictionResponse)
async def predict_rb(request: PredictionRequest, req: Request) -> RBPredictionResponse:
    """Predict RB rushing and receiving stats.

    Takes feature values and returns predicted rushing yards, TDs, carries,
    receiving yards, and receptions.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        RBPredictionResponse with all 5 stat predictions.
    """
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, "RB")

    rushing_yards = round(float(models["rushing_yards"].predict(features)[0]), 1)
    rushing_tds = round(float(models["rushing_tds"].predict(features)[0]), 1)
    carries = round(float(models["carries"].predict(features)[0]), 1)
    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    return RBPredictionResponse(
        rushing_yards=rushing_yards,
        rushing_tds=rushing_tds,
        carries=carries,
        receiving_yards=receiving_yards,
        receptions=receptions,
    )


@router.post("/wr", response_model=ReceiverPredictionResponse)
async def predict_wr(
    request: PredictionRequest, req: Request
) -> ReceiverPredictionResponse:
    """Predict WR receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, and receptions.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        ReceiverPredictionResponse with receiving_yards, receiving_tds, and receptions.
    """
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, "WR")

    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receiving_tds = round(float(models["receiving_tds"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    return ReceiverPredictionResponse(
        receiving_yards=receiving_yards,
        receiving_tds=receiving_tds,
        receptions=receptions,
    )


@router.post("/te", response_model=ReceiverPredictionResponse)
async def predict_te(
    request: PredictionRequest, req: Request
) -> ReceiverPredictionResponse:
    """Predict TE receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, and receptions.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        ReceiverPredictionResponse with receiving_yards, receiving_tds, and receptions.
    """
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, "TE")

    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receiving_tds = round(float(models["receiving_tds"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    return ReceiverPredictionResponse(
        receiving_yards=receiving_yards,
        receiving_tds=receiving_tds,
        receptions=receptions,
    )
