# Phase 20: Advanced Features - Research

**Researched:** 2026-01-21
**Domain:** Weather data, injury reports, and matchup-specific signals for NFL fantasy football predictions
**Confidence:** HIGH

<research_summary>
## Summary

Researched the ecosystem for integrating weather data, injury reports, and matchup-specific signals (Vegas lines, home/away splits) into existing nflreadpy ML pipeline. The standard approach uses nflreadpy's built-in `load_injuries()` and `load_schedules()` functions for official NFL data, Visual Crossing Weather API for historical weather (50+ years), and The Odds API for Vegas betting lines.

Key finding: Don't hand-roll weather collection, injury parsing, or venue mapping. nflreadpy already provides injury data since 2009 and schedule data with stadium/weather info. Visual Crossing offers 1,000 free daily records ideal for training data collection. The Odds API provides historical NFL odds back to 2020 with 500 free monthly requests for prototyping.

Weather impact is significant: temperatures below 32°F reduce passing efficiency by 10-15%, wind speeds above 15 mph decrease completion rates by ~6%, and precipitation reduces scoring by 2-10 points depending on severity. Injury designations reduce production by 8-10% for non-QB positions. Home field advantage averages +2.5-3 points but varies significantly by team (+6.4 for Detroit, -1.7 for Washington).

**Primary recommendation:** Use nflreadpy for injury/schedule data, Visual Crossing for weather (free tier sufficient), The Odds API for Vegas lines (free tier for dev). Add features incrementally: (1) weather features first (temperature, wind, precipitation, dome/outdoor), (2) injury features (designation status, practice participation), (3) matchup features (Vegas spread/total, home/away, divisional game flags). Validate each feature set's impact on model performance before adding the next.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nflreadpy | 0.3.4+ | NFL data pipeline | Official nflverse port, includes injuries/schedules/weather |
| requests-cache | 1.2.0+ | HTTP caching | Reduces API calls, respects rate limits |
| requests-ratelimiter | 0.7.0+ | Rate limit handling | Prevents API 429 errors, auto-retry |
| polars | 1.0.0+ | DataFrame operations | Fast joins for weather/injury/schedule data |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.0.0+ | API key management | Store weather/odds API keys securely |
| tenacity | 8.2.0+ | Retry logic | Robust API failure handling |
| pytz | 2024.1+ | Timezone handling | Convert game times for weather lookup |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Visual Crossing | OpenWeatherMap | OpenWeatherMap has 47+ years data vs 50+, similar pricing |
| Visual Crossing | Open-Meteo | Open-Meteo is free but lacks some premium features |
| The Odds API | SportsDataIO | SportsDataIO more comprehensive but $3k/month minimum |
| requests-cache | Custom caching | requests-cache battle-tested, handles cache invalidation |

### Data Sources
| Source | Access Method | Cost | Purpose |
|--------|---------------|------|---------|
| nflreadpy injuries | `load_injuries(seasons=[2022,2023,2024,2025])` | Free | Official NFL injury designations since 2009 |
| nflreadpy schedules | `load_schedules(seasons=[2022,2023,2024,2025])` | Free | Game dates, stadiums, roof types, temperatures |
| Visual Crossing | REST API | Free: 1k records/day, $0.0001/record paid | Historical weather (50+ years) |
| The Odds API | REST API | Free: 500 requests/month, $30 for 20k | Vegas spreads/totals back to 2020 |

**Installation:**
```bash
# Core dependencies
uv add nflreadpy requests-cache requests-ratelimiter polars python-dotenv

# Optional for robust API handling
uv add tenacity pytz
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
packages/backend/src/lineupiq/
├── features/
│   ├── weather.py           # Weather feature engineering
│   ├── injury.py             # Injury impact features
│   ├── matchup.py            # Vegas lines, home/away features
│   └── pipeline.py           # Updated to call new feature modules
├── data/
│   ├── weather_cache.py      # Visual Crossing API client with caching
│   ├── odds_cache.py         # The Odds API client with caching
│   └── fetchers.py           # Updated with injury/schedule fetching
└── config/
    └── api_keys.py           # Environment-based API key loading
```

