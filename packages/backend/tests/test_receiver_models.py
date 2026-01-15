"""Tests for receiver (WR/TE) model training module."""

import numpy as np
import polars as pl
import pytest

from lineupiq.features.pipeline import get_feature_columns
from lineupiq.models import RECEIVER_TARGETS, load_model, prepare_receiver_data
from lineupiq.models.receiver import train_te_models, train_wr_models


@pytest.fixture
def sample_wr_data() -> pl.DataFrame:
    """Create sample data for WR model testing."""
    # Create 100 rows of sample data
    n_rows = 100
    feature_cols = get_feature_columns()

    # Build DataFrame with required columns
    data = {
        # Identifier columns
        "player_id": [f"WR{i}" for i in range(n_rows)],
        "player_name": [f"Wide Receiver {i}" for i in range(n_rows)],
        "position": ["WR"] * n_rows,
        "team": ["KC"] * n_rows,
        "season": [2024] * n_rows,
        "week": list(range(1, n_rows + 1)),
        # Target columns
        "receiving_yards": np.random.uniform(20, 120, n_rows).tolist(),
        "receiving_tds": np.random.uniform(0, 2, n_rows).tolist(),
        "receptions": np.random.uniform(2, 10, n_rows).tolist(),
    }

    # Add feature columns with random values
    for col in feature_cols:
        if col.endswith("_roll3"):
            # Rolling stats - reasonable ranges
            if "yards" in col:
                data[col] = np.random.uniform(20, 150, n_rows).tolist()
            elif "tds" in col:
                data[col] = np.random.uniform(0, 2, n_rows).tolist()
            else:
                data[col] = np.random.uniform(0, 10, n_rows).tolist()
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
def sample_te_data() -> pl.DataFrame:
    """Create sample data for TE model testing."""
    # Create 100 rows of sample data with TE-appropriate stat distributions
    n_rows = 100
    feature_cols = get_feature_columns()

    # Build DataFrame with required columns
    data = {
        # Identifier columns
        "player_id": [f"TE{i}" for i in range(n_rows)],
        "player_name": [f"Tight End {i}" for i in range(n_rows)],
        "position": ["TE"] * n_rows,
        "team": ["KC"] * n_rows,
        "season": [2024] * n_rows,
        "week": list(range(1, n_rows + 1)),
        # Target columns - TE typically has lower stats than WR
        "receiving_yards": np.random.uniform(10, 80, n_rows).tolist(),
        "receiving_tds": np.random.uniform(0, 1.5, n_rows).tolist(),
        "receptions": np.random.uniform(1, 7, n_rows).tolist(),
    }

    # Add feature columns with random values
    for col in feature_cols:
        if col.endswith("_roll3"):
            # Rolling stats - reasonable ranges
            if "yards" in col:
                data[col] = np.random.uniform(10, 100, n_rows).tolist()
            elif "tds" in col:
                data[col] = np.random.uniform(0, 1.5, n_rows).tolist()
            else:
                data[col] = np.random.uniform(0, 8, n_rows).tolist()
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
def mixed_position_data(sample_wr_data: pl.DataFrame, sample_te_data: pl.DataFrame) -> pl.DataFrame:
    """Create sample data with mixed positions (WR, TE, and QB for filtering test)."""
    # Add QB rows
    qb_data = sample_wr_data.clone().with_columns(
        pl.lit("QB").alias("position"),
        pl.col("player_id").str.replace("WR", "QB"),
    )

    return pl.concat([sample_wr_data, sample_te_data, qb_data])


class TestPrepareReceiverDataWR:
    """Tests for prepare_receiver_data function with WR position."""

    def test_filters_to_wr_position(self, mixed_position_data: pl.DataFrame):
        """Verify only WR data is returned when filtering for WR."""
        X, y_dict = prepare_receiver_data(mixed_position_data, "WR")

        # Should have 100 WR rows (not 300 total)
        assert X.shape[0] == 100
        for target in RECEIVER_TARGETS:
            assert len(y_dict[target]) == 100

    def test_returns_correct_feature_count(self, sample_wr_data: pl.DataFrame):
        """Verify feature count matches get_feature_columns()."""
        X, _ = prepare_receiver_data(sample_wr_data, "WR")
        expected_features = len(get_feature_columns())

        assert X.shape[1] == expected_features

    def test_returns_all_receiver_targets(self, sample_wr_data: pl.DataFrame):
        """Verify all receiver targets are returned."""
        _, y_dict = prepare_receiver_data(sample_wr_data, "WR")

        for target in RECEIVER_TARGETS:
            assert target in y_dict
            assert len(y_dict[target]) > 0


class TestPrepareReceiverDataTE:
    """Tests for prepare_receiver_data function with TE position."""

    def test_filters_to_te_position(self, mixed_position_data: pl.DataFrame):
        """Verify only TE data is returned when filtering for TE."""
        X, y_dict = prepare_receiver_data(mixed_position_data, "TE")

        # Should have 100 TE rows (not 300 total)
        assert X.shape[0] == 100
        for target in RECEIVER_TARGETS:
            assert len(y_dict[target]) == 100

    def test_returns_correct_feature_count(self, sample_te_data: pl.DataFrame):
        """Verify feature count matches get_feature_columns()."""
        X, _ = prepare_receiver_data(sample_te_data, "TE")
        expected_features = len(get_feature_columns())

        assert X.shape[1] == expected_features


