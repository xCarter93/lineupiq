"""
Injury feature engineering for ML models.

Encodes NFL injury designations (Out, Doubtful, Questionable, Probable) into
numeric severity features. Research shows 8-10% production drop for non-QB
injuries based on designation status.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def engineer_injury_features(
    player_stats: pl.DataFrame, injuries: pl.DataFrame
) -> pl.DataFrame:
    """Add injury status features to player-week data.

    Joins injury reports to player statistics and creates numeric severity
    features based on NFL injury designations. Uses most recent injury report
    when multiple reports exist for the same player-week.

    Injury severity encoding (research: 8-10% production drop for non-QB injuries):
    - Out: 1.0 (100% impact - player won't play)
    - Doubtful: 0.75 (75% impact - unlikely to play)
    - Questionable: 0.5 (50% impact - may play limited)
    - Probable: 0.25 (25% impact - likely to play, slight limitation)
    - Not on report: 0.0 (no impact)

    Note: "Probable" designation was deprecated after 2016 season but exists
    in historical data.

    Args:
        player_stats: Player statistics DataFrame with columns:
            - gsis_id: Player identifier
            - season: Season year
            - week: Week number
        injuries: Injury reports DataFrame with columns:
            - gsis_id: Player identifier
            - season: Season year
            - week: Week number
            - report_status: Injury designation (Out, Doubtful, Questionable, Probable)
            - date_modified: Report update timestamp

    Returns:
        player_stats DataFrame with two new columns:
        - injury_severity: float 0.0-1.0 based on report_status
        - on_injury_report: binary 0/1 flag (1 if report_status is not null)

    Example:
        >>> injuries_df = fetch_injuries([2024])
        >>> player_stats_df = process_player_stats([2024])
        >>> df = engineer_injury_features(player_stats_df, injuries_df)
        >>> "injury_severity" in df.columns
        True
        >>> df.filter(pl.col("injury_severity") == 1.0).shape[0]  # Out players
        234
    """
    logger.info(
        f"Engineering injury features for {len(player_stats)} player-week records"
    )

    # For multiple injury reports per player-week (updated during week),
    # take most recent by date_modified
    if "date_modified" in injuries.columns:
        injuries_final = (
            injuries.sort("date_modified")
            .group_by(["gsis_id", "season", "week"])
            .last()
        )
        logger.info(
            f"Reduced {len(injuries)} injury records to {len(injuries_final)} "
            f"final reports (most recent per player-week)"
        )
    else:
        # Fallback if date_modified not available
        injuries_final = injuries.unique(["gsis_id", "season", "week"])
        logger.info(
            f"Using {len(injuries_final)} unique injury records "
            f"(no date_modified available)"
        )

    # Create injury severity mapping
    injuries_with_severity = injuries_final.with_columns([
        pl.when(pl.col("report_status") == "Out")
        .then(1.0)
        .when(pl.col("report_status") == "Doubtful")
        .then(0.75)
        .when(pl.col("report_status") == "Questionable")
        .then(0.5)
        .when(pl.col("report_status") == "Probable")
        .then(0.25)
        .otherwise(0.0)
        .alias("injury_severity"),
        pl.col("report_status").is_not_null().cast(pl.Int8).alias("on_injury_report"),
    ])

    # Select only needed columns for join
    injury_features = injuries_with_severity.select([
        "gsis_id",
        "season",
        "week",
        "injury_severity",
        "on_injury_report",
    ])

    # Left join to player stats - players without injuries get nulls
    df = player_stats.join(
        injury_features, on=["gsis_id", "season", "week"], how="left"
    )

    # Fill nulls with zeros (no injury report = 0.0 severity, 0 flag)
    df = df.with_columns([
        pl.col("injury_severity").fill_null(0.0),
        pl.col("on_injury_report").fill_null(0),
    ])

    injury_count = df.filter(pl.col("on_injury_report") == 1).shape[0]
    logger.info(
        f"Added injury features: {injury_count}/{len(df)} "
        f"({100 * injury_count / len(df):.1f}%) player-weeks have injury reports"
    )

    return df