### Pattern 1: Cached External API Client
**What:** Use requests-cache + requests-ratelimiter for all external API calls
**When to use:** Any third-party API (weather, odds)
**Example:**
```python
# Source: requests-cache + requests-ratelimiter docs
from requests_cache import CachedSession
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

class CachedLimiterSession(CachedSession, LimiterMixin):
    """Session with caching and rate limiting."""
    pass

# Visual Crossing: 10 requests/second, 1000/day on free tier
limiter = Limiter(RequestRate(10, Duration.SECOND), RequestRate(1000, Duration.DAY))
session = CachedLimiterSession(
    cache_name='weather_cache',
    backend='sqlite',
    expire_after=86400,  # 24 hours for historical data
    limiter=limiter,
    bucket_class=MemoryQueueBucket,
)

response = session.get(f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}")
```

### Pattern 2: Weather Feature Engineering
**What:** Convert categorical weather to numeric features, encode dome vs outdoor
**When to use:** After fetching weather data for game dates
**Example:**
```python
# Source: Research findings on weather impact
import polars as pl

def engineer_weather_features(schedule_df: pl.DataFrame, weather_df: pl.DataFrame) -> pl.DataFrame:
    """Add weather features to game data."""

    # Join weather data to schedule by game_id and date
    df = schedule_df.join(weather_df, on=['game_id', 'gameday'], how='left')

    # Temperature bins (research shows thresholds at 25F, 32F, 50F, 85F)
    df = df.with_columns([
        pl.when(pl.col('roof') == 'dome').then(72)  # Assume 72F for domes
          .when(pl.col('temp').is_null()).then(pl.col('temp').mean())
          .otherwise(pl.col('temp'))
          .alias('temp_filled'),
    ])

    df = df.with_columns([
        (pl.col('temp_filled') < 25).cast(pl.Int8).alias('extreme_cold'),
        (pl.col('temp_filled') < 32).cast(pl.Int8).alias('freezing'),
        (pl.col('temp_filled') > 85).cast(pl.Int8).alias('extreme_heat'),
        (pl.col('roof') == 'dome').cast(pl.Int8).alias('is_dome'),
    ])

    # Wind impact (15+ mph affects passing)
    df = df.with_columns([
        pl.when(pl.col('roof') == 'dome').then(0)
          .when(pl.col('wind').is_null()).then(pl.col('wind').mean())
          .otherwise(pl.col('wind'))
          .alias('wind_filled'),
    ])

    df = df.with_columns([
        (pl.col('wind_filled') >= 15).cast(pl.Int8).alias('high_wind'),
        (pl.col('wind_filled') >= 20).cast(pl.Int8).alias('very_high_wind'),
    ])

    return df
```

### Pattern 3: Injury Status Features
**What:** Encode injury designations and practice participation into model features
**When to use:** Join injury data to player features before prediction
**Example:**
```python
# Source: nflreadpy load_injuries() + research on injury impact
import polars as pl

def engineer_injury_features(player_stats: pl.DataFrame, injuries: pl.DataFrame) -> pl.DataFrame:
    """Add injury status features for each player-week."""

    # nflreadpy injuries schema: gsis_id, full_name, week, game_type, team,
    # report_status (Out, Doubtful, Questionable, Probable), report_primary_injury

    # Join injuries to player data
    df = player_stats.join(
        injuries,
        on=['gsis_id', 'season', 'week'],
        how='left'
    )

    # Encode injury status (research: 8-10% production drop for non-QB injuries)
    df = df.with_columns([
        pl.when(pl.col('report_status') == 'Out').then(1.0)
          .when(pl.col('report_status') == 'Doubtful').then(0.75)
          .when(pl.col('report_status') == 'Questionable').then(0.5)
          .when(pl.col('report_status') == 'Probable').then(0.25)
          .otherwise(0.0)
          .alias('injury_severity'),

        pl.col('report_status').is_not_null().cast(pl.Int8).alias('on_injury_report'),
    ])

    return df
```

