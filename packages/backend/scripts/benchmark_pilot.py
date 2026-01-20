"""
Pilot benchmark script for QB passing_yards.

Validates the benchmark_ensemble_strategies function on a single stat
before running the full benchmark across all positions.
"""

import logging

import polars as pl

from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.ensemble import benchmark_ensemble_strategies
from lineupiq.models.qb import prepare_qb_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run pilot benchmark on QB passing_yards."""
    logger.info("Starting pilot benchmark for QB passing_yards")

    # Load training data (2022-2023) and holdout data (2024)
    logger.info("Loading and processing data")
    df = build_features([2022, 2023, 2024])

    # Split train/holdout by season
    train_df = df.filter(pl.col("season").is_in([2022, 2023]))
    holdout_df = df.filter(pl.col("season") == 2024)

    logger.info(f"Training data: {len(train_df)} rows")
    logger.info(f"Holdout data: {len(holdout_df)} rows")

    # Prepare QB data
    X_train, y_train_dict = prepare_qb_data(train_df)
    X_holdout, y_holdout_dict = prepare_qb_data(holdout_df)

    # Get passing_yards targets
    y_train = y_train_dict["passing_yards"]
    y_holdout = y_holdout_dict["passing_yards"]

    logger.info(f"QB passing_yards - Train samples: {len(y_train)}, Holdout samples: {len(y_holdout)}")

    # Run benchmark
    results = benchmark_ensemble_strategies(
        position="QB",
        stat="passing_yards",
        X_train=X_train,
        y_train=y_train,
        X_holdout=X_holdout,
        y_holdout=y_holdout,
    )

    # Display results
    print("\n" + "=" * 80)
    print("PILOT BENCHMARK RESULTS: QB passing_yards")
    print("=" * 80)
    print(f"\nBase model diversity (correlation): {results['correlation']:.3f}")
    print(f"Optimal weights: LightGBM={results['optimal_weights'][0]:.2f}, XGBoost={results['optimal_weights'][1]:.2f}")
    print(f"\nBest strategy: {results['best_strategy']}")
    print("\nAll strategies:")
    print("-" * 80)
    print(f"{'Strategy':<20} {'MAE':<15} {'R²':<15}")
    print("-" * 80)

    for strategy, metrics in results["results"].items():
        mae = metrics["mae"]
        r2 = metrics["r2"]
        marker = " ← BEST" if strategy == results["best_strategy"] else ""
        print(f"{strategy:<20} {mae:<15.2f} {r2:<15.3f}{marker}")

    print("=" * 80)

    # Interpretation
    print("\nInterpretation:")
    print(f"- Correlation {results['correlation']:.3f}: ", end="")
    if results['correlation'] < 0.7:
        print("Good diversity, ensemble likely to help")
    elif results['correlation'] < 0.9:
        print("Moderate diversity, ensemble may help slightly")
    else:
        print("Low diversity, ensemble unlikely to improve")

    # Check if ensemble beats single models
    best_single_mae = min(
        results["results"]["lgbm_solo"]["mae"],
        results["results"]["xgb_solo"]["mae"],
    )
    best_ensemble_mae = min(
        results["results"]["voting_simple"]["mae"],
        results["results"]["voting_weighted"]["mae"],
        results["results"]["stacking"]["mae"],
    )

    improvement = ((best_single_mae - best_ensemble_mae) / best_single_mae) * 100
    print(f"\nBest single model MAE: {best_single_mae:.2f}")
    print(f"Best ensemble MAE: {best_ensemble_mae:.2f}")
    print(f"Improvement: {improvement:.1f}%")

    logger.info("Pilot benchmark complete")


if __name__ == "__main__":
    main()
