"""
Unit tests for opponent defensive strength features.

Tests verify:
1. Defensive stats aggregation is correct
2. Ranking ordering is correct (rank 1 = best defense)
3. No data leakage (rankings use only prior weeks)
4. Normalization is correct (0-1 scale)
5. Opponent join works correctly
"""

import polars as pl
import pytest

from lineupiq.features.opponent_features import (
    add_opponent_strength,
    compute_defensive_rankings,
    compute_defensive_stats,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def basic_player_data() -> pl.DataFrame:
    """Basic player data for testing defensive stats aggregation."""
    return pl.DataFrame({
        "player_id": ["p1", "p2", "p3", "p4"],
        "player_name": ["Player 1", "Player 2", "Player 3", "Player 4"],
        "opponent": ["KC", "KC", "BUF", "BUF"],  # Two games: vs KC and vs BUF
        "season": [2024, 2024, 2024, 2024],
        "week": [1, 1, 1, 1],
        "passing_yards": [100.0, 150.0, 200.0, 50.0],  # KC allows 250, BUF allows 250
        "rushing_yards": [50.0, 30.0, 80.0, 100.0],   # KC allows 80, BUF allows 180
        "receiving_yards": [0.0, 0.0, 0.0, 0.0],
        "passing_tds": [1.0, 1.0, 2.0, 0.0],
        "rushing_tds": [0.0, 1.0, 0.0, 1.0],
        "receiving_tds": [0.0, 0.0, 0.0, 0.0],
    })


@pytest.fixture
def multi_week_player_data() -> pl.DataFrame:
    """Multi-week data for testing no data leakage."""
    # Week 1: Team A vs KC, Team B vs BUF
    # Week 2: Team A vs BUF, Team B vs KC
    # Week 3: Team A vs LAC, Team B vs DEN
    data = []

    # Week 1: KC allows 100 pass, 50 rush; BUF allows 200 pass, 80 rush
    data.append({"player_id": "p1", "opponent": "KC", "season": 2024, "week": 1,
                 "passing_yards": 100.0, "rushing_yards": 50.0, "receiving_yards": 0.0,
                 "passing_tds": 1.0, "rushing_tds": 0.0, "receiving_tds": 0.0})
    data.append({"player_id": "p2", "opponent": "BUF", "season": 2024, "week": 1,
                 "passing_yards": 200.0, "rushing_yards": 80.0, "receiving_yards": 0.0,
                 "passing_tds": 2.0, "rushing_tds": 1.0, "receiving_tds": 0.0})

    # Week 2: KC allows 150 pass, 40 rush; BUF allows 180 pass, 90 rush
    data.append({"player_id": "p1", "opponent": "BUF", "season": 2024, "week": 2,
                 "passing_yards": 180.0, "rushing_yards": 90.0, "receiving_yards": 0.0,
                 "passing_tds": 1.0, "rushing_tds": 0.0, "receiving_tds": 0.0})
    data.append({"player_id": "p2", "opponent": "KC", "season": 2024, "week": 2,
                 "passing_yards": 150.0, "rushing_yards": 40.0, "receiving_yards": 0.0,
                 "passing_tds": 1.0, "rushing_tds": 1.0, "receiving_tds": 0.0})

    # Week 3: LAC allows 250 pass, 100 rush; DEN allows 120 pass, 60 rush
    data.append({"player_id": "p1", "opponent": "LAC", "season": 2024, "week": 3,
                 "passing_yards": 250.0, "rushing_yards": 100.0, "receiving_yards": 0.0,
                 "passing_tds": 3.0, "rushing_tds": 1.0, "receiving_tds": 0.0})
    data.append({"player_id": "p2", "opponent": "DEN", "season": 2024, "week": 3,
                 "passing_yards": 120.0, "rushing_yards": 60.0, "receiving_yards": 0.0,
                 "passing_tds": 1.0, "rushing_tds": 0.0, "receiving_tds": 0.0})

    return pl.DataFrame(data)


@pytest.fixture
def ranking_test_data() -> pl.DataFrame:
    """Data specifically for testing ranking order."""
    # Create 4 teams with clearly different defensive stats
    # Best pass defense = Team A (allows 100 total), worst = Team D (allows 400)
    data = []

    # Week 1 data
    for team, pass_allowed in [("TeamA", 100), ("TeamB", 200), ("TeamC", 300), ("TeamD", 400)]:
        data.append({
            "player_id": f"p_{team}",
            "opponent": team,
            "season": 2024,
            "week": 1,
            "passing_yards": float(pass_allowed),
            "rushing_yards": float(pass_allowed // 2),  # Rush is half of pass
            "receiving_yards": 0.0,
            "passing_tds": 1.0,
            "rushing_tds": 0.0,
            "receiving_tds": 0.0,
        })

    # Week 2 data - same pattern to maintain ranking
    for team, pass_allowed in [("TeamA", 100), ("TeamB", 200), ("TeamC", 300), ("TeamD", 400)]:
        data.append({
            "player_id": f"p_{team}",
            "opponent": team,
            "season": 2024,
            "week": 2,
            "passing_yards": float(pass_allowed),
            "rushing_yards": float(pass_allowed // 2),
            "receiving_yards": 0.0,
            "passing_tds": 1.0,
            "rushing_tds": 0.0,
            "receiving_tds": 0.0,
        })

    return pl.DataFrame(data)


# =============================================================================
# Test Defensive Stats Aggregation
# =============================================================================


def test_defensive_stats_aggregation(basic_player_data: pl.DataFrame):
    """Verify stats are summed by opponent correctly."""
    result = compute_defensive_stats(basic_player_data)

    # KC should have allowed: 100 + 150 = 250 pass, 50 + 30 = 80 rush
    kc_stats = result.filter(pl.col("team") == "KC")
    assert len(kc_stats) == 1
    assert kc_stats["pass_yards_allowed"][0] == 250.0
    assert kc_stats["rush_yards_allowed"][0] == 80.0

    # BUF should have allowed: 200 + 50 = 250 pass, 80 + 100 = 180 rush
    buf_stats = result.filter(pl.col("team") == "BUF")
    assert len(buf_stats) == 1
    assert buf_stats["pass_yards_allowed"][0] == 250.0
    assert buf_stats["rush_yards_allowed"][0] == 180.0


def test_defensive_stats_null_handling():
    """Verify null stats are treated as 0."""
    df = pl.DataFrame({
        "player_id": ["p1"],
        "opponent": ["KC"],
        "season": [2024],
        "week": [1],
        "passing_yards": [None],  # Null
        "rushing_yards": [50.0],
        "receiving_yards": [None],
        "passing_tds": [None],
        "rushing_tds": [1.0],
        "receiving_tds": [None],
    })

    result = compute_defensive_stats(df)
    kc_stats = result.filter(pl.col("team") == "KC")

    # Null passing yards should become 0
    assert kc_stats["pass_yards_allowed"][0] == 0.0
    assert kc_stats["rush_yards_allowed"][0] == 50.0


# =============================================================================
# Test Defensive Rankings Ordering
# =============================================================================


def test_defensive_rankings_ordering(ranking_test_data: pl.DataFrame):
    """Verify ranking order is correct: rank 1 = best defense (fewest yards)."""
    defensive_stats = compute_defensive_stats(ranking_test_data)
    rankings = compute_defensive_rankings(defensive_stats)

    # For week 2, rankings should be computed from week 1 data only
    week2_rankings = rankings.filter(pl.col("week") == 2)

    # TeamA allows fewest (100 pass) -> should be rank 1
    team_a = week2_rankings.filter(pl.col("team") == "TeamA")
    assert team_a["opp_pass_yards_allowed_rank"][0] == 1

    # TeamD allows most (400 pass) -> should be rank 4
    team_d = week2_rankings.filter(pl.col("team") == "TeamD")
    assert team_d["opp_pass_yards_allowed_rank"][0] == 4

    # TeamB should be rank 2, TeamC should be rank 3
    team_b = week2_rankings.filter(pl.col("team") == "TeamB")
    team_c = week2_rankings.filter(pl.col("team") == "TeamC")
    assert team_b["opp_pass_yards_allowed_rank"][0] == 2
    assert team_c["opp_pass_yards_allowed_rank"][0] == 3


def test_defensive_rankings_rush_ordering(ranking_test_data: pl.DataFrame):
    """Verify rush rankings are also correct."""
    defensive_stats = compute_defensive_stats(ranking_test_data)
    rankings = compute_defensive_rankings(defensive_stats)

    week2_rankings = rankings.filter(pl.col("week") == 2)

    # Rush yards are half of pass, so order should be same
    team_a = week2_rankings.filter(pl.col("team") == "TeamA")
    team_d = week2_rankings.filter(pl.col("team") == "TeamD")

    assert team_a["opp_rush_yards_allowed_rank"][0] == 1
    assert team_d["opp_rush_yards_allowed_rank"][0] == 4


# =============================================================================
# Test No Data Leakage
# =============================================================================


def test_no_data_leakage(multi_week_player_data: pl.DataFrame):
    """Critical: verify week N rankings only use weeks < N."""
    defensive_stats = compute_defensive_stats(multi_week_player_data)
    rankings = compute_defensive_rankings(defensive_stats)

    # After week 1: KC allowed 100 pass, BUF allowed 200 pass
    # So for week 2 rankings: KC should be ranked better (rank 1)
    week2_rankings = rankings.filter(pl.col("week") == 2)

    kc_week2 = week2_rankings.filter(pl.col("team") == "KC")
    buf_week2 = week2_rankings.filter(pl.col("team") == "BUF")

    # KC allowed fewer pass yards in week 1, so should have lower (better) rank
    assert kc_week2["opp_pass_yards_allowed_rank"][0] < buf_week2["opp_pass_yards_allowed_rank"][0]

    # After weeks 1-2: KC total = 100 + 150 = 250, BUF total = 200 + 180 = 380
    # So for week 3: KC should still be ranked better
    week3_rankings = rankings.filter(pl.col("week") == 3)

    # Should have KC and BUF from weeks 1-2
    kc_week3 = week3_rankings.filter(pl.col("team") == "KC")
    buf_week3 = week3_rankings.filter(pl.col("team") == "BUF")

    assert len(kc_week3) == 1, "KC should have week 3 ranking"
    assert len(buf_week3) == 1, "BUF should have week 3 ranking"

    # KC (250 total) should rank better than BUF (380 total)
    assert kc_week3["opp_pass_yards_allowed_rank"][0] < buf_week3["opp_pass_yards_allowed_rank"][0]


def test_week1_has_no_rankings(basic_player_data: pl.DataFrame):
    """Week 1 should have no rankings (no prior data to compute from)."""
    defensive_stats = compute_defensive_stats(basic_player_data)
    rankings = compute_defensive_rankings(defensive_stats)

    # Basic data only has week 1, so rankings should be empty
    # (no prior weeks to compute from)
    assert len(rankings) == 0


# =============================================================================
# Test Opponent Strength Normalization
# =============================================================================


def test_opponent_strength_normalization(ranking_test_data: pl.DataFrame):
    """Verify 0-1 normalization: best defense (rank 1) = 0, worst = 1."""
    defensive_stats = compute_defensive_stats(ranking_test_data)
    rankings = compute_defensive_rankings(defensive_stats)

    week2_rankings = rankings.filter(pl.col("week") == 2)

    # Best pass defense (TeamA, rank 1) should have strength = 0
    team_a = week2_rankings.filter(pl.col("team") == "TeamA")
    assert team_a["opp_pass_defense_strength"][0] == pytest.approx(0.0)

    # Worst pass defense (TeamD, rank 4) should have strength = 1
    # With 4 teams: (4 - 1) / (4 - 1) = 1.0
    team_d = week2_rankings.filter(pl.col("team") == "TeamD")
    assert team_d["opp_pass_defense_strength"][0] == pytest.approx(1.0)

    # Middle teams should have intermediate values
    team_b = week2_rankings.filter(pl.col("team") == "TeamB")
    team_c = week2_rankings.filter(pl.col("team") == "TeamC")

    # TeamB (rank 2): (2-1)/(4-1) = 0.333
    assert team_b["opp_pass_defense_strength"][0] == pytest.approx(1/3, rel=0.01)

    # TeamC (rank 3): (3-1)/(4-1) = 0.666
    assert team_c["opp_pass_defense_strength"][0] == pytest.approx(2/3, rel=0.01)


def test_normalization_bounds():
    """Verify normalized values are always in [0, 1]."""
    # Create data with many teams
    data = []
    for i in range(32):  # 32 teams like NFL
        data.append({
            "player_id": f"p{i}",
            "opponent": f"Team{i:02d}",
            "season": 2024,
            "week": 1,
            "passing_yards": float(100 * (i + 1)),  # 100, 200, ..., 3200
            "rushing_yards": float(50 * (i + 1)),
            "receiving_yards": 0.0,
            "passing_tds": 1.0,
            "rushing_tds": 0.0,
            "receiving_tds": 0.0,
        })
        # Add week 2 data
        data.append({
            "player_id": f"p{i}",
            "opponent": f"Team{i:02d}",
            "season": 2024,
            "week": 2,
            "passing_yards": float(100 * (i + 1)),
            "rushing_yards": float(50 * (i + 1)),
            "receiving_yards": 0.0,
            "passing_tds": 1.0,
            "rushing_tds": 0.0,
            "receiving_tds": 0.0,
        })

    df = pl.DataFrame(data)
    defensive_stats = compute_defensive_stats(df)
    rankings = compute_defensive_rankings(defensive_stats)

    # Check all strength values are in [0, 1]
    pass_strength = rankings["opp_pass_defense_strength"]
    rush_strength = rankings["opp_rush_defense_strength"]

    assert pass_strength.min() >= 0.0
    assert pass_strength.max() <= 1.0
    assert rush_strength.min() >= 0.0
    assert rush_strength.max() <= 1.0


# =============================================================================
# Test Opponent Join
# =============================================================================


def test_opponent_join(ranking_test_data: pl.DataFrame):
    """Verify opponent strength joins correctly to player data."""
    result = add_opponent_strength(ranking_test_data)

    # Check that new columns exist
    assert "opp_pass_defense_strength" in result.columns
    assert "opp_rush_defense_strength" in result.columns
    assert "opp_pass_yards_allowed_rank" in result.columns

    # Week 2 players should have opponent strength values
    week2_players = result.filter(pl.col("week") == 2)

    # Player playing against TeamA should get TeamA's defensive strength
    # (which should be 0 since TeamA is best defense)
    player_vs_team_a = week2_players.filter(pl.col("opponent") == "TeamA")
    assert len(player_vs_team_a) == 1
    assert player_vs_team_a["opp_pass_defense_strength"][0] == pytest.approx(0.0)

    # Player playing against TeamD should get TeamD's defensive strength
    # (which should be 1 since TeamD is worst defense)
    player_vs_team_d = week2_players.filter(pl.col("opponent") == "TeamD")
    assert len(player_vs_team_d) == 1
    assert player_vs_team_d["opp_pass_defense_strength"][0] == pytest.approx(1.0)


def test_opponent_join_week1_null():
    """Week 1 should have null opponent strength (no prior data)."""
    df = pl.DataFrame({
        "player_id": ["p1"],
        "opponent": ["KC"],
        "season": [2024],
        "week": [1],
        "passing_yards": [200.0],
        "rushing_yards": [50.0],
        "receiving_yards": [0.0],
        "passing_tds": [1.0],
        "rushing_tds": [0.0],
        "receiving_tds": [0.0],
    })

    result = add_opponent_strength(df)

    # Week 1 should have null opponent strength (no prior weeks)
    assert result["opp_pass_defense_strength"][0] is None
    assert result["opp_rush_defense_strength"][0] is None


def test_opponent_column_required():
    """Should raise error if opponent column is missing."""
    df = pl.DataFrame({
        "player_id": ["p1"],
        # Missing "opponent" column
        "season": [2024],
        "week": [1],
        "passing_yards": [200.0],
    })

    with pytest.raises(ValueError, match="missing 'opponent' column"):
        add_opponent_strength(df)
