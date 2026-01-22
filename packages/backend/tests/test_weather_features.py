"""
Tests for weather feature engineering module.

Validates:
- engineer_weather_features() creates expected columns
- Dome games have neutral weather values (72°F, 0 wind, no precip)
- Outdoor games with missing weather get mean-filled values
- Temperature/wind bins work correctly (freezing flag for 31°F, high_wind for 16mph)
- Precipitation detection (has_precip=1 when precip>0)
"""

import polars as pl
import pytest

from lineupiq.features.weather import engineer_weather_features, get_weather_feature_columns


def test_engineer_weather_features_creates_expected_columns():
    """Test that engineer_weather_features creates all 9 expected columns."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_GB_CHI"],
        "season": [2024],
        "week": [1],
        "gameday": ["2024-09-08"],
        "roof": ["outdoors"],
        "temp": [65.0],
        "wind": [10.0],
    })

    result = engineer_weather_features(schedule)

    # Check that all 9 new weather feature columns exist
    expected_columns = [
        "extreme_cold", "freezing", "extreme_heat",
        "temp_filled", "high_wind", "very_high_wind",
        "wind_filled", "has_precip", "precip_amount"
    ]

    for col in expected_columns:
        assert col in result.columns, f"Missing expected column: {col}"


def test_dome_games_have_neutral_weather_values():
    """Test that dome games get neutral weather values (72°F, 0 wind, 0 precip)."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_NO_ATL", "2024_01_DET_LAR"],
        "season": [2024, 2024],
        "week": [1, 1],
        "gameday": ["2024-09-08", "2024-09-08"],
        "roof": ["dome", "closed"],  # Both dome and closed count as indoor
        "temp": [None, None],
        "wind": [None, None],
    })

    result = engineer_weather_features(schedule)

    # Check neutral temperature values for dome games
    assert result["temp_filled"][0] == 72, "Dome game should have 72°F temp"
    assert result["temp_filled"][1] == 72, "Closed roof game should have 72°F temp"

    # Check neutral wind values for dome games
    assert result["wind_filled"][0] == 0, "Dome game should have 0 mph wind"
    assert result["wind_filled"][1] == 0, "Closed roof game should have 0 mph wind"

    # Check no precipitation for dome games
    assert result["precip_amount"][0] == 0, "Dome game should have 0 precip"
    assert result["precip_amount"][1] == 0, "Closed roof game should have 0 precip"
    assert result["has_precip"][0] == 0, "Dome game should have has_precip=0"
    assert result["has_precip"][1] == 0, "Closed roof game should have has_precip=0"


def test_outdoor_games_with_missing_weather_get_mean_filled():
    """Test that missing outdoor weather values get mean-filled from other outdoor games."""
    schedule = pl.DataFrame({
        "game_id": ["2024_01_GB_CHI", "2024_01_BUF_NYJ", "2024_01_SEA_DEN"],
        "season": [2024, 2024, 2024],
        "week": [1, 1, 1],
        "gameday": ["2024-09-08", "2024-09-08", "2024-09-08"],
        "roof": ["outdoors", "outdoors", "outdoors"],
        "temp": [65.0, 70.0, None],  # Third game missing temp
        "wind": [10.0, None, 8.0],   # Second game missing wind
    })

    result = engineer_weather_features(schedule)

    # Check that missing temp is filled with mean of outdoor games (65 + 70) / 2 = 67.5
    expected_temp_mean = (65.0 + 70.0) / 2
    assert result["temp_filled"][2] == pytest.approx(expected_temp_mean, abs=0.1), \
        f"Missing outdoor temp should be filled with mean {expected_temp_mean}"

    # Check that missing wind is filled with mean of outdoor games (10 + 8) / 2 = 9.0
    expected_wind_mean = (10.0 + 8.0) / 2
    assert result["wind_filled"][1] == pytest.approx(expected_wind_mean, abs=0.1), \
        f"Missing outdoor wind should be filled with mean {expected_wind_mean}"


def test_temperature_bins_work_correctly():
    """Test that temperature bins correctly identify extreme cold, freezing, and extreme heat."""
    schedule = pl.DataFrame({
        "game_id": ["game1", "game2", "game3", "game4", "game5"],
        "roof": ["outdoors", "outdoors", "outdoors", "outdoors", "outdoors"],
        "temp": [20.0, 31.0, 50.0, 86.0, 100.0],
        "wind": [0.0, 0.0, 0.0, 0.0, 0.0],
    })

    result = engineer_weather_features(schedule)

    # Test extreme_cold (<25°F)
    assert result["extreme_cold"][0] == 1, "20°F should be extreme_cold"
    assert result["extreme_cold"][1] == 0, "31°F should not be extreme_cold"

    # Test freezing (<32°F)
    assert result["freezing"][0] == 1, "20°F should be freezing"
    assert result["freezing"][1] == 1, "31°F should be freezing"
    assert result["freezing"][2] == 0, "50°F should not be freezing"

    # Test extreme_heat (>85°F)
    assert result["extreme_heat"][2] == 0, "50°F should not be extreme_heat"
    assert result["extreme_heat"][3] == 1, "86°F should be extreme_heat"
    assert result["extreme_heat"][4] == 1, "100°F should be extreme_heat"


