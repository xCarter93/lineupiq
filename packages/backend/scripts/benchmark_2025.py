"""
Benchmark script for 2025 holdout validation.

Trains on 2020-2024 data and tests on 2025 to validate ensemble findings
with more training data and the most recent season.
"""

import logging
from pathlib import Path

import polars as pl

from lineupiq.features.pipeline import build_features
from lineupiq.models.ensemble import benchmark_ensemble_strategies
from lineupiq.models.qb import QB_TARGETS, prepare_qb_data
from lineupiq.models.rb import RB_TARGETS, prepare_rb_data
from lineupiq.models.receiver import RECEIVER_TARGETS, prepare_receiver_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define positions and their targets
POSITIONS = {
    "QB": QB_TARGETS,
    "RB": RB_TARGETS,
    "WR": RECEIVER_TARGETS,
    "TE": RECEIVER_TARGETS,  # WR and TE use same targets
}


def main() -> None:
    """Run benchmark on 2025 holdout with 2020-2024 training data."""
    logger.info("Starting 2025 holdout benchmark (training on 2020-2024)")

    # Load training data (2020-2024) and holdout data (2025)
    logger.info("Loading and processing data")
    df = build_features([2020, 2021, 2022, 2023, 2024, 2025])

    # Split train/holdout by season
    train_df = df.filter(pl.col("season").is_in([2020, 2021, 2022, 2023, 2024]))
    holdout_df = df.filter(pl.col("season") == 2025)

    logger.info(f"Training data: {len(train_df)} rows")
    logger.info(f"Holdout data: {len(holdout_df)} rows")

    # Prepare data for each position
    position_data = {}

    # QB data
    logger.info("Preparing QB data")
    X_train, y_train_dict = prepare_qb_data(train_df)
    X_holdout, y_holdout_dict = prepare_qb_data(holdout_df)
    position_data["QB"] = {
        "X_train": X_train,
        "y_train": y_train_dict,
        "X_holdout": X_holdout,
        "y_holdout": y_holdout_dict,
    }

    # RB data
    logger.info("Preparing RB data")
    X_train, y_train_dict = prepare_rb_data(train_df)
    X_holdout, y_holdout_dict = prepare_rb_data(holdout_df)
    position_data["RB"] = {
        "X_train": X_train,
        "y_train": y_train_dict,
        "X_holdout": X_holdout,
        "y_holdout": y_holdout_dict,
    }

    # WR data
    logger.info("Preparing WR data")
    X_train, y_train_dict = prepare_receiver_data(train_df, "WR")
    X_holdout, y_holdout_dict = prepare_receiver_data(holdout_df, "WR")
    position_data["WR"] = {
        "X_train": X_train,
        "y_train": y_train_dict,
        "X_holdout": X_holdout,
        "y_holdout": y_holdout_dict,
    }

    # TE data
    logger.info("Preparing TE data")
    X_train, y_train_dict = prepare_receiver_data(train_df, "TE")
    X_holdout, y_holdout_dict = prepare_receiver_data(holdout_df, "TE")
    position_data["TE"] = {
        "X_train": X_train,
        "y_train": y_train_dict,
        "X_holdout": X_holdout,
        "y_holdout": y_holdout_dict,
    }

    # Run benchmarks for all position/stat combinations
    all_results = []
    total_stats = sum(len(targets) for targets in POSITIONS.values())
    current_stat = 0

    for position, targets in POSITIONS.items():
        for stat in targets:
            current_stat += 1
            logger.info(f"[{current_stat}/{total_stats}] Benchmarking {position}_{stat}")

            try:
                # Get data for this position
                data = position_data[position]
                y_train = data["y_train"][stat]
                y_holdout = data["y_holdout"][stat]

                # Run benchmark
                results = benchmark_ensemble_strategies(
                    position=position,
                    stat=stat,
                    X_train=data["X_train"],
                    y_train=y_train,
                    X_holdout=data["X_holdout"],
                    y_holdout=y_holdout,
                )

                # Store results with position/stat info
                all_results.append({
                    "position": position,
                    "stat": stat,
                    "results": results["results"],
                    "best_strategy": results["best_strategy"],
                    "correlation": results["correlation"],
                    "optimal_weights": results["optimal_weights"],
                })

                logger.info(
                    f"  Best: {results['best_strategy']} "
                    f"(MAE: {results['results'][results['best_strategy']]['mae']:.2f})"
                )

            except FileNotFoundError as e:
                logger.warning(f"  Skipping {position}_{stat}: Models not found ({e})")
            except Exception as e:
                logger.error(f"  Error benchmarking {position}_{stat}: {e}")

    # Generate BENCHMARK_RESULTS_2025.md
    logger.info("Generating BENCHMARK_RESULTS_2025.md")
    generate_results_markdown(all_results)

    logger.info(f"Benchmark complete: {len(all_results)}/{total_stats} stats benchmarked")


