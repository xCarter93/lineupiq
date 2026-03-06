"""Over/under probability engine comparing model output to market lines."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, sqrt


@dataclass
class OverUnderEdge:
    line: float
    model_over_probability: float
    market_over_probability: float
    edge: float
    recommendation: str


def _norm_cdf(x: float, mean: float, std: float) -> float:
    z = (x - mean) / (std * sqrt(2))
    return 0.5 * (1 + erf(z))


def compute_over_under_edge(
    prediction_mean: float,
    lower_bound: float,
    upper_bound: float,
    line: float,
    market_over_probability: float = 0.5,
) -> OverUnderEdge:
    """Compute model-vs-market edge using interval-implied uncertainty."""
    spread = max(upper_bound - lower_bound, 1e-6)
    sigma = spread / (2 * 1.645)  # approximate 90% interval
    model_over_probability = 1.0 - _norm_cdf(line, prediction_mean, max(sigma, 1e-6))
    edge = model_over_probability - market_over_probability
    recommendation = "pass"
    if edge >= 0.05:
        recommendation = "over"
    elif edge <= -0.05:
        recommendation = "under"
    return OverUnderEdge(
        line=line,
        model_over_probability=float(model_over_probability),
        market_over_probability=float(market_over_probability),
        edge=float(edge),
        recommendation=recommendation,
    )