class TestPrepareReceiverDataValidation:
    """Tests for prepare_receiver_data validation."""

    def test_invalid_position_raises_error(self, sample_wr_data: pl.DataFrame):
        """Verify invalid position raises ValueError."""
        with pytest.raises(ValueError, match="Position must be 'WR' or 'TE'"):
            prepare_receiver_data(sample_wr_data, "QB")

    def test_drops_null_values(self, sample_wr_data: pl.DataFrame):
        """Verify rows with null values are dropped."""
        # Add some null values
        df_with_nulls = sample_wr_data.with_columns(
            pl.when(pl.col("week") <= 5)
            .then(None)
            .otherwise(pl.col("receiving_yards_roll3"))
            .alias("receiving_yards_roll3")
        )

        X, y_dict = prepare_receiver_data(df_with_nulls, "WR")

        # Should have 95 rows (100 - 5 nulls)
        assert X.shape[0] == 95
        assert len(y_dict["receiving_yards"]) == 95


class TestWRModelPredictions:
    """Tests for saved WR model predictions."""

    def test_wr_receiving_yards_predictions_reasonable(self, sample_wr_data: pl.DataFrame):
        """Verify WR receiving_yards predictions are in reasonable range.

        WR receiving yards typically range from 0-250 per game.
        """
        try:
            model, metadata = load_model("WR", "receiving_yards")
        except FileNotFoundError:
            pytest.skip("WR receiving_yards model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_wr_data, "WR")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # WR predictions should be in reasonable range
        assert np.all(predictions >= -30), "Predictions should be >= -30"
        assert np.all(predictions <= 250), "Predictions should be <= 250 yards"

        # Mean should be in typical WR range
        mean_pred = np.mean(predictions)
        assert 10 <= mean_pred <= 150, f"Mean prediction {mean_pred} outside typical range"

    def test_wr_receiving_tds_predictions_reasonable(self, sample_wr_data: pl.DataFrame):
        """Verify WR receiving_tds predictions are in reasonable range.

        WR receiving TDs typically range from 0-4 per game.
        """
        try:
            model, metadata = load_model("WR", "receiving_tds")
        except FileNotFoundError:
            pytest.skip("WR receiving_tds model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_wr_data, "WR")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # No extreme values
        assert np.all(predictions >= -0.5), "Predictions should be >= -0.5"
        assert np.all(predictions <= 4), "Predictions should be <= 4 TDs"

    def test_wr_receptions_predictions_reasonable(self, sample_wr_data: pl.DataFrame):
        """Verify WR receptions predictions are in reasonable range.

        WR receptions typically range from 0-18 per game.
        """
        try:
            model, metadata = load_model("WR", "receptions")
        except FileNotFoundError:
            pytest.skip("WR receptions model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_wr_data, "WR")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # No extreme values
        assert np.all(predictions >= -2), "Predictions should be >= -2"
        assert np.all(predictions <= 18), "Predictions should be <= 18 receptions"


class TestTEModelPredictions:
    """Tests for saved TE model predictions."""

    def test_te_receiving_yards_predictions_reasonable(self, sample_te_data: pl.DataFrame):
        """Verify TE receiving_yards predictions are in reasonable range.

        TE receiving yards typically range from 0-150 per game (lower than WR).
        """
        try:
            model, metadata = load_model("TE", "receiving_yards")
        except FileNotFoundError:
            pytest.skip("TE receiving_yards model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_te_data, "TE")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # TE predictions should be in reasonable range
        assert np.all(predictions >= -30), "Predictions should be >= -30"
        assert np.all(predictions <= 150), "Predictions should be <= 150 yards"

    def test_te_receiving_tds_predictions_reasonable(self, sample_te_data: pl.DataFrame):
        """Verify TE receiving_tds predictions are in reasonable range.

        TE receiving TDs typically range from 0-3 per game (lower than WR).
        """
        try:
            model, metadata = load_model("TE", "receiving_tds")
        except FileNotFoundError:
            pytest.skip("TE receiving_tds model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_te_data, "TE")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # No extreme values
        assert np.all(predictions >= -0.5), "Predictions should be >= -0.5"
        assert np.all(predictions <= 3), "Predictions should be <= 3 TDs"

    def test_te_receptions_predictions_reasonable(self, sample_te_data: pl.DataFrame):
        """Verify TE receptions predictions are in reasonable range.

        TE receptions typically range from 0-12 per game (lower than WR).
        """
        try:
            model, metadata = load_model("TE", "receptions")
        except FileNotFoundError:
            pytest.skip("TE receptions model not trained yet")

        # Get feature data
        X, _ = prepare_receiver_data(sample_te_data, "TE")

        # Make predictions
        predictions = model.predict(X)

        # Most predictions should be positive
        pct_positive = np.sum(predictions >= 0) / len(predictions)
        assert pct_positive >= 0.9, f"Only {pct_positive:.1%} predictions positive"

        # No extreme values
        assert np.all(predictions >= -2), "Predictions should be >= -2"
        assert np.all(predictions <= 12), "Predictions should be <= 12 receptions"


class TestTrainWRModels:
    """Integration tests for train_wr_models function."""

    @pytest.mark.slow
    def test_train_wr_models_creates_models(self):
        """Integration test - train WR models with minimal trials for speed."""
        # Use small n_trials for fast test
        results = train_wr_models(seasons=[2023, 2024], n_trials=5)

        # Should return results for all receiver targets
        for target in RECEIVER_TARGETS:
            assert target in results

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


class TestTrainTEModels:
    """Integration tests for train_te_models function."""

    @pytest.mark.slow
    def test_train_te_models_creates_models(self):
        """Integration test - train TE models with minimal trials for speed."""
        # Use small n_trials for fast test
        results = train_te_models(seasons=[2023, 2024], n_trials=5)

        # Should return results for all receiver targets
        for target in RECEIVER_TARGETS:
            assert target in results

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
