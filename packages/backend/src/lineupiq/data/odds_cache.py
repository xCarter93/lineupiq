"""
The Odds API client with caching for NFL betting lines.

Provides historical Vegas spreads and totals for NFL games using The Odds API
with SQLite caching to minimize API calls and respect rate limits.
"""

import logging
import os
from typing import Any

import polars as pl
from dotenv import load_dotenv
from requests_cache import CachedSession

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class OddsClient:
    """The Odds API client for NFL betting lines with caching.

    Free tier: 500 requests/month (sufficient for prototyping).
    Historical data available back to mid-2020.
    """

    def __init__(self, api_key: str | None = None, cache_name: str = "odds_cache") -> None:
        """Initialize Odds API client with caching.

        Args:
            api_key: The Odds API key (defaults to ODDS_API_KEY env var).
            cache_name: SQLite cache filename without extension.
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            logger.warning(
                "ODDS_API_KEY not found. Set in .env for Vegas spreads/totals. "
                "See https://the-odds-api.com/#get-access"
            )

        self.base_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"

        # Use CachedSession with 7-day expiration (betting lines can shift during week)
        self.session = CachedSession(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=604800,  # 7 days in seconds
        )

        logger.info(f"OddsClient initialized with cache: {cache_name}.sqlite")

    def get_historical_odds(self, date: str) -> list[dict[str, Any]]:
        """Fetch historical NFL odds for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (must be within historical range, mid-2020+).

        Returns:
            List of games with bookmaker odds. Each game contains:
            - id: Game identifier
            - commence_time: Game start time (ISO format)
            - home_team: Home team name
            - away_team: Away team name
            - bookmakers: List of bookmaker odds with markets (spreads, totals)

        Raises:
            ValueError: If ODDS_API_KEY is not set.
            requests.exceptions.HTTPError: If API request fails.

        Example:
            >>> client = OddsClient()
            >>> games = client.get_historical_odds("2024-09-05")
            >>> len(games) > 0
            True
        """
        if not self.api_key:
            raise ValueError(
                "ODDS_API_KEY required for fetching Vegas lines. "
                "Get free API key at https://the-odds-api.com/#get-access"
            )

        url = f"{self.base_url}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "spreads,totals",
            "dateFormat": "iso",
            "date": date,  # Historical date in YYYY-MM-DD format
        }

        logger.debug(f"Fetching odds for {date} from The Odds API")
        response = self.session.get(url, params=params)
        response.raise_for_status()

        games = response.json()
        logger.info(f"Fetched {len(games)} games for {date}")

        return games

    def parse_odds(self, games_json: list[dict[str, Any]]) -> pl.DataFrame:
        """Extract average spreads and totals across bookmakers.

        Averages betting lines across all available bookmakers for each game
        to get market consensus values.

        Args:
            games_json: List of games from get_historical_odds().

        Returns:
            Polars DataFrame with columns:
            - game_id: Game identifier
            - home_team: Home team name
            - away_team: Away team name
            - home_spread: Average home team spread (negative = home favored)
            - total_points: Average over/under total

        Example:
            >>> client = OddsClient()
            >>> games = client.get_historical_odds("2024-09-05")
            >>> df = client.parse_odds(games)
            >>> "home_spread" in df.columns
            True
            >>> "total_points" in df.columns
            True
        """
        odds_data = []

        for game in games_json:
            # Average spreads across bookmakers for home team
            spreads = [
                outcome["point"]
                for bookmaker in game.get("bookmakers", [])
                for market in bookmaker.get("markets", [])
                if market["key"] == "spreads"
                for outcome in market.get("outcomes", [])
                if outcome["name"] == game["home_team"]
            ]

            # Average totals across bookmakers
            totals = [
                outcome["point"]
                for bookmaker in game.get("bookmakers", [])
                for market in bookmaker.get("markets", [])
                if market["key"] == "totals"
                for outcome in market.get("outcomes", [])
            ]

            odds_data.append({
                "game_id": game["id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "home_spread": sum(spreads) / len(spreads) if spreads else None,
                "total_points": sum(totals) / len(totals) if totals else None,
            })

        df = pl.DataFrame(odds_data)
        logger.info(f"Parsed odds for {len(df)} games")

        return df
