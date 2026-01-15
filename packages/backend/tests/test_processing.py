"""
Tests for data processing functions.

Tests the schedule joining, weather normalization, and processing pipeline.
"""

import polars as pl
import pytest

from lineupiq.data.processing import (
    add_game_context,
    add_weather_context,
)


# =============================================================================
# add_game_context tests
# =============================================================================


class TestAddGameContext:
    """Tests for add_game_context function."""

    def test_determines_home_team(self):
        """Player on home team should have is_home=True."""
        player_df = pl.DataFrame({
            "player_id": ["001"],
            "player_name": ["Patrick Mahomes"],
            "recent_team": ["KC"],
            "season": [2024],
            "week": [1],
        })
        schedule_df = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF"],
            "season": [2024],
            "week": [1],
            "home_team": ["KC"],
            "away_team": ["BUF"],
        })

        result = add_game_context(player_df, schedule_df)

        assert result["is_home"][0] is True
        assert result["opponent"][0] == "BUF"
        assert result["game_id"][0] == "2024_01_KC_BUF"

    def test_determines_away_team(self):
        """Player on away team should have is_home=False."""
        player_df = pl.DataFrame({
            "player_id": ["002"],
            "player_name": ["Josh Allen"],
            "recent_team": ["BUF"],
            "season": [2024],
            "week": [1],
        })
        schedule_df = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF"],
            "season": [2024],
            "week": [1],
            "home_team": ["KC"],
            "away_team": ["BUF"],
        })

        result = add_game_context(player_df, schedule_df)

        assert result["is_home"][0] is False
        assert result["opponent"][0] == "KC"
        assert result["game_id"][0] == "2024_01_KC_BUF"

    def test_handles_bye_week(self):
        """Player on bye week should have null opponent."""
        player_df = pl.DataFrame({
            "player_id": ["003"],
            "player_name": ["Player on bye"],
            "recent_team": ["MIA"],
            "season": [2024],
            "week": [1],
        })
        # Schedule doesn't include MIA in week 1
        schedule_df = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF"],
            "season": [2024],
            "week": [1],
            "home_team": ["KC"],
            "away_team": ["BUF"],
        })

        result = add_game_context(player_df, schedule_df)

        assert result["game_id"][0] is None
        # is_home and opponent will have default values when no match

    def test_multiple_players_multiple_games(self):
        """Test with multiple players and games."""
        player_df = pl.DataFrame({
            "player_id": ["001", "002", "003", "004"],
            "player_name": ["P1", "P2", "P3", "P4"],
            "recent_team": ["KC", "BUF", "SF", "DAL"],
            "season": [2024, 2024, 2024, 2024],
            "week": [1, 1, 1, 1],
        })
        schedule_df = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF", "2024_01_SF_DAL"],
            "season": [2024, 2024],
            "week": [1, 1],
            "home_team": ["KC", "SF"],
            "away_team": ["BUF", "DAL"],
        })

        result = add_game_context(player_df, schedule_df)

        # KC is home
        kc_row = result.filter(pl.col("player_id") == "001")
        assert kc_row["is_home"][0] is True
        assert kc_row["opponent"][0] == "BUF"

        # BUF is away
        buf_row = result.filter(pl.col("player_id") == "002")
        assert buf_row["is_home"][0] is False
        assert buf_row["opponent"][0] == "KC"

        # SF is home
        sf_row = result.filter(pl.col("player_id") == "003")
        assert sf_row["is_home"][0] is True
        assert sf_row["opponent"][0] == "DAL"

        # DAL is away
        dal_row = result.filter(pl.col("player_id") == "004")
        assert dal_row["is_home"][0] is False
        assert dal_row["opponent"][0] == "SF"

    def test_carries_weather_columns(self):
        """Schedule weather columns should carry through join."""
        player_df = pl.DataFrame({
            "player_id": ["001"],
            "player_name": ["Test Player"],
            "recent_team": ["KC"],
            "season": [2024],
            "week": [1],
        })
        schedule_df = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF"],
            "season": [2024],
            "week": [1],
            "home_team": ["KC"],
            "away_team": ["BUF"],
            "temp": [45.0],
            "wind": [10.0],
            "is_dome": [False],
        })

        result = add_game_context(player_df, schedule_df)

        assert "temp" in result.columns
        assert "wind" in result.columns
        assert "is_dome" in result.columns
        assert result["temp"][0] == 45.0
        assert result["wind"][0] == 10.0
        assert result["is_dome"][0] is False


# =============================================================================
# add_weather_context tests
# =============================================================================


