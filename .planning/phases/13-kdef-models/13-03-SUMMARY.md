---
phase: 13-kdef-models
plan: 03
subsystem: data
tags: [kicker, defense, nflreadpy, polars, rolling-features]

# Dependency graph
requires:
  - phase: 02-data-pipeline
    provides: fetchers.py pattern, fetch_schedules
provides:
  - fetch_kicker_stats for K position data
  - fetch_team_defense_stats for team defense data
  - process_kicker_data for kicker ML features
  - process_defense_data for defense ML features
  - FG distance bucket aggregations (0-39, 40-49, 50+)
  - Rolling 3-week features for K/DEF
affects: [13-05-kicker-models, 13-06-defense-models]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - K/DEF data pipelines follow existing player processing pattern
    - Rolling features use shift(1) to prevent data leakage
    - Team defense uses schedule join for points_allowed

key-files:
  created:
    - packages/backend/src/lineupiq/data/kicker_processing.py
    - packages/backend/src/lineupiq/data/defense_processing.py
  modified:
    - packages/backend/src/lineupiq/data/fetchers.py
    - packages/backend/src/lineupiq/data/__init__.py

key-decisions:
  - "Team defense uses schedule join for points_allowed (not team_stats)"
  - "FG attempts bucketed to match ESPN scoring (0-39, 40-49, 50+)"

patterns-established:
  - "K/DEF data processing follows same structure as skill position processing"

# Metrics
duration: 4min
completed: 2026-01-15
---

# Phase 13 Plan 03: K/DEF Data Pipeline Summary

**Kicker and team defense data pipelines with rolling 3-week features and FG distance buckets matching ESPN scoring**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-15T15:36:43Z
- **Completed:** 2026-01-15T15:40:33Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Created `fetch_kicker_stats()` that filters player stats to K position (569 rows for 2024)
- Created `fetch_team_defense_stats()` that loads team-level defensive stats (570 rows for 2024)
- Built kicker processing pipeline with FG attempts by distance bucket (0-39, 40-49, 50+)
- Built defense processing pipeline that joins schedules for points_allowed
- Added rolling 3-week features for both K and DEF with proper shift to prevent leakage

## Task Commits

Each task was committed atomically:

1. **Task 1: Add kicker data fetcher to fetchers.py** - `25ba39a` (feat)
2. **Task 2: Create kicker_processing.py module** - `b87f004` (feat)
3. **Task 3: Create defense_processing.py module** - `10b0b7e` (feat)
4. **Task 4: Export new modules from data package** - `0fa3cb9` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/data/fetchers.py` - Added fetch_kicker_stats() and fetch_team_defense_stats()
- `packages/backend/src/lineupiq/data/kicker_processing.py` - Kicker data processing with FG distance buckets
- `packages/backend/src/lineupiq/data/defense_processing.py` - Team defense processing with points_allowed join
- `packages/backend/src/lineupiq/data/__init__.py` - Updated exports and docstring

## Decisions Made

- **Team defense uses schedule join for points_allowed:** The nflreadpy `load_team_stats` doesn't directly provide points allowed, so we compute it from schedule home_score/away_score
- **FG attempts bucketed by distance:** Matches ESPN scoring granularity (0-39=3pts, 40-49=4pts, 50+=5pts)
- **Rolling features use shift(1):** Prevents data leakage by only using prior game data

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Polars API: min_periods -> min_samples**
- **Found during:** Task 2 (kicker_processing.py creation)
- **Issue:** Plan used `min_periods` parameter but Polars uses `min_samples`
- **Fix:** Changed `rolling_mean(window_size=3, min_periods=1)` to `rolling_mean(window_size=3, min_samples=1)`
- **Files modified:** kicker_processing.py
- **Verification:** mypy passes, runtime works
- **Committed in:** b87f004 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking API mismatch)
**Impact on plan:** Minor parameter name correction. No scope change.

## Issues Encountered

None - plan executed successfully after API parameter fix.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- K/DEF data pipelines ready for model training (Plans 13-05, 13-06)
- Kicker pipeline produces 28 columns including 3 features and 5 targets
- Defense pipeline produces 9 columns including 5 features and 5 targets
- Both pipelines verified working with 2024 data

---
*Phase: 13-kdef-models*
*Completed: 2026-01-15*
