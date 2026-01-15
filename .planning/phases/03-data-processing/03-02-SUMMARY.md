---
phase: 03-data-processing
plan: 02
subsystem: data
tags: [polars, normalization, nfl-data, team-mapping, player-id]

# Dependency graph
requires:
  - phase: 02-data-pipeline
    provides: Raw NFL data fetching and Parquet storage
  - phase: 03-01
    provides: Data cleaning pipeline (clean_player_stats, clean_schedules)
provides:
  - TEAM_MAPPING dict for historical team relocations
  - CURRENT_TEAMS frozenset with all 32 NFL teams
  - normalize_team and normalize_team_columns for team standardization
  - standardize_player_id with player_key for case-insensitive matching
  - normalize_position for FB->RB and case normalization
  - normalize_player_data orchestrator for full pipeline
affects: [04-feature-engineering, 05-model-development]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Team abbreviation mapping for historical relocations
    - Player ID standardization with lowercase player_key
    - Position normalization with FB->RB grouping

key-files:
  created:
    - packages/backend/src/lineupiq/data/normalization.py
    - packages/backend/tests/test_normalization.py
  modified:
    - packages/backend/src/lineupiq/data/__init__.py

key-decisions:
  - "Map historical teams to current: OAK->LV, STL->LA, SD->LAC, PHO->ARI"
  - "Group fullbacks with running backs (FB->RB) for fantasy purposes"
  - "Create player_key as lowercase player_id for case-insensitive matching"

patterns-established:
  - "normalize_team_columns uses replace_strict with default for unmapped values"
  - "normalize_player_data orchestrates team -> player_id -> position pipeline"

# Metrics
duration: 3 min
completed: 2026-01-15
---

# Phase 3 Plan 2: Player and Team ID Normalization Summary

**Team abbreviation mapping for NFL relocations (OAK->LV, STL->LA, SD->LAC) with player ID standardization and position normalization (FB->RB) using Polars expressions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-15T00:08:59Z
- **Completed:** 2026-01-15T00:11:51Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created normalization.py module with TEAM_MAPPING for historical team relocations
- Added CURRENT_TEAMS frozenset with all 32 NFL team abbreviations
- Implemented normalize_team and normalize_team_columns for team standardization
- Added standardize_player_id with player_key for case-insensitive matching
- Implemented normalize_position with uppercase conversion and FB->RB grouping
- Created normalize_player_data orchestrator combining all normalizations
- Added 19 comprehensive tests covering all normalization functions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create team abbreviation normalization** - `5051a0d` (feat)
2. **Task 2: Add player ID and position normalization** - `0237fcb` (feat)
3. **Task 3: Update exports and add tests** - `efc607d` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/data/normalization.py` - Team and player normalization functions
- `packages/backend/tests/test_normalization.py` - 19 tests for all normalization functions
- `packages/backend/src/lineupiq/data/__init__.py` - Updated exports to include normalization module

## Decisions Made

- **Historical team mapping:** OAK->LV (2020), STL->LA (2016), SD->LAC (2017), PHO->ARI
- **Fullback grouping:** FB->RB for fantasy purposes (fullbacks grouped with running backs)
- **Player key:** Lowercase player_id as player_key enables case-insensitive matching

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Polars deprecation warning**
- **Found during:** Task 3 (test execution)
- **Issue:** `replace` with `default` parameter is deprecated in Polars 1.0.0
- **Fix:** Changed to `replace_strict` with `default` parameter
- **Files modified:** packages/backend/src/lineupiq/data/normalization.py
- **Verification:** Tests pass without deprecation warnings
- **Committed in:** efc607d (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor fix to use non-deprecated Polars API. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Normalization module ready for feature engineering phase
- Team columns in historical data will map to current team abbreviations
- Player IDs standardized with player_key for case-insensitive joins
- Position normalization groups FB with RB for fantasy analysis
- All 19 tests passing, module exports complete

---
*Phase: 03-data-processing*
*Completed: 2026-01-15*