def test_wind_thresholds_work_correctly():
    """Test that wind thresholds correctly identify high_wind and very_high_wind."""
    schedule = pl.DataFrame({
        "game_id": ["game1", "game2", "game3", "game4", "game5"],
        "roof": ["outdoors", "outdoors", "outdoors", "outdoors", "outdoors"],
        "temp": [50.0, 50.0, 50.0, 50.0, 50.0],
        "wind": [5.0, 14.0, 16.0, 20.0, 25.0],
    })

    result = engineer_weather_features(schedule)

    # Test high_wind (>=15mph)
    assert result["high_wind"][0] == 0, "5mph should not be high_wind"
    assert result["high_wind"][1] == 0, "14mph should not be high_wind"
    assert result["high_wind"][2] == 1, "16mph should be high_wind"
    assert result["high_wind"][3] == 1, "20mph should be high_wind"

    # Test very_high_wind (>=20mph)
    assert result["very_high_wind"][2] == 0, "16mph should not be very_high_wind"
    assert result["very_high_wind"][3] == 1, "20mph should be very_high_wind"
    assert result["very_high_wind"][4] == 1, "25mph should be very_high_wind"


def test_precipitation_detection():
    """Test that precipitation is correctly detected (has_precip=1 when precip>0)."""
    # Test with precipitation data
    schedule_with_precip = pl.DataFrame({
        "game_id": ["game1", "game2", "game3"],
        "roof": ["outdoors", "outdoors", "dome"],
        "temp": [50.0, 50.0, None],
        "wind": [10.0, 10.0, None],
        "precip": [0.0, 0.5, None],  # No precip, light rain, dome
    })

    result = engineer_weather_features(schedule_with_precip)

    # Test has_precip flag
    assert result["has_precip"][0] == 0, "No precipitation should have has_precip=0"
    assert result["has_precip"][1] == 1, "Precipitation > 0 should have has_precip=1"
    assert result["has_precip"][2] == 0, "Dome game should have has_precip=0"

    # Test precip_amount values
    assert result["precip_amount"][0] == 0.0, "No precip should have amount=0"
    assert result["precip_amount"][1] == 0.5, "Precip should preserve amount"
    assert result["precip_amount"][2] == 0.0, "Dome should have amount=0"


def test_precipitation_with_missing_precip_column():
    """Test that missing precip column is handled gracefully (sets all to 0)."""
    schedule_no_precip = pl.DataFrame({
        "game_id": ["game1", "game2"],
        "roof": ["outdoors", "dome"],
        "temp": [50.0, None],
        "wind": [10.0, None],
        # No precip column
    })

    result = engineer_weather_features(schedule_no_precip)

    # Should create precip_amount and has_precip columns with 0 values
    assert "precip_amount" in result.columns, "Should create precip_amount column"
    assert "has_precip" in result.columns, "Should create has_precip column"
    assert result["precip_amount"][0] == 0.0, "Missing precip should default to 0"
    assert result["has_precip"][0] == 0, "Missing precip should have has_precip=0"


def test_get_weather_feature_columns():
    """Test that get_weather_feature_columns returns 10 expected features."""
    columns = get_weather_feature_columns()

    assert len(columns) == 10, "Should return 10 weather feature columns"

    # Check new detailed features (Phase 20)
    expected_new_features = [
        "extreme_cold", "freezing", "extreme_heat",
        "high_wind", "very_high_wind",
        "has_precip", "precip_amount"
    ]
    for feature in expected_new_features:
        assert feature in columns, f"Missing new weather feature: {feature}"

    # Check existing features (Phase 1-19)
    expected_existing_features = ["temp_normalized", "wind_normalized", "is_dome"]
    for feature in expected_existing_features:
        assert feature in columns, f"Missing existing weather feature: {feature}"


def test_mixed_dome_and_outdoor_games():
    """Test that mixed dome/outdoor games are handled correctly."""
    schedule = pl.DataFrame({
        "game_id": ["outdoor1", "dome1", "outdoor2", "dome2"],
        "roof": ["outdoors", "dome", "outdoors", "closed"],
        "temp": [28.0, None, None, None],  # Only first outdoor has temp
        "wind": [18.0, None, 5.0, None],   # Two outdoor games have wind
    })

    result = engineer_weather_features(schedule)

    # Outdoor game 1: actual values
    assert result["temp_filled"][0] == 28.0, "Outdoor game should keep actual temp"
    assert result["wind_filled"][0] == 18.0, "Outdoor game should keep actual wind"
    assert result["freezing"][0] == 1, "28°F should be freezing"
    assert result["high_wind"][0] == 1, "18mph should be high_wind"

    # Dome game 1: neutral values
    assert result["temp_filled"][1] == 72, "Dome should have 72°F"
    assert result["wind_filled"][1] == 0, "Dome should have 0 wind"
    assert result["freezing"][1] == 0, "72°F should not be freezing"
    assert result["high_wind"][1] == 0, "0 wind should not be high_wind"

    # Outdoor game 2: mean-filled temp from outdoor1
    assert result["temp_filled"][2] == 28.0, "Missing outdoor temp filled with mean (only one outdoor)"
    assert result["wind_filled"][2] == 5.0, "Outdoor game should keep actual wind"

    # Dome game 2: neutral values
    assert result["temp_filled"][3] == 72, "Closed roof should have 72°F"
    assert result["wind_filled"][3] == 0, "Closed roof should have 0 wind"
