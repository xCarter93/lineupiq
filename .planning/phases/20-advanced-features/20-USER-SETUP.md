# Phase 20: User Setup Required

**Generated:** 2026-01-21
**Phase:** 20-advanced-features
**Status:** Incomplete

This phase introduced external services requiring manual configuration before the integration can function.

## Service: Visual Crossing Weather API

**Purpose:** Historical weather data for NFL game conditions

**Why needed:** Provides 50+ years of historical weather data (temperature, wind, precipitation) for improving ML model accuracy on weather-sensitive positions (QB, WR).

---

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `VISUAL_CROSSING_API_KEY` | Visual Crossing Dashboard → Account → API Keys section | `.env` (backend root) |

**How to add:**

1. Create `.env` file in `packages/backend/` directory if it doesn't exist
2. Add the line: `VISUAL_CROSSING_API_KEY=your_api_key_here`
3. The API key will be automatically loaded by WeatherClient using python-dotenv

---

## Account Setup

- [ ] **Create Visual Crossing account**
  - URL: https://www.visualcrossing.com/sign-up
  - Skip if: Already have Visual Crossing account
  - Free tier: 1,000 records/day (sufficient for full 2022-2025 training data)

- [ ] **Get API key**
  - URL: https://www.visualcrossing.com/account
  - Navigate to: API Keys section
  - Copy your API key

---

## Local Development

**Free tier limits:**
- 1,000 records per day (sufficient for full training data collection)
- 10 requests per second (burst handling)

**Caching:**
- SQLite cache with 30-day expiration for historical data
- Cache hits don't count toward API quota
- Pre-fetch all historical weather once, reuse for all training runs

**Testing without API key:**
- Feature pipeline gracefully degrades if `VISUAL_CROSSING_API_KEY` is missing
- Will log warning and skip detailed weather features
- Basic weather features (temp_normalized, wind_normalized, is_dome) still work from nflreadpy schedules

---

## Verification

After completing setup, verify the integration works:

```bash
# Test 1: Verify WeatherClient can be imported
cd packages/backend
uv run python -c "from lineupiq.data.weather_cache import WeatherClient; print('✓ WeatherClient imported successfully')"

# Test 2: Verify API key is loaded (optional - requires actual API key)
uv run python -c "from lineupiq.data.weather_cache import WeatherClient; client = WeatherClient(); print('✓ API key loaded successfully')"

# Test 3: Verify feature pipeline includes detailed weather
uv run python -c "from lineupiq.features.pipeline import get_feature_columns; cols = get_feature_columns(); weather_cols = [c for c in cols if 'weather' in str(c).lower() or c in ['extreme_cold', 'freezing', 'extreme_heat', 'high_wind', 'very_high_wind', 'has_precip', 'precip_amount', 'temp_normalized', 'wind_normalized', 'is_dome']]; print(f'✓ Feature pipeline includes {len(weather_cols)} weather features')"

# Test 4: Run weather feature tests
uv run pytest tests/test_weather_features.py -v
```

**Expected results:**
- Test 1: ✓ WeatherClient imported successfully
- Test 2: ✓ API key loaded successfully (or error if key invalid)
- Test 3: ✓ Feature pipeline includes 10 weather features
- Test 4: 9 passed tests

---

## Troubleshooting

**Error: "Visual Crossing API key required"**
- Make sure `.env` file exists in `packages/backend/` directory
- Verify `VISUAL_CROSSING_API_KEY` is set in `.env`
- Check that there are no extra spaces or quotes around the API key

**Warning: "VISUAL_CROSSING_API_KEY not found - skipping detailed weather features"**
- This is expected if you haven't set up the API key yet
- Feature pipeline will work but without detailed weather features
- Set up API key following instructions above to enable detailed features

**Error: HTTP 401 or 403 from Visual Crossing API**
- API key is invalid or expired
- Get a new API key from https://www.visualcrossing.com/account

**Error: HTTP 429 from Visual Crossing API**
- Rate limit exceeded (1,000 records/day on free tier)
- Wait until next day or upgrade to paid tier
- Check SQLite cache is working (should prevent repeat API calls)

---

**Once all items complete:** Mark status as "Complete" at the top of this file
