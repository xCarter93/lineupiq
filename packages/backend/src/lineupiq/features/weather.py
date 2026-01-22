"""
Weather feature engineering for NFL game predictions.

Converts raw weather data into ML-ready features based on research-backed thresholds:
- Temperature bins: extreme_cold (<25°F), freezing (<32°F), extreme_heat (>85°F)
- Wind thresholds: high_wind (>=15mph), very_high_wind (>=20mph)
- Precipitation indicators: has_precip (>0), precip_amount
- Dome/outdoor encoding: is_dome (1 for dome, 0 for outdoor)

Research findings:
- Temperatures <32°F reduce passing efficiency by 10-15%
- Wind speeds >=15mph decrease completion rates by ~6%
- Precipitation reduces scoring by 2-10 points depending on severity

Dome games are set to neutral weather values (72°F, 0 wind, no precip) to avoid
noise from fetching irrelevant outdoor weather data.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)

# Research-backed weather thresholds
EXTREME_COLD_THRESHOLD = 25  # 10-15% passing efficiency drop
FREEZING_THRESHOLD = 32  # Significant impact on ball handling
EXTREME_HEAT_THRESHOLD = 85  # Player fatigue increases

HIGH_WIND_THRESHOLD = 15  # 6% completion rate drop
VERY_HIGH_WIND_THRESHOLD = 20  # Major impact on passing game

# Neutral values for dome games
DOME_TEMP = 72  # Comfortable indoor temperature
DOME_WIND = 0  # No wind indoors
DOME_PRECIP = 0  # No precipitation indoors


def engineer_weather_features(
    schedule_df: pl.DataFrame,
    weather_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Add detailed weather features to schedule data.

    Creates 9 weather feature columns based on research-backed thresholds:
    1. extreme_cold: Temperature < 25°F (10-15% passing efficiency drop)
    2. freezing: Temperature < 32°F
    3. extreme_heat: Temperature > 85°F
    4. temp_filled: Temperature with dome defaults and mean imputation
    5. high_wind: Wind >= 15mph (6% completion rate drop)
    6. very_high_wind: Wind >= 20mph
    7. wind_filled: Wind speed with dome defaults and mean imputation
    8. has_precip: Precipitation > 0
    9. precip_amount: Precipitation amount in inches

    Dome games (roof='dome' or roof='closed') are handled specially:
    - Set to neutral values: 72°F, 0 wind, 0 precip
    - No API calls wasted on fetching irrelevant outdoor weather

    Outdoor games with missing weather data use mean imputation from available outdoor games.

    Args:
        schedule_df: DataFrame with columns: game_id, season, week, gameday, roof, temp, wind.
        weather_df: Optional DataFrame with detailed weather data from Visual Crossing API.
            If provided, joins on game_id. If None, uses temp/wind from schedule_df.

    Returns:
        DataFrame with original columns plus 9 new weather feature columns.

    Example:
        >>> schedule = pl.DataFrame({
        ...     "game_id": ["2024_01_GB_CHI", "2024_01_NO_ATL"],
        ...     "roof": ["outdoors", "dome"],
        ...     "temp": [28.0, None],
        ...     "wind": [18.0, None],
        ... })
        >>> result = engineer_weather_features(schedule)
        >>> result["extreme_cold"][0]  # 28°F < 25°F is False
        False
        >>> result["freezing"][0]  # 28°F < 32°F is True
        True
        >>> result["high_wind"][0]  # 18mph >= 15mph
        True
        >>> result["temp_filled"][1]  # Dome game
        72
    """
    logger.info(f"Engineering weather features for {len(schedule_df)} games")

    df = schedule_df.clone()

    # Join weather data if provided
    if weather_df is not None:
        logger.debug("Joining external weather data")
        df = df.join(weather_df, on="game_id", how="left")

    # Identify dome games
    if "roof" not in df.columns:
        logger.warning("No 'roof' column found, assuming all games are outdoor")
        df = df.with_columns(pl.lit(False).alias("is_dome_game"))
    else:
        # is_dome_game is temporary for feature engineering, separate from final is_dome feature
        df = df.with_columns(
            pl.col("roof").str.to_lowercase().is_in(["dome", "closed"]).alias("is_dome_game")
        )

    # Count dome vs outdoor games
    dome_count = df.filter(pl.col("is_dome_game")).height
    outdoor_count = df.filter(~pl.col("is_dome_game")).height
    logger.info(f"Games: {outdoor_count} outdoor, {dome_count} dome")

    # Temperature features
    # Step 1: Fill dome games with neutral temp
    df = df.with_columns(
        pl.when(pl.col("is_dome_game"))
        .then(DOME_TEMP)
        .otherwise(pl.col("temp"))
        .alias("temp_filled")
    )

    # Step 2: Fill missing outdoor temps with mean of outdoor games
    outdoor_temp_mean = (
        df.filter(~pl.col("is_dome_game") & pl.col("temp_filled").is_not_null())
        .select(pl.col("temp_filled").mean())
        .item()
    )

    if outdoor_temp_mean is not None:
        df = df.with_columns(
            pl.when(pl.col("temp_filled").is_null())
            .then(outdoor_temp_mean)
            .otherwise(pl.col("temp_filled"))
            .alias("temp_filled")
        )
        logger.debug(f"Filled missing outdoor temps with mean: {outdoor_temp_mean:.1f}°F")

    # Step 3: Create temperature threshold features
    df = df.with_columns(
        [
            (pl.col("temp_filled") < EXTREME_COLD_THRESHOLD).cast(pl.Int8).alias("extreme_cold"),
            (pl.col("temp_filled") < FREEZING_THRESHOLD).cast(pl.Int8).alias("freezing"),
            (pl.col("temp_filled") > EXTREME_HEAT_THRESHOLD).cast(pl.Int8).alias("extreme_heat"),
        ]
    )

    # Wind features
    # Step 1: Fill dome games with 0 wind
    df = df.with_columns(
        pl.when(pl.col("is_dome_game"))
        .then(DOME_WIND)
        .otherwise(pl.col("wind"))
        .alias("wind_filled")
    )

    # Step 2: Fill missing outdoor wind with mean of outdoor games
    outdoor_wind_mean = (
        df.filter(~pl.col("is_dome_game") & pl.col("wind_filled").is_not_null())
        .select(pl.col("wind_filled").mean())
        .item()
    )

    if outdoor_wind_mean is not None:
        df = df.with_columns(
            pl.when(pl.col("wind_filled").is_null())
            .then(outdoor_wind_mean)
            .otherwise(pl.col("wind_filled"))
            .alias("wind_filled")
        )
        logger.debug(f"Filled missing outdoor wind with mean: {outdoor_wind_mean:.1f} mph")

    # Step 3: Create wind threshold features
    df = df.with_columns(
        [
            (pl.col("wind_filled") >= HIGH_WIND_THRESHOLD).cast(pl.Int8).alias("high_wind"),
            (pl.col("wind_filled") >= VERY_HIGH_WIND_THRESHOLD)
            .cast(pl.Int8)
            .alias("very_high_wind"),
        ]
    )

    # Precipitation features
    # If precip column exists in weather data, use it; otherwise create dummy column
    if "precip" in df.columns:
        df = df.with_columns(
            pl.when(pl.col("is_dome_game"))
            .then(DOME_PRECIP)
            .otherwise(pl.col("precip").fill_null(0))
            .alias("precip_amount")
        )
    else:
        # No precipitation data available, set all to 0
        df = df.with_columns(pl.lit(0.0).alias("precip_amount"))

    df = df.with_columns((pl.col("precip_amount") > 0).cast(pl.Int8).alias("has_precip"))

    # Drop temporary is_dome_game column (we have is_dome as final feature)
    df = df.drop("is_dome_game")

    # Log feature statistics
    extreme_cold_count = df.filter(pl.col("extreme_cold") == 1).height
    freezing_count = df.filter(pl.col("freezing") == 1).height
    extreme_heat_count = df.filter(pl.col("extreme_heat") == 1).height
    high_wind_count = df.filter(pl.col("high_wind") == 1).height
    very_high_wind_count = df.filter(pl.col("very_high_wind") == 1).height
    precip_count = df.filter(pl.col("has_precip") == 1).height

    logger.info(
        f"Weather features: {extreme_cold_count} extreme cold, {freezing_count} freezing, "
        f"{extreme_heat_count} extreme heat, {high_wind_count} high wind, "
        f"{very_high_wind_count} very high wind, {precip_count} with precipitation"
    )

    return df


def get_weather_feature_columns() -> list[str]:
    """Get list of weather feature column names for ML.

    Returns:
        List of 10 weather feature column names:
        - 7 new detailed features (extreme_cold, freezing, extreme_heat, high_wind,
          very_high_wind, has_precip, precip_amount)
        - 3 existing features (temp_normalized, wind_normalized, is_dome)

    Example:
        >>> cols = get_weather_feature_columns()
        >>> len(cols)
        10
        >>> "extreme_cold" in cols
        True
        >>> "freezing" in cols
        True
    """
    return [
        # New detailed features (Phase 20)
        "extreme_cold",
        "freezing",
        "extreme_heat",
        "high_wind",
        "very_high_wind",
        "has_precip",
        "precip_amount",
        # Existing normalized features (Phase 1-19)
        "temp_normalized",
        "wind_normalized",
        "is_dome",
    ]
