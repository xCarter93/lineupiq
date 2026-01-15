"""Tests for data cleaning module."""

import polars as pl
import pytest

from lineupiq.data.cleaning import (
    clean_numeric_stats,
    clean_player_stats,
    clean_schedules,
    select_ml_columns,
    validate_player_stats,
)


class TestValidatePlayerStats:
    """Tests for validate_player_stats function."""

    def test_removes_null_player_id(self):
        """Rows with null player_id should be removed."""
        df = pl.DataFrame({
            "player_id": ["001", None, "003"],
            "position": ["QB", "RB", "WR"],
            "season": [2024, 2024, 2024],
            "week": [1, 2, 3],
        })
        result = validate_player_stats(df)
        assert len(result) == 2
        assert None not in result["player_id"].to_list()

    def test_removes_invalid_position(self):
        """Rows with non-skill positions should be removed."""
        df = pl.DataFrame({
            "player_id": ["001", "002", "003", "004"],
            "position": ["QB", "K", "WR", None],
            "season": [2024, 2024, 2024, 2024],
            "week": [1, 2, 3, 4],
        })
        result = validate_player_stats(df)
        assert len(result) == 2
        assert set(result["position"].to_list()) == {"QB", "WR"}

    def test_removes_null_season(self):
        """Rows with null season should be removed."""
        df = pl.DataFrame({
            "player_id": ["001", "002"],
            "position": ["QB", "RB"],
            "season": [2024, None],
            "week": [1, 2],
        })
        result = validate_player_stats(df)
        assert len(result) == 1

    def test_removes_invalid_week(self):
        """Rows with null or <= 0 week should be removed."""
        df = pl.DataFrame({
            "player_id": ["001", "002", "003"],
            "position": ["QB", "RB", "WR"],
            "season": [2024, 2024, 2024],
            "week": [1, None, 0],
        })
        result = validate_player_stats(df)
        assert len(result) == 1
        assert result["week"][0] == 1


class TestCleanNumericStats:
    """Tests for clean_numeric_stats function."""

    def test_fills_nulls_with_zero(self):
        """Null stat values should be filled with 0."""
        df = pl.DataFrame({
            "passing_yards": [None, 300, None],
            "rushing_yards": [100, None, 50],
        })
        result = clean_numeric_stats(df)
        assert result["passing_yards"].to_list() == [0, 300, 0]
        assert result["rushing_yards"].to_list() == [100, 0, 50]

    def test_caps_yards_outliers(self):
        """Yard values > 600 should be capped to 600."""
        df = pl.DataFrame({
            "passing_yards": [300, 700, 550],
            "rushing_yards": [100, 650, 200],
        })
        result = clean_numeric_stats(df)
        assert result["passing_yards"].to_list() == [300, 600, 550]
        assert result["rushing_yards"].to_list() == [100, 600, 200]

    def test_caps_tds_outliers(self):
        """TD values > 8 should be capped to 8."""
        df = pl.DataFrame({
            "passing_tds": [3, 10, 5],
            "rushing_tds": [2, 9, 1],
        })
        result = clean_numeric_stats(df)
        assert result["passing_tds"].to_list() == [3, 8, 5]
        assert result["rushing_tds"].to_list() == [2, 8, 1]

    def test_handles_missing_columns(self):
        """Should work when some stat columns are missing."""
        df = pl.DataFrame({
            "passing_yards": [300],
            "some_other_col": ["value"],
        })
        result = clean_numeric_stats(df)
        assert "passing_yards" in result.columns
        assert "some_other_col" in result.columns


class TestSelectMlColumns:
    """Tests for select_ml_columns function."""

    def test_filters_to_ml_columns_only(self):
        """Should only include ML-relevant columns."""
        df = pl.DataFrame({
            "player_id": ["001"],
            "position": ["QB"],
            "season": [2024],
            "week": [1],
            "passing_yards": [300],
            "random_column": ["should_be_removed"],
            "another_extra": [123],
        })
        result = select_ml_columns(df)
        assert "player_id" in result.columns
        assert "passing_yards" in result.columns
        assert "random_column" not in result.columns
        assert "another_extra" not in result.columns

    def test_handles_missing_ml_columns(self):
        """Should work when some ML columns are missing from input."""
        df = pl.DataFrame({
            "player_id": ["001"],
            "position": ["QB"],
        })
        result = select_ml_columns(df)
        assert "player_id" in result.columns
        assert "position" in result.columns
        # Should not fail even though passing_yards etc are missing


class TestCleanPlayerStats:
    """Tests for clean_player_stats orchestrator function."""

    def test_full_pipeline(self):
        """Full cleaning pipeline should validate, clean, and select columns."""
        df = pl.DataFrame({
            "player_id": ["001", None, "003", "004"],
            "position": ["QB", "RB", "K", "WR"],
            "season": [2024, 2024, 2024, 2024],
            "week": [1, 2, 3, 4],
            "passing_yards": [None, 300, 200, 700],
            "passing_tds": [2, None, 1, 10],
            "extra_column": ["a", "b", "c", "d"],
        })
        result = clean_player_stats(df)

        # Should remove invalid rows (null player_id, K position)
        assert len(result) == 2

        # Should fill nulls
        assert 0 in result["passing_yards"].to_list() or None not in result["passing_yards"].to_list()

        # Should cap outliers (700 -> 600)
        assert 700 not in result["passing_yards"].to_list()

        # Should remove extra columns
        assert "extra_column" not in result.columns


class TestCleanSchedules:
    """Tests for clean_schedules function."""

    def test_removes_null_game_id(self):
        """Rows with null game_id should be removed."""
        df = pl.DataFrame({
            "game_id": ["2024_01_SEA_DEN", None],
            "season": [2024, 2024],
            "week": [1, 2],
            "roof": ["dome", "outdoors"],
        })
        result = clean_schedules(df)
        assert len(result) == 1
        assert result["game_id"][0] == "2024_01_SEA_DEN"

    def test_adds_is_dome_for_dome_roof(self):
        """dome and closed roof values should produce is_dome=True."""
        df = pl.DataFrame({
            "game_id": ["g1", "g2", "g3"],
            "season": [2024, 2024, 2024],
            "week": [1, 2, 3],
            "roof": ["dome", "closed", "outdoors"],
        })
        result = clean_schedules(df)
        assert "is_dome" in result.columns
        assert result["is_dome"].to_list() == [True, True, False]

    def test_fills_temp_wind_for_dome(self):
        """Null temp/wind should be filled for dome games."""
        df = pl.DataFrame({
            "game_id": ["g1", "g2"],
            "season": [2024, 2024],
            "week": [1, 2],
            "roof": ["dome", "outdoors"],
            "temp": [None, None],
            "wind": [None, None],
        })
        result = clean_schedules(df)
        # Dome game should have defaults (65, 5)
        dome_row = result.filter(pl.col("is_dome") == True)
        assert dome_row["temp"][0] == 65
        assert dome_row["wind"][0] == 5
        # Outdoor game should still have None
        outdoor_row = result.filter(pl.col("is_dome") == False)
        assert outdoor_row["temp"][0] is None
        assert outdoor_row["wind"][0] is None

    def test_drops_roof_column(self):
        """Original roof column should be replaced with is_dome."""
        df = pl.DataFrame({
            "game_id": ["g1"],
            "season": [2024],
            "week": [1],
            "roof": ["dome"],
        })
        result = clean_schedules(df)
        assert "roof" not in result.columns
        assert "is_dome" in result.columns
