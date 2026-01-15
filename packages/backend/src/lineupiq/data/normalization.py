"""
Player and team ID normalization module.

Provides functions to ensure consistent identifiers across seasons and datasets.
NFL teams have moved/rebranded (e.g., STL->LA, OAK->LV, SD->LAC, WAS rebrands),
and player IDs need to be consistent for joins.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)

# Historical team abbreviation mapping to current abbreviations
# NFL team relocations and name changes since 1999
TEAM_MAPPING: dict[str, str] = {
    # Relocations
    "STL": "LA",    # St. Louis Rams -> LA Rams (2016)
    "SD": "LAC",    # San Diego Chargers -> LA Chargers (2017)
    "OAK": "LV",    # Oakland Raiders -> Las Vegas Raiders (2020)
    # Name changes (keep same city)
    "WAS": "WAS",   # Washington (various names, abbreviation consistent)
    # Historical (pre-1999, but in case data has them)
    "PHO": "ARI",   # Phoenix Cardinals -> Arizona Cardinals
}

# All 32 current NFL team abbreviations (as of 2024 season)
CURRENT_TEAMS: frozenset[str] = frozenset({
    # AFC East
    "BUF",  # Buffalo Bills
    "MIA",  # Miami Dolphins
    "NE",   # New England Patriots
    "NYJ",  # New York Jets
    # AFC North
    "BAL",  # Baltimore Ravens
    "CIN",  # Cincinnati Bengals
    "CLE",  # Cleveland Browns
    "PIT",  # Pittsburgh Steelers
    # AFC South
    "HOU",  # Houston Texans
    "IND",  # Indianapolis Colts
    "JAX",  # Jacksonville Jaguars
    "TEN",  # Tennessee Titans
    # AFC West
    "DEN",  # Denver Broncos
    "KC",   # Kansas City Chiefs
    "LV",   # Las Vegas Raiders
    "LAC",  # Los Angeles Chargers
    # NFC East
    "DAL",  # Dallas Cowboys
    "NYG",  # New York Giants
    "PHI",  # Philadelphia Eagles
    "WAS",  # Washington Commanders
    # NFC North
    "CHI",  # Chicago Bears
    "DET",  # Detroit Lions
    "GB",   # Green Bay Packers
    "MIN",  # Minnesota Vikings
    # NFC South
    "ATL",  # Atlanta Falcons
    "CAR",  # Carolina Panthers
    "NO",   # New Orleans Saints
    "TB",   # Tampa Bay Buccaneers
    # NFC West
    "ARI",  # Arizona Cardinals
    "LA",   # Los Angeles Rams
    "SEA",  # Seattle Seahawks
    "SF",   # San Francisco 49ers
})


def normalize_team(team: str) -> str:
    """Normalize historical team abbreviation to current abbreviation.

    Handles NFL team relocations and name changes:
    - STL -> LA (Rams moved 2016)
    - SD -> LAC (Chargers moved 2017)
    - OAK -> LV (Raiders moved 2020)
    - PHO -> ARI (Cardinals name change)

    Args:
        team: Team abbreviation (e.g., "OAK", "KC").

    Returns:
        Normalized team abbreviation (e.g., "LV", "KC").

    Example:
        >>> normalize_team("OAK")
        'LV'
        >>> normalize_team("KC")
        'KC'
    """
    normalized = TEAM_MAPPING.get(team, team)

    if normalized not in CURRENT_TEAMS:
        logger.warning(f"Unknown team abbreviation: {team} -> {normalized}")

    return normalized


def normalize_team_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Apply team normalization to common team columns in DataFrame.

    Normalizes team abbreviations in these columns if they exist:
    - recent_team
    - team
    - home_team
    - away_team
    - opponent_team

    Args:
        df: DataFrame with team columns.

    Returns:
        DataFrame with normalized team abbreviations.

    Example:
        >>> df = pl.DataFrame({"recent_team": ["OAK", "KC", "STL"]})
        >>> result = normalize_team_columns(df)
        >>> result["recent_team"].to_list()
        ['LV', 'KC', 'LA']
    """
    team_columns = ["recent_team", "team", "home_team", "away_team", "opponent_team"]
    existing_team_columns = [col for col in team_columns if col in df.columns]

    if not existing_team_columns:
        logger.debug("No team columns found to normalize")
        return df

    for col in existing_team_columns:
        # Apply mapping using replace, defaulting to original value
        df = df.with_columns(
            pl.col(col).replace(TEAM_MAPPING, default=pl.col(col)).alias(col)
        )
        logger.debug(f"Normalized team column: {col}")

    logger.info(f"Normalized {len(existing_team_columns)} team columns")
    return df


