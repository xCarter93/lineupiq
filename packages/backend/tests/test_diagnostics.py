"""Tests for model diagnostics module."""

import numpy as np
import polars as pl
import pytest
from xgboost import XGBRegressor

from lineupiq.models.diagnostics import (
    compute_overfit_ratio,
    compute_train_metrics,
    diagnose_overfitting,
    run_diagnostics,
)
from lineupiq.models.persistence import MODELS_DIR, list_models


class TestComputeOverfitRatio:
    """Tests for compute_overfit_ratio function."""

    def test_compute_overfit_ratio_healthy(self):
        """Test ratio close to 1.0 for balanced train/test performance."""
        # Train RMSE = 10, Test RMSE = 11 (10% gap)
        ratio = compute_overfit_ratio(train_rmse=10.0, test_rmse=11.0)
        assert ratio == pytest.approx(1.1, rel=0.01)

    def test_compute_overfit_ratio_overfitting(self):
        """Test ratio > 1.3 when test much worse than train."""
        # Train RMSE = 10, Test RMSE = 20 (100% gap)
        ratio = compute_overfit_ratio(train_rmse=10.0, test_rmse=20.0)
        assert ratio == pytest.approx(2.0, rel=0.01)
        assert ratio > 1.3  # Clearly overfitting

    def test_compute_overfit_ratio_perfect_train(self):
        """Test ratio is infinite when train RMSE is zero (perfect fit)."""
        ratio = compute_overfit_ratio(train_rmse=0.0, test_rmse=10.0)
        assert ratio == float("inf")

    def test_compute_overfit_ratio_equal_performance(self):
        """Test ratio is 1.0 when train and test have same RMSE."""
        ratio = compute_overfit_ratio(train_rmse=15.0, test_rmse=15.0)
        assert ratio == pytest.approx(1.0, rel=0.01)


class TestDiagnoseOverfitting:
    """Tests for diagnose_overfitting function."""

    def test_diagnose_overfitting_healthy(self):
        """Test returns status='healthy' for good generalization."""
        # Ratio = 1.2 (within default 1.3 threshold)
        result = diagnose_overfitting(train_rmse=10.0, test_rmse=12.0)

        assert result["status"] == "healthy"
        assert result["ratio"] == pytest.approx(1.2, rel=0.01)
        assert "No changes needed" in result["recommendation"]

    def test_diagnose_overfitting_flags_overfit(self):
        """Test returns status='overfitting' when ratio > threshold."""
        # Ratio = 1.5 (above default 1.3 threshold)
        result = diagnose_overfitting(train_rmse=10.0, test_rmse=15.0)

        assert result["status"] == "overfitting"
        assert result["ratio"] == pytest.approx(1.5, rel=0.01)
        assert "regularization" in result["recommendation"].lower()

    def test_diagnose_overfitting_custom_threshold(self):
        """Test custom threshold affects diagnosis."""
        # Ratio = 1.2 - overfitting with strict threshold of 1.1
        result = diagnose_overfitting(train_rmse=10.0, test_rmse=12.0, threshold=1.1)

        assert result["status"] == "overfitting"

    def test_diagnose_overfitting_severe_overfitting(self):
        """Test severely overfitting model with ratio > 2.0."""
        # Ratio = 2.5 (very severe overfitting)
        result = diagnose_overfitting(train_rmse=10.0, test_rmse=25.0)

        assert result["status"] == "overfitting"
        assert result["ratio"] == pytest.approx(2.5, rel=0.01)

    def test_diagnose_overfitting_underfitting(self):
        """Test returns status='underfitting' when both train and test are high."""
        # High absolute error but ratio close to 1.0 = underfitting
        result = diagnose_overfitting(train_rmse=60.0, test_rmse=62.0)

        assert result["status"] == "underfitting"
        assert "more features" in result["recommendation"].lower()


class TestComputeTrainMetrics:
    """Tests for compute_train_metrics function."""

    def test_compute_train_metrics_returns_all_metrics(self):
        """Test that train metrics include MAE, RMSE, and R2."""
        # Create simple model and data
        np.random.seed(42)
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100) * 10 + 50

        model = XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
        model.fit(X_train, y_train)

        metrics = compute_train_metrics(model, X_train, y_train)

        assert "train_mae" in metrics
        assert "train_rmse" in metrics
        assert "train_r2" in metrics

        # Values should be reasonable
        assert metrics["train_mae"] >= 0
        assert metrics["train_rmse"] >= 0
        assert isinstance(metrics["train_r2"], float)

    def test_compute_train_metrics_perfect_fit(self):
        """Test metrics for a model that perfectly memorizes training data."""
        np.random.seed(42)
        X_train = np.random.randn(20, 3)
        y_train = np.random.randn(20) * 5

        # Overfit with many estimators
        model = XGBRegressor(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X_train, y_train)

        metrics = compute_train_metrics(model, X_train, y_train)

        # Should have very low training error
        assert metrics["train_rmse"] < 1.0
        assert metrics["train_r2"] > 0.9


