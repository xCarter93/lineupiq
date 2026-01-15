---
phase: 13-kdef-models
plan: 07
subsystem: ml
tags: [lightgbm, optuna, xgboost, model-training, skill-positions]

# Dependency graph
requires:
  - phase: 13-01
    provides: LightGBM support in training pipeline
  - phase: 13-02
    provides: Team strength and volatility features (28 total)
provides:
  - All 13 skill position models retrained with LightGBM
  - Model metadata includes model_type field
  - 28-feature models (expanded from 17)
affects: [13-08-backtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "model_type parameter for selecting LightGBM vs XGBoost"
    - "Default seasons [2021-2024] when None provided"

key-files:
  created: []
  modified:
    - packages/backend/src/lineupiq/models/qb.py
    - packages/backend/src/lineupiq/models/rb.py
    - packages/backend/src/lineupiq/models/receiver.py

key-decisions:
  - "LightGBM as default model type for all skill positions"
  - "train_receiver_models() convenience function for WR + TE"
  - "Include position, target, model_type in all model metadata"

# Metrics
duration: 176min
completed: 2026-01-15
---

# Phase 13 Plan 07: Retrain Skill Position Models Summary

**All 13 skill position models (QB, RB, WR, TE) retrained with LightGBM using 28 features including team strength and volatility metrics**

## Performance

- **Duration:** 176 min (mostly training time)
- **Started:** 2026-01-15T10:44:15Z
- **Completed:** 2026-01-15T13:40:36Z
- **Tasks:** 5
- **Files modified:** 3

## Accomplishments

- Updated qb.py, rb.py, receiver.py to use LightGBM by default
- All 13 skill position models retrained with new features:
  - QB: passing_yards (RMSE 55.66), passing_tds (0.79)
  - RB: rushing_yards (16.82), rushing_tds (0.38), carries (3.08), receiving_yards (8.32), receptions (0.91)
  - WR: receiving_yards (17.52), receiving_tds (0.36), receptions (1.17)
  - TE: receiving_yards (13.55), receiving_tds (0.33), receptions (1.10)
- Added train_receiver_models() convenience function for training WR + TE together
- Model metadata now includes model_type="lightgbm" and n_features=28

## Task Commits

Each task was committed atomically:

1. **Task 1: Update qb.py** - `479258f` (feat)
2. **Task 2: Update rb.py** - `d83a641` (feat)
3. **Task 3: Update receiver.py** - included in `1fe9d0e` (fix - via parallel plan merge)
4. **Task 4: Retrain models** - Not committed (models/ in .gitignore)
5. **Task 5: Verify features** - Verification only

## Files Created/Modified

- `packages/backend/src/lineupiq/models/qb.py` - Added model_type param, LightGBM default
- `packages/backend/src/lineupiq/models/rb.py` - Added model_type param, LightGBM default
- `packages/backend/src/lineupiq/models/receiver.py` - Added model_type param, LightGBM default, train_receiver_models()

## Decisions Made

1. **LightGBM as default for all positions** - Consistent with 13-01 decision, enables faster experimentation
2. **Include position/target/model_type in metadata** - Better tracking for model provenance
3. **train_receiver_models() convenience function** - Easier to train both WR + TE in one call

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Model files not committed (packages/backend/models/ in .gitignore) - This is intentional for binary files
- Parallel plan execution (13-05, 13-06, 13-07) resulted in interleaved commits - No impact on functionality
- UserWarning about feature names during sklearn validation - Harmless, numpy arrays vs DataFrames

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 13 skill position models retrained with LightGBM and 28 features
- Ready for 13-08 backtest phase to evaluate model performance
- Model metadata includes model_type for tracking

---
*Phase: 13-kdef-models*
*Plan: 07*
*Completed: 2026-01-15*
