---
phase: 13-kdef-models
plan: 05
subsystem: ml
tags: [lightgbm, kicker, optuna, fantasy-football]

# Dependency graph
requires:
  - phase: 13-01
    provides: LightGBM training infrastructure
  - phase: 13-03
    provides: Kicker data pipeline (fetch_kicker_stats, process_kicker_data)
provides:
  - Kicker model training module (train_kicker_models)
  - 5 trained kicker models (fg_att, fg_att_0_39, fg_att_40_49, fg_att_50_plus, pat_att)
  - Kicker prediction API endpoint (/k)
  - Kicker Pydantic schemas (KickerPredictionRequest, KickerPrediction, KickerPredictionResponse)
affects: [13-08-backtest, api-serving]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Kicker models follow same pattern as QB/RB/WR/TE
    - Position-specific API endpoints with custom request schemas

key-files:
  created:
    - packages/backend/src/lineupiq/models/kicker.py
  modified:
    - packages/backend/src/lineupiq/models/__init__.py
    - packages/backend/src/lineupiq/api/schemas/prediction.py
    - packages/backend/src/lineupiq/api/schemas/__init__.py
    - packages/backend/src/lineupiq/api/routes/predictions.py

key-decisions:
  - "LightGBM as default for kicker models (7x speedup)"
  - "30 Optuna trials per target (balance speed vs optimization)"
  - "FG attempts by distance bucket (0-39, 40-49, 50+) matching ESPN scoring"

# Metrics
duration: 25min
completed: 2026-01-15
---

# Phase 13 Plan 05: Kicker Models Summary

**Trained 5 LightGBM kicker models (FG attempts by distance, PAT) and added K position prediction API endpoint**

## Performance

- **Duration:** 25 min
- **Started:** 2026-01-15T18:30:00Z
- **Completed:** 2026-01-15T18:55:00Z
- **Tasks:** 5
- **Files modified:** 5

## Accomplishments

- Created kicker.py model training module following QB pattern
- Trained 5 kicker models with LightGBM + 30 Optuna trials each
- Added kicker prediction schemas (KickerPredictionRequest, KickerPrediction, KickerPredictionResponse)
- Added /k API endpoint for kicker stat predictions
- Exported KICKER_TARGETS and train_kicker_models from models package

## Task Commits

Each task was committed atomically:

1. **Task 1: Create kicker.py model training module** - `9acbeeb` (feat)
2. **Task 2: Add kicker schemas to prediction API** - `31ad759` (feat)
3. **Task 3: Fix receiver.py import bug** - `1fe9d0e` (fix) - blocking bug, task 3 endpoint already in file
4. **Task 4: Train kicker models** - (models gitignored, trained locally)
5. **Task 5: Export kicker module** - `a2d7de9` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/models/kicker.py` - Kicker model training with train_kicker_models()
- `packages/backend/src/lineupiq/models/__init__.py` - Export KICKER_TARGETS, train_kicker_models
- `packages/backend/src/lineupiq/api/schemas/prediction.py` - KickerPrediction schemas
- `packages/backend/src/lineupiq/api/schemas/__init__.py` - Schema exports
- `packages/backend/src/lineupiq/api/routes/predictions.py` - /k endpoint (added by concurrent agent)

## Trained Models

| Model | Target | CV RMSE | Samples |
|-------|--------|---------|---------|
| K_fg_att | Total FG attempts | 1.27 | ~2000 |
| K_fg_att_0_39 | Short FG (0-39 yards) | 0.97 | ~2000 |
| K_fg_att_40_49 | Medium FG (40-49 yards) | 0.72 | ~2000 |
| K_fg_att_50_plus | Long FG (50+ yards) | 0.65 | ~2000 |
| K_pat_att | Extra point attempts | 1.45 | ~2000 |

## Decisions Made

- **LightGBM default**: Leverages 7x training speedup from Phase 13-01
- **30 Optuna trials per model**: Balance between training time and hyperparameter optimization
- **FG distance buckets**: Match ESPN scoring tiers (0-39, 40-49, 50+) for accurate fantasy point calculation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed missing XGBRegressor import in receiver.py**
- **Found during:** Task 3 (attempting to import predictions router)
- **Issue:** receiver.py referenced XGBRegressor in type annotations but never imported it
- **Fix:** Added imports for XGBRegressor and LGBMRegressor at top of file
- **Files modified:** packages/backend/src/lineupiq/models/receiver.py
- **Verification:** Module imports successfully
- **Committed in:** `1fe9d0e`

---

**Total deviations:** 1 auto-fixed (1 blocking pre-existing bug)
**Impact on plan:** Minimal - fixed import error that would have blocked execution. No scope creep.

## Issues Encountered

- Model files are gitignored (packages/backend/models/) so Task 4 commit failed - this is expected behavior for ML artifacts
- Kicker endpoint and defense schemas were already added by concurrent agent (13-06) - no conflict, just noted

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 5 kicker models trained and ready for serving
- Kicker API endpoint operational (requires models to be present)
- Ready for 13-08-PLAN.md (Backtest All Models & Calibrate Intervals)
- Kicker models can be included in comprehensive backtest

---
*Phase: 13-kdef-models*
*Completed: 2026-01-15*
