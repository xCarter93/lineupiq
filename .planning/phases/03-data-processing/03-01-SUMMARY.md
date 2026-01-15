---
phase: 03-data-processing
plan: 01
subsystem: data
tags: [polars, cleaning, validation, nfl-data]

# Dependency graph
requires:
  - phase: 02-data-pipeline
    provides: Raw NFL data fetching and Parquet storage
provides:
  - clean_player_stats function for validated, cleaned player data
  - clean_schedules function with is_dome normalization
  - validate_player_stats, clean_numeric_stats, select_ml_columns granular functions
affects: [04-feature-engineering, 05-model-development]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Polars-based data cleaning pipeline
    - Null handling with fill_null(0) for stats
    - Outlier capping for unrealistic values
    - is_dome boolean normalization from roof column

key-files:
  created:
    - packages/backend/src/lineupiq/data/cleaning.py
    - packages/backend/tests/test_cleaning.py
  modified:
    - packages/backend/src/lineupiq/data/__init__.py

key-decisions:
  - "Cap yards at 600 (NFL single-game record ~550)"
  - "Cap TDs at 8 per game (conservative outlier boundary)"
  - "Default dome temp/wind to 65/5 when null"
  - "Normalize roof to is_dome boolean (dome/closed -> True)"

patterns-established:
  - "Validation -> Clean -> Select column pipeline pattern"
  - "Per-function logging with row count tracking"

# Metrics
duration: 3 min
completed: 2026-01-15
---

# Phase 3 Plan 1: Data Cleaning and Validation Summary

**Polars-based data cleaning pipeline with validation, null handling, outlier capping, and ML column selection for player stats and schedules**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-15T00:03:02Z
- **Completed:** 2026-01-15T00:06:42Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created cleaning.py module with validate_player_stats, clean_numeric_stats, select_ml_columns, and clean_player_stats orchestrator
- Added clean_schedules function with is_dome normalization and weather defaults for dome games
- Exported all cleaning functions from data module
- Created comprehensive test suite with 15 passing tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cleaning module with core validation functions** - `338194d` (feat)
2. **Task 2: Add schedule data cleaning function** - `af76f59` (feat)
3. **Task 3: Update exports and add basic tests** - `b2f1290` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/data/cleaning.py` - Core cleaning functions for player stats and schedules
- `packages/backend/tests/test_cleaning.py` - 15 tests for validation, cleaning, and scheduling
- `packages/backend/src/lineupiq/data/__init__.py` - Updated exports to include cleaning functions

## Decisions Made

- **Outlier caps:** 600 yards (NFL record ~550), 8 TDs per game - conservative boundaries to catch data errors
- **Null handling:** Fill stat nulls with 0 (reasonable for fantasy stats), preserve weather nulls for outdoor games
- **is_dome normalization:** "dome" and "closed" roof values -> True, enables weather feature logic
- **Default dome weather:** 65F temp, 5 mph wind when null - indoor conditions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Cleaning module ready for feature engineering phase
- clean_player_stats returns 19 ML-relevant columns from 114 raw columns
- clean_schedules provides is_dome boolean for weather feature logic
- All tests passing, module exports complete

---
*Phase: 03-data-processing*
*Completed: 2026-01-15*
