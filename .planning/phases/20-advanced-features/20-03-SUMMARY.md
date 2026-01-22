---
phase: 20-advanced-features
plan: 03
subsystem: ml-features
tags: [vegas-lines, odds-api, matchup-features, polars, requests-cache]

# Dependency graph
requires:
  - phase: 20-01
    provides: requests-cache, requests-ratelimiter for API caching
  - phase: 04-feature-engineering
    provides: Feature pipeline infrastructure
provides:
  - OddsClient with SQLite caching for The Odds API
  - engineer_matchup_features() for Vegas lines and divisional games
  - 5 matchup features in ML pipeline (home_spread, total_points, vegas_strength_diff, home_favored, is_divisional)
affects: [21-model-retraining, training, feature-engineering]

# Tech tracking
tech-stack:
  added: [The Odds API integration, OddsClient class]
  patterns: [Vegas line averaging across bookmakers, neutral fills for pre-2020 games, graceful degradation without API key]

key-files:
  created:
    - packages/backend/src/lineupiq/data/odds_cache.py
    - packages/backend/src/lineupiq/features/matchup.py
    - packages/backend/tests/test_matchup_features.py
  modified:
    - packages/backend/src/lineupiq/features/pipeline.py
    - packages/backend/tests/test_feature_pipeline.py

key-decisions:
  - "7-day cache expiration for Vegas lines (lines can shift during week)"
  - "Neutral fills for pre-2020 games: home_spread=0.0, total_points=45.0 (NFL average)"
  - "Divisional flag works without API key (uses nflreadpy teams data)"
  - "Average spreads/totals across bookmakers for market consensus"

patterns-established:
  - "Graceful degradation pattern: divisional flag added even without ODDS_API_KEY"
  - "Neutral value pattern: pre-2020 games without odds get 0.0 spread, 45.0 total"
  - "Market consensus pattern: average Vegas lines across all available bookmakers"

# Metrics
duration: 45min
completed: 2026-01-21
---

# Phase 20-03: Advanced Features Summary

**Vegas betting lines (spreads, totals) and divisional game detection integrated into ML pipeline with graceful degradation**

## Performance

- **Duration:** 45 min
- **Started:** 2026-01-21T[execution-start]
- **Completed:** 2026-01-21T[execution-end]
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- The Odds API integration with OddsClient class (500 free requests/month)
- 5 matchup features added to pipeline: home_spread, total_points, vegas_strength_diff, home_favored, is_divisional
- Graceful degradation: divisional flag works without API key, pre-2020 games get neutral fills
- All tests passing (7 new matchup feature tests, 18 pipeline tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cached Odds API client** - `072e4c9` (feat)
2. **Task 2: Create matchup feature engineering module** - `f4b8689` (feat)
3. **Task 3: Integrate matchup features into pipeline** - `dfed9f9` (feat)

## Files Created/Modified
- `packages/backend/src/lineupiq/data/odds_cache.py` - OddsClient with caching for The Odds API
- `packages/backend/src/lineupiq/features/matchup.py` - engineer_matchup_features() with Vegas lines and divisional flags
- `packages/backend/tests/test_matchup_features.py` - 7 tests for Vegas line joins, home favored logic, missing odds handling, divisional detection
- `packages/backend/src/lineupiq/features/pipeline.py` - Step 7 added for matchup features, graceful degradation when ODDS_API_KEY missing
- `packages/backend/tests/test_feature_pipeline.py` - Fixed pre-existing test bug (window=5 test)

## Decisions Made

1. **7-day cache expiration for Vegas lines** - Betting lines can shift during the week leading up to games, so 7-day expiration balances freshness with API usage efficiency
2. **Neutral fills for pre-2020 games** - The Odds API only has historical data from mid-2020, so pre-2020 games get home_spread=0.0 (neutral) and total_points=45.0 (NFL average)
3. **Average spreads/totals across bookmakers** - Market consensus approach: average all available bookmaker lines to reduce single-source bias
4. **Divisional flag independent of API key** - Uses nflreadpy teams data (free), so divisional game detection works even without ODDS_API_KEY

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Testing] Fixed pre-existing test bug in test_feature_pipeline.py**
- **Found during:** Task 3 (Pipeline integration testing)
- **Issue:** test_window_5_creates_roll5_columns had contradictory assertions - checked for roll5 columns, then asserted they shouldn't exist (copy-paste error)
- **Fix:** Changed second assertion to check for absence of roll3 columns (old default) instead of roll5
- **Files modified:** packages/backend/tests/test_feature_pipeline.py
- **Verification:** All 18 pipeline tests passing
- **Committed in:** dfed9f9 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 testing fix)
**Impact on plan:** Test fix was necessary for correctness - pre-existing bug, not introduced by this plan. No scope creep.

## Issues Encountered
None - plan executed smoothly with all tests passing.

## User Setup Required

**External services require manual configuration.** Users need to:
1. Sign up for The Odds API free tier at https://the-odds-api.com/#get-access
2. Get API key from dashboard
3. Add to `.env`: `ODDS_API_KEY=your_key_here`

**Note:** Pipeline works without ODDS_API_KEY (divisional flag still added), but Vegas spreads/totals require the key. Free tier provides 500 requests/month, sufficient for prototyping.

## Next Phase Readiness
- Matchup features (5 columns) ready for model training
- Vegas lines provide market efficiency signal (research: +2.5-3 points home field advantage)
- Divisional games identified for all seasons (not just 2020+)
- Pipeline handles missing odds gracefully (neutral fills)
- Ready for Phase 21: Model retraining with expanded feature set

---
*Phase: 20-advanced-features*
*Completed: 2026-01-21*
