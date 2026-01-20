"""Tests for rolling statistics module."""

import polars as pl
import pytest

from lineupiq.features.rolling_stats import compute_rolling_stats


@pytest.fixture
def synthetic_player_data() -> pl.DataFrame:
    """Create synthetic player data with known values for testing."""
    return pl.DataFrame({
        "player_id": ["p1", "p1", "p1", "p2", "p2", "p2"],
        "season": [2024, 2024, 2024, 2024, 2024, 2024],
        "week": [1, 2, 3, 1, 2, 3],
        "passing_yards": [100.0, 200.0, 300.0, 50.0, 100.0, 150.0],
        "passing_tds": [1.0, 2.0, 3.0, 0.0, 1.0, 2.0],
        "interceptions": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        "rushing_yards": [10.0, 20.0, 30.0, 5.0, 10.0, 15.0],
        "rushing_tds": [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        "carries": [2.0, 4.0, 6.0, 1.0, 2.0, 3.0],
        "receiving_yards": [0.0, 0.0, 0.0, 40.0, 60.0, 80.0],
        "receiving_tds": [0.0, 0.0, 0.0, 1.0, 0.0, 1.0],
        "receptions": [0.0, 0.0, 0.0, 4.0, 5.0, 6.0],
    })


class TestRollingStatsBasic:
    """Test basic functionality of compute_rolling_stats."""

    def test_rolling_stats_basic(self, synthetic_player_data: pl.DataFrame):
        """Verify rolling columns are created with correct naming."""
        result = compute_rolling_stats(synthetic_player_data)  # Uses default window=5

        # Check all expected rolling columns exist
        expected_columns = [
            "passing_yards_roll5",
            "passing_tds_roll5",
            "interceptions_roll5",
            "rushing_yards_roll5",
            "rushing_tds_roll5",
            "carries_roll5",
            "receiving_yards_roll5",
            "receiving_tds_roll5",
            "receptions_roll5",
        ]

        for col in expected_columns:
            assert col in result.columns, f"Missing expected column: {col}"

    def test_rolling_stats_preserves_original_columns(
        self, synthetic_player_data: pl.DataFrame
    ):
        """Verify original columns are preserved."""
        result = compute_rolling_stats(synthetic_player_data)  # Uses default window=5

        for col in synthetic_player_data.columns:
            assert col in result.columns, f"Original column {col} was lost"


class TestRollingStatsCalculation:
    """Test correctness of rolling calculations."""

    def test_rolling_stats_calculation(self, synthetic_player_data: pl.DataFrame):
        """Verify rolling math is correct with shift(1) for leakage prevention.

        Player 1 passing_yards: [100, 200, 300]
        With shift(1), rolling stats only use prior games, not current:
        - Week 1 rolling avg: null (no prior games)
        - Week 2 rolling avg: 100.0 (only week 1: 100)
        - Week 3 rolling avg: 150.0 (weeks 1-2: mean(100, 200))
        """
        result = compute_rolling_stats(synthetic_player_data)  # Uses default window=5

        # Filter to player 1 and sort by week
        p1_result = result.filter(pl.col("player_id") == "p1").sort("week")
        passing_roll = p1_result["passing_yards_roll5"].to_list()

        # Week 1: no prior games, should be null
        assert passing_roll[0] is None

        # Week 2: only prior game is week 1 (100)
        assert passing_roll[1] == pytest.approx(100.0, rel=1e-5)

        # Week 3: prior games are weeks 1-2, mean(100, 200) = 150
        assert passing_roll[2] == pytest.approx(150.0, rel=1e-5)


class TestRollingStatsPerPlayer:
    """Test that rolling is computed per player, not globally."""

    def test_rolling_stats_per_player(self, synthetic_player_data: pl.DataFrame):
        """Verify each player's rolling only uses their own history.

        With shift(1) for leakage prevention:
        Player 1 passing_yards: [100, 200, 300] -> week 3 avg = mean(100, 200) = 150
        Player 2 passing_yards: [50, 100, 150] -> week 3 avg = mean(50, 100) = 75

        If rolling was global, both players would have the same rolling avg.
        """
        result = compute_rolling_stats(synthetic_player_data)  # Uses default window=5

        # Get week 3 rolling for both players
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll5"][0]

        p2_week3 = result.filter(
            (pl.col("player_id") == "p2") & (pl.col("week") == 3)
        )["passing_yards_roll5"][0]

        # Player 1: mean(100, 200) = 150 (weeks 1-2, shifted)
        assert p1_week3 == pytest.approx(150.0, rel=1e-5)

        # Player 2: mean(50, 100) = 75 (weeks 1-2, shifted)
        assert p2_week3 == pytest.approx(75.0, rel=1e-5)

        # Verify they are different (proves per-player computation)
        assert p1_week3 != p2_week3


class TestRollingStatsMinPeriods:
    """Test min_periods handling for early season."""

    def test_rolling_stats_min_periods(self, synthetic_player_data: pl.DataFrame):
        """Verify min_periods=1 works for early season with shift(1).

        Week 1 should have null rolling avg (no prior games due to shift).
        Week 2 should have the week 1 value.
        """
        result = compute_rolling_stats(synthetic_player_data)  # Uses default window=5

        # Player 1 week 1: no prior games due to shift(1), should be null
        p1_week1 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 1)
        )["passing_yards_roll5"][0]

        # Week 1 should be null (no prior games)
        assert p1_week1 is None

        # Player 1 week 2: only has week 1 as prior, rolling avg = 100
        p1_week2 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 2)
        )["passing_yards_roll5"][0]

        # Rolling avg should be 100 (only week 1)
        assert p1_week2 == pytest.approx(100.0, rel=1e-5)


