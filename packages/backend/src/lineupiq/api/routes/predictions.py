"""
Prediction routes for all positions (QB, RB, WR, TE).

Each endpoint accepts feature values and returns predicted stats
for the specified position. Responses are cached to reduce redundant
model inference.
"""

import numpy as np
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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


@router.post("/qb")
async def predict_qb(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict QB passing stats.

    Takes feature values and returns predicted passing yards and TDs.
    Responses are cached to reduce redundant inference.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with passing_yards, passing_tds, and X-Cache header.
    """
    position = "QB"
    features_dict = request.model_dump()
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, features_dict)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, position)

    passing_yards = round(float(models["passing_yards"].predict(features)[0]), 1)
    passing_tds = round(float(models["passing_tds"].predict(features)[0]), 1)

    response_data = {"passing_yards": passing_yards, "passing_tds": passing_tds}

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/rb")
async def predict_rb(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict RB rushing and receiving stats.

    Takes feature values and returns predicted rushing yards, TDs, carries,
    receiving yards, and receptions. Responses are cached.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with all 5 stat predictions and X-Cache header.
    """
    position = "RB"
    features_dict = request.model_dump()
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, features_dict)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, position)

    rushing_yards = round(float(models["rushing_yards"].predict(features)[0]), 1)
    rushing_tds = round(float(models["rushing_tds"].predict(features)[0]), 1)
    carries = round(float(models["carries"].predict(features)[0]), 1)
    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    response_data = {
        "rushing_yards": rushing_yards,
        "rushing_tds": rushing_tds,
        "carries": carries,
        "receiving_yards": receiving_yards,
        "receptions": receptions,
    }

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/wr")
async def predict_wr(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict WR receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, and receptions.
    Responses are cached.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with receiving_yards, receiving_tds, receptions, and X-Cache header.
    """
    position = "WR"
    features_dict = request.model_dump()
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, features_dict)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, position)

    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receiving_tds = round(float(models["receiving_tds"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    response_data = {
        "receiving_yards": receiving_yards,
        "receiving_tds": receiving_tds,
        "receptions": receptions,
    }

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/te")
async def predict_te(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict TE receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, and receptions.
    Responses are cached.

    Args:
        request: PredictionRequest with all 17 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with receiving_yards, receiving_tds, receptions, and X-Cache header.
    """
    position = "TE"
    features_dict = request.model_dump()
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, features_dict)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_features(request)
    models = get_position_models(req.app.state.models, position)

    receiving_yards = round(float(models["receiving_yards"].predict(features)[0]), 1)
    receiving_tds = round(float(models["receiving_tds"].predict(features)[0]), 1)
    receptions = round(float(models["receptions"].predict(features)[0]), 1)

    response_data = {
        "receiving_yards": receiving_yards,
        "receiving_tds": receiving_tds,
        "receptions": receptions,
    }

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})
