"""
Compute R², MAE, and RMSE for all RB models.
"""

import joblib
import numpy as np
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

from lineupiq.features.pipeline import build_features
from lineupiq.models.rb import prepare_rb_data


def compute_metrics_for_model(model_path, X, y):
    """Compute R², MAE, and RMSE for a trained model."""
    artifact = joblib.load(model_path)
    model = artifact['model']

    # Use TimeSeriesSplit for cross-validation (same as training)
    cv = TimeSeriesSplit(n_splits=5)

    r2_scores = []
    mae_scores = []
    rmse_scores = []

    for train_idx, test_idx in cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Predict on test set
        y_pred = model.predict(X_test)

        # Compute metrics
        r2_scores.append(r2_score(y_test, y_pred))
        mae_scores.append(mean_absolute_error(y_test, y_pred))
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))

    return {
        'r2': np.mean(r2_scores),
        'mae': np.mean(mae_scores),
        'rmse': np.mean(rmse_scores),
        'r2_std': np.std(r2_scores),
        'mae_std': np.std(mae_scores),
        'rmse_std': np.std(rmse_scores),
    }


def main():
    print("Loading RB training data...")

    # Load data using same pipeline as training
    seasons = [2022, 2023, 2024, 2025]
    df = build_features(seasons, rolling_window=5)

    # Prepare RB data
    X, targets = prepare_rb_data(df)

    print(f"Loaded {len(X)} RB samples with {X.shape[1]} features")
    print(f"Targets: {list(targets.keys())}")
    print()

    # Define model order to match training output
    model_order = [
        'rushing_yards',
        'rushing_tds',
        'carries',
        'receiving_yards',
        'receptions',
        'receiving_tds',
        'fumbles_lost'
    ]

    results = []

    for target_name in model_order:
        model_path = Path(__file__).parent / 'models' / f'RB_{target_name}.joblib'

        if not model_path.exists():
            print(f"⚠️  Model not found: {model_path}")
            continue

        print(f"Computing metrics for {target_name}...")
        y = targets[target_name]
        metrics = compute_metrics_for_model(model_path, X, y)

        results.append({
            'target': target_name,
            'r2': metrics['r2'],
            'mae': metrics['mae'],
            'rmse': metrics['rmse'],
            'r2_std': metrics['r2_std'],
            'mae_std': metrics['mae_std'],
            'rmse_std': metrics['rmse_std'],
            'samples': len(X)
        })

    print()
    print("=" * 80)
    print("RB MODEL PERFORMANCE METRICS")
    print("=" * 80)
    print(f"{'Model':<20} {'R²':<8} {'MAE':<10} {'RMSE':<10} {'Samples':<10}")
    print("-" * 80)

    for result in results:
        print(f"{result['target']:<20} {result['r2']:<8.3f} {result['mae']:<10.2f} {result['rmse']:<10.2f} {result['samples']:<10}")

    print("=" * 80)

    # Calculate average R²
    avg_r2 = np.mean([r['r2'] for r in results])
    print(f"\nAverage R²: {avg_r2:.3f}")

    # Save results to file for documentation
    output_file = Path(__file__).parent / 'rb_metrics.txt'
    with open(output_file, 'w') as f:
        f.write("RB MODEL PERFORMANCE METRICS\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'Model':<20} {'R²':<8} {'MAE':<10} {'RMSE':<12} {'CV RMSE':<12} {'Samples':<10}\n")
        f.write("-" * 80 + "\n")

        for result in results:
            cv_rmse = f"{result['rmse']:.2f} ± {result['rmse_std']:.2f}"
            f.write(f"{result['target']:<20} {result['r2']:<8.3f} {result['mae']:<10.2f} {result['rmse']:<12.2f} {cv_rmse:<12} {result['samples']:<10}\n")

        f.write("=" * 80 + "\n")
        f.write(f"\nAverage R²: {avg_r2:.3f}\n")

    print(f"\nMetrics saved to {output_file}")


if __name__ == '__main__':
    main()
