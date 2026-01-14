"""
Tests for data fetcher functions.

Note: These are integration tests that hit the network to fetch real NFL data.
Mark as slow/integration if adding to CI.
"""

import polars as pl
import pytest

from lineupiq.data import (
    SKILL_POSITIONS,
    fetch_player_stats,
    fetch_schedules,
    fetch_snap_counts,
    filter_skill_positions,
)


class TestFetchers:
    """Test data fetcher functions."""

    def test_fetch_player_stats_returns_polars(self) -> None:
        """Player stats returns Polars DataFrame."""
        df = fetch_player_stats([2024])
        assert isinstance(df, pl.DataFrame)

    def test_fetch_player_stats_has_expected_columns(self) -> None:
        """Player stats has key fantasy columns."""
        df = fetch_player_stats([2024])
        required = {"player_id", "passing_yards", "rushing_yards", "receiving_yards"}
        assert required.issubset(set(df.columns))

    def test_fetch_player_stats_has_114_columns(self) -> None:
        """Player stats has expected column count (114)."""
        df = fetch_player_stats([2024])
        assert df.shape[1] == 114

    def test_fetch_schedules_returns_polars(self) -> None:
        """Schedules returns Polars DataFrame."""
        df = fetch_schedules([2024])
        assert isinstance(df, pl.DataFrame)

    def test_fetch_schedules_has_weather_columns(self) -> None:
        """Schedules includes weather data."""
        df = fetch_schedules([2024])
        assert {"temp", "wind", "roof"}.issubset(set(df.columns))

    def test_fetch_snap_counts_returns_polars(self) -> None:
        """Snap counts returns Polars DataFrame."""
        df = fetch_snap_counts([2024])
        assert isinstance(df, pl.DataFrame)

    def test_fetch_snap_counts_has_snap_columns(self) -> None:
        """Snap counts includes snap participation columns."""
        df = fetch_snap_counts([2024])
        # Check for key snap columns
        assert "offense_snaps" in df.columns or "snap_count" in df.columns


class TestFilterSkillPositions:
    """Test position filtering utility."""

    def test_filter_skill_positions_returns_only_skill(self) -> None:
        """Skill filter returns only QB/RB/WR/TE."""
        df = fetch_player_stats([2024])
        filtered = filter_skill_positions(df)
        positions = set(filtered["position"].unique().to_list())
        assert positions.issubset(SKILL_POSITIONS)

    def test_filter_skill_positions_reduces_rows(self) -> None:
        """Skill filter reduces row count (excludes non-skill positions)."""
        df = fetch_player_stats([2024])
        filtered = filter_skill_positions(df)
        assert filtered.shape[0] < df.shape[0]

    def test_filter_skill_positions_preserves_columns(self) -> None:
        """Skill filter preserves all columns."""
        df = fetch_player_stats([2024])
        filtered = filter_skill_positions(df)
        assert df.columns == filtered.columns

    def test_filter_skill_positions_requires_position_column(self) -> None:
        """Skill filter raises if position column missing."""
        df = pl.DataFrame({"name": ["Player A"], "yards": [100]})
        with pytest.raises(ValueError, match="position"):
            filter_skill_positions(df)


class TestSkillPositions:
    """Test SKILL_POSITIONS constant."""

    def test_skill_positions_is_frozenset(self) -> None:
        """SKILL_POSITIONS is a frozenset."""
        assert isinstance(SKILL_POSITIONS, frozenset)

    def test_skill_positions_has_four_positions(self) -> None:
        """SKILL_POSITIONS contains exactly QB, RB, WR, TE."""
        assert SKILL_POSITIONS == {"QB", "RB", "WR", "TE"}
