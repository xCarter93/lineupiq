---
phase: 04-feature-engineering
plan: 01
subsystem: features
tags: [polars, rolling-stats, feature-engineering, ml-features, nfl-data]

# Dependency graph
requires:
  - phase: 03-data-processing
    provides: process_player_stats for ML-ready data with game context
provides:
  - compute_rolling_stats: Rolling window averages for passing/rushing/receiving stats
  - Per-player rolling computation with configurable window size
affects: [05-model-development, 04-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Polars rolling_mean with over() for per-player grouped rolling
    - min_samples=1 for early season players with fewer games
    - Feature columns named with _roll{window} suffix convention

key-files:
  created:
    - packages/backend/src/lineupiq/features/__init__.py
    - packages/backend/src/lineupiq/features/rolling_stats.py
    - packages/backend/tests/test_rolling_stats.py
  modified: []

key-decisions:
  - "Use min_samples=1 to handle players with fewer than window games"
  - "Group rolling computation by player_id to ensure per-player history"
  - "Sort by player_id, season, week before computing for correct ordering"

patterns-established:
  - "Features module for ML feature engineering utilities"
  - "Suffix rolling columns with _roll{window} for clarity"

# Metrics
duration: 3 min
completed: 2026-01-15
---

# Phase 4 Plan 1: Rolling Window Stats Summary

**Polars-based rolling window statistics module computing 3-week rolling averages for passing/rushing/receiving stats per player with min_samples=1 for early season handling**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-15T00:25:23Z
- **Completed:** 2026-01-15T00:28:25Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created features/ module structure for ML feature engineering
- Implemented compute_rolling_stats() with configurable window parameter
- Computes rolling means for 8 stat columns: passing_yards, passing_tds, interceptions, rushing_yards, rushing_tds, carries, receiving_yards, receiving_tds, receptions
- Uses Polars over() with partition_by for efficient per-player rolling
- 10 unit tests covering calculation correctness, per-player grouping, min_samples handling, and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Create rolling_stats module with position-specific rolling averages** - `989e817` (feat)
2. **Task 2: Add unit tests for rolling stats** - `c39b5a4` (test)

## Files Created/Modified

- `packages/backend/src/lineupiq/features/__init__.py` - Features module exports
- `packages/backend/src/lineupiq/features/rolling_stats.py` - Rolling stats computation with compute_rolling_stats()
- `packages/backend/tests/test_rolling_stats.py` - 10 unit tests for rolling stats

## Decisions Made

- **min_samples=1:** Handle players with fewer than window games (early season, new players). Using actual games played is more accurate than filling with zeros.
- **Per-player grouping:** Rolling stats computed per player_id, not globally. Player's week 3 rolling avg only includes their weeks 1-2.
- **Sort before rolling:** Sort by player_id, season, week to ensure correct chronological ordering for rolling window computation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Polars API deprecation**
- **Found during:** Task 2 (running tests)
- **Issue:** Polars 1.21+ renamed `min_periods` parameter to `min_samples` causing deprecation warnings
- **Fix:** Updated rolling_mean() call to use min_samples=1
- **Files modified:** packages/backend/src/lineupiq/features/rolling_stats.py
- **Verification:** All tests pass without deprecation warnings
- **Committed in:** c39b5a4 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor API compatibility fix. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Rolling stats module complete and tested
- compute_rolling_stats() adds 8 rolling columns for key stats
- Per-player grouping ensures correct rolling window computation
- Ready for 04-02 (opponent defensive strength metrics)

---
*Phase: 04-feature-engineering*
*Completed: 2026-01-15*
