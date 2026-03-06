"""Regression-to-mean scoring using expected fantasy points (xFP)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegressionSignal:
    luck_factor: float
    label: str
    confidence: float


def compute_regression_signal(actual_fp_recent: float, xfp_recent: float) -> RegressionSignal:
    """Compute buy-low / sell-high signal from actual minus expected FP."""
    luck_factor = actual_fp_recent - xfp_recent
    magnitude = abs(luck_factor)
    confidence = min(1.0, magnitude / 5.0)
    if luck_factor >= 2.0:
        label = "sell_high"
    elif luck_factor <= -2.0:
        label = "buy_low"
    else:
        label = "neutral"
    return RegressionSignal(
        luck_factor=float(luck_factor),
        label=label,
        confidence=float(confidence),
    )
