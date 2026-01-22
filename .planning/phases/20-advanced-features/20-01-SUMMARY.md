---
phase: 20-advanced-features
plan: 01
subsystem: ml-features
tags: [weather, visual-crossing, polars, feature-engineering, lightgbm]

# Dependency graph
requires:
  - phase: 04-feature-engineering
    provides: Basic weather features (temp_normalized, wind_normalized, is_dome)
  - phase: 13-all-positions
    provides: Feature pipeline architecture with rolling stats and opponent features
provides:
  - Detailed weather feature engineering with research-backed thresholds
  - Visual Crossing Weather API integration with caching and rate limiting
  - 7 new weather features (extreme_cold, freezing, extreme_heat, high_wind, very_high_wind, has_precip, precip_amount)
  - Graceful degradation without API key
affects: [21-model-retraining, training-workflows]

# Tech tracking
tech-stack:
  added: [requests-cache, requests-ratelimiter, python-dotenv]
  patterns: [cached-api-client, research-backed-thresholds, graceful-degradation]

key-files:
  created:
    - packages/backend/src/lineupiq/data/weather_cache.py
    - packages/backend/src/lineupiq/features/weather.py
    - packages/backend/tests/test_weather_features.py
  modified:
    - packages/backend/pyproject.toml
    - packages/backend/src/lineupiq/features/pipeline.py

key-decisions:
  - "Use Visual Crossing Weather API with free tier (1,000 records/day sufficient for training data)"
  - "Research-backed thresholds: <25°F extreme cold, <32°F freezing, >85°F extreme heat, >=15mph high wind"
  - "Dome games set to neutral values (72°F, 0 wind, no precip) to avoid noise"
  - "Mean imputation for missing outdoor weather from other outdoor games"
  - "Graceful degradation: skip detailed features if VISUAL_CROSSING_API_KEY missing"

patterns-established:
  - "CachedLimiterSession pattern: combine requests-cache + requests-ratelimiter for external APIs"
  - "Weather feature engineering: fill dome games first, then mean-fill missing outdoor values"
  - "Test-driven feature development: 9 comprehensive tests covering all edge cases"

# Metrics
duration: 18min
completed: 2026-01-21
---

# Phase 20 Plan 01: Advanced Features - Weather Summary

**Expanded weather features from basic temp/wind to detailed conditions with Visual Crossing API integration, research-backed thresholds (freezing <32°F, high wind >15mph), and 7 new ML features**

## Performance

- **Duration:** 18 min
- **Started:** 2026-01-21T18:45:00Z
- **Completed:** 2026-01-21T19:03:00Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- Integrated Visual Crossing Weather API with SQLite caching and rate limiting (10 req/sec, 1000/day)
- Created detailed weather feature engineering with research-backed thresholds (temperatures <25°F, <32°F, >85°F; wind >=15mph, >=20mph; precipitation detection)
- Expanded weather features from 3 to 10 total (7 new: extreme_cold, freezing, extreme_heat, high_wind, very_high_wind, has_precip, precip_amount)
- Dome games handled correctly with neutral values (72°F, 0 wind, no precip)
- Comprehensive test suite (9 tests) validates feature engineering logic
- Graceful degradation when VISUAL_CROSSING_API_KEY missing

## Task Commits

Each task was committed atomically:

1. **Task 1: Install weather API dependencies and create cached client** - `1e0d32c` (chore)
2. **Task 2: Create detailed weather feature engineering module** - `56609b0` (feat)
3. **Task 3: Integrate detailed weather features into pipeline** - `61f76c6` (feat)

## Files Created/Modified

- `packages/backend/pyproject.toml` - Added requests-cache, requests-ratelimiter, python-dotenv, polars dependencies
- `packages/backend/src/lineupiq/data/weather_cache.py` - WeatherClient class with Visual Crossing API integration, SQLite caching, rate limiting
- `packages/backend/src/lineupiq/features/weather.py` - engineer_weather_features() with research-backed thresholds, dome/outdoor handling, mean imputation
- `packages/backend/src/lineupiq/features/pipeline.py` - Updated build_features() to integrate detailed weather, updated get_feature_columns() to include 7 new features
- `packages/backend/tests/test_weather_features.py` - 9 comprehensive tests covering all feature engineering scenarios

## Decisions Made

**Visual Crossing Weather API:**
- Selected for 50+ years historical data, free tier sufficient for training (1,000 records/day)
- CachedLimiterSession pattern combines caching + rate limiting in single session
- SQLite cache with 30-day expiration (historical weather doesn't change)

**Research-backed thresholds:**
- extreme_cold (<25°F): 10-15% passing efficiency drop per research
- freezing (<32°F): Significant impact on ball handling
- extreme_heat (>85°F): Player fatigue increases
- high_wind (>=15mph): 6% completion rate drop per research
- very_high_wind (>=20mph): Major impact on passing game

**Dome game handling:**
- Set to neutral values (72°F, 0 wind, 0 precip) to avoid noise
- Prevents wasted API calls fetching irrelevant outdoor weather

**Graceful degradation:**
- Feature pipeline checks for VISUAL_CROSSING_API_KEY env var
- Skips detailed features if key missing, logs warning
- Allows development/testing without API key

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

**External services require manual configuration.** See [20-USER-SETUP.md](./20-USER-SETUP.md) for:
- Environment variables to add (VISUAL_CROSSING_API_KEY)
- Account setup steps (create free Visual Crossing account)
- Verification commands (test WeatherClient import)

## Next Phase Readiness

- Weather features ready for model retraining (Phase 21)
- API integration tested with graceful degradation
- Comprehensive test suite ensures feature engineering correctness
- Free tier sufficient for development and training data collection

---
*Phase: 20-advanced-features*
*Completed: 2026-01-21*