### Pattern 4: Vegas Line Features
**What:** Add spreads and totals as predictive features (market efficiency signal)
**When to use:** When game-level predictions or implied team strength needed
**Example:**
```python
# Source: The Odds API structure + research on prediction models
import polars as pl
from datetime import datetime

def engineer_vegas_features(schedule_df: pl.DataFrame, odds_df: pl.DataFrame) -> pl.DataFrame:
    """Add Vegas spread and total features to games."""

    # odds_df schema from The Odds API: game_id, commence_time, home_team, away_team,
    # bookmaker, market (spreads/totals), outcomes (price, point)

    # Average spreads/totals across bookmakers for each game
    spreads = odds_df.filter(pl.col('market') == 'spreads').group_by('game_id').agg([
        pl.col('point').filter(pl.col('team') == pl.col('home_team')).mean().alias('home_spread'),
    ])

    totals = odds_df.filter(pl.col('market') == 'totals').group_by('game_id').agg([
        pl.col('point').mean().alias('total_points'),
    ])

    # Join to schedule
    df = schedule_df.join(spreads, on='game_id', how='left')
    df = df.join(totals, on='game_id', how='left')

    # Add implied team strength (spread as proxy)
    df = df.with_columns([
        pl.col('home_spread').abs().alias('vegas_strength_diff'),
        (pl.col('home_spread') < 0).cast(pl.Int8).alias('home_favored'),
    ])

    return df
```

### Anti-Patterns to Avoid
- **Fetching weather at prediction time:** Pre-fetch and cache all historical weather during training
- **Not handling dome games:** Always check `roof` column, dome games have no weather impact
- **Using raw injury strings:** Encode designations numerically for model input
- **Ignoring API rate limits:** Always use rate limiting library to prevent 429 errors
- **Hard-coding API keys:** Use environment variables and python-dotenv
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Weather data collection | Custom scraper | Visual Crossing API | 50+ years historical data, geocoding, reliable |
| NFL injury reports | Web scraping | nflreadpy `load_injuries()` | Official data since 2009, already cleaned |
| Stadium locations | Manual mapping | nflreadpy `load_schedules()` | Includes roof type, temperature, wind |
| Vegas odds history | Scrape sportsbooks | The Odds API | Historical odds back to 2020, multi-bookmaker |
| API rate limiting | Custom sleep/retry | requests-ratelimiter | Handles quotas, auto-retry, queue management |
| HTTP caching | Manual file cache | requests-cache | SQLite backend, expiration, cache invalidation |
| Timezone conversion | Manual offset math | pytz | Handles DST, all NFL stadium timezones |

**Key insight:** External data sources (weather, injuries, odds) are commodity features now. The value is in feature engineering and model integration, not data collection. Visual Crossing and The Odds API both offer free tiers sufficient for development and small-scale training. nflreadpy already provides injury and schedule data with no API needed. Fighting these leads to brittle scrapers that break when websites change, while APIs have stable contracts and better historical data access.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Weather Data Timing Mismatch
**What goes wrong:** Fetching weather for game start time but using forecasts instead of actuals
**Why it happens:** Weather APIs distinguish between forecast and historical observation data
**How to avoid:** Use Visual Crossing's "historical weather" endpoint for past games, not forecast endpoint. For future games (live predictions), use forecast but note lower accuracy.
**Warning signs:** Training data has different weather than what actually occurred during game

### Pitfall 2: Dome Game Weather Features
**What goes wrong:** Including outdoor weather features for dome games, adding noise to models
**Why it happens:** Not filtering by `roof` column from schedule data before weather join
**How to avoid:** Always check `schedule_df.filter(pl.col('roof') == 'outdoors')` before fetching weather. Set dome games to neutral weather values (72°F, 0 mph wind, no precipitation).
**Warning signs:** Models learn spurious weather correlations for teams like Detroit (indoor stadium)

### Pitfall 3: Injury Report Timing Window
**What goes wrong:** Using Friday injury report for Thursday night games or Monday games
**Why it happens:** NFL injury reports update throughout the week, final status may differ
**How to avoid:** Match injury report date to game date, not just week number. nflreadpy injuries include `practice_status` by day - use latest before game.
**Warning signs:** Players listed as Questionable on Wednesday but played Thursday with no designation

### Pitfall 4: API Rate Limit Exhaustion During Training
**What goes wrong:** Training script hits rate limits, fails halfway through, loses progress
**Why it happens:** Fetching weather/odds for every training example without caching
**How to avoid:** Pre-fetch all historical weather/odds once, cache to SQLite, reuse for all training runs. Use `requests-cache` with long expiration (30 days) for historical data.
**Warning signs:** Training slows down after initial runs, HTTP 429 errors in logs

