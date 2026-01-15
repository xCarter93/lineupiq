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
        result = compute_rolling_stats(synthetic_player_data, window=3)

        # Check all expected rolling columns exist
        expected_columns = [
            "passing_yards_roll3",
            "passing_tds_roll3",
            "interceptions_roll3",
            "rushing_yards_roll3",
            "rushing_tds_roll3",
            "carries_roll3",
            "receiving_yards_roll3",
            "receiving_tds_roll3",
            "receptions_roll3",
        ]

        for col in expected_columns:
            assert col in result.columns, f"Missing expected column: {col}"

    def test_rolling_stats_preserves_original_columns(
        self, synthetic_player_data: pl.DataFrame
    ):
        """Verify original columns are preserved."""
        result = compute_rolling_stats(synthetic_player_data, window=3)

        for col in synthetic_player_data.columns:
            assert col in result.columns, f"Original column {col} was lost"


class TestRollingStatsCalculation:
    """Test correctness of rolling calculations."""

    def test_rolling_stats_calculation(self, synthetic_player_data: pl.DataFrame):
        """Verify rolling math is correct.

        Player 1 passing_yards: [100, 200, 300]
        - Week 1 rolling avg: 100 (only 1 period)
        - Week 2 rolling avg: 150 (mean of 100, 200)
        - Week 3 rolling avg: 200 (mean of 100, 200, 300)
        """
        result = compute_rolling_stats(synthetic_player_data, window=3)

        # Filter to player 1 and sort by week
        p1_result = result.filter(pl.col("player_id") == "p1").sort("week")
        passing_roll = p1_result["passing_yards_roll3"].to_list()

        # Week 1: only 1 period, avg = 100
        assert passing_roll[0] == pytest.approx(100.0, rel=1e-5)

        # Week 2: mean(100, 200) = 150
        assert passing_roll[1] == pytest.approx(150.0, rel=1e-5)

        # Week 3: mean(100, 200, 300) = 200
        assert passing_roll[2] == pytest.approx(200.0, rel=1e-5)


class TestRollingStatsPerPlayer:
    """Test that rolling is computed per player, not globally."""

    def test_rolling_stats_per_player(self, synthetic_player_data: pl.DataFrame):
        """Verify each player's rolling only uses their own history.

        Player 1 passing_yards: [100, 200, 300] -> week 3 avg = 200
        Player 2 passing_yards: [50, 100, 150] -> week 3 avg = 100

        If rolling was global, both players would have the same rolling avg.
        """
        result = compute_rolling_stats(synthetic_player_data, window=3)

        # Get week 3 rolling for both players
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll3"][0]

        p2_week3 = result.filter(
            (pl.col("player_id") == "p2") & (pl.col("week") == 3)
        )["passing_yards_roll3"][0]

        # Player 1: mean(100, 200, 300) = 200
        assert p1_week3 == pytest.approx(200.0, rel=1e-5)

        # Player 2: mean(50, 100, 150) = 100
        assert p2_week3 == pytest.approx(100.0, rel=1e-5)

        # Verify they are different (proves per-player computation)
        assert p1_week3 != p2_week3


class TestRollingStatsMinPeriods:
    """Test min_periods handling for early season."""

    def test_rolling_stats_min_periods(self, synthetic_player_data: pl.DataFrame):
        """Verify min_periods=1 works for early season.

        Week 1 should have rolling avg equal to week 1 value (only 1 period available).
        """
        result = compute_rolling_stats(synthetic_player_data, window=3)

        # Player 1 week 1: only has 1 game, rolling avg = that game's value
        p1_week1 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 1)
        )["passing_yards_roll3"][0]

        # Original value is 100, rolling should be 100
        assert p1_week1 == pytest.approx(100.0, rel=1e-5)


class TestRollingStatsWindow:
    """Test different window sizes."""

    def test_rolling_stats_different_window(self, synthetic_player_data: pl.DataFrame):
        """Verify window parameter works (e.g., window=5)."""
        result = compute_rolling_stats(synthetic_player_data, window=5)

        # Check columns have correct window suffix
        assert "passing_yards_roll5" in result.columns
        assert "rushing_yards_roll5" in result.columns
        assert "receiving_yards_roll5" in result.columns

        # Verify window=3 columns don't exist
        assert "passing_yards_roll3" not in result.columns

        # With window=5, week 3 player 1 should still be mean(100, 200, 300) = 200
        # because min_periods=1 uses whatever data is available
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll5"][0]

        assert p1_week3 == pytest.approx(200.0, rel=1e-5)

    def test_rolling_stats_window_2(self, synthetic_player_data: pl.DataFrame):
        """Verify window=2 produces different results than window=3."""
        result = compute_rolling_stats(synthetic_player_data, window=2)

        # Player 1 week 3 with window=2: mean(200, 300) = 250
        p1_week3 = result.filter(
            (pl.col("player_id") == "p1") & (pl.col("week") == 3)
        )["passing_yards_roll2"][0]

        assert p1_week3 == pytest.approx(250.0, rel=1e-5)


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

        result = compute_rolling_stats(df, window=3)

        # Should have passing rolling column
        assert "passing_yards_roll3" in result.columns

        # Should NOT have rushing/receiving rolling columns
        assert "rushing_yards_roll3" not in result.columns
        assert "receiving_yards_roll3" not in result.columns
