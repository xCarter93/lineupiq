"""Honest walk-forward 2025 evaluation: LightGBM vs a naive 5-game-mean baseline.

Trains one model per target on seasons <= 2024 and scores 2025 on a usage-thresholded
population. Walk-forward is legitimate because every feature is lagged/pre-game.

Rubric (fixed): SHIP_MODEL iff model MAE < naive MAE AND model R2 > 0, else SHIP_BASELINE.

Usage: uv run python scripts/evaluate_honest.py [--positions QB RB] [--trials 12]
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.metrics import mean_absolute_error, r2_score

from lineupiq.data.defense_processing import (
    get_defense_feature_columns,
    process_defense_data,
)
from lineupiq.data.kicker_processing import (
    get_kicker_feature_columns,
    get_kicker_target_columns,
    process_kicker_data,
)
from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.defense import DEF_TARGETS
from lineupiq.models.qb import QB_TARGETS
from lineupiq.models.rb import RB_TARGETS
from lineupiq.models.receiver import RECEIVER_TARGETS
from lineupiq.models.training import train_model, tune_hyperparameters

logger = logging.getLogger(__name__)

SEASONS = [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]
TRAIN_MAX_SEASON = 2024
EVAL_SEASON = 2025
WINDOW = 5
CV_SPLITS = 3
OUTPUT_PATH = Path(__file__).parent.parent / "eval" / "honest_2025.json"

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]

# Ex-ante usage gates: lagged rolling usage only, so the same gate is applicable at
# prediction time. K/DEF have no gate beyond "the entity played that week".
THRESHOLDS = {
    "QB": "lagged 5-game mean pass attempts >= 10",
    "RB": "lagged 5-game mean (carries + targets) >= 3",
    "WR": "lagged 5-game mean targets >= 3",
    "TE": "lagged 5-game mean targets >= 3",
    "K": "played that week (kicker-game row exists)",
    "DEF": "played that week (team-game row exists)",
}


def lagged_mean(expr: pl.Expr, group: str) -> pl.Expr:
    """Lagged rolling mean - the idiom from features/rolling_stats.py."""
    return expr.shift(1).rolling_mean(window_size=WINDOW, min_samples=1).over(group)


def skill_target_exprs(position: str) -> dict[str, pl.Expr]:
    """Target columns per position, mirroring models/{qb,rb,receiver}.py derivations."""
    if position == "QB":
        return {
            "passing_yards": pl.col("passing_yards"),
            "passing_tds": pl.col("passing_tds"),
            "interceptions": pl.col("passing_interceptions").fill_null(0),
            "rushing_yards": pl.col("rushing_yards"),
            "rushing_tds": pl.col("rushing_tds"),
            "fumbles_lost": pl.col("sack_fumbles_lost").fill_null(0)
            + pl.col("rushing_fumbles_lost").fill_null(0),
        }
    if position == "RB":
        return {t: pl.col(t) for t in RB_TARGETS if t != "fumbles_lost"} | {
            "fumbles_lost": pl.col("rushing_fumbles_lost").fill_null(0)
            + pl.col("receiving_fumbles_lost").fill_null(0),
        }
    return {t: pl.col(t) for t in RECEIVER_TARGETS if t != "fumbles_lost"} | {
        "fumbles_lost": pl.col("receiving_fumbles_lost").fill_null(0),
    }


def usage_expr(position: str) -> pl.Expr:
    if position == "QB":
        return lagged_mean(pl.col("attempts"), "player_id") >= 10
    if position == "RB":
        return lagged_mean(pl.col("carries") + pl.col("targets"), "player_id") >= 3
    return lagged_mean(pl.col("targets"), "player_id") >= 3


def prepare_skill(df: pl.DataFrame, position: str) -> tuple[pl.DataFrame, list[str], list[str]]:
    """Build the eval frame for QB/RB/WR/TE from the shared feature frame."""
    targets = {"QB": QB_TARGETS, "RB": RB_TARGETS}.get(position, RECEIVER_TARGETS)
    feature_cols = get_feature_columns()

    pos_df = df.filter(pl.col("position") == position)
    pos_df = pos_df.with_columns(
        **{name: expr for name, expr in skill_target_exprs(position).items()}
    )
    # Naive baseline and usage gate are computed before any null-drop so the rolling
    # window sees the player's real prior games.
    pos_df = pos_df.with_columns(
        usage_ok=usage_expr(position),
        **{f"naive_{t}": lagged_mean(pl.col(t), "player_id") for t in targets},
    )
    return pos_df.drop_nulls(subset=feature_cols + targets), feature_cols, targets


def prepare_kicker() -> tuple[pl.DataFrame, list[str], list[str]]:
    targets = get_kicker_target_columns()
    feature_cols = get_kicker_feature_columns()
    df = process_kicker_data(SEASONS).with_columns(
        usage_ok=pl.lit(True),
        **{f"naive_{t}": lagged_mean(pl.col(t), "player_id") for t in targets},
    )
    # process_kicker_data sorts by player; CV needs chronological row order.
    df = df.drop_nulls(subset=feature_cols + targets).sort(["season", "week"])
    return df, feature_cols, targets


def prepare_defense() -> tuple[pl.DataFrame, list[str], list[str]]:
    targets = DEF_TARGETS
    feature_cols = get_defense_feature_columns()
    df = process_defense_data(SEASONS).with_columns(
        usage_ok=pl.lit(True),
        **{f"naive_{t}": lagged_mean(pl.col(t), "team") for t in targets},
    )
    df = df.drop_nulls(subset=feature_cols + targets).sort(["season", "week"])
    return df, feature_cols, targets


def evaluate_target(
    frame: pl.DataFrame,
    feature_cols: list[str],
    position: str,
    target: str,
    trials: int,
) -> dict[str, Any]:
    train = frame.filter(pl.col("season") <= TRAIN_MAX_SEASON)
    evalr = frame.filter(
        (pl.col("season") == EVAL_SEASON)
        & pl.col("usage_ok")
        & pl.col(f"naive_{target}").is_not_null()
    )

    X_train = train.select(feature_cols).to_numpy().astype(np.float64)
    y_train = train.select(target).to_numpy().flatten().astype(np.float64)
    season_train = train.select("season").to_numpy().flatten().astype(np.int64)
    if not np.all(np.diff(season_train) >= 0):
        raise ValueError(f"{position}_{target}: training rows are not chronologically ordered")

    X_eval = evalr.select(feature_cols).to_numpy().astype(np.float64)
    y_eval = evalr.select(target).to_numpy().flatten().astype(np.float64)
    naive = evalr.select(f"naive_{target}").to_numpy().flatten().astype(np.float64)

    started = time.time()
    best_params, _ = tune_hyperparameters(
        X_train,
        y_train,
        n_trials=trials,
        n_splits=CV_SPLITS,
        model_type="lightgbm",
        target=target,
        season_array=season_train,
    )
    model, _ = train_model(
        X_train,
        y_train,
        params=best_params,
        n_splits=CV_SPLITS,
        model_type="lightgbm",
        season_array=season_train,
    )
    pred = model.predict(X_eval)

    model_mae = float(mean_absolute_error(y_eval, pred))
    naive_mae = float(mean_absolute_error(y_eval, naive))
    model_r2 = float(r2_score(y_eval, pred))
    verdict = "SHIP_MODEL" if model_mae < naive_mae and model_r2 > 0 else "SHIP_BASELINE"

    return {
        "position": position,
        "target": target,
        "n_train_rows": len(y_train),
        "n_eval_rows": len(y_eval),
        "threshold": THRESHOLDS[position],
        "model_mae": model_mae,
        "naive_mae": naive_mae,
        "model_r2": model_r2,
        "naive_r2": float(r2_score(y_eval, naive)),
        "verdict": verdict,
        "seconds": round(time.time() - started, 1),
    }


def build_manifest(results: list[dict[str, Any]], trials: int, elapsed: float) -> dict[str, Any]:
    return {
        "seasons": SEASONS,
        "train_seasons": [s for s in SEASONS if s <= TRAIN_MAX_SEASON],
        "eval_season": EVAL_SEASON,
        "n_optuna_trials": trials,
        "cv_splits": CV_SPLITS,
        "model_type": "lightgbm",
        "naive_baseline": (
            "per-entity lagged 5-game rolling mean of the target "
            "(shift(1) then rolling_mean, min_samples=1)"
        ),
        "rubric": "SHIP_MODEL iff model_mae < naive_mae and model_r2 > 0",
        "thresholds": THRESHOLDS,
        "notes": [
            "Postseason weeks (19-22) are not filtered out; the pipeline keeps them.",
            "K/DEF pipeline features backfill rolling nulls with a global column mean "
            "computed over all seasons, a mild train/eval leak in their favour.",
        ],
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
    }


def print_table(results: list[dict[str, Any]]) -> None:
    header = (
        f"{'target':26s} {'n':>6s} {'model_mae':>10s} {'naive_mae':>10s} "
        f"{'model_r2':>9s} {'naive_r2':>9s}  verdict"
    )
    print("\n" + header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['position'] + '_' + r['target']:26s} {r['n_eval_rows']:6d} "
            f"{r['model_mae']:10.3f} {r['naive_mae']:10.3f} "
            f"{r['model_r2']:9.3f} {r['naive_r2']:9.3f}  {r['verdict']}"
        )
    ship = sum(r["verdict"] == "SHIP_MODEL" for r in results)
    total = len(results)
    print(f"\nSHIP_MODEL: {ship}/{total}   SHIP_BASELINE: {total - ship}/{total}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positions", nargs="+", default=POSITIONS, choices=POSITIONS)
    parser.add_argument("--trials", type=int, default=12, help="Optuna trials per target")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Manifest path; use a separate file for partial-position runs",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    run_started = time.time()

    skill_positions = [p for p in args.positions if p in ("QB", "RB", "WR", "TE")]
    feature_df = build_features(SEASONS) if skill_positions else None

    results: list[dict[str, Any]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for position in args.positions:
        if position == "K":
            frame, feature_cols, targets = prepare_kicker()
        elif position == "DEF":
            frame, feature_cols, targets = prepare_defense()
        else:
            assert feature_df is not None
            frame, feature_cols, targets = prepare_skill(feature_df, position)

        for target in targets:
            print(f"[{position}_{target}] training...", flush=True)
            result = evaluate_target(frame, feature_cols, position, target, args.trials)
            results.append(result)
            print(
                f"[{position}_{target}] n={result['n_eval_rows']} "
                f"mae {result['model_mae']:.3f} vs naive {result['naive_mae']:.3f} "
                f"r2 {result['model_r2']:.3f} -> {result['verdict']} "
                f"({result['seconds']}s)",
                flush=True,
            )
            # Rewrite after every target so a crash never costs the whole run.
            manifest = build_manifest(results, args.trials, time.time() - run_started)
            args.output.write_text(json.dumps(manifest, indent=2))

    print_table(results)
    print(f"\nWrote {args.output}")
    print(f"Total wall-clock: {time.time() - run_started:.1f}s")


if __name__ == "__main__":
    main()
