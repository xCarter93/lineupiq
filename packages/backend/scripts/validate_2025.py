#!/usr/bin/env python3
"""
Generate week-by-week predictions for 2025 season using proper time-series validation.

This script uses walk-forward validation to prove model quality: for each week,
we retrain models through the previous week and predict the target week using
only data available before that week.

The output provides predicted vs actual values for all players/positions, allowing
us to demonstrate model accuracy on real 2025 data.

Usage:
    # All positions, weeks 1-18, 30 trials (full validation)
    uv run python scripts/validate_2025.py

    # Quick mode for testing (weeks 1-4, 10 trials)
    uv run python scripts/validate_2025.py --quick

    # Specific weeks and positions
    uv run python scripts/validate_2025.py --weeks 1 2 3 --positions QB RB WR TE

    # Custom output file
    uv run python scripts/validate_2025.py --output my_predictions.json

Examples:
    # Full season validation (takes ~12-24 hours)
    uv run python scripts/validate_2025.py --weeks 1-18

    # Quick test (10-15 minutes)
    uv run python scripts/validate_2025.py --quick

    # Single position, single week
    uv run python scripts/validate_2025.py --weeks 1 --positions QB --trials 10
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from sklearn.metrics import mean_absolute_error, r2_score

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lineupiq.models.walkforward import run_walkforward_validation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate 2025 season predictions with walk-forward validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--weeks",
        nargs="+",
        help=(
            "Week numbers to validate (e.g., '1 2 3' or '1-18'). "
            "Use '1-18' notation for ranges. Default: 1-18"
        ),
    )

    parser.add_argument(
        "--positions",
        nargs="+",
        choices=["QB", "RB", "WR", "TE", "K", "DEF"],
        default=["QB", "RB", "WR", "TE", "K", "DEF"],
        help="Positions to validate (default: all)",
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=30,
        help="Number of Optuna trials for hyperparameter tuning (default: 30)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: weeks 1-4 with 10 trials (for testing)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="validation_2025_predictions.json",
        help="Output JSON file path (default: validation_2025_predictions.json)",
    )

    parser.add_argument(
        "--rolling-window",
        type=int,
        default=5,
        help="Rolling window size for features (default: 5)",
    )

    return parser.parse_args()


def parse_weeks(week_args: list[str] | None, quick: bool) -> list[int]:
    """Parse week arguments into list of week numbers.

    Supports:
    - None: defaults to 1-18
    - ["1", "2", "3"]: explicit list
    - ["1-4"]: range notation

    Args:
        week_args: Raw week arguments from argparse
        quick: Quick mode flag (overrides to weeks 1-4)

    Returns:
        List of week numbers (e.g., [1, 2, 3, 4])
    """
    if quick:
        return [1, 2, 3, 4]

    if week_args is None:
        # Default: all weeks 1-18
        return list(range(1, 19))

    weeks = []
    for arg in week_args:
        if "-" in arg:
            # Range notation: "1-4"
            start, end = arg.split("-")
            weeks.extend(range(int(start), int(end) + 1))
        else:
            # Single week: "1"
            weeks.append(int(arg))

    return sorted(set(weeks))  # Remove duplicates and sort


def compute_metrics_by_position(predictions_df) -> dict:
    """Compute MAE and R² by position.

    Args:
        predictions_df: Polars DataFrame with predictions and actuals

    Returns:
        Dict mapping position to {"mae": float, "r2": float, "n": int}
    """
    metrics = {}

    positions = predictions_df["position"].unique().sort().to_list()

    for position in positions:
        pos_df = predictions_df.filter(predictions_df["position"] == position)

        predicted = pos_df["predicted_value"].to_numpy()
        actual = pos_df["actual_value"].to_numpy()

        mae = mean_absolute_error(actual, predicted)
        r2 = r2_score(actual, predicted)

        metrics[position] = {
            "mae": float(mae),
            "r2": float(r2),
            "n_predictions": len(pos_df),
        }

    return metrics


def print_summary(predictions_df, weeks: list[int], positions: list[str], elapsed_time: float):
    """Print validation summary statistics.

    Args:
        predictions_df: Polars DataFrame with predictions
        weeks: List of weeks validated
        positions: List of positions validated
        elapsed_time: Total execution time in seconds
    """
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\nWeeks validated: {min(weeks)}-{max(weeks)} ({len(weeks)} weeks)")
    print(f"Positions: {', '.join(positions)}")
    print(f"Total predictions: {len(predictions_df)}")
    print(f"Execution time: {elapsed_time / 60:.1f} minutes")

    # Compute metrics by position
    metrics = compute_metrics_by_position(predictions_df)

    print("\n" + "-" * 80)
    print(f"{'Position':<12} {'MAE':>10} {'R²':>10} {'Predictions':>15}")
    print("-" * 80)

    for position in sorted(metrics.keys()):
        m = metrics[position]
        print(
            f"{position:<12} "
            f"{m['mae']:>10.2f} "
            f"{m['r2']:>10.3f} "
            f"{m['n_predictions']:>15,}"
        )

    print("-" * 80)

    # Overall metrics
    all_predicted = predictions_df["predicted_value"].to_numpy()
    all_actual = predictions_df["actual_value"].to_numpy()
    overall_mae = mean_absolute_error(all_actual, all_predicted)
    overall_r2 = r2_score(all_actual, all_predicted)

    print(
        f"{'OVERALL':<12} "
        f"{overall_mae:>10.2f} "
        f"{overall_r2:>10.3f} "
        f"{len(predictions_df):>15,}"
    )

    print("=" * 80)


def main():
    """Main execution function."""
    args = parse_args()

    # Parse weeks
    weeks = parse_weeks(args.weeks, args.quick)

    # Override trials if quick mode
    n_trials = 10 if args.quick else args.trials

    # Print configuration
    logger.info("=" * 80)
    logger.info("2025 SEASON VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Weeks: {min(weeks)}-{max(weeks)} ({len(weeks)} weeks)")
    logger.info(f"Positions: {', '.join(args.positions)}")
    logger.info(f"Optuna trials: {n_trials}")
    logger.info(f"Rolling window: {args.rolling_window}")
    logger.info(f"Output file: {args.output}")
    logger.info("=" * 80)

    if len(weeks) > 4 and n_trials < 20:
        logger.warning(
            f"⚠️  Running {len(weeks)} weeks with only {n_trials} trials. "
            f"Consider increasing --trials for better model quality."
        )

    # Estimate execution time
    # Rough estimate: 1 week * 6 positions * 30 trials ≈ 45 minutes
    estimated_minutes = len(weeks) * len(args.positions) * n_trials * 0.025
    if estimated_minutes > 60:
        logger.info(
            f"⏱️  Estimated execution time: {estimated_minutes / 60:.1f} hours"
        )
    else:
        logger.info(f"⏱️  Estimated execution time: {estimated_minutes:.0f} minutes")

    # Run validation
    start_time = time.time()

    try:
        predictions_df = run_walkforward_validation(
            season=2025,
            weeks=weeks,
            positions=args.positions,
            n_trials=n_trials,
            rolling_window=args.rolling_window,
        )

        if len(predictions_df) == 0:
            logger.error("❌ No predictions generated!")
            return 1

        elapsed_time = time.time() - start_time

        # Convert to list of dicts for JSON serialization
        predictions_list = predictions_df.to_dicts()

        # Save to JSON
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(predictions_list, f, indent=2)

        logger.info(f"✅ Predictions saved to: {output_path}")

        # Print summary
        print_summary(predictions_df, weeks, args.positions, elapsed_time)

        return 0

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