def generate_results_markdown(all_results: list[dict]) -> None:
    """Generate BENCHMARK_RESULTS_2025.md with comprehensive analysis."""
    output_path = Path(__file__).parent.parent.parent.parent / ".planning" / "phases" / "19-ensemble-models" / "BENCHMARK_RESULTS_2025.md"

    # Calculate summary statistics
    strategy_wins = {}
    ensemble_beats_single = 0
    total_benchmarked = len(all_results)

    for result in all_results:
        # Count strategy wins
        best = result["best_strategy"]
        strategy_wins[best] = strategy_wins.get(best, 0) + 1

        # Check if ensemble beats single models
        best_single_mae = min(
            result["results"]["lgbm_solo"]["mae"],
            result["results"]["xgb_solo"]["mae"],
        )
        ensemble_strategies = ["voting_simple", "voting_weighted", "stacking"]
        best_ensemble_mae = min(
            result["results"][s]["mae"] for s in ensemble_strategies
        )

        if best_ensemble_mae < best_single_mae:
            ensemble_beats_single += 1

    # Calculate average correlation
    avg_correlation = sum(r["correlation"] for r in all_results) / len(all_results)

    # Generate markdown
    content = f"""# Ensemble Benchmark Results (2025 Holdout)

**Date:** 2026-01-20
**Training Data:** 2020-2024 seasons (5 years)
**Holdout Season:** 2025
**Total Stats Benchmarked:** {total_benchmarked}

## Executive Summary

This benchmark evaluates 5 strategies (lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking) across all skill position stats on 2025 holdout data with 5 years of training data (2020-2024).

**Comparison to 2024 Benchmark:** This uses 5 years of training data vs 2 years (2022-2023) in the original benchmark, and tests on the most recent 2025 season.

### Key Findings

1. **Model Diversity:** Average correlation between LightGBM and XGBoost predictions: {avg_correlation:.3f}
   - <0.7: Good diversity (ensemble likely helps)
   - 0.7-0.9: Moderate diversity
   - >0.9: Low diversity (ensemble unlikely to help)

2. **Ensemble Performance:** Ensembles beat best single model in {ensemble_beats_single}/{total_benchmarked} stats ({ensemble_beats_single/total_benchmarked*100:.1f}%)

3. **Winning Strategies:**
"""

    # Add strategy win counts
    for strategy in sorted(strategy_wins.keys(), key=lambda k: strategy_wins[k], reverse=True):
        count = strategy_wins[strategy]
        pct = count / total_benchmarked * 100
        content += f"   - {strategy}: {count}/{total_benchmarked} ({pct:.1f}%)\n"

    content += "\n## Summary Table\n\n"
    content += "| Position | Stat | Best Strategy | Best MAE | Best R² | Correlation | Optimal Weights |\n"
    content += "|----------|------|---------------|----------|---------|-------------|-----------------|\n"

    for result in all_results:
        position = result["position"]
        stat = result["stat"]
        best = result["best_strategy"]
        mae = result["results"][best]["mae"]
        r2 = result["results"][best]["r2"]
        corr = result["correlation"]
        weights = result["optimal_weights"]
        weights_str = f"{weights[0]:.2f}/{weights[1]:.2f}"

        content += f"| {position} | {stat} | {best} | {mae:.2f} | {r2:.3f} | {corr:.3f} | {weights_str} |\n"

    content += "\n## Full Results\n\n"
    content += "Detailed breakdown for each position/stat showing all 5 strategies.\n\n"

    for result in all_results:
        position = result["position"]
        stat = result["stat"]
        best = result["best_strategy"]

        content += f"### {position}_{stat}\n\n"
        content += f"- **Best Strategy:** {best}\n"
        content += f"- **Correlation:** {result['correlation']:.3f}\n"
        content += f"- **Optimal Weights:** LightGBM={result['optimal_weights'][0]:.2f}, XGBoost={result['optimal_weights'][1]:.2f}\n\n"
        content += "| Strategy | MAE | R² |\n"
        content += "|----------|-----|----|\n"

        for strategy in ["lgbm_solo", "xgb_solo", "voting_simple", "voting_weighted", "stacking"]:
            mae = result["results"][strategy]["mae"]
            r2 = result["results"][strategy]["r2"]
            marker = " ← BEST" if strategy == best else ""
            content += f"| {strategy} | {mae:.2f} | {r2:.3f}{marker} |\n"

        content += "\n"

    # Add analysis section
    content += """## Analysis

### Model Diversity

"""

    # Analyze diversity by correlation ranges
    low_diversity = sum(1 for r in all_results if r["correlation"] >= 0.9)
    mod_diversity = sum(1 for r in all_results if 0.7 <= r["correlation"] < 0.9)
    high_diversity = sum(1 for r in all_results if r["correlation"] < 0.7)

    content += f"- High diversity (correlation < 0.7): {high_diversity}/{total_benchmarked} stats\n"
    content += f"- Moderate diversity (0.7-0.9): {mod_diversity}/{total_benchmarked} stats\n"
    content += f"- Low diversity (>= 0.9): {low_diversity}/{total_benchmarked} stats\n\n"

    content += """### Ensemble vs Single Model Performance

"""

    # Compare ensemble vs single for each stat
    ensemble_better = []
    single_better = []

    for result in all_results:
        best_single_mae = min(
            result["results"]["lgbm_solo"]["mae"],
            result["results"]["xgb_solo"]["mae"],
        )
        ensemble_strategies = ["voting_simple", "voting_weighted", "stacking"]
        best_ensemble_mae = min(
            result["results"][s]["mae"] for s in ensemble_strategies
        )

        if best_ensemble_mae < best_single_mae:
            improvement = ((best_single_mae - best_ensemble_mae) / best_single_mae) * 100
            ensemble_better.append((result["position"], result["stat"], improvement))
        else:
            degradation = ((best_ensemble_mae - best_single_mae) / best_single_mae) * 100
            single_better.append((result["position"], result["stat"], degradation))

    content += f"**Stats where ensemble wins:** {len(ensemble_better)}/{total_benchmarked}\n\n"

    if ensemble_better:
        content += "Top ensemble improvements:\n"
        for pos, stat, improvement in sorted(ensemble_better, key=lambda x: x[2], reverse=True)[:5]:
            content += f"- {pos}_{stat}: {improvement:.1f}% improvement\n"

    content += f"\n**Stats where single model wins:** {len(single_better)}/{total_benchmarked}\n\n"

    if single_better:
        content += "Worst ensemble degradations:\n"
        for pos, stat, degradation in sorted(single_better, key=lambda x: x[2], reverse=True)[:5]:
            content += f"- {pos}_{stat}: {degradation:.1f}% worse\n"

    # Add recommendation
    content += "\n## Recommendation\n\n"

    if ensemble_beats_single / total_benchmarked >= 0.5:
        content += f"""**Adopt ensemble models** - Ensembles beat single models on {ensemble_beats_single}/{total_benchmarked} ({ensemble_beats_single/total_benchmarked*100:.1f}%) stats.

Recommended approach:
- Use {max(strategy_wins, key=strategy_wins.get)} as default ensemble strategy (wins most frequently)
- Deploy ensemble models for production predictions
- Keep single models as fallback for comparison
"""
    else:
        content += f"""**Keep single models** - Ensembles only beat single models on {ensemble_beats_single}/{total_benchmarked} ({ensemble_beats_single/total_benchmarked*100:.1f}%) stats.

Findings:
- High correlation ({avg_correlation:.3f}) indicates low model diversity
- Single models already performing well, ensemble overhead not justified
- Recommend improving base models or adding more diverse estimators before revisiting ensembles
"""

    content += """
## Methodology

- **Training Data:** 2020-2024 seasons (5 years)
- **Holdout Data:** 2025 season (strict holdout, never seen during training)
- **Strategies Tested:**
  1. `lgbm_solo`: LightGBM model alone
  2. `xgb_solo`: XGBoost model alone
  3. `voting_simple`: Simple averaging (equal weights)
  4. `voting_weighted`: Weighted averaging (optimal weights via grid search)
  5. `stacking`: Ridge meta-learner with 5-fold CV
- **Metrics:** MAE (lower is better), R² (higher is better)
- **Best Strategy:** Selected by lowest MAE on holdout data

## Comparison to 2024 Benchmark

The original benchmark (BENCHMARK_RESULTS.md) trained on 2022-2023 and tested on 2024 holdout. This benchmark:
- Uses 5 years vs 2 years of training data (2020-2024 vs 2022-2023)
- Tests on most recent 2025 season vs 2024
- Validates whether ensemble findings hold with more training data and recent season
"""

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logger.info(f"Results written to {output_path}")


if __name__ == "__main__":
    main()