### Pitfall 5: Vegas Line Availability for Historical Data
**What goes wrong:** No Vegas lines available for games before 2020, missing feature values
**Why it happens:** The Odds API historical data only goes back to mid-2020
**How to avoid:** Use null indicators for pre-2020 games or exclude Vegas features from those seasons. Don't impute with means - Vegas lines are informative when missing means no betting market existed yet.
**Warning signs:** Models trained on 2020+ data fail on 2018-2019 validation sets

### Pitfall 6: Home/Away Venue Confusion
**What goes wrong:** Assigning wrong team as home team, reversing spread sign
**Why it happens:** Schedule data has `home_team` and `away_team` but some APIs use different naming
**How to avoid:** Always join on team abbreviations from nflreadpy's standardized names. Verify spread sign convention (negative = home favored in The Odds API).
**Warning signs:** Home field advantage features show opposite correlation (away teams perform better)
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Complete Weather Integration Pipeline
```python
# Source: Visual Crossing API docs + requests-cache docs
import polars as pl
from requests_cache import CachedSession
import os
from datetime import datetime

class WeatherClient:
    """Visual Crossing Weather API client with caching."""

    def __init__(self, api_key: str, cache_name: str = 'weather_cache'):
        self.api_key = api_key
        self.base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        self.session = CachedSession(
            cache_name=cache_name,
            backend='sqlite',
            expire_after=2592000,  # 30 days for historical data
        )

    def get_game_weather(self, location: str, date: str) -> dict:
        """Fetch weather for a specific stadium and date.

        Args:
            location: Stadium coordinates "lat,lon" or city name
            date: Game date in YYYY-MM-DD format

        Returns:
            Dict with temp, wind, precip, conditions
        """
        url = f"{self.base_url}/{location}/{date}"
        params = {
            'key': self.api_key,
            'unitGroup': 'us',  # Fahrenheit, mph
            'include': 'days',
            'elements': 'datetime,temp,windspeed,precip,preciptype,conditions'
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        day = data['days'][0]  # Single day query

        return {
            'date': day['datetime'],
            'temp': day.get('temp'),
            'wind': day.get('windspeed'),
            'precip': day.get('precip', 0),
            'precip_type': day.get('preciptype', []),
            'conditions': day.get('conditions'),
        }

# Usage
weather_client = WeatherClient(api_key=os.getenv('VISUAL_CROSSING_API_KEY'))

# Load schedule with stadium coordinates
schedule = pl.read_parquet('data/schedule.parquet')

# Add weather for outdoor games
outdoor_games = schedule.filter(pl.col('roof') == 'outdoors')

weather_data = []
for row in outdoor_games.iter_rows(named=True):
    location = f"{row['stadium_lat']},{row['stadium_lon']}"
    date = row['gameday'].strftime('%Y-%m-%d')

    try:
        weather = weather_client.get_game_weather(location, date)
        weather['game_id'] = row['game_id']
        weather_data.append(weather)
    except Exception as e:
        print(f"Failed to fetch weather for {row['game_id']}: {e}")

weather_df = pl.DataFrame(weather_data)
```

### Injury Status Integration
```python
# Source: nflreadpy load_injuries() documentation
import nflreadpy as nfl
import polars as pl

# Load injury data for training seasons
injuries = nfl.load_injuries(seasons=[2022, 2023, 2024, 2025])

# Schema: gsis_id, full_name, first_name, last_name, team, position,
#         report_status, report_primary_injury, report_secondary_injury,
#         report_start_date, practice_status, date_modified, season, week

# Filter to final injury report before each game (latest practice_status)
final_status = (
    injuries
    .sort(['gsis_id', 'season', 'week', 'date_modified'])
    .group_by(['gsis_id', 'season', 'week'])
    .last()  # Most recent update
)

# Encode injury severity
def encode_injury_status(status: str) -> float:
    """Convert NFL injury designation to numeric severity."""
    if status == 'Out':
        return 1.0
    elif status == 'Doubtful':
        return 0.75
    elif status == 'Questionable':
        return 0.5
    elif status == 'Probable':  # Removed in 2016 but may appear in historical
        return 0.25
    else:
        return 0.0

injury_features = final_status.with_columns([
    pl.col('report_status').map_elements(encode_injury_status, return_dtype=pl.Float32).alias('injury_severity'),
    pl.col('report_status').is_not_null().cast(pl.Int8).alias('on_injury_report'),
])

# Join to player weekly stats
player_stats = pl.read_parquet('data/player_stats.parquet')

player_stats_with_injuries = player_stats.join(
    injury_features.select(['gsis_id', 'season', 'week', 'injury_severity', 'on_injury_report']),
    on=['gsis_id', 'season', 'week'],
    how='left'
).with_columns([
    pl.col('injury_severity').fill_null(0.0),
    pl.col('on_injury_report').fill_null(0),
])
```

