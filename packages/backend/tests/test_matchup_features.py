"""
Tests for matchup feature engineering.

Validates Vegas line joins, home/away flags, divisional game detection,
and graceful handling of missing odds data.
"""

import polars as pl
import pytest

from lineupiq.features.matchup import engineer_matchup_features


def test_vegas_line_join() -> None:
    """Test that Vegas lines are correctly joined to schedule."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_KC_BUF", "2024_01_SF_DAL"],
        "season": [2024, 2024],
        "week": [1, 1],
        "home_team": ["KC", "SF"],
        "away_team": ["BUF", "DAL"],
    })

    odds = pl.DataFrame({
        "game_id": ["2024_01_KC_BUF", "2024_01_SF_DAL"],
        "home_spread": [-3.5, -7.0],
        "total_points": [52.5, 48.0],
    })

    result = engineer_matchup_features(schedule, odds)

    # Check columns exist
    assert "home_spread" in result.columns
    assert "total_points" in result.columns

    # Check values joined correctly
    assert result.filter(pl.col("game_id") == "2024_01_KC_BUF")["home_spread"][0] == -3.5
    assert result.filter(pl.col("game_id") == "2024_01_KC_BUF")["total_points"][0] == 52.5
    assert result.filter(pl.col("game_id") == "2024_01_SF_DAL")["home_spread"][0] == -7.0
    assert result.filter(pl.col("game_id") == "2024_01_SF_DAL")["total_points"][0] == 48.0


def test_home_favored_flag() -> None:
    """Test that home_favored flag is set correctly based on spread sign."""
    schedule = pl.DataFrame({
        "game_id": ["game1", "game2", "game3"],
        "season": [2024, 2024, 2024],
        "week": [1, 1, 1],
        "home_team": ["KC", "BUF", "MIA"],
        "away_team": ["BUF", "NYJ", "NE"],
    })

    odds = pl.DataFrame({
        "game_id": ["game1", "game2", "game3"],
        "home_spread": [-3.5, 2.5, 0.0],  # Home favored, away favored, pick'em
        "total_points": [50.0, 45.0, 42.0],
    })

    result = engineer_matchup_features(schedule, odds)

    # home_spread < 0 means home favored
    assert result.filter(pl.col("game_id") == "game1")["home_favored"][0] == 1
    assert result.filter(pl.col("game_id") == "game2")["home_favored"][0] == 0
    assert result.filter(pl.col("game_id") == "game3")["home_favored"][0] == 0  # Pick'em = not favored


def test_vegas_strength_diff() -> None:
    """Test that vegas_strength_diff is absolute value of spread."""
    schedule = pl.DataFrame({
        "game_id": ["game1", "game2"],
        "season": [2024, 2024],
        "week": [1, 1],
        "home_team": ["KC", "BUF"],
        "away_team": ["BUF", "NYJ"],
    })

    odds = pl.DataFrame({
        "game_id": ["game1", "game2"],
        "home_spread": [-7.0, 3.5],  # Different signs
        "total_points": [50.0, 45.0],
    })

    result = engineer_matchup_features(schedule, odds)

    # vegas_strength_diff should be abs(home_spread)
    assert result.filter(pl.col("game_id") == "game1")["vegas_strength_diff"][0] == 7.0
    assert result.filter(pl.col("game_id") == "game2")["vegas_strength_diff"][0] == 3.5


def test_missing_odds_handling() -> None:
    """Test that games without odds get neutral fill values."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_KC_BUF", "2018_01_NE_KC"],  # 2018 pre-dates odds API
        "season": [2024, 2018],
        "week": [1, 1],
        "home_team": ["KC", "KC"],
        "away_team": ["BUF", "NE"],
    })

    odds = pl.DataFrame({
        "game_id": ["2024_01_KC_BUF"],  # Only 2024 game has odds
        "home_spread": [-3.5],
        "total_points": [52.5],
    })

    result = engineer_matchup_features(schedule, odds)

    # 2024 game should have actual odds
    row_2024 = result.filter(pl.col("season") == 2024)
    assert row_2024["home_spread"][0] == -3.5
    assert row_2024["total_points"][0] == 52.5

    # 2018 game should have neutral fills
    row_2018 = result.filter(pl.col("season") == 2018)
    assert row_2018["home_spread"][0] == 0.0  # Neutral
    assert row_2018["total_points"][0] == 45.0  # NFL average
    assert row_2018["vegas_strength_diff"][0] == 0.0
    assert row_2018["home_favored"][0] == 0


def test_no_odds_provided() -> None:
    """Test graceful degradation when no odds data provided."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_KC_BUF"],
        "season": [2024],
        "week": [1],
        "home_team": ["KC"],
        "away_team": ["BUF"],
    })

    # Pass None for odds
    result = engineer_matchup_features(schedule, odds_df=None)

    # Should still have divisional flag
    assert "is_divisional" in result.columns

    # Should NOT have Vegas features
    assert "home_spread" not in result.columns
    assert "total_points" not in result.columns
    assert "vegas_strength_diff" not in result.columns
    assert "home_favored" not in result.columns


def test_divisional_game_flag() -> None:
    """Test that divisional games are correctly identified."""
    # AFC West: KC, LAC, LV, DEN
    # NFC East: DAL, PHI, NYG, WAS
    schedule = pl.DataFrame({
        "game_id": ["game1", "game2", "game3"],
        "season": [2024, 2024, 2024],
        "week": [1, 1, 1],
        "home_team": ["KC", "DAL", "KC"],
        "away_team": ["LAC", "PHI", "DAL"],  # Div game, Div game, Non-div game
    })

    result = engineer_matchup_features(schedule, odds_df=None)

    # KC vs LAC (both AFC West) = divisional
    assert result.filter(pl.col("game_id") == "game1")["is_divisional"][0] == 1

    # DAL vs PHI (both NFC East) = divisional
    assert result.filter(pl.col("game_id") == "game2")["is_divisional"][0] == 1

    # KC (AFC West) vs DAL (NFC East) = non-divisional
    assert result.filter(pl.col("game_id") == "game3")["is_divisional"][0] == 0


def test_all_features_together() -> None:
    """Test that all features are created when odds provided."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_KC_LAC"],
        "season": [2024],
        "week": [1],
        "home_team": ["KC"],
        "away_team": ["LAC"],
    })

    odds = pl.DataFrame({
        "game_id": ["2024_01_KC_LAC"],
        "home_spread": [-5.5],
        "total_points": [49.0],
    })

    result = engineer_matchup_features(schedule, odds)

    # Should have all 5 features
    assert "home_spread" in result.columns
    assert "total_points" in result.columns
    assert "vegas_strength_diff" in result.columns
    assert "home_favored" in result.columns
    assert "is_divisional" in result.columns

    # Verify values
    assert result["home_spread"][0] == -5.5
    assert result["total_points"][0] == 49.0
    assert result["vegas_strength_diff"][0] == 5.5
    assert result["home_favored"][0] == 1
    assert result["is_divisional"][0] == 1  # KC vs LAC (both AFC West)
