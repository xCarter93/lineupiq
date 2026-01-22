# Phase 20 Plan 02: Injury Features Summary

**Completed:** 2026-01-21
**Duration:** 8 min
**Type:** execute
**Status:** ✅ Complete

## One-line Summary

Added injury status features using nflreadpy official injury reports, encoding NFL designations (Out, Doubtful, Questionable, Probable) into injury_severity (0.0-1.0) and on_injury_report (0/1) columns for 8-10% production impact modeling.

## Objective

Add injury status features using nflreadpy's official injury reports to capture 8-10% production impact from injury designations.

Purpose: Improve prediction accuracy for injured players by encoding NFL injury designations into numeric severity features.
Output: Injury feature module integrating nflreadpy load_injuries() data with player-week features, adding injury_severity and on_injury_report columns to ML pipeline.

## Tasks Completed

### Task 1: Add injury data fetching to data layer ✅
- **Files:** `packages/backend/src/lineupiq/data/fetchers.py`
- **Changes:**
  - Added `fetch_injuries(seasons: list[int])` function
  - Uses `nflreadpy.load_injuries()` to load official NFL injury reports since 2009
  - Returns polars DataFrame with injury designations and practice status
  - Added logging for data loading (consistent with existing fetch functions)
- **Commit:** `a760b96`

### Task 2: Create injury feature engineering module ✅
- **Files:** `packages/backend/src/lineupiq/features/injury.py`, `packages/backend/tests/test_injury_features.py`
- **Changes:**
  - Created `engineer_injury_features(player_stats, injuries)` function
  - Encodes injury severity: Out=1.0, Doubtful=0.75, Questionable=0.5, Probable=0.25, Not on report=0.0
  - Creates 2 features: `injury_severity` (float 0.0-1.0), `on_injury_report` (binary 0/1)
  - Joins injuries to player-week data on [player_id, season, week]
  - Uses most recent report when multiple updates per week (`date_modified` sorting)
  - Fills missing injuries with zeros
  - Handles player_id/gsis_id column naming mismatch (renames gsis_id to player_id)
  - Added comprehensive test suite with 7 tests covering:
    - Injury severity encoding (all designations)
    - on_injury_report flag behavior
    - Player-week join correctness
    - Multiple reports per week (most recent wins)
    - Missing injury data handling
    - Column presence verification
    - date_modified fallback handling
- **Commit:** `0f567ca`

### Task 3: Integrate injury features into pipeline ✅
- **Files:** `packages/backend/src/lineupiq/features/pipeline.py`
- **Changes:**
  - Added Step 7 (injury features) to `build_features()` after weather features
  - Renumbered matchup features to Step 8 (were Step 7)
  - Fetches injuries using `fetch_injuries(seasons)`
  - Calls `engineer_injury_features(df, injuries_df)` to add injury columns
  - Updated `get_feature_columns()` to include `["injury_severity", "on_injury_report"]`
  - Updated docstring to document injury features and 8-10% production impact finding
  - Updated logging to track injury feature count (2 columns added)
  - Total feature count increased from 40 to 42
- **Commit:** `94a4883`

## Verification Checklist

- [x] `fetch_injuries()` function exists in data/fetchers.py
- [x] `engineer_injury_features()` creates injury_severity and on_injury_report columns
- [x] `build_features()` includes Step 7 for injury features
- [x] `get_feature_columns()` returns injury_severity and on_injury_report
- [x] `pytest tests/test_injury_features.py` passes (all 7 new tests)
- [x] Pipeline integration doesn't break existing tests
- [x] Injury severity encoding matches research values (Out=1.0, Doubtful=0.75, etc.)

## Files Created/Modified

**Created:**
- `packages/backend/src/lineupiq/features/injury.py` (127 lines)
- `packages/backend/tests/test_injury_features.py` (245 lines)

**Modified:**
- `packages/backend/src/lineupiq/data/fetchers.py` (+50 lines: fetch_injuries function)
- `packages/backend/src/lineupiq/features/pipeline.py` (+24 lines: Step 7 integration, updated docstring and feature list)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Use player_id for joins (rename gsis_id) | Player stats use player_id column; injuries use gsis_id; renamed in injury module for consistency |
| Out=1.0, Doubtful=0.75, Questionable=0.5, Probable=0.25 | Research shows 8-10% production drop; encoded as severity gradient for model training |
| Most recent report per player-week | Injury status updates during week; final status before game most predictive |
| Left join with zero fill | Not all players have injury reports; zeros indicate no injury designation |
| 2 features (severity + flag) | Severity captures impact gradient; flag indicates any injury presence |

## Issues Encountered

**Column naming mismatch:** Player stats DataFrame uses `player_id` while nflreadpy injuries use `gsis_id`. Fixed by renaming `gsis_id` to `player_id` at the start of `engineer_injury_features()` to ensure joins work correctly.

## Performance Notes

- Duration: 8 minutes
- Test coverage: 7 new tests, all passing
- Feature count increase: 40 → 42 total features
- Pipeline integration: Clean insertion as Step 7 between weather and matchup features

## Next Phase Readiness

**Status:** ✅ Ready
**Blockers:** None

**Output:**
- Injury features available for model training (2 new columns)
- nflreadpy injury data integrated correctly
- Injury designations encoded to numeric severity (0.0-1.0)
- Tests validate feature engineering and encoding logic

## Next Steps

- Phase 20-04: Test injury features with model retraining
- Validate prediction accuracy improvements from injury status features
- Consider expanding to practice participation tracking (Full/Limited/DNP)