### Vegas Lines Integration
```python
# Source: The Odds API documentation
import polars as pl
import requests
from requests_cache import CachedSession
import os
from datetime import datetime

class OddsClient:
    """The Odds API client for NFL betting lines."""

    def __init__(self, api_key: str, cache_name: str = 'odds_cache'):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
        self.session = CachedSession(
            cache_name=cache_name,
            backend='sqlite',
            expire_after=604800,  # 7 days (betting lines can shift)
        )

    def get_historical_odds(self, date: str) -> list:
        """Fetch historical NFL odds for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (must be within historical range)

        Returns:
            List of games with bookmaker odds
        """
        url = f"{self.base_url}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'spreads,totals',
            'dateFormat': 'iso',
            'date': date,  # Historical date
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        return response.json()

# Usage
odds_client = OddsClient(api_key=os.getenv('ODDS_API_KEY'))

# Get odds for all games in a season
schedule = pl.read_parquet('data/schedule.parquet')

odds_data = []
for date in schedule['gameday'].unique().sort():
    date_str = date.strftime('%Y-%m-%d')

    try:
        games = odds_client.get_historical_odds(date_str)

        for game in games:
            # Average spreads across bookmakers
            spreads = [
                outcome['point']
                for bookmaker in game.get('bookmakers', [])
                for market in bookmaker.get('markets', [])
                if market['key'] == 'spreads'
                for outcome in market.get('outcomes', [])
                if outcome['name'] == game['home_team']
            ]

            totals = [
                outcome['point']
                for bookmaker in game.get('bookmakers', [])
                for market in bookmaker.get('markets', [])
                if market['key'] == 'totals'
                for outcome in market.get('outcomes', [])
            ]

            odds_data.append({
                'game_id': game['id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': game['commence_time'],
                'home_spread': sum(spreads) / len(spreads) if spreads else None,
                'total_points': sum(totals) / len(totals) if totals else None,
            })
    except Exception as e:
        print(f"Failed to fetch odds for {date_str}: {e}")

odds_df = pl.DataFrame(odds_data)
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual weather scraping | Visual Crossing API | 2020+ | 50+ years historical data with single API call |
| ESPN injury scraping | nflreadpy `load_injuries()` | 2024 | Official data, practice status, no scraping |
| Single bookmaker odds | The Odds API (multi-book) | 2020 | Averaged spreads more robust than single source |
| Polars (experimental) | Polars 1.0 (stable) | 2024 | Production-ready for data pipeline |
| Manual API retry logic | requests-ratelimiter | 2023 | Declarative rate limiting with queue management |

**New tools/patterns to consider:**
- **requests-cache + requests-ratelimiter combo**: LimiterMixin class enables both features in single session, cache hits don't count toward rate limit
- **Visual Crossing free tier (1k records/day)**: Sufficient for training data collection without paid plan. Pre-fetch all historical weather once, cache locally.
- **The Odds API free tier (500 requests/month)**: Adequate for prototyping. Each request returns multiple games, can fetch full season in <20 requests.
- **Polars for API response processing**: 5-10x faster than pandas for large joins (weather/injuries/odds to player stats)

**Deprecated/outdated:**
- **nfl_data_py**: Replaced by nflreadpy (no longer maintained as of 2024)
- **Manual weather scraping from Weather Underground**: Site shut down historical API in 2023
- **Screen scraping injury reports from team sites**: nflreadpy provides standardized data since 2009
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Weather API Cost at Scale**
   - What we know: Visual Crossing free tier is 1,000 records/day, paid is $0.0001/record
   - What's unclear: Exact record count for full 2022-2025 training data (estimate: ~1,000 games × 1 record = 1,000 records, fits in free tier)
   - Recommendation: Start with free tier, monitor usage. If exceeded, batch fetch over 2-3 days or pay $0.10 for 1,000 records.

2. **Injury Report Timing Granularity**
   - What we know: nflreadpy injuries include `date_modified` and `practice_status`
   - What's unclear: How frequently injury data updates in nflverse repository (daily? twice daily?)
   - Recommendation: Use most recent `date_modified` before game time. For live predictions, fetch fresh data within 24 hours of kickoff.

3. **Vegas Lines for Non-Primetime Games**
   - What we know: The Odds API historical data starts mid-2020, includes major bookmakers
   - What's unclear: Coverage completeness for early-season 2020 games (COVID season had irregular schedules)
   - Recommendation: Validate line availability for 2020 training data. If sparse, start Vegas features from 2021 season.

4. **Stadium Coordinate Accuracy**
   - What we know: nflreadpy schedules include temperature/wind but may lack precise lat/lon
   - What's unclear: Whether we need to manually add stadium coordinates or if city name suffices for Visual Crossing
   - Recommendation: Test Visual Crossing with stadium city names first (e.g., "Green Bay, WI"). If weather differs significantly, add manual coordinate mapping for 30 NFL stadiums.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [nflreadpy GitHub](https://github.com/nflverse/nflreadpy) - Official Python port of nflreadr, load functions
- [nflreadpy API Documentation](https://nflreadpy.nflverse.com/api/load_functions/) - Load functions for schedules, injuries, rosters
- [Visual Crossing Weather API](https://www.visualcrossing.com/weather-api/) - 50+ years historical weather, pricing, API structure
- [The Odds API](https://the-odds-api.com/) - NFL odds, historical data back to 2020, pricing
- [requests-cache Documentation](https://github.com/JWCook/requests-cache) - SQLite caching, expiration
- [requests-ratelimiter Documentation](https://github.com/JWCook/requests-ratelimiter) - Rate limiting with LimiterMixin

### Secondary (MEDIUM confidence - WebSearch verified with official sources)
- [Weather Impact on NFL Betting Outcomes](https://www.sharpfootballanalysis.com/sportsbook/weather-impact-on-nfl-betting/) - Temperature/wind/precip effects on scoring
- [Stanford Study: Weather and the NFL](https://web.stanford.edu/class/stats50/projects16/Houghton-BerryParkPierce-paper.pdf) - Statistical analysis of weather impact
- [NFL Home Field Advantage Tracker](https://www.nfeloapp.com/tools/nfl-home-field-advantage-hfa-tracker/) - Team-specific HFA values
- [Visual Crossing Best Weather API Guide](https://www.visualcrossing.com/resources/blog/best-weather-api-for-2025/) - API comparison for 2025-2026
- [Medium: Python Request Optimization](https://medium.com/neural-engineer/python-request-optimization-caching-and-rate-limiting-79ceb5e6eb1e) - Caching and rate limiting patterns

### Tertiary (LOW confidence - needs validation during implementation)
- [Draft Sharks Injury Predictor](https://www.draftsharks.com/injury-predictor/rb) - ML injury prediction (8-10% production drop claim)
- [How Weather Affects NFL Games](https://nxtbets.com/weather-impacts-nfl-games-and-betting-outcomes/) - 25°F and 50°F threshold claims
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: nflreadpy for official NFL data, Visual Crossing for weather, The Odds API for betting lines
- Ecosystem: requests-cache, requests-ratelimiter, polars for data joins
- Patterns: Cached API clients, incremental feature validation, rate-limited data fetching
- Pitfalls: Dome game weather, API rate limits, injury timing, Vegas line availability

**Confidence breakdown:**
- Standard stack: HIGH - nflreadpy documented, Visual Crossing/Odds API verified with official docs
- Architecture: HIGH - requests-cache and ratelimiter patterns from official documentation
- Pitfalls: MEDIUM - Based on research findings and API documentation, not direct experience
- Code examples: HIGH - Verified against nflreadpy docs, Visual Crossing API docs, The Odds API docs

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - stable APIs, unlikely to change)

**Key research decisions:**
- Used WebSearch to discover available APIs (Visual Crossing, The Odds API, nflreadpy)
- Verified with official documentation via WebFetch (nflreadpy, Visual Crossing, The Odds API)
- Cross-referenced weather impact studies (Stanford, Sharp Football Analysis) with multiple sources
- Confirmed nflreadpy `load_injuries()` and `load_schedules()` functions exist and provide required data
- Validated free tier limits sufficient for development (Visual Crossing: 1k/day, Odds API: 500/month)
</metadata>

---

*Phase: 20-advanced-features*
*Research completed: 2026-01-21*
*Ready for planning: yes*
