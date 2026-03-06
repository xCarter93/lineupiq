"""Monte Carlo simulation engine for distribution-based player outcomes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MonteCarloSummary:
    mean: float
    median: float
    floor_p10: float
    ceiling_p90: float
    p25: float
    p75: float
    std_dev: float
    hit_rate_over_line: float | None = None


def simulate_player_outcomes(
    mean: float,
    lower_bound: float,
    upper_bound: float,
    n_simulations: int = 10_000,
    line: float | None = None,
) -> MonteCarloSummary:
    """Simulate distribution of outcomes from conformal interval bounds.

    We approximate uncertainty with a normal distribution parameterized from
    interval width: sigma ~= (upper-lower)/(2*1.645) for ~90% bounds.
    """
    spread = max(upper_bound - lower_bound, 1e-6)
    sigma = spread / (2 * 1.645)
    sims = np.random.normal(loc=mean, scale=sigma, size=n_simulations)
    sims = np.clip(sims, a_min=0.0, a_max=None)

    hit_rate = None
    if line is not None:
        hit_rate = float(np.mean(sims > line))

    return MonteCarloSummary(
        mean=float(np.mean(sims)),
        median=float(np.percentile(sims, 50)),
        floor_p10=float(np.percentile(sims, 10)),
        ceiling_p90=float(np.percentile(sims, 90)),
        p25=float(np.percentile(sims, 25)),
        p75=float(np.percentile(sims, 75)),
        std_dev=float(np.std(sims)),
        hit_rate_over_line=hit_rate,
    )


def simulate_correlated_outcomes(
    means: np.ndarray,
    covariance: np.ndarray,
    n_simulations: int = 10_000,
) -> np.ndarray:
    """Simulate correlated player outcomes for stacks (QB-WR, game scripts)."""
    sims = np.random.multivariate_normal(means, covariance, size=n_simulations)
    return np.clip(sims, a_min=0.0, a_max=None)
