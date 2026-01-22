#!/usr/bin/env python3
"""
Compute R², MAE, and RMSE for WR and TE models on training data.
"""
import joblib
import numpy as np
import polars as pl
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from lineupiq.features.pipeline import build_features

# Model paths
MODELS_DIR = Path(__file__).parent.parent / "models"

# Positions and targets
POSITIONS = {
    "WR": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
    "TE": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"]
}

# Training seasons
SEASONS = [2022, 2023, 2024, 2025]

def compute_metrics_for_position(position: str, target: str, df: pl.DataFrame):
    """Compute metrics for a specific position and target."""

    # Load model
    model_path = MODELS_DIR / f"{position}_{target}.joblib"
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return None

    model_dict = joblib.load(model_path)
    model = model_dict['model']

    # Filter to position
    df_pos = df.filter(pl.col("position") == position)

    # Map receiving_fumbles_lost to fumbles_lost for consistency
    df_pos = df_pos.with_columns(
        pl.col("receiving_fumbles_lost").fill_null(0).alias("fumbles_lost")
    )

    # Use get_feature_columns to get actual feature names instead of the stored ones
    from lineupiq.features.pipeline import get_feature_columns
    feature_cols = get_feature_columns()

    # Remove rows with missing target or features
    required_cols = feature_cols + [target]
    df_clean = df_pos.drop_nulls(subset=required_cols)

    # Prepare X and y
    X = df_clean.select(feature_cols).to_numpy().astype(np.float64)
    y = df_clean.select(target).to_numpy().flatten().astype(np.float64)

    # Make predictions
    y_pred = model.predict(X)

    # Compute metrics
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    n_samples = len(y)

    return {
        'position': position,
        'target': target,
        'r2': r2,
        'mae': mae,
        'rmse': rmse,
        'n_samples': n_samples
    }

def main():
    print("Computing metrics for WR and TE models...")
    print("Loading features from seasons:", SEASONS)
    print()

    # Build features once for all models
    df = build_features(SEASONS)
    print(f"Loaded {len(df)} total rows")
    print()

    results = []
    for position in ["WR", "TE"]:
        for target in POSITIONS[position]:
            print(f"Processing {position}_{target}...")
            metrics = compute_metrics_for_position(position, target, df)
            if metrics:
                results.append(metrics)
                print(f"  R²={metrics['r2']:.3f}, MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, n={metrics['n_samples']}")

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    for position in ["WR", "TE"]:
        print(f"\n{position} Models:")
        print(f"{'Model':<20} {'R²':>8} {'MAE':>8} {'RMSE':>8} {'Samples':>8}")
        print("-" * 60)

        position_results = [r for r in results if r['position'] == position]
        for r in position_results:
            print(f"{r['target']:<20} {r['r2']:>8.3f} {r['mae']:>8.2f} {r['rmse']:>8.2f} {r['n_samples']:>8}")

        avg_r2 = np.mean([r['r2'] for r in position_results])
        print(f"\n{position} Average R²: {avg_r2:.3f}")

if __name__ == "__main__":
    main()
