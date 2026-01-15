---
phase: 05-model-development
plan: 04
subsystem: ml
tags: [xgboost, optuna, receiver-models, wr, te, receiving-stats]

# Dependency graph
requires:
  - phase: 05-01
    provides: Training pipeline (tune_hyperparameters, train_model, save_model)
  - phase: 04-03
    provides: Feature pipeline (build_features, get_feature_columns)
provides:
  - WR receiving stat models (receiving_yards, receiving_tds, receptions)
  - TE receiving stat models (receiving_yards, receiving_tds, receptions)
  - prepare_receiver_data for WR/TE data preparation
affects: [06-model-evaluation, 07-prediction-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [Position-specific model training, separate WR/TE models for stat distribution accuracy]

key-files:
  created:
    - packages/backend/src/lineupiq/models/receiver.py
    - packages/backend/tests/test_receiver_models.py
    - packages/backend/models/WR_receiving_yards.joblib
    - packages/backend/models/WR_receiving_tds.joblib
    - packages/backend/models/WR_receptions.joblib
    - packages/backend/models/TE_receiving_yards.joblib
    - packages/backend/models/TE_receiving_tds.joblib
    - packages/backend/models/TE_receptions.joblib
  modified:
    - packages/backend/src/lineupiq/models/__init__.py

key-decisions:
  - "Separate WR and TE models for different stat distributions"
  - "WR typically higher volume (14,138 samples vs TE 7,024 samples)"
  - "TE models have lower RMSE due to lower stat variance"

patterns-established:
  - "RECEIVER_TARGETS constant for shared target columns"
  - "prepare_receiver_data(df, position) pattern for position filtering"

# Metrics
duration: 35min
completed: 2026-01-15
---

# Phase 5 Plan 4: WR/TE Receiving Models Summary

**XGBoost models for WR and TE receiving stats with Optuna hyperparameter tuning, achieving CV RMSE of 22.78 yards (WR) and 16.59 yards (TE) for receiving_yards**

## Performance

- **Duration:** 35 min
- **Started:** 2026-01-15T03:54:37Z
- **Completed:** 2026-01-15T04:29:51Z
- **Tasks:** 4
- **Files modified:** 3 source files, 6 model artifacts

## Accomplishments

- Created receiver.py module with train_wr_models and train_te_models functions
- Trained 3 WR models (receiving_yards, receiving_tds, receptions) on 14,138 samples
- Trained 3 TE models (receiving_yards, receiving_tds, receptions) on 7,024 samples
- Added 15 comprehensive tests for receiver model training and predictions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create receiver model training module** - `9da4a9c` (feat)
2. **Task 2: Train and persist WR models** - No commit (models are gitignored artifacts)
3. **Task 3: Train and persist TE models** - No commit (models are gitignored artifacts)
4. **Task 4: Add WR/TE model tests** - `1da4fd0` (test)

## Model Performance Metrics

### WR Models (14,138 training samples)

| Target | CV RMSE | Std Dev | Best max_depth |
|--------|---------|---------|----------------|
| receiving_yards | 22.78 | 0.62 | 3 |
| receiving_tds | 0.37 | 0.01 | 3 |
| receptions | 1.47 | 0.05 | 3 |

### TE Models (7,024 training samples)

| Target | CV RMSE | Std Dev | Best max_depth |
|--------|---------|---------|----------------|
| receiving_yards | 16.59 | 0.35 | 3 |
| receiving_tds | 0.33 | 0.02 | 3 |
| receptions | 1.27 | 0.04 | 3 |

TE models show lower RMSE due to lower stat variance (TEs typically have fewer targets and lower volume than WRs).

## Files Created/Modified

- `packages/backend/src/lineupiq/models/receiver.py` - RECEIVER_TARGETS, prepare_receiver_data, train_wr_models, train_te_models
- `packages/backend/src/lineupiq/models/__init__.py` - Export receiver module functions
- `packages/backend/tests/test_receiver_models.py` - 15 tests for receiver model training
- `packages/backend/models/WR_*.joblib` - 3 trained WR models (gitignored artifacts)
- `packages/backend/models/TE_*.joblib` - 3 trained TE models (gitignored artifacts)

## Decisions Made

1. **Separate WR and TE models** - Despite sharing the same targets (receiving_yards, receiving_tds, receptions), WR and TE have different stat distributions. TEs typically have lower volume and fewer TDs due to blocking assignments and shorter routes. Separate models provide better accuracy.

2. **50 Optuna trials per target** - Matches other position models for consistency and provides good hyperparameter optimization.

3. **6 seasons training data (2019-2024)** - Consistent with QB and RB models for robust training.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 position types now have trained models (QB, RB, WR, TE)
- Phase 5 complete - ready for Phase 6: Model Evaluation
- 13 total models trained (2 QB, 5 RB, 3 WR, 3 TE)
- All models use consistent 50-trial Optuna optimization and TimeSeriesSplit CV

---
*Phase: 05-model-development*
*Completed: 2026-01-15*
