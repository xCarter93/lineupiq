"""
Tests for normalization module.

Tests team abbreviation mapping, player ID standardization,
and position normalization functions.
"""

import polars as pl
import pytest

from lineupiq.data.normalization import (
    CURRENT_TEAMS,
    TEAM_MAPPING,
    normalize_player_data,
    normalize_position,
    normalize_team,
    normalize_team_columns,
    standardize_player_id,
)


class TestNormalizeTeam:
    """Tests for normalize_team function."""

    def test_normalize_team_handles_relocations(self):
        """Historical relocations map to current teams."""
        assert normalize_team("OAK") == "LV"  # Raiders moved 2020
        assert normalize_team("STL") == "LA"  # Rams moved 2016
        assert normalize_team("SD") == "LAC"  # Chargers moved 2017

    def test_normalize_team_preserves_current(self):
        """Current team abbreviations are unchanged."""
        assert normalize_team("KC") == "KC"
        assert normalize_team("BUF") == "BUF"
        assert normalize_team("SF") == "SF"
        assert normalize_team("DAL") == "DAL"

    def test_normalize_team_handles_pho_to_ari(self):
        """Phoenix Cardinals -> Arizona Cardinals."""
        assert normalize_team("PHO") == "ARI"


class TestCurrentTeams:
    """Tests for CURRENT_TEAMS constant."""

    def test_current_teams_has_32(self):
        """CURRENT_TEAMS contains exactly 32 teams."""
        assert len(CURRENT_TEAMS) == 32

    def test_current_teams_has_all_divisions(self):
        """CURRENT_TEAMS contains teams from all divisions."""
        # AFC East
        assert "BUF" in CURRENT_TEAMS
        assert "MIA" in CURRENT_TEAMS
        assert "NE" in CURRENT_TEAMS
        assert "NYJ" in CURRENT_TEAMS
        # NFC West
        assert "ARI" in CURRENT_TEAMS
        assert "LA" in CURRENT_TEAMS
        assert "SEA" in CURRENT_TEAMS
        assert "SF" in CURRENT_TEAMS

    def test_team_mapping_maps_to_current_teams(self):
        """All values in TEAM_MAPPING are in CURRENT_TEAMS."""
        for old_team, new_team in TEAM_MAPPING.items():
            assert new_team in CURRENT_TEAMS, f"{old_team} -> {new_team} not in CURRENT_TEAMS"


class TestNormalizeTeamColumns:
    """Tests for normalize_team_columns function."""

    def test_normalize_team_columns_applies(self):
        """Normalizes team columns in DataFrame."""
        df = pl.DataFrame({
            "recent_team": ["OAK", "KC", "STL"],
            "player_id": ["001", "002", "003"],
        })
        result = normalize_team_columns(df)
        assert result["recent_team"].to_list() == ["LV", "KC", "LA"]

    def test_normalize_team_columns_multiple(self):
        """Normalizes multiple team columns."""
        df = pl.DataFrame({
            "home_team": ["OAK", "SD"],
            "away_team": ["STL", "KC"],
        })
        result = normalize_team_columns(df)
        assert result["home_team"].to_list() == ["LV", "LAC"]
        assert result["away_team"].to_list() == ["LA", "KC"]

    def test_normalize_team_columns_no_team_columns(self):
        """Returns unchanged when no team columns exist."""
        df = pl.DataFrame({
            "player_id": ["001", "002"],
            "score": [10, 20],
        })
        result = normalize_team_columns(df)
        assert result.columns == ["player_id", "score"]


class TestStandardizePlayerId:
    """Tests for standardize_player_id function."""

    def test_standardize_player_id_strips_whitespace(self):
        """Strips leading/trailing whitespace from player_id."""
        df = pl.DataFrame({"player_id": [" ABC123 ", "  DEF456", "GHI789  "]})
        result = standardize_player_id(df)
        assert result["player_id"].to_list() == ["ABC123", "DEF456", "GHI789"]

    def test_standardize_player_id_creates_player_key(self):
        """Creates lowercase player_key column."""
        df = pl.DataFrame({"player_id": ["ABC123", "DEF456"]})
        result = standardize_player_id(df)
        assert "player_key" in result.columns
        assert result["player_key"].to_list() == ["abc123", "def456"]

    def test_standardize_player_id_no_player_id_column(self):
        """Returns unchanged when no player_id column."""
        df = pl.DataFrame({"name": ["Test", "Test2"]})
        result = standardize_player_id(df)
        assert "player_key" not in result.columns


class TestNormalizePosition:
    """Tests for normalize_position function."""

    def test_normalize_position_uppercase(self):
        """Converts lowercase positions to uppercase."""
        df = pl.DataFrame({"position": ["qb", "rb", "wr", "te"]})
        result = normalize_position(df)
        assert result["position"].to_list() == ["QB", "RB", "WR", "TE"]

    def test_normalize_position_fb_to_rb(self):
        """Converts FB (fullback) to RB."""
        df = pl.DataFrame({"position": ["FB", "fb", "Fb"]})
        result = normalize_position(df)
        assert result["position"].to_list() == ["RB", "RB", "RB"]

    def test_normalize_position_preserves_standard(self):
        """Standard uppercase positions are unchanged."""
        df = pl.DataFrame({"position": ["QB", "RB", "WR", "TE"]})
        result = normalize_position(df)
        assert result["position"].to_list() == ["QB", "RB", "WR", "TE"]

    def test_normalize_position_no_position_column(self):
        """Returns unchanged when no position column."""
        df = pl.DataFrame({"name": ["Test", "Test2"]})
        result = normalize_position(df)
        assert result.columns == ["name"]


class TestNormalizePlayerData:
    """Tests for normalize_player_data orchestrator function."""

    def test_normalize_player_data_full_pipeline(self):
        """All normalizations applied in pipeline."""
        df = pl.DataFrame({
            "player_id": [" ABC123 "],
            "position": ["fb"],
            "recent_team": ["OAK"],
            "name": ["Test Player"],
        })
        result = normalize_player_data(df)

        # Team normalization
        assert result["recent_team"][0] == "LV"
        # Player ID standardization
        assert result["player_id"][0] == "ABC123"
        assert result["player_key"][0] == "abc123"
        # Position normalization
        assert result["position"][0] == "RB"
        # Original columns preserved
        assert result["name"][0] == "Test Player"

    def test_normalize_player_data_preserves_row_count(self):
        """Row count is preserved through normalization."""
        df = pl.DataFrame({
            "player_id": ["001", "002", "003"],
            "position": ["QB", "RB", "WR"],
            "recent_team": ["KC", "BUF", "SF"],
        })
        result = normalize_player_data(df)
        assert len(result) == 3

    def test_normalize_player_data_adds_player_key(self):
        """normalize_player_data adds player_key column."""
        df = pl.DataFrame({
            "player_id": ["ABC123"],
            "position": ["QB"],
        })
        result = normalize_player_data(df)
        assert "player_key" in result.columns
