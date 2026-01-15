# Plan 14-01 Summary: QB Complete Fantasy Stats

## Outcome
SUCCESS - All 3 tasks completed successfully.

## What Was Built
Expanded QB model coverage from 2 stats to 6 stats to enable complete fantasy point calculations:

### Stats Added
1. **interceptions** - Predicted INT count (mapped from passing_interceptions)
2. **rushing_yards** - QB rushing yards
3. **rushing_tds** - QB rushing touchdowns
4. **fumbles_lost** - Computed from sack_fumbles_lost + rushing_fumbles_lost

### Model Performance (CV RMSE)
| Target | CV RMSE |
|--------|---------|
| passing_yards | 55.86 |
| passing_tds | 0.79 |
| interceptions | 0.83 |
| rushing_yards | 11.90 |
| rushing_tds | 0.33 |
| fumbles_lost | 0.43 |

## Changes Made

### Task 1: Add missing stats to QB model targets
- **qb.py**: Updated QB_TARGETS list from 2 to 6 stats
- **qb.py**: Updated prepare_qb_data() to compute derived columns:
  - `interceptions` from `passing_interceptions` column
  - `fumbles_lost` from `sack_fumbles_lost + rushing_fumbles_lost`
- **cleaning.py**: Added `passing_interceptions` and `sack_fumbles_lost` to ML column selection

### Task 2: Train and save all QB models
- Trained 6 LightGBM models with 30 Optuna trials each
- Models saved to `packages/backend/models/QB_*.joblib`
- Note: Models directory is gitignored (not committed to source control)

### Task 3: Update API to return all QB stats
- **prediction.py schema**: Added 4 new fields to QBPredictionResponse
- **predictions.py route**: Updated /predictions/qb endpoint to:
  - Load and predict all 6 QB models
  - Apply non-negative clamping for interceptions, rushing_tds, fumbles_lost
  - Return all 6 stats in response

## Commits
| Hash | Description |
|------|-------------|
| e39e787 | feat(14-01): add complete QB fantasy stats to model targets |
| 638020e | feat(14-01): update API to return all 6 QB fantasy stats |

## Files Modified
- `packages/backend/src/lineupiq/models/qb.py`
- `packages/backend/src/lineupiq/data/cleaning.py`
- `packages/backend/src/lineupiq/api/schemas/prediction.py`
- `packages/backend/src/lineupiq/api/routes/predictions.py`

## Technical Decisions
1. **Column mapping approach**: Rather than modifying the entire data pipeline, computed derived columns in `prepare_qb_data()` to keep changes scoped to QB module
2. **Non-negative clamping**: Applied `max(0.0, ...)` to interceptions, rushing_tds, and fumbles_lost predictions to prevent negative values that don't make sense
3. **Training parameters**: Used 30 Optuna trials (reduced from default 50) for faster training while still achieving good hyperparameter tuning

## Notes
- Model files are not committed to git (gitignored) - this is expected behavior
- All 6 models trained successfully and saved to disk
- API endpoint returns all 6 stats in response
