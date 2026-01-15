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