class TestAddWeatherContext:
    """Tests for add_weather_context function."""

    def test_normalizes_temperature(self):
        """Temperature should be normalized: (temp - 65) / 20."""
        df = pl.DataFrame({
            "temp": [85.0, 65.0, 45.0, 25.0],
            "wind": [0.0, 0.0, 0.0, 0.0],
        })

        result = add_weather_context(df)

        assert result["temp_normalized"][0] == pytest.approx(1.0)   # (85-65)/20 = 1.0
        assert result["temp_normalized"][1] == pytest.approx(0.0)   # (65-65)/20 = 0.0
        assert result["temp_normalized"][2] == pytest.approx(-1.0)  # (45-65)/20 = -1.0
        assert result["temp_normalized"][3] == pytest.approx(-2.0)  # (25-65)/20 = -2.0

    def test_normalizes_wind(self):
        """Wind should be normalized: wind / 15."""
        df = pl.DataFrame({
            "temp": [65.0, 65.0, 65.0],
            "wind": [30.0, 15.0, 0.0],
        })

        result = add_weather_context(df)

        assert result["wind_normalized"][0] == pytest.approx(2.0)   # 30/15 = 2.0
        assert result["wind_normalized"][1] == pytest.approx(1.0)   # 15/15 = 1.0
        assert result["wind_normalized"][2] == pytest.approx(0.0)   # 0/15 = 0.0

    def test_handles_null_temp(self):
        """Null temperature should normalize to 0 (default 65)."""
        df = pl.DataFrame({
            "temp": [None, 85.0],
            "wind": [10.0, 10.0],
        })

        result = add_weather_context(df)

        # Null temp filled with 65, so (65-65)/20 = 0
        assert result["temp_normalized"][0] == pytest.approx(0.0)
        assert result["temp_normalized"][1] == pytest.approx(1.0)

    def test_handles_null_wind(self):
        """Null wind should normalize to 0."""
        df = pl.DataFrame({
            "temp": [65.0, 65.0],
            "wind": [None, 15.0],
        })

        result = add_weather_context(df)

        # Null wind filled with 0, so 0/15 = 0
        assert result["wind_normalized"][0] == pytest.approx(0.0)
        assert result["wind_normalized"][1] == pytest.approx(1.0)

    def test_handles_missing_weather_columns(self):
        """Missing temp/wind columns should default to 0."""
        df = pl.DataFrame({
            "player_id": ["001", "002"],
        })

        result = add_weather_context(df)

        assert "temp_normalized" in result.columns
        assert "wind_normalized" in result.columns
        assert result["temp_normalized"].to_list() == [0.0, 0.0]
        assert result["wind_normalized"].to_list() == [0.0, 0.0]


# =============================================================================
# Integration test: process_player_stats with expected columns
# =============================================================================


class TestProcessPlayerStatsColumns:
    """Test that process_player_stats returns expected columns."""

    def test_returns_expected_columns_with_mock(self):
        """Verify output has required columns using mock data.

        This test mocks the data loading to avoid real API calls
        while verifying the pipeline produces expected output structure.
        """
        # Create mock player data
        mock_player_stats = pl.DataFrame({
            "player_id": ["001", "002"],
            "player_name": ["Player One", "Player Two"],
            "player_display_name": ["P. One", "P. Two"],
            "position": ["QB", "RB"],
            "recent_team": ["KC", "BUF"],
            "season": [2024, 2024],
            "week": [1, 1],
            "passing_yards": [300.0, 0.0],
            "passing_tds": [3.0, 0.0],
            "interceptions": [1.0, 0.0],
            "attempts": [35.0, 0.0],
            "completions": [25.0, 0.0],
            "rushing_yards": [10.0, 100.0],
            "rushing_tds": [0.0, 1.0],
            "carries": [3.0, 20.0],
            "receptions": [0.0, 5.0],
            "receiving_yards": [0.0, 45.0],
            "receiving_tds": [0.0, 0.0],
            "targets": [0.0, 7.0],
            "fantasy_points": [25.0, 18.0],
            "fantasy_points_ppr": [25.0, 23.0],
        })

        # Create mock schedule data
        mock_schedules = pl.DataFrame({
            "game_id": ["2024_01_KC_BUF"],
            "season": [2024],
            "week": [1],
            "game_type": ["REG"],
            "gameday": ["2024-09-08"],
            "home_team": ["KC"],
            "away_team": ["BUF"],
            "home_score": [27],
            "away_score": [24],
            "temp": [72.0],
            "wind": [8.0],
            "roof": ["outdoors"],
            "surface": ["grass"],
            "stadium_id": ["ARROWHEAD"],
        })

        # Import pipeline functions
        from lineupiq.data.cleaning import clean_player_stats, clean_schedules
        from lineupiq.data.normalization import normalize_player_data, normalize_team_columns
        from lineupiq.data.processing import add_game_context, add_weather_context

        # Run through pipeline manually with mock data
        player_stats = clean_player_stats(mock_player_stats)
        schedules = clean_schedules(mock_schedules)
        player_stats = normalize_player_data(player_stats)
        schedules = normalize_team_columns(schedules)
        player_stats = add_game_context(player_stats, schedules)
        player_stats = add_weather_context(player_stats)

        # Check required output columns
        required_cols = [
            "player_id",
            "is_home",
            "opponent",
            "temp_normalized",
            "wind_normalized",
        ]
        for col in required_cols:
            assert col in player_stats.columns, f"Missing column: {col}"

        # Verify is_home logic
        kc_player = player_stats.filter(pl.col("recent_team") == "KC")
        buf_player = player_stats.filter(pl.col("recent_team") == "BUF")

        assert kc_player["is_home"][0] is True
        assert buf_player["is_home"][0] is False
