"""Tests for ensemble module."""

import numpy as np
import pytest
from pathlib import Path
from sklearn.datasets import make_regression
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import VotingRegressor, StackingRegressor

from lineupiq.models.ensemble import (
    create_voting_ensemble,
    create_stacking_ensemble,
    save_ensemble,
    load_ensemble,
    MODELS_DIR,
)


class TestCreateVotingSimple:
    """Tests for create_voting_ensemble with simple averaging."""

    def test_create_voting_simple_returns_voting_regressor(self):
        """Test that simple averaging returns VotingRegressor."""
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="mean")

        ensemble = create_voting_ensemble(lgbm_model, xgb_model, weights=None)

        assert isinstance(ensemble, VotingRegressor)
        assert ensemble.weights is None  # Simple averaging uses equal weights

    def test_create_voting_simple_averages_predictions(self):
        """Test that simple averaging correctly averages predictions."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create two dummy models with different strategies
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")

        # Fit models separately
        lgbm_model.fit(X, y)
        xgb_model.fit(X, y)

        # Create and fit ensemble
        ensemble = create_voting_ensemble(lgbm_model, xgb_model)
        ensemble.fit(X, y)

        # Predictions should be average of both models
        lgbm_pred = lgbm_model.predict(X[:10])
        xgb_pred = xgb_model.predict(X[:10])
        ensemble_pred = ensemble.predict(X[:10])

        expected = (lgbm_pred + xgb_pred) / 2
        np.testing.assert_array_almost_equal(ensemble_pred, expected, decimal=5)


class TestCreateVotingWeighted:
    """Tests for create_voting_ensemble with weighted averaging."""

    def test_create_voting_weighted_returns_voting_regressor(self):
        """Test that weighted averaging returns VotingRegressor with weights."""
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="mean")

        ensemble = create_voting_ensemble(lgbm_model, xgb_model, weights=[0.6, 0.4])

        assert isinstance(ensemble, VotingRegressor)
        assert ensemble.weights == [0.6, 0.4]

    def test_create_voting_weighted_respects_weights(self):
        """Test that weighted averaging respects custom weights."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create two dummy models
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")

        # Fit models
        lgbm_model.fit(X, y)
        xgb_model.fit(X, y)

        # Create weighted ensemble (60% LightGBM, 40% XGBoost)
        ensemble = create_voting_ensemble(lgbm_model, xgb_model, weights=[0.6, 0.4])
        ensemble.fit(X, y)

        # Predictions should be weighted average
        lgbm_pred = lgbm_model.predict(X[:10])
        xgb_pred = xgb_model.predict(X[:10])
        ensemble_pred = ensemble.predict(X[:10])

        expected = 0.6 * lgbm_pred + 0.4 * xgb_pred
        np.testing.assert_array_almost_equal(ensemble_pred, expected, decimal=5)


class TestCreateStacking:
    """Tests for create_stacking_ensemble."""

    def test_create_stacking_returns_stacking_regressor(self):
        """Test that stacking returns StackingRegressor."""
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="mean")

        ensemble = create_stacking_ensemble(lgbm_model, xgb_model, cv=3)

        assert isinstance(ensemble, StackingRegressor)
        assert ensemble.cv == 3
        assert ensemble.passthrough is False

    def test_create_stacking_with_ridge_meta_learner(self):
        """Test that stacking uses Ridge meta-learner."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create and fit dummy models
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")

        # Create stacking ensemble
        ensemble = create_stacking_ensemble(lgbm_model, xgb_model, cv=3)

        # Fit ensemble (this trains meta-learner)
        ensemble.fit(X, y)

        # Meta-learner should be Ridge with alpha=1.0
        from sklearn.linear_model import Ridge
        assert isinstance(ensemble.final_estimator_, Ridge)
        assert ensemble.final_estimator_.alpha == 1.0

    def test_create_stacking_makes_predictions(self):
        """Test that stacking ensemble can make predictions."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create and fit models
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")

        ensemble = create_stacking_ensemble(lgbm_model, xgb_model, cv=3)
        ensemble.fit(X, y)

        # Should be able to predict
        predictions = ensemble.predict(X[:10])

        assert predictions.shape == (10,)
        assert not np.isnan(predictions).any()


