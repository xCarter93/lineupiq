# Plan 14-02 Summary: Expand RB Models for Complete Fantasy Scoring

## Result: SUCCESS

## Commits
| Hash | Message |
|------|---------|
| b6c7510 | feat(14-02): add receiving_tds and fumbles_lost to RB model targets |
| 3142055 | feat(14-02): update RB API to return all 7 fantasy stats |

## Changes Made

### Task 1: Add receiving_tds and fumbles_lost to RB model targets
- **Files Modified:**
  - `packages/backend/src/lineupiq/data/cleaning.py` - Added `rushing_fumbles_lost` and `receiving_fumbles_lost` to ML columns
  - `packages/backend/src/lineupiq/models/rb.py` - Expanded `RB_TARGETS` to 7 targets, updated `prepare_rb_data()` to compute combined `fumbles_lost`

### Task 2: Train and save all 7 RB models
- **Models Trained (30 Optuna trials each, LightGBM):**
  | Model | CV RMSE |
  |-------|---------|
  | rushing_yards | 16.94 |
  | rushing_tds | 0.38 |
  | carries | 3.09 |
  | receiving_yards | 8.35 |
  | receptions | 0.92 |
  | receiving_tds | 0.19 |
  | fumbles_lost | 0.20 |
- **Note:** Model files in `packages/backend/models/` are gitignored (binary files)

### Task 3: Update API to return all RB stats
- **Files Modified:**
  - `packages/backend/src/lineupiq/api/schemas/prediction.py` - Added `receiving_tds` and `fumbles_lost` fields to `RBPredictionResponse`
  - `packages/backend/src/lineupiq/api/routes/predictions.py` - Updated `/rb` endpoint to call all 7 models

## Decisions
- Combined `fumbles_lost` from `rushing_fumbles_lost + receiving_fumbles_lost` in `prepare_rb_data()` per plan spec
- Added `max(0.0, ...)` guards for count-based stats (TDs, fumbles) to prevent negative predictions
- Training took ~4 hours with 30 trials per model (longer than estimated 25 min due to Optuna tuning overhead)

## Metrics
- 7 RB models now available for complete fantasy point calculations
- receiving_tds and fumbles_lost have very low RMSE (~0.2) due to rare occurrence (~0.05/game avg)