class TestRunDiagnostics:
    """Tests for run_diagnostics function."""

    def test_run_diagnostics_returns_complete_dict(self):
        """Test that run_diagnostics returns dict with all expected keys."""
        # Check if any models are saved
        models = list_models()

        if not models:
            pytest.skip("No saved models available for testing")

        # Use first available model
        position, target = models[0]

        # Create minimal synthetic DataFrames
        np.random.seed(42)
        n_samples = 100

        # Feature columns from get_feature_columns
        feature_cols = [
            "passing_yards_roll3",
            "passing_tds_roll3",
            "rushing_yards_roll3",
            "rushing_tds_roll3",
            "carries_roll3",
            "receiving_yards_roll3",
            "receiving_tds_roll3",
            "receptions_roll3",
            "opp_pass_defense_strength",
            "opp_rush_defense_strength",
            "opp_pass_yards_allowed_rank",
            "opp_rush_yards_allowed_rank",
            "opp_total_yards_allowed_rank",
            "temp_normalized",
            "wind_normalized",
            "is_home",
            "is_dome",
        ]

        # Create test DataFrames
        train_data = {
            "position": [position] * n_samples,
            target: np.random.randn(n_samples) * 50 + 200,
        }
        for col in feature_cols:
            train_data[col] = np.random.randn(n_samples)

        test_data = {
            "position": [position] * n_samples,
            target: np.random.randn(n_samples) * 50 + 200,
        }
        for col in feature_cols:
            test_data[col] = np.random.randn(n_samples)

        train_df = pl.DataFrame(train_data)
        test_df = pl.DataFrame(test_data)

        result = run_diagnostics(
            position=position,
            target=target,
            train_df=train_df,
            test_df=test_df,
            feature_cols=feature_cols,
        )

        # Check all expected keys present
        assert "position" in result
        assert "target" in result
        assert "train_metrics" in result
        assert "test_metrics" in result
        assert "overfit_ratio" in result
        assert "diagnosis" in result
        assert "n_train" in result
        assert "n_test" in result

        # Check nested structures
        assert "train_rmse" in result["train_metrics"]
        assert "test_rmse" in result["test_metrics"]
        assert "status" in result["diagnosis"]
        assert "recommendation" in result["diagnosis"]

    @pytest.mark.skipif(
        not MODELS_DIR.exists() or not list(MODELS_DIR.glob("QB_*.joblib")),
        reason="No QB models available for testing",
    )
    def test_run_diagnostics_with_qb_model(self):
        """Test diagnostics with actual QB model if available."""
        # Create synthetic data for QB
        np.random.seed(42)
        n_samples = 100

        feature_cols = [
            "passing_yards_roll3",
            "passing_tds_roll3",
            "rushing_yards_roll3",
            "rushing_tds_roll3",
            "carries_roll3",
            "receiving_yards_roll3",
            "receiving_tds_roll3",
            "receptions_roll3",
            "opp_pass_defense_strength",
            "opp_rush_defense_strength",
            "opp_pass_yards_allowed_rank",
            "opp_rush_yards_allowed_rank",
            "opp_total_yards_allowed_rank",
            "temp_normalized",
            "wind_normalized",
            "is_home",
            "is_dome",
        ]

        # Find first QB target
        qb_models = [m for m in list_models() if m[0] == "QB"]
        if not qb_models:
            pytest.skip("No QB models available")

        position, target = qb_models[0]

        # Create test DataFrames
        train_data = {
            "position": ["QB"] * n_samples,
            target: np.random.randn(n_samples) * 80 + 220,
        }
        for col in feature_cols:
            train_data[col] = np.random.randn(n_samples)

        test_data = {
            "position": ["QB"] * n_samples,
            target: np.random.randn(n_samples) * 80 + 220,
        }
        for col in feature_cols:
            test_data[col] = np.random.randn(n_samples)

        train_df = pl.DataFrame(train_data)
        test_df = pl.DataFrame(test_data)

        result = run_diagnostics(
            position=position,
            target=target,
            train_df=train_df,
            test_df=test_df,
            feature_cols=feature_cols,
        )

        assert result["position"] == "QB"
        assert result["target"] == target
        assert result["n_train"] == n_samples
        assert result["n_test"] == n_samples
        assert result["diagnosis"]["status"] in ["healthy", "overfitting", "underfitting"]
