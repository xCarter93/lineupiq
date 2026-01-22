"""
Visual Crossing Weather API client with caching and rate limiting.

Provides a cached, rate-limited HTTP session for fetching historical weather data
for NFL games. Designed for Visual Crossing's free tier (1,000 records/day).
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from pyrate_limiter import Duration, Limiter, RequestRate
from requests_cache import CachedSession
from requests_ratelimiter import LimiterMixin

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CachedLimiterSession(CachedSession, LimiterMixin):
    """HTTP session combining caching and rate limiting.

    Inherits from both CachedSession (requests-cache) and LimiterMixin
    (requests-ratelimiter) to provide:
    - SQLite-backed response caching (reduces API calls)
    - Rate limiting (10 req/sec, 1000 req/day for Visual Crossing free tier)
    - Cache hits don't count toward rate limits
    """

    pass


class WeatherClient:
    """Visual Crossing Weather API client with caching and rate limiting.

    Fetches historical weather data for NFL game locations and dates.
    Uses SQLite cache with 30-day expiration for historical data (doesn't change).
    Rate limiter prevents hitting Visual Crossing API quotas.

    Free tier limits:
    - 1,000 records per day
    - 10 requests per second (burst)

    Example:
        >>> client = WeatherClient()
        >>> weather = client.get_game_weather("40.8128,-74.0742", "2024-09-08")
        >>> weather['temp']
        72.5
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_name: str = "weather_cache",
        cache_expire_seconds: int = 2592000,  # 30 days
    ):
        """Initialize Weather API client.

        Args:
            api_key: Visual Crossing API key. If None, loads from VISUAL_CROSSING_API_KEY env var.
            cache_name: SQLite cache file name (default: "weather_cache").
            cache_expire_seconds: Cache expiration time in seconds (default: 30 days).

        Raises:
            ValueError: If API key not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv("VISUAL_CROSSING_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Visual Crossing API key required. Set VISUAL_CROSSING_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.base_url = (
            "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        )

        # Rate limiter: 10 requests/second, 1000 requests/day
        limiter = Limiter(
            RequestRate(10, Duration.SECOND),
            RequestRate(1000, Duration.DAY),
        )

        # Create cached + rate-limited session
        self.session = CachedLimiterSession(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=cache_expire_seconds,
            limiter=limiter,
        )

        logger.info(
            f"Initialized WeatherClient with cache={cache_name}, expire={cache_expire_seconds}s"
        )

    def get_game_weather(self, location: str, date: str) -> dict[str, Any]:
        """Fetch weather for a specific stadium location and game date.

        Args:
            location: Stadium coordinates "lat,lon" (e.g., "40.8128,-74.0742") or city name.
            date: Game date in YYYY-MM-DD format.

        Returns:
            Dict with weather data:
            - date: Game date (YYYY-MM-DD)
            - temp: Temperature in Fahrenheit
            - wind: Wind speed in mph
            - precip: Precipitation amount in inches
            - precip_type: List of precipitation types (e.g., ["rain"])
            - conditions: Weather conditions description

        Raises:
            requests.HTTPError: If API request fails (non-2xx status).

        Example:
            >>> client = WeatherClient()
            >>> weather = client.get_game_weather("40.8128,-74.0742", "2024-09-08")
            >>> weather['temp']
            72.5
            >>> weather['wind']
            8.2
        """
        url = f"{self.base_url}/{location}/{date}"
        params = {
            "key": self.api_key,
            "unitGroup": "us",  # Fahrenheit, mph
            "include": "days",  # Only daily data, not hourly
            "elements": "datetime,temp,windspeed,precip,preciptype,conditions",
        }

        logger.debug(f"Fetching weather for {location} on {date}")
        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        day = data["days"][0]  # Single day query

        weather = {
            "date": day["datetime"],
            "temp": day.get("temp"),
            "wind": day.get("windspeed"),
            "precip": day.get("precip", 0),
            "precip_type": day.get("preciptype", []),
            "conditions": day.get("conditions"),
        }

        # Log cache status
        if hasattr(response, "from_cache"):
            logger.debug(f"Weather data {'from cache' if response.from_cache else 'from API'}")

        return weather
