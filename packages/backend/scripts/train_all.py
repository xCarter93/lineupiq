#!/usr/bin/env python3
"""
Canonical training script for all LineupIQ models.

This is the single source of truth for retraining models. All other
training scripts should be considered deprecated.

Usage:
    # Train all positions with default settings (2022-2025, 30 trials)
    uv run python scripts/train_all.py

    # Quick training for testing (10 trials)
    uv run python scripts/train_all.py --quick

    # Train specific positions
    uv run python scripts/train_all.py --positions QB RB WR TE

    # Custom seasons
    uv run python scripts/train_all.py --seasons 2020 2021 2022 2023 2024 2025

    # Custom trial count
    uv run python scripts/train_all.py --trials 50
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train all LineupIQ prediction models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--positions",
        nargs="+",
        choices=["QB", "RB", "WR", "TE", "K", "DEF"],
        default=["QB", "RB", "WR", "TE", "K", "DEF"],
        help="Positions to train (default: all)"
    )

    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=[2022, 2023, 2024, 2025],
        help="Seasons to train on (default: 2022-2025)"
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=30,
        help="Number of Optuna trials for hyperparameter tuning (default: 30)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick training mode (10 trials, useful for testing)"
    )

    parser.add_argument(
        "--rolling-window",
        type=int,
        default=5,
        help="Rolling window size for feature engineering (default: 5)"
    )

    return parser.parse_args()


def train_position(
    position: str,
    seasons: List[int],
    n_trials: int,
    rolling_window: int
) -> Dict[str, Any]:
    """Train all models for a specific position."""

    if position == "QB":
        from lineupiq.models.qb import train_qb_models
        logger.info("=" * 80)
        logger.info("TRAINING QB MODELS (6 targets)")
        logger.info("=" * 80)
        results = train_qb_models(seasons=seasons, n_trials=n_trials)
        return {f"QB_{k}": v for k, v in results.items()}

    elif position == "RB":
        from lineupiq.models.rb import train_rb_models
        logger.info("=" * 80)
        logger.info("TRAINING RB MODELS (7 targets)")
        logger.info("=" * 80)
        results = train_rb_models(seasons=seasons, n_trials=n_trials, rolling_window=rolling_window)
        return {f"RB_{k}": v for k, v in results.items()}

    elif position == "WR":
        from lineupiq.models.receiver import train_wr_models
        logger.info("=" * 80)
        logger.info("TRAINING WR MODELS (4 targets)")
        logger.info("=" * 80)
        results = train_wr_models(seasons=seasons, n_trials=n_trials)
        return {f"WR_{k}": v for k, v in results.items()}

    elif position == "TE":
        from lineupiq.models.receiver import train_te_models
        logger.info("=" * 80)
        logger.info("TRAINING TE MODELS (4 targets)")
        logger.info("=" * 80)
        results = train_te_models(seasons=seasons, n_trials=n_trials)
        return {f"TE_{k}": v for k, v in results.items()}

    elif position == "K":
        from lineupiq.models.kicker import train_kicker_models
        logger.info("=" * 80)
        logger.info("TRAINING KICKER MODELS (5 targets)")
        logger.info("=" * 80)
        results = train_kicker_models(seasons=seasons, n_trials=n_trials)
        return {f"K_{k}": v for k, v in results.items()}

    elif position == "DEF":
        from lineupiq.models.defense import train_defense_models
        logger.info("=" * 80)
        logger.info("TRAINING DEFENSE MODELS (5 targets)")
        logger.info("=" * 80)
        results = train_defense_models(seasons=seasons, n_trials=n_trials)
        return {f"DEF_{k}": v for k, v in results.items()}

    else:
        raise ValueError(f"Unknown position: {position}")


def print_summary(all_results: Dict[str, Any]):
    """Print training summary table."""
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"{'Position_Target':<35} {'RMSE Mean':>12} {'RMSE Std':>12} {'Samples':>10}")
    print("-" * 80)

    for model_name in sorted(all_results.keys()):
        model, metrics = all_results[model_name]
        print(
            f"{model_name:<35} "
            f"{metrics['cv_rmse_mean']:>12.2f} "
            f"{metrics['cv_rmse_std']:>12.2f} "
            f"{metrics['n_samples']:>10}"
        )

    print("=" * 80)
    print(f"Total models trained: {len(all_results)}")
    print("=" * 80)


def train_all_models(
    positions: List[str] = None,
    seasons: List[int] = None,
    n_trials: int = 30,
    rolling_window: int = 5
) -> Dict[str, Any]:
    """
    Train all models programmatically (callable from other Python code).

    Args:
        positions: List of positions to train (default: all)
        seasons: List of seasons to train on (default: 2022-2025)
        n_trials: Number of Optuna trials (default: 30)
        rolling_window: Rolling window size (default: 5)

    Returns:
        Dict of all trained models with their metrics

    Example:
        from scripts.train_all import train_all_models

        # Train all models
        results = train_all_models()

        # Train just QB with quick settings
        results = train_all_models(positions=["QB"], n_trials=10)
    """
    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
    if seasons is None:
        seasons = [2022, 2023, 2024, 2025]

    # Print configuration
    logger.info("=" * 80)
    logger.info("LINEUPIQ MODEL TRAINING")
    logger.info("=" * 80)
    logger.info(f"Positions: {', '.join(positions)}")
    logger.info(f"Seasons: {seasons} ({len(seasons)} years)")
    logger.info(f"Optuna trials: {n_trials}")
    logger.info(f"Rolling window: {rolling_window} games")
    logger.info("=" * 80)

    # Train all requested positions
    all_results = {}

    for position in positions:
        try:
            results = train_position(
                position=position,
                seasons=seasons,
                n_trials=n_trials,
                rolling_window=rolling_window
            )
            all_results.update(results)

            # Log position completion
            logger.info(f"\n✓ {position} training complete ({len(results)} models)")

        except Exception as e:
            logger.error(f"✗ {position} training failed: {e}", exc_info=True)
            continue

    # Print final summary
    if all_results:
        print_summary(all_results)
        logger.info(f"\n✓ Training complete! {len(all_results)} models saved to packages/backend/models/")
        return all_results
    else:
        logger.error("\n✗ No models were successfully trained!")
        return None


def main():
    """Main CLI entrypoint."""
    args = parse_args()

    # Override trials if quick mode
    n_trials = 10 if args.quick else args.trials

    # Call the programmatic function
    results = train_all_models(
        positions=args.positions,
        seasons=args.seasons,
        n_trials=n_trials,
        rolling_window=args.rolling_window
    )

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
