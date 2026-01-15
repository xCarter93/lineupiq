---
phase: 12-ml-pipeline-improvements
plan: 01
subsystem: ml
tags: [backtesting, accuracy, holdout-validation, confidence-metrics, polars]

# Dependency graph
requires:
  - phase: 11-ml-pipeline-audit
    provides: Audit findings and prioritized implementation roadmap
provides:
  - Backtesting infrastructure for holdout season validation
  - Accuracy metrics module with confidence ratings
  - User-facing accuracy percentage and confidence tiers
affects: [api, ui, model-training]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Backtesting pattern for true out-of-sample validation
    - Accuracy percentage as 100 * (1 - MAE / mean)
    - Directional accuracy for above/below mean predictions
    - Three-tier confidence rating (High/Medium/Low)

key-files:
  created:
    - packages/backend/src/lineupiq/models/backtesting.py
    - packages/backend/src/lineupiq/models/accuracy.py
  modified:
    - packages/backend/src/lineupiq/models/__init__.py

key-decisions:
  - "Accuracy percentage formula: 100 * (1 - MAE / mean(actuals)) - provides 0-100% scale"
  - "Directional accuracy: % predictions with correct above/below mean direction"
  - "Confidence tiers: High (R2>0.5 AND acc>80%), Medium (R2>0.3 OR acc>70%), Low otherwise"

patterns-established:
  - "Holdout loading loads N-1 season for rolling stats, then filters to N"
  - "Backtest results include metadata (player_id, week, opponent) for traceability"
  - "Summary structure designed for API consumption with by_model breakdown"

# Metrics
duration: 3 min
completed: 2026-01-15
---

# Phase 12 Plan 01: Backtesting Infrastructure Summary

**Created backtesting infrastructure for validating models on 2025 holdout data, with accuracy metrics module providing user-facing confidence percentages**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-15T15:03:29Z
- **Completed:** 2026-01-15T15:06:32Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Backtesting module to run trained models on holdout seasons (2025)
- Accuracy metrics with user-friendly percentage scale (0-100%)
- Three-tier confidence ratings (High/Medium/Low) for user trust
- Full public API exports from lineupiq.models

## Task Commits

Each task was committed atomically:

1. **Task 1: Create backtesting module** - `e73e6ab` (feat)
2. **Task 2: Create accuracy metrics module** - `b8fffc2` (feat)
3. **Task 3: Update models __init__.py exports** - `4e1bae8` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/models/backtesting.py` - Holdout data loading and backtest execution
- `packages/backend/src/lineupiq/models/accuracy.py` - Accuracy percentages and confidence tiers
- `packages/backend/src/lineupiq/models/__init__.py` - Public exports for new modules

## Decisions Made

1. **Accuracy percentage formula**: `100 * (1 - MAE / mean(actuals))` - provides intuitive 0-100% scale where 100% is perfect
2. **Directional accuracy**: Percentage of predictions where above/below mean matches actual - captures directional correctness
3. **Confidence tiers**: High requires both R2>0.5 AND accuracy>80%, Medium is R2>0.3 OR accuracy>70%, otherwise Low
4. **Holdout loading**: Loads season N-1 alongside N to ensure rolling stats have history, then filters to N only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Backtesting infrastructure ready for 2025 season validation
- Accuracy metrics can be surfaced in prediction API responses
- Foundation laid for model confidence UI in future phases
- Ready for next plan in Phase 12

---
*Phase: 12-ml-pipeline-improvements*
*Completed: 2026-01-15*
