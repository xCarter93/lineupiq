"""
Tests for injury feature engineering.

Validates injury severity encoding, on_injury_report flag, and correct
handling of multiple reports per player-week.
"""

import polars as pl
import pytest

from lineupiq.features.injury import engineer_injury_features


def test_injury_severity_encoding():
    """Test injury severity values for each designation."""
    # Create player stats
    player_stats = pl.DataFrame({
        "gsis_id": ["P1", "P2", "P3", "P4", "P5", "P6"],
        "season": [2024] * 6,
        "week": [1] * 6,
        "passing_yards": [250, 180, 0, 220, 300, 200],
    })

    # Create injury data with all designation types
    injuries = pl.DataFrame({
        "gsis_id": ["P1", "P2", "P3", "P4", "P5"],
        "season": [2024] * 5,
        "week": [1] * 5,
        "report_status": ["Out", "Doubtful", "Questionable", "Probable", None],
        "date_modified": ["2024-09-15"] * 5,
    })

    result = engineer_injury_features(player_stats, injuries)

    # Verify severity encoding
    assert result.filter(pl.col("gsis_id") == "P1")["injury_severity"][0] == 1.0  # Out
    assert (
        result.filter(pl.col("gsis_id") == "P2")["injury_severity"][0] == 0.75
    )  # Doubtful
    assert (
        result.filter(pl.col("gsis_id") == "P3")["injury_severity"][0] == 0.5
    )  # Questionable
    assert (
        result.filter(pl.col("gsis_id") == "P4")["injury_severity"][0] == 0.25
    )  # Probable
    assert (
        result.filter(pl.col("gsis_id") == "P5")["injury_severity"][0] == 0.0
    )  # None status
    assert (
        result.filter(pl.col("gsis_id") == "P6")["injury_severity"][0] == 0.0
    )  # Not in injury data


def test_on_injury_report_flag():
    """Test on_injury_report flag is 1 when status exists, 0 when null."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1", "P2", "P3"],
        "season": [2024] * 3,
        "week": [1] * 3,
        "rushing_yards": [85, 120, 95],
    })

    injuries = pl.DataFrame({
        "gsis_id": ["P1", "P2"],
        "season": [2024] * 2,
        "week": [1] * 2,
        "report_status": ["Questionable", "Out"],
        "date_modified": ["2024-09-15"] * 2,
    })

    result = engineer_injury_features(player_stats, injuries)

    # P1 and P2 have injury reports
    assert result.filter(pl.col("gsis_id") == "P1")["on_injury_report"][0] == 1
    assert result.filter(pl.col("gsis_id") == "P2")["on_injury_report"][0] == 1

    # P3 not on injury report
    assert result.filter(pl.col("gsis_id") == "P3")["on_injury_report"][0] == 0


def test_join_on_player_week():
    """Test join correctly matches injuries to player-week records."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1", "P1", "P2", "P2"],
        "season": [2024, 2024, 2024, 2024],
        "week": [1, 2, 1, 2],
        "receiving_yards": [80, 0, 95, 110],
    })

    injuries = pl.DataFrame({
        "gsis_id": ["P1", "P2"],
        "season": [2024, 2024],
        "week": [2, 1],  # P1 injured week 2, P2 injured week 1
        "report_status": ["Out", "Questionable"],
        "date_modified": ["2024-09-18", "2024-09-11"],
    })

    result = engineer_injury_features(player_stats, injuries)

    # P1 week 1: no injury
    assert (
        result.filter((pl.col("gsis_id") == "P1") & (pl.col("week") == 1))[
            "injury_severity"
        ][0]
        == 0.0
    )
    # P1 week 2: Out (1.0)
    assert (
        result.filter((pl.col("gsis_id") == "P1") & (pl.col("week") == 2))[
            "injury_severity"
        ][0]
        == 1.0
    )
    # P2 week 1: Questionable (0.5)
    assert (
        result.filter((pl.col("gsis_id") == "P2") & (pl.col("week") == 1))[
            "injury_severity"
        ][0]
        == 0.5
    )
    # P2 week 2: no injury
    assert (
        result.filter((pl.col("gsis_id") == "P2") & (pl.col("week") == 2))[
            "injury_severity"
        ][0]
        == 0.0
    )


def test_multiple_reports_per_week():
    """Test multiple reports per week take most recent date_modified."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1"],
        "season": [2024],
        "week": [1],
        "rushing_yards": [75],
    })

    # P1 has multiple injury updates during week 1
    injuries = pl.DataFrame({
        "gsis_id": ["P1", "P1", "P1"],
        "season": [2024, 2024, 2024],
        "week": [1, 1, 1],
        "report_status": ["Questionable", "Doubtful", "Out"],  # Worsening injury
        "date_modified": ["2024-09-13", "2024-09-14", "2024-09-15"],  # Most recent last
    })

    result = engineer_injury_features(player_stats, injuries)

    # Should use most recent status: "Out" (1.0)
    assert result["injury_severity"][0] == 1.0
    assert result["on_injury_report"][0] == 1


def test_missing_injury_data_filled_with_zeros():
    """Test missing injury data filled with zeros."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1", "P2", "P3"],
        "season": [2024] * 3,
        "week": [1] * 3,
        "passing_yards": [280, 310, 250],
    })

    # No injury data at all - need schema for empty DataFrame
    injuries = pl.DataFrame(
        schema={
            "gsis_id": pl.Utf8,
            "season": pl.Int64,
            "week": pl.Int64,
            "report_status": pl.Utf8,
            "date_modified": pl.Utf8,
        }
    )

    result = engineer_injury_features(player_stats, injuries)

    # All players should have 0.0 severity and 0 flag
    assert result["injury_severity"].to_list() == [0.0, 0.0, 0.0]
    assert result["on_injury_report"].to_list() == [0, 0, 0]


def test_injury_features_columns_added():
    """Test that injury_severity and on_injury_report columns are added."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1"],
        "season": [2024],
        "week": [1],
        "receptions": [8],
    })

    injuries = pl.DataFrame({
        "gsis_id": ["P1"],
        "season": [2024],
        "week": [1],
        "report_status": ["Questionable"],
        "date_modified": ["2024-09-15"],
    })

    result = engineer_injury_features(player_stats, injuries)

    # Verify new columns exist
    assert "injury_severity" in result.columns
    assert "on_injury_report" in result.columns

    # Verify original columns preserved
    assert "gsis_id" in result.columns
    assert "season" in result.columns
    assert "week" in result.columns
    assert "receptions" in result.columns


def test_injury_features_without_date_modified():
    """Test injury feature engineering when date_modified is missing."""
    player_stats = pl.DataFrame({
        "gsis_id": ["P1", "P2"],
        "season": [2024] * 2,
        "week": [1] * 2,
        "rushing_yards": [85, 120],
    })

    # Injury data without date_modified column
    injuries = pl.DataFrame({
        "gsis_id": ["P1", "P2"],
        "season": [2024] * 2,
        "week": [1] * 2,
        "report_status": ["Out", "Questionable"],
    })

    result = engineer_injury_features(player_stats, injuries)

    # Should still create features correctly
    assert result.filter(pl.col("gsis_id") == "P1")["injury_severity"][0] == 1.0
    assert result.filter(pl.col("gsis_id") == "P2")["injury_severity"][0] == 0.5
    assert result.filter(pl.col("gsis_id") == "P1")["on_injury_report"][0] == 1
    assert result.filter(pl.col("gsis_id") == "P2")["on_injury_report"][0] == 1
