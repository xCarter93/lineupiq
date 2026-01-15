---
phase: 12-ml-pipeline-improvements
plan: 02
subsystem: ml
tags: [mapie, conformal-prediction, uncertainty, prediction-intervals, xgboost]

# Dependency graph
requires:
  - phase: 11-ml-pipeline-audit
    provides: Identification of prediction intervals as highest priority improvement
provides:
  - Split conformal prediction for uncertainty quantification
  - Per-prediction 90% confidence intervals
  - API-ready interval formatting
affects: [12-04, 12-05, prediction-api, ui-visualization]

# Tech tracking
tech-stack:
  added: [mapie>=1.2.0]
  patterns: [split-conformal-prediction, calibration-quantile]

key-files:
  created: [packages/backend/src/lineupiq/models/uncertainty.py]
  modified: [packages/backend/pyproject.toml, packages/backend/src/lineupiq/models/__init__.py]

key-decisions:
  - "Split conformal approach over MAPIE wrapper - works with existing trained models without retraining"
  - "90% coverage (alpha=0.1) as default - balances informativeness with reliability"
  - "Finite sample correction for quantile calculation - more accurate for small calibration sets"

patterns-established:
  - "Per-prediction intervals via calibration quantile: calibrate_intervals() -> predict_with_intervals()"
  - "Non-negative bounds enforcement for stat predictions"

# Metrics
duration: 5 min
completed: 2026-01-15
---

# Phase 12 Plan 02: Prediction Intervals with MAPIE Summary

**Split conformal prediction intervals using calibration residuals, providing 90% coverage bounds for per-prediction uncertainty**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-15T18:20:00Z
- **Completed:** 2026-01-15T18:25:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- MAPIE 1.2.0 dependency added for conformal prediction methodology
- Split conformal approach implemented that works with existing trained models
- 5 core functions for interval calibration, prediction, and formatting
- Type-safe implementation passing mypy strict checks

## Task Commits

Each task was committed atomically:

1. **Task 1: Add MAPIE dependency** - `3b87f08` (chore)
2. **Task 2: Create uncertainty module** - `defbb39` (feat)
3. **Task 3: Export uncertainty functions** - `35497d9` (feat)

## Files Created/Modified
- `packages/backend/pyproject.toml` - Added mapie>=1.2.0 dependency
- `packages/backend/src/lineupiq/models/uncertainty.py` - New module with split conformal prediction
- `packages/backend/src/lineupiq/models/__init__.py` - Exported uncertainty functions

## Decisions Made
- **Split conformal over MAPIE wrapper**: MAPIE's MapieRegressor requires retraining. Split conformal works with our existing joblib models - just need calibration data to compute residual quantile.
- **90% confidence intervals**: alpha=0.1 provides informative bounds without excessive uncertainty. Higher confidence (95%) would produce intervals too wide to be actionable.
- **Finite sample correction**: Using (n+1)(1-alpha)/n quantile instead of exact (1-alpha) quantile for better coverage with small calibration sets.

## Deviations from Plan

### Auto-additions

**1. [Rule 2 - Missing Critical] Added get_interval_coverage function**
- **Found during:** Task 2 (uncertainty module creation)
- **Issue:** Plan didn't specify a way to verify interval calibration quality
- **Fix:** Added get_interval_coverage() to measure empirical coverage vs target
- **Files modified:** packages/backend/src/lineupiq/models/uncertainty.py
- **Verification:** Function computes fraction of true values within bounds
- **Committed in:** defbb39 (Task 2 commit)

---

**Total deviations:** 1 auto-added (missing critical for validation)
**Impact on plan:** Essential for verifying interval quality. No scope creep.

## Issues Encountered
None - plan executed smoothly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Uncertainty module ready for integration with prediction API
- Calibration workflow can use holdout data from 12-01's backtesting module
- Next plan (12-01 or 12-04) can build on this foundation
- 2/5 plans complete for Phase 12

---
*Phase: 12-ml-pipeline-improvements*
*Completed: 2026-01-15*
