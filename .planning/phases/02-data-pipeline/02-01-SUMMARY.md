---
phase: 02-data-pipeline
plan: 01
subsystem: data
tags: [nflreadpy, polars, python, data-fetching]

# Dependency graph
requires:
  - phase: 01-foundation plan 02
    provides: Python ML backend package structure with nflreadpy installed
provides:
  - Data fetcher module with typed functions for NFL data
  - fetch_player_stats() for weekly/seasonal player stats (114 columns)
  - fetch_schedules() for game schedules with weather/venue data
  - fetch_snap_counts() for snap participation data
  - filter_skill_positions() utility for skill position filtering
  - SKILL_POSITIONS constant for QB/RB/WR/TE
affects: [02-data-pipeline plans 02-04, 05-model-development]

# Tech tracking
tech-stack:
  added: [polars]
  patterns: [nflreadpy-wrapper-functions, typed-dataframe-returns]

key-files:
  created:
    - packages/backend/src/lineupiq/data/__init__.py
    - packages/backend/src/lineupiq/data/fetchers.py
    - packages/backend/tests/test_fetchers.py
  modified: []

key-decisions:
  - "Return Polars DataFrames natively (no pandas conversion) for performance"
  - "Use SeasonList type alias for consistent seasons parameter handling"
  - "Include comprehensive docstrings with arg/return documentation"

patterns-established:
  - "Data fetcher pattern: wrap nflreadpy with logging and error handling"
  - "Polars-first approach: return Polars, let callers convert if needed"

# Metrics
duration: 3min
completed: 2026-01-14
---

# Phase 02 Plan 01: NFLreadpy Data Fetcher Module Summary

**Data fetcher module with typed functions for player stats (114 cols), schedules, and snap counts returning Polars DataFrames, plus skill position filter utility**

## Performance

- **Duration:** 3 min 7 sec
- **Started:** 2026-01-14T21:20:06Z
- **Completed:** 2026-01-14T21:23:13Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments

- Created data subpackage (lineupiq.data) with clean public API
- Implemented fetch_player_stats() returning 114-column Polars DataFrame
- Implemented fetch_schedules() with weather columns (temp, wind, roof)
- Implemented fetch_snap_counts() for snap participation data
- Added filter_skill_positions() utility returning only QB/RB/WR/TE rows
- Exported SKILL_POSITIONS frozenset constant
- Added comprehensive integration tests (13 tests, all passing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create data fetcher module with typed interfaces** - `dd48315` (feat)
2. **Task 2: Add position filtering utility** - (included in Task 1 commit - implemented together)
3. **Task 3: Add basic test coverage** - `e02ea0d` (test)

## Files Created/Modified

- `packages/backend/src/lineupiq/data/__init__.py` - Public API exports for data module
- `packages/backend/src/lineupiq/data/fetchers.py` - Fetcher functions and utilities
- `packages/backend/tests/test_fetchers.py` - Integration tests for all fetchers

## Decisions Made

1. **Return Polars DataFrames natively** - nflreadpy returns Polars, keeping it avoids unnecessary conversion overhead. Callers can use .to_pandas() if needed.
2. **SeasonList type alias** - Consistent typing for the seasons parameter pattern across all fetch functions (None/True/int/list[int]).
3. **Comprehensive docstrings** - Each function documents args, returns, raises, and examples for IDE support.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect nflreadpy parameter name**
- **Found during:** Task 1 verification
- **Issue:** Used `stat_type` parameter instead of correct `summary_level`
- **Fix:** Changed to `summary_level` matching nflreadpy API
- **Files modified:** packages/backend/src/lineupiq/data/fetchers.py
- **Verification:** fetch_player_stats([2024]) returns (18981, 114)
- **Committed in:** dd48315 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix was necessary for correct operation. No scope creep.

## Issues Encountered

None - all verifications passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Data fetcher module complete and tested
- All three fetch functions verified working with 2024 data
- filter_skill_positions ready for use in feature engineering
- Ready for plan 02-02 (Parquet storage/caching)

---
*Phase: 02-data-pipeline*
*Completed: 2026-01-14*
