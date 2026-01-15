"""Tests for QB-specific model training module."""

import numpy as np
import polars as pl
import pytest

from lineupiq.features.pipeline import get_feature_columns
from lineupiq.models import QB_TARGETS, load_model, prepare_qb_data
from lineupiq.models.qb import train_qb_models


@pytest.fixture
def sample_qb_data() -> pl.DataFrame:
    """Create sample data for QB model testing."""
    # Create 100 rows of sample data
    n_rows = 100
    feature_cols = get_feature_columns()

    # Build DataFrame with required columns
    data = {
        # Identifier columns
        "player_id": [f"QB{i}" for i in range(n_rows)],
        "player_name": [f"Quarterback {i}" for i in range(n_rows)],
        "position": ["QB"] * n_rows,
        "team": ["KC"] * n_rows,
        "season": [2024] * n_rows,
        "week": list(range(1, n_rows + 1)),
        # Target columns
        "passing_yards": np.random.uniform(150, 350, n_rows).tolist(),
        "passing_tds": np.random.uniform(0, 4, n_rows).tolist(),
    }

    # Add feature columns with random values
    for col in feature_cols:
        if col.endswith("_roll3"):
            # Rolling stats - reasonable ranges
            if "yards" in col:
                data[col] = np.random.uniform(50, 300, n_rows).tolist()
            elif "tds" in col:
                data[col] = np.random.uniform(0, 3, n_rows).tolist()
            else:
                data[col] = np.random.uniform(0, 20, n_rows).tolist()
        elif col.startswith("opp_"):
            # Opponent features - 0 to 1 for strength, 1 to 32 for ranks
            if "strength" in col:
                data[col] = np.random.uniform(0, 1, n_rows).tolist()
            else:
                data[col] = np.random.uniform(1, 32, n_rows).tolist()
        elif col in ["temp_normalized", "wind_normalized"]:
            # Weather features - normalized around 0
            data[col] = np.random.uniform(-1, 1, n_rows).tolist()
        elif col in ["is_home", "is_dome"]:
            # Binary features
            data[col] = np.random.choice([0, 1], n_rows).tolist()

    return pl.DataFrame(data)


@pytest.fixture
def mixed_position_data(sample_qb_data: pl.DataFrame) -> pl.DataFrame:
    """Create sample data with mixed positions (QB, RB, WR)."""
    # Add RB and WR rows
    rb_data = sample_qb_data.clone().with_columns(
        pl.lit("RB").alias("position"),
        pl.col("player_id").str.replace("QB", "RB"),
    )
    wr_data = sample_qb_data.clone().with_columns(
        pl.lit("WR").alias("position"),
        pl.col("player_id").str.replace("QB", "WR"),
    )

    return pl.concat([sample_qb_data, rb_data, wr_data])


class TestPrepareQbData:
    """Tests for prepare_qb_data function."""

    def test_filters_to_qb_position(self, mixed_position_data: pl.DataFrame):
        """Verify only QB data is returned."""
        X, y_dict = prepare_qb_data(mixed_position_data)

        # Should have 100 QB rows (not 300 total)
        assert X.shape[0] == 100
        assert len(y_dict["passing_yards"]) == 100
        assert len(y_dict["passing_tds"]) == 100

    def test_returns_correct_feature_count(self, sample_qb_data: pl.DataFrame):
        """Verify feature count matches get_feature_columns()."""
        X, _ = prepare_qb_data(sample_qb_data)
        expected_features = len(get_feature_columns())

        assert X.shape[1] == expected_features

    def test_returns_all_qb_targets(self, sample_qb_data: pl.DataFrame):
        """Verify all QB targets are returned."""
        _, y_dict = prepare_qb_data(sample_qb_data)

        for target in QB_TARGETS:
            assert target in y_dict
            assert len(y_dict[target]) > 0

    def test_drops_null_values(self, sample_qb_data: pl.DataFrame):
        """Verify rows with null values are dropped."""
        # Add some null values
        df_with_nulls = sample_qb_data.with_columns(
            pl.when(pl.col("week") <= 5)
            .then(None)
            .otherwise(pl.col("passing_yards_roll3"))
            .alias("passing_yards_roll3")
        )

        X, y_dict = prepare_qb_data(df_with_nulls)

        # Should have 95 rows (100 - 5 nulls)
        assert X.shape[0] == 95
        assert len(y_dict["passing_yards"]) == 95


class TestQbModelPredictions:
    """Tests for saved QB model predictions."""

    def test_passing_yards_predictions_reasonable(self, sample_qb_data: pl.DataFrame):
        """Verify passing_yards predictions are in reasonable range [0, 600]."""
        try:
            model, metadata = load_model("QB", "passing_yards")
        except FileNotFoundError:
            pytest.skip("QB passing_yards model not trained yet")

        # Get feature data
        X, _ = prepare_qb_data(sample_qb_data)

        # Make predictions
        predictions = model.predict(X)

        # All predictions should be in reasonable range
        assert np.all(predictions >= 0), "Predictions should be >= 0"
        assert np.all(predictions <= 600), "Predictions should be <= 600 yards"

        # Mean should be in typical QB range
        mean_pred = np.mean(predictions)
        assert 100 <= mean_pred <= 400, f"Mean prediction {mean_pred} outside typical range"

    def test_passing_tds_predictions_reasonable(self, sample_qb_data: pl.DataFrame):
        """Verify passing_tds predictions are in reasonable range [0, 8]."""
        try:
            model, metadata = load_model("QB", "passing_tds")
        except FileNotFoundError:
            pytest.skip("QB passing_tds model not trained yet")

        # Get feature data
        X, _ = prepare_qb_data(sample_qb_data)

        # Make predictions
        predictions = model.predict(X)

        # All predictions should be in reasonable range
        assert np.all(predictions >= 0), "Predictions should be >= 0"
        assert np.all(predictions <= 8), "Predictions should be <= 8 TDs"

        # Mean should be in typical range
        mean_pred = np.mean(predictions)
        assert 0 <= mean_pred <= 5, f"Mean TD prediction {mean_pred} outside typical range"


class TestTrainQbModels:
    """Integration tests for train_qb_models function."""

    @pytest.mark.slow
    def test_train_qb_models_creates_models(self):
        """Integration test - train models with minimal trials for speed."""
        # Use small n_trials for fast test
        # This test trains real models, so mark as slow
        results = train_qb_models(seasons=[2023, 2024], n_trials=5)

        # Should return results for both targets
        assert "passing_yards" in results
        assert "passing_tds" in results

        # Each result should be (model, metrics) tuple
        for target in QB_TARGETS:
            model, metrics = results[target]

            # Model should be fitted
            assert hasattr(model, "predict")

            # Metrics should contain expected keys
            assert "cv_rmse_mean" in metrics
            assert "cv_rmse_std" in metrics
            assert "best_params" in metrics
            assert "n_samples" in metrics

            # RMSE should be positive
            assert metrics["cv_rmse_mean"] > 0
            assert metrics["cv_rmse_std"] >= 0