class TestSaveLoadEnsemble:
    """Tests for save_ensemble and load_ensemble."""

    def test_save_load_ensemble_voting_simple(self, tmp_path):
        """Test save/load round-trip preserves voting_simple predictions."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create and fit ensemble
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")
        lgbm_model.fit(X, y)
        xgb_model.fit(X, y)

        ensemble = create_voting_ensemble(lgbm_model, xgb_model)
        ensemble.fit(X, y)

        # Get predictions before save
        original_pred = ensemble.predict(X[:10])

        # Save ensemble to temporary directory
        original_models_dir = MODELS_DIR
        try:
            # Temporarily override MODELS_DIR
            import lineupiq.models.ensemble as ensemble_module
            ensemble_module.MODELS_DIR = tmp_path

            save_path = save_ensemble(ensemble, "QB", "passing_yards", "voting_simple")
            assert save_path.exists()
            assert save_path.name == "QB_passing_yards_voting_simple.joblib"

            # Load ensemble
            loaded_ensemble = load_ensemble("QB", "passing_yards", "voting_simple")

            # Predictions should match
            loaded_pred = loaded_ensemble.predict(X[:10])
            np.testing.assert_array_almost_equal(original_pred, loaded_pred, decimal=5)
        finally:
            # Restore original MODELS_DIR
            ensemble_module.MODELS_DIR = original_models_dir

    def test_save_load_ensemble_weighted(self, tmp_path):
        """Test save/load round-trip preserves weighted ensemble predictions."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create and fit weighted ensemble
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")
        lgbm_model.fit(X, y)
        xgb_model.fit(X, y)

        ensemble = create_voting_ensemble(lgbm_model, xgb_model, weights=[0.7, 0.3])
        ensemble.fit(X, y)

        original_pred = ensemble.predict(X[:10])

        # Save and load
        import lineupiq.models.ensemble as ensemble_module
        original_models_dir = ensemble_module.MODELS_DIR
        try:
            ensemble_module.MODELS_DIR = tmp_path

            save_ensemble(ensemble, "RB", "rushing_yards", "voting_weighted")
            loaded_ensemble = load_ensemble("RB", "rushing_yards", "voting_weighted")

            loaded_pred = loaded_ensemble.predict(X[:10])
            np.testing.assert_array_almost_equal(original_pred, loaded_pred, decimal=5)
        finally:
            ensemble_module.MODELS_DIR = original_models_dir

    def test_save_load_ensemble_stacking(self, tmp_path):
        """Test save/load round-trip preserves stacking ensemble predictions."""
        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)

        # Create and fit stacking ensemble
        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="median")

        ensemble = create_stacking_ensemble(lgbm_model, xgb_model, cv=3)
        ensemble.fit(X, y)

        original_pred = ensemble.predict(X[:10])

        # Save and load
        import lineupiq.models.ensemble as ensemble_module
        original_models_dir = ensemble_module.MODELS_DIR
        try:
            ensemble_module.MODELS_DIR = tmp_path

            save_ensemble(ensemble, "WR", "receiving_yards", "stacking")
            loaded_ensemble = load_ensemble("WR", "receiving_yards", "stacking")

            loaded_pred = loaded_ensemble.predict(X[:10])
            np.testing.assert_array_almost_equal(original_pred, loaded_pred, decimal=5)
        finally:
            ensemble_module.MODELS_DIR = original_models_dir

    def test_load_ensemble_raises_file_not_found(self):
        """Test that load_ensemble raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError, match="Ensemble not found"):
            load_ensemble("QB", "nonexistent_stat", "voting_simple")

    def test_save_ensemble_creates_models_dir(self, tmp_path):
        """Test that save_ensemble creates models directory if it doesn't exist."""
        np.random.seed(42)
        X, y = make_regression(n_samples=50, n_features=5, random_state=42)

        lgbm_model = DummyRegressor(strategy="mean")
        xgb_model = DummyRegressor(strategy="mean")
        lgbm_model.fit(X, y)
        xgb_model.fit(X, y)

        ensemble = create_voting_ensemble(lgbm_model, xgb_model)
        ensemble.fit(X, y)

        # Point to new directory that doesn't exist
        import lineupiq.models.ensemble as ensemble_module
        original_models_dir = ensemble_module.MODELS_DIR
        try:
            new_dir = tmp_path / "new_models_dir"
            assert not new_dir.exists()

            ensemble_module.MODELS_DIR = new_dir
            save_ensemble(ensemble, "QB", "passing_yards", "voting_simple")

            # Directory should now exist
            assert new_dir.exists()
            assert (new_dir / "QB_passing_yards_voting_simple.joblib").exists()
        finally:
            ensemble_module.MODELS_DIR = original_models_dir