# =============================================================================
# Player ID and position normalization
# =============================================================================

# Position mapping for normalization
POSITION_MAPPING: dict[str, str] = {
    # Lowercase to uppercase
    "qb": "QB",
    "rb": "RB",
    "wr": "WR",
    "te": "TE",
    # Mixed case to uppercase
    "Qb": "QB",
    "Rb": "RB",
    "Wr": "WR",
    "Te": "TE",
    # Fullback to RB (grouped for fantasy purposes)
    "FB": "RB",
    "fb": "RB",
    "Fb": "RB",
}


def standardize_player_id(df: pl.DataFrame) -> pl.DataFrame:
    """Standardize player_id column for consistent joins.

    Processing:
    - Ensures player_id is string type
    - Strips leading/trailing whitespace
    - Creates player_key column (lowercase player_id for case-insensitive matching)

    Args:
        df: DataFrame with player_id column.

    Returns:
        DataFrame with standardized player_id and new player_key column.

    Example:
        >>> df = pl.DataFrame({"player_id": [" ABC123 ", "DEF456"]})
        >>> result = standardize_player_id(df)
        >>> result["player_id"].to_list()
        ['ABC123', 'DEF456']
        >>> result["player_key"].to_list()
        ['abc123', 'def456']
    """
    if "player_id" not in df.columns:
        logger.debug("No player_id column found")
        return df

    initial_count = len(df)

    # Cast to string and strip whitespace
    df = df.with_columns(
        pl.col("player_id").cast(pl.Utf8).str.strip_chars().alias("player_id")
    )

    # Count fixes (where original != cleaned, approximating with whitespace check)
    # Note: Exact fix count requires comparing before/after which is expensive

    # Create player_key for case-insensitive matching
    df = df.with_columns(
        pl.col("player_id").str.to_lowercase().alias("player_key")
    )

    logger.info(f"Standardized player_id for {initial_count} rows, added player_key")
    return df


def normalize_position(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize position values to uppercase with FB->RB grouping.

    Processing:
    - Converts position to uppercase (qb -> QB, Rb -> RB)
    - Groups fullbacks with running backs (FB -> RB)

    Args:
        df: DataFrame with position column.

    Returns:
        DataFrame with normalized position values.

    Example:
        >>> df = pl.DataFrame({"position": ["qb", "FB", "WR"]})
        >>> result = normalize_position(df)
        >>> result["position"].to_list()
        ['QB', 'RB', 'WR']
    """
    if "position" not in df.columns:
        logger.debug("No position column found")
        return df

    initial_positions = df["position"].unique().to_list()

    # First convert to uppercase, then apply position mapping for special cases
    df = df.with_columns(
        pl.col("position").str.to_uppercase().alias("position")
    )

    # Handle FB -> RB conversion
    df = df.with_columns(
        pl.when(pl.col("position") == "FB")
        .then(pl.lit("RB"))
        .otherwise(pl.col("position"))
        .alias("position")
    )

    final_positions = df["position"].unique().to_list()
    logger.info(
        f"Normalized positions: {len(initial_positions)} unique -> "
        f"{len(final_positions)} unique"
    )

    return df


def normalize_player_data(df: pl.DataFrame) -> pl.DataFrame:
    """Orchestrator: apply all player data normalizations.

    Pipeline:
    1. normalize_team_columns - Standardize team abbreviations
    2. standardize_player_id - Clean player IDs and create player_key
    3. normalize_position - Uppercase positions, FB -> RB

    Args:
        df: DataFrame with player data.

    Returns:
        Fully normalized player DataFrame ready for joins.

    Example:
        >>> df = pl.DataFrame({
        ...     "player_id": [" ABC123 "],
        ...     "position": ["fb"],
        ...     "recent_team": ["OAK"]
        ... })
        >>> result = normalize_player_data(df)
        >>> result["player_id"][0]
        'ABC123'
        >>> result["position"][0]
        'RB'
        >>> result["recent_team"][0]
        'LV'
    """
    logger.info(f"Starting player data normalization ({len(df)} rows)")

    df = normalize_team_columns(df)
    df = standardize_player_id(df)
    df = normalize_position(df)

    logger.info(f"Player data normalization complete: {df.shape}")
    return df
