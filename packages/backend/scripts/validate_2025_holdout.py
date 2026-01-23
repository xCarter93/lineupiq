#!/usr/bin/env python3
"""
Generate 2025 season predictions using holdout validation.

Trains models on 2022-2024 data only, then predicts entire 2025 season.
This proves model quality on completely unseen data.

Usage:
  # Full validation (all weeks, 30 trials, ~45-60 min)
  uv run python scripts/validate_2025_holdout.py

  # Quick mode (10 trials, ~20-25 min)
  uv run python scripts/validate_2025_holdout.py --quick

  # Specific positions or weeks
  uv run python scripts/validate_2025_holdout.py --positions QB RB --weeks 1 2 3 4

  # Use existing models (skip training)
  uv run python scripts/validate_2025_holdout.py --use-existing models_holdout/
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.metrics import mean_absolute_error, r2_score

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate 2025 season predictions using holdout validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--positions",
        nargs="+",
        choices=["QB", "RB", "WR", "TE", "K", "DEF"],
        default=["QB", "RB", "WR", "TE", "K", "DEF"],
        help="Positions to validate (default: all)"
    )

    parser.add_argument(
        "--weeks",
        nargs="+",
        type=int,
        default=None,
        help="Specific weeks to predict (default: all available weeks)"
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
        help="Quick mode (10 trials, faster training)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="validation_2025_predictions.json",
        help="Output file for predictions (default: validation_2025_predictions.json)"
    )

    parser.add_argument(
        "--use-existing",
        type=str,
        default=None,
        help="Use existing models from specified directory (skip training)"
    )

    return parser.parse_args()


def compute_metrics(predictions_df: pl.DataFrame) -> dict[str, dict[str, float]]:
    """Compute performance metrics by position.

    Args:
        predictions_df: DataFrame with predicted_value and actual_value columns.

    Returns:
        Dict mapping position to metrics dict (MAE, R2, accuracy_pct).
    """
    metrics = {}

    for position in predictions_df["position"].unique().to_list():
        pos_df = predictions_df.filter(pl.col("position") == position)

        y_pred = pos_df["predicted_value"].to_numpy()
        y_actual = pos_df["actual_value"].to_numpy()

        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)

        # Accuracy % based on R² (Phase 19.2-02 decision)
        accuracy_pct = max(0, min(100, 100 * r2))

        metrics[position] = {
            "mae": float(mae),
            "r2": float(r2),
            "accuracy_pct": float(accuracy_pct),
            "n_predictions": len(y_pred),
        }

    return metrics


def print_summary(predictions_df: pl.DataFrame, metrics: dict[str, dict[str, float]]):
    """Print validation summary table.

    Args:
        predictions_df: DataFrame with predictions.
        metrics: Performance metrics by position.
    """
    print("\n" + "=" * 80)
    print("2025 HOLDOUT VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total predictions: {len(predictions_df):,}")
    print(f"Positions: {', '.join(sorted(predictions_df['position'].unique().to_list()))}")
    print(f"Weeks: {sorted(predictions_df['week'].unique().to_list())}")
    print(f"Players: {predictions_df['player_id'].n_unique():,}")
    print()

    print(f"{'Position':<12} {'MAE':>10} {'R²':>10} {'Accuracy %':>12} {'Predictions':>14}")
    print("-" * 80)

    for position in sorted(metrics.keys()):
        m = metrics[position]
        print(
            f"{position:<12} "
            f"{m['mae']:>10.2f} "
            f"{m['r2']:>10.3f} "
            f"{m['accuracy_pct']:>12.1f}% "
            f"{m['n_predictions']:>14,}"
        )

    # Overall averages (weighted by number of predictions)
    total_preds = sum(m["n_predictions"] for m in metrics.values())
    avg_mae = sum(m["mae"] * m["n_predictions"] for m in metrics.values()) / total_preds
    avg_r2 = sum(m["r2"] * m["n_predictions"] for m in metrics.values()) / total_preds
    avg_acc = sum(m["accuracy_pct"] * m["n_predictions"] for m in metrics.values()) / total_preds

    print("-" * 80)
    print(
        f"{'AVERAGE':<12} "
        f"{avg_mae:>10.2f} "
        f"{avg_r2:>10.3f} "
        f"{avg_acc:>12.1f}% "
        f"{total_preds:>14,}"
    )

    print("=" * 80)


def save_predictions(predictions_df: pl.DataFrame, output_file: str):
    """Save predictions to JSON file.

    Args:
        predictions_df: DataFrame with predictions.
        output_file: Path to output JSON file.
    """
    # Convert to list of dicts for JSON serialization
    records = predictions_df.to_dicts()

    output_path = Path(output_file)
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    logger.info(f"Saved predictions to {output_path}")
    logger.info(f"File size: {output_path.stat().st_size:,} bytes")


def main():
    """Main CLI entrypoint."""
    args = parse_args()

    # Override trials if quick mode
    n_trials = 10 if args.quick else args.trials

    # Print configuration
    logger.info("=" * 80)
    logger.info("2025 HOLDOUT VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Positions: {', '.join(args.positions)}")
    logger.info(f"Weeks: {args.weeks or 'all available'}")
    logger.info(f"Optuna trials: {n_trials}")
    logger.info(f"Output file: {args.output}")

    if args.use_existing:
        logger.info(f"Using existing models: {args.use_existing}")
    else:
        logger.info(f"Training new models on 2022-2024 data")

    logger.info("=" * 80)

    try:
        # Step 1: Train or load models
        if args.use_existing:
            model_dir = args.use_existing
            logger.info(f"\nUsing existing models from {model_dir}/")
        else:
            from lineupiq.models.holdout import train_holdout_models

            logger.info("\nTraining models on 2022-2024 data (holdout: 2025)...")
            train_seasons = [2022, 2023, 2024]

            # Validate no overlap between train and test
            if 2025 in train_seasons:
                raise ValueError("Holdout season (2025) cannot be in training seasons!")

            model_paths = train_holdout_models(
                train_seasons=train_seasons,
                positions=args.positions,
                n_trials=n_trials,
                output_dir="models_holdout"
            )

            logger.info(f"\n✓ Training complete: {len(model_paths)} models")
            model_dir = "models_holdout"

        # Step 2: Generate predictions for 2025
        from lineupiq.models.holdout import predict_season

        logger.info(f"\nPredicting 2025 season using models from {model_dir}/...")
        predictions_df = predict_season(
            season=2025,
            model_dir=model_dir,
            positions=args.positions,
            weeks=args.weeks
        )

        logger.info(f"✓ Predictions complete: {len(predictions_df)} total predictions")

        # Step 3: Compute metrics
        logger.info("\nComputing performance metrics...")
        metrics = compute_metrics(predictions_df)

        # Step 4: Print summary
        print_summary(predictions_df, metrics)

        # Step 5: Save predictions
        save_predictions(predictions_df, args.output)

        logger.info("\n✓ Validation complete!")
        return 0

    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
