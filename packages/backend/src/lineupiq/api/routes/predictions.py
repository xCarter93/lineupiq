"""
Prediction routes for all positions (QB, RB, WR, TE, K, DEF).

Each endpoint accepts feature values and returns predicted stats
for the specified position. Responses are cached to reduce redundant
model inference.
"""

import numpy as np
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from lineupiq.api.models_loader import get_position_models
from lineupiq.api.schemas import (
    DefensePrediction,
    DefensePredictionRequest,
    DefensePredictionResponse,
    KickerPrediction,
    KickerPredictionRequest,
    KickerPredictionResponse,
    PredictionRequest,
    QBPredictionResponse,
    RBPredictionResponse,
    ReceiverPredictionResponse,
)
from lineupiq.data.defense_processing import get_defense_feature_columns
from lineupiq.data.kicker_processing import get_kicker_feature_columns
from lineupiq.features import get_feature_columns

router = APIRouter()

def _predict_with_intervals(
    model: object,
    mapie_model: object | None,
    features: np.ndarray,
    floor_zero: bool = False,
) -> dict[str, float]:
    """Make a prediction with optional conformal intervals.

    Args:
        model: Base model (LightGBM/XGBoost/ensemble).
        mapie_model: MAPIE CrossConformalRegressor for intervals (or None).
        features: Feature array of shape (1, n_features).
        floor_zero: If True, clamp prediction and bounds at 0.

    Returns:
        Dict with "prediction", and optionally "lower_90" and "upper_90".
    """
    pred = float(model.predict(features)[0])
    if floor_zero:
        pred = max(0.0, pred)
    result = {"prediction": round(pred, 1)}

    if mapie_model is not None:
        try:
            # MAPIE 1.3+ API: predict_interval returns (preds, intervals)
            # intervals shape: (n_samples, 2, n_confidence_levels)
            _, intervals = mapie_model.predict_interval(features)
            lower = float(intervals[0, 0, 0])
            upper = float(intervals[0, 1, 0])
            if floor_zero:
                lower = max(0.0, lower)
                upper = max(0.0, upper)
            result["lower_90"] = round(lower, 1)
            result["upper_90"] = round(upper, 1)
        except Exception:
            pass  # Silently skip intervals if MAPIE fails

    return result


