"""
Pydantic schemas for model validation API responses.
"""

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """Metrics for a single trained model."""
    position: str = Field(..., description="Player position (QB, RB, WR, TE)")
    target: str = Field(..., description="Target stat (passing_yards, etc.)")
    accuracy_pct: float = Field(..., description="Accuracy percentage 0-100")
    confidence: str = Field(..., description="Confidence tier: High, Medium, Low")
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    r2: float = Field(..., description="R-squared coefficient")
    sample_count: int = Field(..., description="Number of validation samples")


class OverallMetrics(BaseModel):
    """Aggregated metrics across all models."""
    overall_accuracy_pct: float = Field(..., description="Overall accuracy percentage")
    overall_confidence: str = Field(..., description="Overall confidence tier")
    model_count: int = Field(..., description="Number of models included")


class ValidationResponse(BaseModel):
    """Full validation results response."""
    overall: OverallMetrics
    by_model: list[ModelMetrics]
    validation_season: int = Field(..., description="Season used for validation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "overall": {
                        "overall_accuracy_pct": 72.5,
                        "overall_confidence": "Medium",
                        "model_count": 11,
                    },
                    "by_model": [
                        {
                            "position": "QB",
                            "target": "passing_yards",
                            "accuracy_pct": 75.2,
                            "confidence": "Medium",
                            "mae": 52.3,
                            "rmse": 68.1,
                            "r2": 0.42,
                            "sample_count": 340,
                        }
                    ],
                    "validation_season": 2025,
                }
            ]
        }
    }


class PredictionInterval(BaseModel):
    """Prediction interval for uncertainty quantification."""
    lower: float = Field(..., description="Lower bound of 90% interval")
    upper: float = Field(..., description="Upper bound of 90% interval")
    confidence: float = Field(default=0.9, description="Confidence level")
