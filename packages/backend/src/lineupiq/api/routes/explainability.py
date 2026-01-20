"""
Explainability routes for SHAP-based prediction explanations.

Provides endpoint to explain individual predictions by showing feature
contributions using SHAP values.
"""

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from lineupiq.api.schemas import (
    ExplainabilityRequest,
    ExplainabilityResponse,
    FeatureContribution,
    FEATURE_DISPLAY_NAMES,
    TARGET_DISPLAY_NAMES,
    VALID_TARGETS,
)
from lineupiq.features import get_feature_columns
from lineupiq.models.importance import compute_shap_values
from lineupiq.models.persistence import load_model

router = APIRouter()


def prepare_features(request: ExplainabilityRequest) -> np.ndarray:
    """Convert explainability request to numpy array for model inference.

    Extracts feature values in the exact order expected by the model,
    converting boolean fields to floats.

    Args:
        request: ExplainabilityRequest with all feature fields.

    Returns:
        2D numpy array of shape (1, 28) for single prediction.
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


def generate_summary(
    prediction: float,
    target: str,
    contributions: list[FeatureContribution],
) -> str:
    """Generate natural language summary explaining the prediction.

    Builds a human-readable explanation highlighting the top positive
    and negative contributors to the prediction.

    Args:
        prediction: The predicted value.
        target: Target stat name (e.g., "passing_yards").
        contributions: List of feature contributions sorted by absolute impact.

    Returns:
        Natural language summary string (1-2 sentences).
    """
    target_display = TARGET_DISPLAY_NAMES.get(target, target.replace("_", " "))

    # Get top positive and negative contributors
    positive = [c for c in contributions if c.direction == "up"][:3]
    negative = [c for c in contributions if c.direction == "down"][:2]

    # Build the summary
    pred_str = f"{prediction:.0f}" if prediction >= 10 else f"{prediction:.1f}"

    if positive and negative:
        # Format: "Projected X {stat} - boosted by A and B, tempered by C."
        pos_factors = " and ".join([c.display_name.lower() for c in positive[:2]])
        neg_factors = " and ".join([c.display_name.lower() for c in negative[:1]])
        summary = f"Projected {pred_str} {target_display} - boosted by {pos_factors}, tempered by {neg_factors}."
    elif positive:
        # Only positive factors
        pos_factors = " and ".join([c.display_name.lower() for c in positive[:2]])
        summary = f"Projected {pred_str} {target_display} - driven by {pos_factors}."
    elif negative:
        # Only negative factors (rare)
        neg_factors = " and ".join([c.display_name.lower() for c in negative[:2]])
        summary = f"Projected {pred_str} {target_display} - limited by {neg_factors}."
    else:
        # No significant contributors
        summary = f"Projected {pred_str} {target_display} - prediction near baseline average."

    return summary


@router.post("/{position}/{target}", response_model=ExplainabilityResponse)
async def explain_prediction(
    position: str,
    target: str,
    request: ExplainabilityRequest,
    req: Request,
) -> ExplainabilityResponse:
    """Explain a prediction using SHAP feature contributions.

    Returns the predicted value along with feature contributions showing
    which features pushed the prediction up or down, and a natural language
    summary for decision support.

    Args:
        position: Player position (QB, RB, WR, TE).
        target: Target stat (e.g., passing_yards, rushing_yards).
        request: ExplainabilityRequest with all 28 feature fields.
        req: FastAPI Request object for accessing app state.

    Returns:
        ExplainabilityResponse with prediction, contributions, and summary.

    Raises:
        HTTPException: 400 if position or target is invalid.
    """
    # Validate position
    position_upper = position.upper()
    if position_upper not in VALID_TARGETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position '{position}'. Must be one of: {', '.join(VALID_TARGETS.keys())}",
        )

    # Validate target for position
    valid_targets = VALID_TARGETS[position_upper]
    if target not in valid_targets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target '{target}' for {position_upper}. Valid targets: {', '.join(valid_targets)}",
        )

    # Load the trained model
    try:
        model, metadata = load_model(position_upper, target)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for {position_upper}/{target}. Ensure models are trained.",
        )

    # Prepare features
    features = prepare_features(request)
    feature_columns = get_feature_columns()

    # Make prediction
    prediction = float(model.predict(features)[0])

    # Compute SHAP values
    shap_values, expected_value = compute_shap_values(model, features, feature_columns)

    # Build contributions list
    contributions: list[FeatureContribution] = []
    shap_row = shap_values[0]  # Single sample

    for i, col in enumerate(feature_columns):
        shap_val = float(shap_row[i])
        feature_value = float(features[0, i])

        contribution = FeatureContribution(
            feature=col,
            display_name=FEATURE_DISPLAY_NAMES.get(col, col.replace("_", " ").title()),
            value=round(feature_value, 3),
            contribution=round(shap_val, 3),
            direction="up" if shap_val >= 0 else "down",
        )
        contributions.append(contribution)

    # Sort by absolute contribution (most impactful first)
    contributions.sort(key=lambda c: abs(c.contribution), reverse=True)

    # Generate natural language summary
    summary = generate_summary(prediction, target, contributions)

    # Round prediction for display
    prediction = round(prediction, 1)

    return ExplainabilityResponse(
        position=position_upper,
        target=target,
        prediction=prediction,
        base_value=round(expected_value, 1),
        contributions=contributions,
        summary=summary,
    )
