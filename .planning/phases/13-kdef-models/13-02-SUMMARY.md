---
phase: 13-kdef-models
plan: 02
subsystem: features
tags: [polars, rolling-stats, team-strength, volatility, ml-features]

# Dependency graph
requires:
  - phase: 04-feature-engineering
    provides: Feature pipeline infrastructure (build_features, rolling_stats)
provides:
  - Team offensive strength features (points, yards, plays rolling avg)
  - Player volatility metrics (std, CV for boom/bust identification)
  - Extended get_feature_columns() API
affects: [13-05, 13-06, 13-07, 13-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shift(1) for data leakage prevention in rolling features"
    - "Coefficient of variation (CV) for normalized volatility"

key-files:
  created:
    - packages/backend/src/lineupiq/features/team_strength.py
  modified:
    - packages/backend/src/lineupiq/features/rolling_stats.py
    - packages/backend/src/lineupiq/features/pipeline.py
    - packages/backend/src/lineupiq/features/__init__.py

key-decisions:
  - "Use shift(1) on all rolling calculations to prevent data leakage"
  - "Fill null team strength values with league averages"
  - "Fill null volatility values with 0 (no variance for new players)"
  - "min_samples=2 for rolling_std to avoid single-sample std"

patterns-established:
  - "Team-level features joined via (season, week, team) keys"
  - "Volatility features: {stat}_std{window} and {stat}_cv{window}"

# Metrics
duration: 5min
completed: 2026-01-15
---

# Phase 13 Plan 02: Team Strength and Volatility Features Summary

**Added 11 new features: 3 team strength (points, yards, plays) + 8 volatility (std and cv for 4 stats). Feature count increased from 17 to 28.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-15T15:36:53Z
- **Completed:** 2026-01-15T15:41:46Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Created team_strength.py module with compute_team_strength() for rolling team offensive metrics
- Added compute_volatility_features() and get_volatility_columns() to rolling_stats.py
- Integrated both feature types into build_features() pipeline
- Updated get_feature_columns() to return all 28 ML features

## Task Commits

Each task was committed atomically:

1. **Task 1: Create team_strength.py module** - `4315e62` (feat)
2. **Task 2: Add volatility features to rolling_stats.py** - `8440b5d` (feat)
3. **Task 3: Update feature pipeline to include new features** - `058d59f` (feat)
4. **Task 4: Export new functions from package** - `56213ee` (feat)

## Files Created/Modified

- `packages/backend/src/lineupiq/features/team_strength.py` - New module for team offensive strength metrics
- `packages/backend/src/lineupiq/features/rolling_stats.py` - Added volatility features (std, CV)
- `packages/backend/src/lineupiq/features/pipeline.py` - Integrated new features into build_features()
- `packages/backend/src/lineupiq/features/__init__.py` - Exported new public API functions

## Decisions Made

1. **Shift(1) for data leakage prevention** - All rolling calculations use shift(1) to ensure only prior games are used, never the current game being predicted
2. **League average fill for team strength nulls** - New teams or early-season games with no history get league average values
3. **Zero fill for volatility nulls** - Players with insufficient history get 0 volatility (conservative assumption)
4. **min_samples=2 for rolling_std** - Require at least 2 samples for standard deviation to be meaningful

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Polars parameter name**
- **Found during:** Task 1 (team_strength.py creation)
- **Issue:** Plan used `min_periods` but Polars uses `min_samples` for rolling functions
- **Fix:** Changed all occurrences from `min_periods=1` to `min_samples=1`
- **Files modified:** team_strength.py
- **Verification:** mypy passes
- **Committed in:** 4315e62 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor API correction, no scope change.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Team strength and volatility features integrated into pipeline
- Feature count increased from 17 to 28 columns
- Ready for parallel plans: 13-03 (K/DEF Data Pipeline), 13-04 (Fantasy Scoring Config)
- Models can be retrained with new features in 13-07

---
*Phase: 13-kdef-models*
*Plan: 02*
*Completed: 2026-01-15*
