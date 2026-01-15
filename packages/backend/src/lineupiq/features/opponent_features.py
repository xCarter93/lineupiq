"""
Opponent defensive strength features.

Computes defensive strength rankings for NFL teams based on stats allowed.
Key features:
- Opponent pass defense strength (0-1 scale)
- Opponent rush defense strength (0-1 scale)

Important: Rankings are computed from data PRIOR to the current week to
avoid data leakage. Week 3's opponent strength uses only weeks 1-2 data.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def compute_defensive_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate stats ALLOWED by each defense per season and week.

    This computes what each defense gave up (stats scored AGAINST them).
    For example, if Team A scores 300 passing yards against Team B,
    Team B's defense allowed 300 passing yards that week.

    Args:
        df: Player stats DataFrame with opponent, season, week, and stat columns.
            Must have columns: opponent, season, week, passing_yards, rushing_yards,
            receiving_yards, passing_tds, rushing_tds, receiving_tds.

    Returns:
        DataFrame with defensive stats per team per week:
        - team: The defensive team
        - season: Season year
        - week: Week number
        - pass_yards_allowed: Total passing yards allowed that week
        - rush_yards_allowed: Total rushing yards allowed that week
        - total_yards_allowed: Total yards allowed that week
        - tds_allowed: Total TDs allowed that week

    Example:
        >>> df = pl.DataFrame({
        ...     "opponent": ["KC", "KC", "BUF"],
        ...     "season": [2024, 2024, 2024],
        ...     "week": [1, 1, 1],
        ...     "passing_yards": [100.0, 50.0, 200.0],
        ...     "rushing_yards": [30.0, 20.0, 80.0],
        ...     "receiving_yards": [0.0, 0.0, 0.0],
        ...     "passing_tds": [1.0, 0.0, 2.0],
        ...     "rushing_tds": [0.0, 1.0, 0.0],
        ...     "receiving_tds": [0.0, 0.0, 0.0],
        ... })
        >>> result = compute_defensive_stats(df)
        >>> kc_allowed = result.filter(pl.col("team") == "KC")
        >>> kc_allowed["pass_yards_allowed"][0]
        150.0
    """
    logger.info(f"Computing defensive stats from {len(df)} player rows")

    # Verify required columns
    required_cols = [
        "opponent", "season", "week",
        "passing_yards", "rushing_yards", "receiving_yards",
        "passing_tds", "rushing_tds", "receiving_tds"
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Fill nulls with 0 for stat columns
    stat_cols = [
        "passing_yards", "rushing_yards", "receiving_yards",
        "passing_tds", "rushing_tds", "receiving_tds"
    ]
    df = df.with_columns([
        pl.col(col).fill_null(0.0) for col in stat_cols
    ])

    # Group by opponent (defensive team), season, week and sum stats
    # This gives us what each defense allowed in each game
    defensive_stats = df.group_by(["opponent", "season", "week"]).agg([
        pl.col("passing_yards").sum().alias("pass_yards_allowed"),
        pl.col("rushing_yards").sum().alias("rush_yards_allowed"),
        (pl.col("passing_yards") + pl.col("rushing_yards") + pl.col("receiving_yards"))
        .sum().alias("total_yards_allowed"),
        (pl.col("passing_tds") + pl.col("rushing_tds") + pl.col("receiving_tds"))
        .sum().alias("tds_allowed"),
    ])

    # Rename opponent to team for clarity (this IS the defensive team)
    defensive_stats = defensive_stats.rename({"opponent": "team"})

    logger.info(
        f"Computed defensive stats: {len(defensive_stats)} team-week combinations"
    )

    return defensive_stats


def compute_defensive_rankings(defensive_df: pl.DataFrame) -> pl.DataFrame:
    """Compute season-to-date defensive rankings for each team per week.

    Rankings are computed using data from PRIOR weeks only (no data leakage).
    Week 3 rankings use only weeks 1-2 data.

    Rank 1 = best defense (allows fewest yards)
    Rank 32 (or N teams) = worst defense (allows most yards)

    Args:
        defensive_df: DataFrame from compute_defensive_stats with:
            team, season, week, pass_yards_allowed, rush_yards_allowed, total_yards_allowed

    Returns:
        DataFrame with rankings per team per week:
        - team: Team abbreviation
        - season: Season year
        - week: Week number
        - opp_pass_yards_allowed_rank: Rank 1-32 for pass yards allowed (1=best)
        - opp_rush_yards_allowed_rank: Rank 1-32 for rush yards allowed (1=best)
        - opp_total_yards_allowed_rank: Rank 1-32 for total yards allowed (1=best)
        - opp_pass_defense_strength: Normalized 0-1 (0=best, 1=worst)
        - opp_rush_defense_strength: Normalized 0-1 (0=best, 1=worst)

    Example:
        >>> df = compute_defensive_rankings(defensive_df)
        >>> # Team with rank 1 should have strength near 0
        >>> best_pass_def = df.filter(pl.col("opp_pass_yards_allowed_rank") == 1)
        >>> best_pass_def["opp_pass_defense_strength"][0]
        0.0
    """
    logger.info("Computing defensive rankings from defensive stats")

    # Get unique seasons and weeks
    seasons = defensive_df["season"].unique().sort().to_list()

    all_rankings = []

    for season in seasons:
        season_df = defensive_df.filter(pl.col("season") == season)
        weeks = season_df["week"].unique().sort().to_list()

        for week in weeks:
            # For week N, compute rankings using weeks 1 to N-1 only
            prior_weeks_df = season_df.filter(pl.col("week") < week)

            if len(prior_weeks_df) == 0:
                # Week 1 has no prior data, skip (will be null)
                continue

            # Compute season-to-date totals per team
            season_totals = prior_weeks_df.group_by("team").agg([
                pl.col("pass_yards_allowed").sum().alias("pass_yards_ytd"),
                pl.col("rush_yards_allowed").sum().alias("rush_yards_ytd"),
                pl.col("total_yards_allowed").sum().alias("total_yards_ytd"),
            ])

            # Rank teams (1 = fewest yards allowed = best defense)
            # Lower yards allowed = lower rank number = better
            num_teams = len(season_totals)

            season_totals = season_totals.with_columns([
                pl.col("pass_yards_ytd").rank(method="min").alias("opp_pass_yards_allowed_rank"),
                pl.col("rush_yards_ytd").rank(method="min").alias("opp_rush_yards_allowed_rank"),
                pl.col("total_yards_ytd").rank(method="min").alias("opp_total_yards_allowed_rank"),
            ])

            # Normalize to 0-1 scale: (rank - 1) / (num_teams - 1)
            # 0 = best defense (rank 1), 1 = worst defense (rank N)
            denominator = max(num_teams - 1, 1)  # Avoid division by zero

            season_totals = season_totals.with_columns([
                ((pl.col("opp_pass_yards_allowed_rank") - 1) / denominator)
                .alias("opp_pass_defense_strength"),
                ((pl.col("opp_rush_yards_allowed_rank") - 1) / denominator)
                .alias("opp_rush_defense_strength"),
            ])

            # Add season and week columns
            season_totals = season_totals.with_columns([
                pl.lit(season).alias("season"),
                pl.lit(week).alias("week"),
            ])

            # Select only the columns we need
            season_totals = season_totals.select([
                "team", "season", "week",
                "opp_pass_yards_allowed_rank", "opp_rush_yards_allowed_rank",
                "opp_total_yards_allowed_rank",
                "opp_pass_defense_strength", "opp_rush_defense_strength",
            ])

            all_rankings.append(season_totals)

    if not all_rankings:
        # Return empty DataFrame with correct schema
        return pl.DataFrame({
            "team": pl.Series([], dtype=pl.Utf8),
            "season": pl.Series([], dtype=pl.Int64),
            "week": pl.Series([], dtype=pl.Int64),
            "opp_pass_yards_allowed_rank": pl.Series([], dtype=pl.Float64),
            "opp_rush_yards_allowed_rank": pl.Series([], dtype=pl.Float64),
            "opp_total_yards_allowed_rank": pl.Series([], dtype=pl.Float64),
            "opp_pass_defense_strength": pl.Series([], dtype=pl.Float64),
            "opp_rush_defense_strength": pl.Series([], dtype=pl.Float64),
        })

    rankings_df = pl.concat(all_rankings)
    logger.info(f"Computed rankings for {len(rankings_df)} team-week combinations")

    return rankings_df


def add_opponent_strength(df: pl.DataFrame) -> pl.DataFrame:
    """Add opponent defensive strength features to player data.

    This is the main entry point for opponent features. It:
    1. Computes defensive stats from player data
    2. Computes defensive rankings (using prior weeks only - no leakage)
    3. Joins rankings back to player data on opponent + season + week

    After this, each player row will have their opponent's defensive rankings
    attached, enabling the model to understand matchup difficulty.

    Args:
        df: Player stats DataFrame with:
            - opponent: Team abbreviation of opponent
            - season: Season year
            - week: Week number
            - passing_yards, rushing_yards, receiving_yards: Stat columns
            - passing_tds, rushing_tds, receiving_tds: TD columns

    Returns:
        Original DataFrame with added columns:
        - opp_pass_defense_strength: 0-1 (0=best defense, 1=worst)
        - opp_rush_defense_strength: 0-1 (0=best defense, 1=worst)
        - opp_pass_yards_allowed_rank: 1-32 rank
        - opp_rush_yards_allowed_rank: 1-32 rank
        - opp_total_yards_allowed_rank: 1-32 rank

    Example:
        >>> from lineupiq.data import process_player_stats
        >>> df = process_player_stats([2024])
        >>> result = add_opponent_strength(df)
        >>> "opp_pass_defense_strength" in result.columns
        True
        >>> # Values should be in 0-1 range
        >>> strength = result["opp_pass_defense_strength"].drop_nulls()
        >>> strength.min() >= 0 and strength.max() <= 1
        True
    """
    logger.info(f"Adding opponent strength features to {len(df)} player rows")

    # Check for opponent column
    if "opponent" not in df.columns:
        raise ValueError(
            "DataFrame missing 'opponent' column. "
            "Run add_game_context first to join schedule data."
        )

    # Step 1: Compute defensive stats
    defensive_stats = compute_defensive_stats(df)

    # Step 2: Compute rankings
    rankings = compute_defensive_rankings(defensive_stats)

    # Step 3: Join rankings to player data on opponent + season + week
    # The rankings are keyed by defensive team, and we want to join
    # based on who the player's opponent is
    result = df.join(
        rankings,
        left_on=["opponent", "season", "week"],
        right_on=["team", "season", "week"],
        how="left",
    )

    # Log join stats
    matched = result.filter(pl.col("opp_pass_defense_strength").is_not_null()).shape[0]
    total = len(result)
    null_pct = (total - matched) / total * 100 if total > 0 else 0

    logger.info(
        f"Opponent strength join: {matched}/{total} matched "
        f"({null_pct:.1f}% null - expected for week 1)"
    )

    return result
