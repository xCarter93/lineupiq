# Plan 14-03 Summary: Add Fumbles Lost to WR/TE Models

## Result: SUCCESS

## Commits
| Hash | Message |
|------|---------|
| 89016e3 | feat(14-03): add fumbles_lost to receiver model targets |
| 1d92c25 | feat(14-03): update API to return fumbles_lost for WR/TE |

## Changes Made

### Task 1: Add fumbles_lost to receiver model targets
- **Files Modified:**
  - `packages/backend/src/lineupiq/models/receiver.py` - Added `fumbles_lost` to `RECEIVER_TARGETS`, updated `prepare_receiver_data()` to map `receiving_fumbles_lost` to `fumbles_lost`

### Task 2: Train and save all WR/TE models
- **Models Trained (30 Optuna trials each, LightGBM):**
  | Position | Model | File Size |
  |----------|-------|-----------|
  | WR | receiving_yards | 695KB |
  | WR | receiving_tds | 545KB |
  | WR | receptions | 1.1MB |
  | WR | fumbles_lost | 41KB |
  | TE | receiving_yards | 1.1MB |
  | TE | receiving_tds | 113KB |
  | TE | receptions | 3.2MB |
  | TE | fumbles_lost | 40KB |
- **Note:** Model files in `packages/backend/models/` are gitignored (binary files), not committed
- **Training Time:** ~2 hours wall time with parallelized Optuna tuning

### Task 3: Update API to return fumbles_lost for receivers
- **Files Modified:**
  - `packages/backend/src/lineupiq/api/schemas/prediction.py` - Added `fumbles_lost` field to `ReceiverPredictionResponse`
  - `packages/backend/src/lineupiq/api/routes/predictions.py` - Updated `/wr` and `/te` endpoints to predict and return `fumbles_lost`

## Decisions
- Mapped `receiving_fumbles_lost` to `fumbles_lost` in `prepare_receiver_data()` for consistency with API naming
- Added `max(0.0, ...)` guards for count-based stats to prevent negative predictions
- Rounded `fumbles_lost` to 2 decimal places (rare events ~0.01-0.02/game average)
- Small model file sizes for fumbles_lost (40-41KB) reflect sparse target values

## Verification
- [x] RECEIVER_TARGETS includes all 4 targets: receiving_yards, receiving_tds, receptions, fumbles_lost
- [x] 8 WR/TE model files exist (4 per position)
- [x] API /wr and /te endpoints return fumbles_lost
- [x] No Python errors introduced

## Next Steps
Ready for 14-04-PLAN.md if additional fantasy stats are needed.
