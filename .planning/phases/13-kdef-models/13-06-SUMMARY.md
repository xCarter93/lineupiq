---
phase: 13-kdef-models
plan: 06
subsystem: ml
tags: [lightgbm, defense, team-stats, nflreadpy, fantasy-dst]

# Dependency graph
requires:
  - phase: 13-01
    provides: LightGBM training infrastructure with model_type selection
  - phase: 13-03
    provides: K/DEF data processing pipelines with rolling features
provides:
  - train_defense_models() for team DST prediction
  - DEF position models (points_allowed, def_sacks, def_interceptions, def_fumbles, total_def_tds)
  - DefensePrediction API schema
  - POST /defense/{team} prediction endpoint
affects: [13-08-backtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Team-level prediction (DEF is team, not player)
    - Defense uses def_ prefix column names from nflreadpy

key-files:
  created:
    - packages/backend/src/lineupiq/models/defense.py
    - packages/backend/models/DEF_*.joblib
  modified:
    - packages/backend/src/lineupiq/api/schemas/prediction.py
    - packages/backend/src/lineupiq/api/routes/predictions.py
    - packages/backend/src/lineupiq/data/defense_processing.py
    - packages/backend/src/lineupiq/models/__init__.py

key-decisions:
  - "Defense column names use def_ prefix to match nflreadpy (def_sacks, not sacks)"
  - "Trained 5 target models: points_allowed, def_sacks, def_interceptions, def_fumbles, total_def_tds"
  - "Defense endpoint takes team, opponent, week as path/query params with rolling features in body"

# Metrics
duration: 45min
completed: 2026-01-15
---

# Phase 13 Plan 06: Defense Models Summary

**LightGBM defense models trained for team DST fantasy scoring with API endpoint for predictions**

## Performance

- **Duration:** 45 min
- **Started:** 2026-01-15T15:44:25Z
- **Completed:** 2026-01-15T16:29:43Z
- **Tasks:** 5
- **Files modified:** 6

## Accomplishments

- Created defense.py model training module using LightGBM
- Trained 5 defense models (points_allowed, def_sacks, def_interceptions, def_fumbles, total_def_tds)
- Added DefensePrediction/DefensePredictionResponse schemas
- Added POST /defense/{team} endpoint with caching
- Exported train_defense_models and DEF_TARGETS from models package

## Task Commits

Each task was committed atomically:

1. **Task 1: Create defense.py model training module** - `f998f85` (feat)
2. **Task 2: Add defense schemas to prediction API** - `ae4a3e5` (feat)
3. **Task 3: Add defense endpoint to predictions router** - `97200eb` (feat)
4. **Task 4: Train defense models** - `e2e0fb6` (fix - included column name corrections)
5. **Task 5: Export defense module** - `c1ce5e7` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/models/defense.py` - Defense model training module
- `packages/backend/models/DEF_*.joblib` - Trained defense models (5 files)
- `packages/backend/src/lineupiq/api/schemas/prediction.py` - Defense prediction schemas
- `packages/backend/src/lineupiq/api/routes/predictions.py` - Defense prediction endpoint
- `packages/backend/src/lineupiq/data/defense_processing.py` - Fixed column names
- `packages/backend/src/lineupiq/models/__init__.py` - Defense exports

## Decisions Made

- **Defense column names use def_ prefix**: nflreadpy team_stats uses `def_sacks`, `def_interceptions`, `def_fumbles` - not bare names
- **5 target models trained**: Covers main fantasy DST scoring categories (points allowed, sacks, INTs, fumbles, TDs)
- **Defense endpoint structure**: Takes team/opponent/week as params, rolling features in request body

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected defense column names to match nflreadpy**
- **Found during:** Task 4 (Training defense models)
- **Issue:** Plan used `sacks`, `interceptions`, `fumbles_forced` but nflreadpy uses `def_sacks`, `def_interceptions`, `def_fumbles`
- **Fix:** Updated DEFENSE_STAT_COLUMNS, DEFENSE_TARGETS, rolling_configs, and all schema/endpoint references
- **Files modified:** defense_processing.py, defense.py, prediction.py (schemas), predictions.py (routes)
- **Verification:** Training completed successfully with 5 models saved
- **Committed in:** e2e0fb6 (fix commit during Task 4)

---

**Total deviations:** 1 auto-fixed (1 blocking data mismatch)
**Impact on plan:** Column name mismatch required updates across multiple files. No scope creep.

## Issues Encountered

- Initial training with n_trials=30 was slow (~30 min for first model). Reduced to n_trials=10 for faster completion.
- The 5 models took approximately 25 minutes total to train.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Defense models trained and ready for predictions
- API endpoint available at POST /defense/{team}
- Ready for 13-08 backtest and calibration phase

---
*Phase: 13-kdef-models*
*Completed: 2026-01-15*