def prepare_features(request: PredictionRequest) -> np.ndarray:
    """Convert prediction request to numpy array for model inference.

    Extracts feature values in the exact order expected by the model,
    converting boolean fields to floats.

    Args:
        request: PredictionRequest with all 40 feature fields.

    Returns:
        2D numpy array of shape (1, 40) for single prediction.
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
    """Predict all QB fantasy-relevant stats.

    Takes feature values and returns predicted passing yards, TDs, interceptions,
    rushing yards, rushing TDs, and fumbles lost. Responses are cached.

    Args:
        request: PredictionRequest with all 40 feature fields (Phase 20+21).
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with all 6 QB stat predictions and X-Cache header.
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
    mapie_models = get_position_models(
        getattr(req.app.state, "mapie_models", {}), position
    )

    # Predict all 6 QB targets with optional intervals
    targets = {
        "passing_yards": False,
        "passing_tds": False,
        "interceptions": True,
        "rushing_yards": False,
        "rushing_tds": True,
        "fumbles_lost": True,
    }
    response_data: dict[str, object] = {}
    intervals: dict[str, dict[str, float]] = {}

    for target, floor_zero in targets.items():
        result = _predict_with_intervals(
            models[target], mapie_models.get(target), features, floor_zero=floor_zero
        )
        response_data[target] = result["prediction"]
        if "lower_90" in result:
            intervals[target] = {"lower_90": result["lower_90"], "upper_90": result["upper_90"]}

    if intervals:
        response_data["intervals"] = intervals

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/rb")
async def predict_rb(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict all RB fantasy-relevant stats.

    Takes feature values and returns all 7 RB predictions:
    - Rushing: rushing_yards, rushing_tds, carries
    - Receiving: receiving_yards, receptions, receiving_tds
    - Turnovers: fumbles_lost

    Responses are cached to reduce redundant model inference.

    Args:
        request: PredictionRequest with all 28 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with all 7 stat predictions and X-Cache header.
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
    mapie_models = get_position_models(
        getattr(req.app.state, "mapie_models", {}), position
    )

    # Predict all 7 RB targets with optional intervals
    targets = {
        "rushing_yards": False,
        "rushing_tds": True,
        "carries": False,
        "receiving_yards": False,
        "receptions": False,
        "receiving_tds": True,
        "fumbles_lost": True,
    }
    response_data: dict[str, object] = {}
    intervals: dict[str, dict[str, float]] = {}

    for target, floor_zero in targets.items():
        result = _predict_with_intervals(
            models[target], mapie_models.get(target), features, floor_zero=floor_zero
        )
        response_data[target] = result["prediction"]
        if "lower_90" in result:
            intervals[target] = {"lower_90": result["lower_90"], "upper_90": result["upper_90"]}

    if intervals:
        response_data["intervals"] = intervals

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/wr")
async def predict_wr(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict WR receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, receptions,
    and fumbles lost. Responses are cached.

    Args:
        request: PredictionRequest with all 28 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with all 4 WR stat predictions and X-Cache header.
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
    mapie_models = get_position_models(
        getattr(req.app.state, "mapie_models", {}), position
    )

    targets = {
        "receiving_yards": False,
        "receiving_tds": True,
        "receptions": False,
        "fumbles_lost": True,
    }
    response_data: dict[str, object] = {}
    intervals: dict[str, dict[str, float]] = {}

    for target, floor_zero in targets.items():
        result = _predict_with_intervals(
            models[target], mapie_models.get(target), features, floor_zero=floor_zero
        )
        response_data[target] = result["prediction"]
        if "lower_90" in result:
            intervals[target] = {"lower_90": result["lower_90"], "upper_90": result["upper_90"]}

    if intervals:
        response_data["intervals"] = intervals

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


@router.post("/te")
async def predict_te(request: PredictionRequest, req: Request) -> JSONResponse:
    """Predict TE receiving stats.

    Takes feature values and returns predicted receiving yards, TDs, receptions,
    and fumbles lost. Responses are cached.

    Args:
        request: PredictionRequest with all 28 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with all 4 TE stat predictions and X-Cache header.
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
    mapie_models = get_position_models(
        getattr(req.app.state, "mapie_models", {}), position
    )

    targets = {
        "receiving_yards": False,
        "receiving_tds": True,
        "receptions": False,
        "fumbles_lost": True,
    }
    response_data: dict[str, object] = {}
    intervals: dict[str, dict[str, float]] = {}

    for target, floor_zero in targets.items():
        result = _predict_with_intervals(
            models[target], mapie_models.get(target), features, floor_zero=floor_zero
        )
        response_data[target] = result["prediction"]
        if "lower_90" in result:
            intervals[target] = {"lower_90": result["lower_90"], "upper_90": result["upper_90"]}

    if intervals:
        response_data["intervals"] = intervals

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


def prepare_kicker_features(request: KickerPredictionRequest) -> np.ndarray:
    """Convert kicker prediction request to numpy array for model inference.

    Extracts feature values in the exact order expected by the kicker model.

    Args:
        request: KickerPredictionRequest with kicker feature fields.

    Returns:
        2D numpy array of shape (1, 3) for single prediction.
    """
    feature_columns = get_kicker_feature_columns()
    feature_values = []

    for col in feature_columns:
        value = getattr(request, col)
        feature_values.append(value)

    return np.array([feature_values], dtype=np.float32)


@router.post("/k")
async def predict_kicker(
    request: KickerPredictionRequest, req: Request
) -> JSONResponse:
    """Predict kicker stats.

    Takes kicker feature values and returns predicted FG attempts by distance
    and PAT attempts. Responses are cached.

    Args:
        request: KickerPredictionRequest with 3 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with kicker predictions and X-Cache header.
    """
    position = "K"
    features_dict = request.model_dump()
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, features_dict)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_kicker_features(request)
    models = get_position_models(req.app.state.models, position)

    # Predict each target, ensuring non-negative values
    kicker_targets = ["fg_att", "fg_att_0_39", "fg_att_40_49", "fg_att_50_plus", "pat_att"]
    predictions_dict: dict[str, float] = {}

    for target in kicker_targets:
        if target in models:
            pred = max(0.0, round(float(models[target].predict(features)[0]), 1))
            predictions_dict[target] = pred
        else:
            predictions_dict[target] = 0.0

    response_data = {"predictions": predictions_dict}

    # Store in cache
    cache.set(position, features_dict, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})


def prepare_defense_features(request: DefensePredictionRequest) -> np.ndarray:
    """Convert defense prediction request to numpy array for model inference.

    Extracts feature values in the exact order expected by the defense model.

    Args:
        request: DefensePredictionRequest with defense feature fields.

    Returns:
        2D numpy array of shape (1, 5) for single prediction.
    """
    feature_columns = get_defense_feature_columns()
    feature_values = []

    for col in feature_columns:
        value = getattr(request, col)
        feature_values.append(value)

    return np.array([feature_values], dtype=np.float32)


@router.post("/defense/{team}")
async def predict_defense(
    team: str,
    opponent: str,
    week: int,
    request: DefensePredictionRequest,
    req: Request,
) -> JSONResponse:
    """Predict team defense stats.

    Takes team defense feature values and returns predicted defensive stats
    (points allowed, sacks, interceptions, fumbles, TDs). Responses are cached.

    Args:
        team: NFL team abbreviation (e.g., "PHI", "DAL").
        opponent: Opponent team abbreviation.
        week: NFL week number.
        request: DefensePredictionRequest with 5 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        JSONResponse with defense predictions and X-Cache header.
    """
    position = "DEF"
    features_dict = request.model_dump()
    cache_key = {**features_dict, "team": team, "opponent": opponent, "week": week}
    cache = req.app.state.cache

    # Check cache
    cached = cache.get(position, cache_key)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT"})

    # Cache miss - run prediction
    features = prepare_defense_features(request)
    models = get_position_models(req.app.state.models, position)

    # Defense targets match model naming (using def_ prefix from nflreadpy)
    defense_targets = [
        "points_allowed",
        "def_sacks",
        "def_interceptions",
        "def_fumbles",
        "total_def_tds",
    ]

    predictions_dict: dict[str, float] = {}

    for target in defense_targets:
        if target in models:
            pred = round(float(models[target].predict(features)[0]), 1)
            # Non-negative except points_allowed can be any value
            if target != "points_allowed":
                pred = max(0.0, pred)
            predictions_dict[target] = pred
        else:
            # Default values if model not found
            defaults = {
                "points_allowed": 21.0,
                "def_sacks": 2.0,
                "def_interceptions": 1.0,
                "def_fumbles": 0.5,
                "total_def_tds": 0.2,
            }
            predictions_dict[target] = defaults.get(target, 0.0)

    response_data = {
        "team": team.upper(),
        "opponent": opponent.upper(),
        "week": week,
        "predictions": predictions_dict,
    }

    # Store in cache
    cache.set(position, cache_key, response_data)

    return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})
