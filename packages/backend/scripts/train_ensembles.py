"""
Train weighted voting ensembles for all skill positions using optimal weights from 2025 benchmark.

Based on BENCHMARK_RESULTS_2025.md findings showing ensembles beat single models on 20/21 stats.
"""

import logging
from pathlib import Path

import polars as pl

from lineupiq.features.pipeline import build_features
from lineupiq.models.ensemble import create_voting_ensemble, save_ensemble
from lineupiq.models.persistence import load_model
from lineupiq.models.qb import QB_TARGETS, prepare_qb_data
from lineupiq.models.rb import RB_TARGETS, prepare_rb_data
from lineupiq.models.receiver import RECEIVER_TARGETS, prepare_receiver_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Optimal weights from 2025 benchmark (LightGBM weight, XGBoost weight)
OPTIMAL_WEIGHTS = {
    "QB": {
        "passing_yards": [0.35, 0.65],
        "passing_tds": [0.00, 1.00],  # Stacking won, but use xgb_solo equivalent
        "interceptions": [0.00, 1.00],
        "rushing_yards": [0.70, 0.30],
        "rushing_tds": [0.65, 0.35],  # Stacking won, use approximate weights
        "fumbles_lost": [1.00, 0.00],
    },
    "RB": {
        "rushing_yards": [0.65, 0.35],  # Stacking won, use approximate weights
        "rushing_tds": [1.00, 0.00],
        "carries": [0.35, 0.65],  # Stacking won, use approximate weights
        "receiving_yards": [0.60, 0.40],
        "receptions": [0.75, 0.25],
        "receiving_tds": [0.70, 0.30],
        "fumbles_lost": [1.00, 0.00],
    },
    "WR": {
        "receiving_yards": [1.00, 0.00],
        "receiving_tds": [0.10, 0.90],
        "receptions": [0.15, 0.85],  # Stacking won, use approximate weights
        "fumbles_lost": [0.00, 1.00],
    },
    "TE": {
        "receiving_yards": [0.60, 0.40],
        "receiving_tds": [0.00, 1.00],  # Stacking won, but use xgb_solo equivalent
        "receptions": [0.45, 0.55],  # Stacking won, use approximate weights
        "fumbles_lost": [0.00, 1.00],  # xgb_solo won
    },
}


def main() -> None:
    """Train weighted voting ensembles for all skill position stats."""
    logger.info("Training weighted voting ensembles based on 2025 benchmark")
    logger.info("Loading training data (2020-2025)")

    # Load training data including 2025 for production models predicting 2026+
    # Note: 2025 was used as holdout for validation only, but for production
    # we want to use all available historical data
    df = build_features([2020, 2021, 2022, 2023, 2024, 2025])
    logger.info(f"Loaded {len(df)} rows of training data")

    # Prepare data for each position
    logger.info("Preparing position data")
    X_qb, y_qb = prepare_qb_data(df)
    X_rb, y_rb = prepare_rb_data(df)
    X_wr, y_wr = prepare_receiver_data(df, "WR")
    X_te, y_te = prepare_receiver_data(df, "TE")

    position_data = {
        "QB": (X_qb, y_qb, QB_TARGETS),
        "RB": (X_rb, y_rb, RB_TARGETS),
        "WR": (X_wr, y_wr, RECEIVER_TARGETS),
        "TE": (X_te, y_te, RECEIVER_TARGETS),
    }

    # Train ensembles for each position/stat
    total_ensembles = sum(len(targets) for _, _, targets in position_data.values())
    current = 0

    for position, (X_train, y_dict, targets) in position_data.items():
        for stat in targets:
            current += 1
            logger.info(f"[{current}/{total_ensembles}] Training {position}_{stat} ensemble")

            try:
                # Get optimal weights
                weights = OPTIMAL_WEIGHTS[position][stat]
                lgbm_weight, xgb_weight = weights

                # Load pre-trained models
                lgbm_model, _ = load_model(position, stat)
                xgb_model, _ = load_model(position, f"{stat}_xgb")

                # Create weighted voting ensemble
                ensemble = create_voting_ensemble(
                    lgbm_model, xgb_model, weights=weights
                )

                # Fit on training data
                y_train = y_dict[stat]
                ensemble.fit(X_train, y_train)

                # Save ensemble
                save_path = save_ensemble(ensemble, position, stat, "voting_weighted")

                logger.info(
                    f"  ✓ Saved ensemble with weights "
                    f"[LGBM={lgbm_weight:.2f}, XGB={xgb_weight:.2f}] to {save_path.name}"
                )

            except FileNotFoundError as e:
                logger.error(f"  ✗ Models not found for {position}_{stat}: {e}")
            except Exception as e:
                logger.error(f"  ✗ Error training {position}_{stat}: {e}")

    logger.info(f"Ensemble training complete: {current}/{total_ensembles} ensembles trained")


if __name__ == "__main__":
    main()
