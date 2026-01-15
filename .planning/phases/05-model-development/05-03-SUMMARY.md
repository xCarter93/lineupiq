---
phase: 05-model-development
plan: 03
subsystem: ml
tags: [xgboost, optuna, rb-models, running-back, rushing, receiving]

# Dependency graph
requires:
  - phase: 05-01
    provides: Training pipeline infrastructure (train_model, tune_hyperparameters, save_model)
  - phase: 04-feature-engineering
    provides: Feature pipeline (build_features, get_feature_columns)
provides:
  - RB model training module (train_rb_models, prepare_rb_data)
  - 5 trained RB models (rushing_yards, rushing_tds, carries, receiving_yards, receptions)
  - RB model test suite
affects: [06-model-evaluation, 07-prediction-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [Position-specific model training module pattern]

key-files:
  created:
    - packages/backend/src/lineupiq/models/rb.py
    - packages/backend/tests/test_rb_models.py
    - packages/backend/models/RB_rushing_yards.joblib
    - packages/backend/models/RB_rushing_tds.joblib
    - packages/backend/models/RB_carries.joblib
    - packages/backend/models/RB_receiving_yards.joblib
    - packages/backend/models/RB_receptions.joblib
  modified:
    - packages/backend/src/lineupiq/models/__init__.py

key-decisions:
  - "Use same training infrastructure as QB models for consistency"
  - "5 RB targets: rushing_yards, rushing_tds, carries, receiving_yards, receptions"
  - "50 Optuna trials with 5-fold TimeSeriesSplit CV per target"

patterns-established:
  - "Position-specific model module pattern: prepare_*_data, train_*_models, *_TARGETS"

# Metrics
duration: 27min
completed: 2026-01-15
---

# Phase 5 Plan 3: RB Rushing/Receiving Models Summary

**XGBoost models for 5 RB stats (rushing_yards, rushing_tds, carries, receiving_yards, receptions) with Optuna tuning achieving CV RMSE well below expected ranges**

## Performance

- **Duration:** 27 min
- **Started:** 2026-01-15T00:55:05Z
- **Completed:** 2026-01-15T01:22:07Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created RB model training module following QB module pattern
- Trained 5 RB models with 50 Optuna trials each (250 total trials)
- Achieved CV RMSE results better than expected for all targets
- Added 6 unit tests verifying RB model training and predictions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create RB model training module** - `bf2e458` (feat)
2. **Task 2: Train and persist RB models** - (models saved as artifacts, not committed)
3. **Task 3: Add RB model tests** - `cfb830f` (test)

## Files Created/Modified

- `packages/backend/src/lineupiq/models/rb.py` - RB_TARGETS, prepare_rb_data, train_rb_models
- `packages/backend/src/lineupiq/models/__init__.py` - Export RB training functions
- `packages/backend/tests/test_rb_models.py` - 6 unit tests for RB models
- `packages/backend/models/RB_*.joblib` - 5 trained model artifacts (gitignored)

## Model Training Results

| Target | CV RMSE | Expected Range | Status |
|--------|---------|----------------|--------|
| rushing_yards | 20.68 +/- 0.69 | 30-50 | Better than expected |
| rushing_tds | 0.39 +/- 0.02 | 0.4-0.7 | Better than expected |
| carries | 3.46 +/- 0.13 | 5-8 | Better than expected |
| receiving_yards | 11.89 +/- 0.54 | 15-25 | Better than expected |
| receptions | 1.18 +/- 0.07 | 1-2 | Within expected |

**Training Configuration:**
- Seasons: 2019-2024 (6 seasons)
- Optuna trials: 50 per target
- CV splits: 5 (TimeSeriesSplit)

## Decisions Made

1. **Same training infrastructure as QB** - Reuse train_model, tune_hyperparameters, save_model
2. **All 5 RB targets** - Cover both rushing (yards, TDs, carries) and receiving (yards, receptions)
3. **50 trials per target** - Balance training time vs optimization quality

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RB models trained and persisted
- Ready for 05-04: WR/TE receiving stat models
- Model evaluation (Phase 6) can begin after all position models complete

---
*Phase: 05-model-development*
*Completed: 2026-01-15*
