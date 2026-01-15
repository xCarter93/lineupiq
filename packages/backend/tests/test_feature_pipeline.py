"""
Tests for the unified feature engineering pipeline.

Verifies that the pipeline correctly combines rolling stats, opponent strength,
and weather features into ML-ready datasets.
"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from lineupiq.features import (
    build_features,
    get_feature_columns,
    get_target_columns,
    save_features,
)


class TestBuildFeaturesColumns:
    """Test that build_features returns expected columns."""

    @pytest.fixture
    def feature_df(self):
        """Build features for 2024 season (cached after first call)."""
        return build_features([2024])

    def test_has_rolling_columns(self, feature_df):
        """Verify rolling columns are present."""
        rolling_cols = [c for c in feature_df.columns if "_roll" in c]
        assert len(rolling_cols) >= 6, f"Expected at least 6 rolling columns, got {rolling_cols}"

        # Check specific expected columns
        expected = ["passing_yards_roll3", "rushing_yards_roll3", "receiving_yards_roll3"]
        for col in expected:
            assert col in feature_df.columns, f"Missing rolling column: {col}"

    def test_has_opponent_columns(self, feature_df):
        """Verify opponent strength columns are present."""
        opp_cols = [c for c in feature_df.columns if "opp_" in c]
        assert len(opp_cols) >= 2, f"Expected at least 2 opponent columns, got {opp_cols}"

        # Check specific expected columns
        expected = ["opp_pass_defense_strength", "opp_rush_defense_strength"]
        for col in expected:
            assert col in feature_df.columns, f"Missing opponent column: {col}"

    def test_has_weather_columns(self, feature_df):
        """Verify weather columns are present."""
        assert "temp_normalized" in feature_df.columns
        assert "wind_normalized" in feature_df.columns

    def test_has_context_columns(self, feature_df):
        """Verify game context columns are present."""
        assert "is_home" in feature_df.columns
        assert "opponent" in feature_df.columns
        assert "week" in feature_df.columns
        assert "season" in feature_df.columns


class TestBuildFeaturesNoNulls:
    """Test that key feature columns don't have excessive nulls."""

    @pytest.fixture
    def feature_df(self):
        """Build features for 2024 season."""
        return build_features([2024])

    def test_rolling_features_have_values(self, feature_df):
        """Rolling features should have values (min_periods=1)."""
        rolling_cols = [c for c in feature_df.columns if "_roll3" in c]

        for col in rolling_cols:
            non_null_count = feature_df[col].drop_nulls().len()
            # Most rows should have rolling values
            assert non_null_count > len(feature_df) * 0.5, f"{col} has too many nulls"

    def test_weather_features_no_nulls(self, feature_df):
        """Weather features should default to 0 for nulls."""
        # After processing, these should have no nulls (filled with 0)
        null_temp = feature_df["temp_normalized"].null_count()
        null_wind = feature_df["wind_normalized"].null_count()

        assert null_temp == 0, f"temp_normalized has {null_temp} nulls"
        assert null_wind == 0, f"wind_normalized has {null_wind} nulls"


class TestGetFeatureColumns:
    """Test get_feature_columns helper function."""

    def test_returns_list(self):
        """Should return a list of column names."""
        cols = get_feature_columns()
        assert isinstance(cols, list)
        assert len(cols) > 0

    def test_includes_rolling_features(self):
        """Should include rolling feature columns."""
        cols = get_feature_columns()
        assert "passing_yards_roll3" in cols
        assert "rushing_yards_roll3" in cols

    def test_includes_opponent_features(self):
        """Should include opponent strength columns."""
        cols = get_feature_columns()
        assert "opp_pass_defense_strength" in cols
        assert "opp_rush_defense_strength" in cols

    def test_includes_weather_features(self):
        """Should include weather columns."""
        cols = get_feature_columns()
        assert "temp_normalized" in cols
        assert "wind_normalized" in cols

    def test_excludes_identifiers(self):
        """Should NOT include identifier columns."""
        cols = get_feature_columns()
        assert "player_id" not in cols
        assert "player_name" not in cols
        assert "game_id" not in cols


class TestGetTargetColumns:
    """Test get_target_columns helper function."""

    def test_returns_dict(self):
        """Should return a dict mapping positions to targets."""
        targets = get_target_columns()
        assert isinstance(targets, dict)

    def test_has_all_positions(self):
        """Should have entries for QB, RB, WR, TE."""
        targets = get_target_columns()
        assert "QB" in targets
        assert "RB" in targets
        assert "WR" in targets
        assert "TE" in targets

    def test_qb_targets_include_passing_stats(self):
        """QB targets should include passing stats."""
        targets = get_target_columns()
        assert "passing_yards" in targets["QB"]
        assert "passing_tds" in targets["QB"]

    def test_rb_targets_include_rushing_stats(self):
        """RB targets should include rushing stats."""
        targets = get_target_columns()
        assert "rushing_yards" in targets["RB"]
        assert "rushing_tds" in targets["RB"]
        assert "carries" in targets["RB"]

    def test_wr_targets_include_receiving_stats(self):
        """WR targets should include receiving stats."""
        targets = get_target_columns()
        assert "receiving_yards" in targets["WR"]
        assert "receiving_tds" in targets["WR"]
        assert "receptions" in targets["WR"]


class TestBuildFeaturesWithWindow:
    """Test custom rolling window parameter."""

    def test_window_5_creates_roll5_columns(self):
        """Using window=5 should create _roll5 columns."""
        df = build_features([2024], rolling_window=5)

        roll5_cols = [c for c in df.columns if "_roll5" in c]
        assert len(roll5_cols) >= 6, f"Expected _roll5 columns, got {roll5_cols}"

        # Should NOT have _roll3 columns
        roll3_cols = [c for c in df.columns if "_roll3" in c]
        assert len(roll3_cols) == 0, f"Should not have _roll3 columns with window=5: {roll3_cols}"


class TestSaveAndLoadFeatures:
    """Test save/load roundtrip for features."""

    def test_save_and_load_roundtrip(self):
        """Features should be identical after save/load cycle."""
        # Build features
        df = build_features([2024])

        # Save to temp location
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_features.parquet"

            # We need to save directly since save_features uses fixed path
            df.write_parquet(save_path)

            # Load back
            loaded = pl.read_parquet(save_path)

            # Compare
            assert len(loaded) == len(df), "Row count mismatch"
            assert set(loaded.columns) == set(df.columns), "Column mismatch"

            # Verify data matches for a sample column
            orig_vals = df["passing_yards_roll3"].drop_nulls().to_list()[:10]
            load_vals = loaded["passing_yards_roll3"].drop_nulls().to_list()[:10]
            assert orig_vals == load_vals, "Data values don't match after roundtrip"