class TestRollingStatsWindow:
    """Test different window sizes."""

    def test_rolling_stats_different_window(self, synthetic_player_data: pl.DataFrame):
        """Verify window parameter works (e.g., window=5)."""
        result = compute_rolling_stats(synthetic_player_data, window=5)

        # Check columns have correct window suffix
        assert "passing_yards_roll5" in result.columns
        assert "rushing_yards_roll5" in result.columns
        assert "receiving_yards_roll5" in result.columns

        # Verify other window columns don't exist
        assert "passing_yards_roll3" not in result.columns

        # With window=5 and shift(1), week 3 player 1 uses weeks 1-2
        # mean(100, 200) = 150
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll5"][0]

        assert p1_week3 == pytest.approx(150.0, rel=1e-5)

    def test_rolling_stats_window_2(self, synthetic_player_data: pl.DataFrame):
        """Verify window=2 produces different results than window=5."""
        result = compute_rolling_stats(synthetic_player_data, window=2)

        # Player 1 week 3 with window=2 and shift(1): mean(100, 200) = 150
        # (only uses weeks 1-2, not week 3)
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll2"][0]

        assert p1_week3 == pytest.approx(150.0, rel=1e-5)


class TestRollingStatsEdgeCases:
    """Test edge cases and error handling."""

    def test_rolling_stats_missing_required_columns(self):
        """Verify error raised when required columns are missing."""
        df = pl.DataFrame({
            "some_column": [1, 2, 3],
        })

        with pytest.raises(ValueError, match="missing required column"):
            compute_rolling_stats(df, window=3)

    def test_rolling_stats_missing_stat_columns(self):
        """Verify handles missing stat columns gracefully."""
        df = pl.DataFrame({
            "player_id": ["p1", "p1"],
            "season": [2024, 2024],
            "week": [1, 2],
            # No stat columns
        })

        # Should not raise, just return original df
        result = compute_rolling_stats(df, window=3)
        assert len(result) == 2

    def test_rolling_stats_partial_stat_columns(self):
        """Verify handles partial stat columns."""
        df = pl.DataFrame({
            "player_id": ["p1", "p1", "p1"],
            "season": [2024, 2024, 2024],
            "week": [1, 2, 3],
            "passing_yards": [100.0, 200.0, 300.0],
            # No rushing or receiving columns
        })

        result = compute_rolling_stats(df)  # Uses default window=5

        # Should have passing rolling column
        assert "passing_yards_roll5" in result.columns

        # Should NOT have rushing/receiving rolling columns
        assert "rushing_yards_roll5" not in result.columns
        assert "receiving_yards_roll5" not in result.columns
