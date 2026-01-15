---
phase: 12-ml-pipeline-improvements
plan: 03
subsystem: database
tags: [convex, model-metrics, validation, schema]

# Dependency graph
requires:
  - phase: 08-convex-backend
    provides: Convex schema patterns and database structure
provides:
  - modelMetrics table for per-model validation storage
  - overallMetrics table for aggregate confidence
  - Query/mutation functions for metrics CRUD
affects: [14-complete-fantasy-stats, 17-model-explainability-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Upsert pattern for idempotent metric updates
    - Index-based lookups for position/target combinations

key-files:
  created:
    - packages/frontend/convex/modelMetrics.ts
  modified:
    - packages/frontend/convex/schema.ts

key-decisions:
  - "Separate tables for per-model and overall metrics for efficient queries"
  - "Upsert mutations for idempotent updates from backend validation runs"

patterns-established:
  - "Model metrics storage pattern: position+target+season composite key"

# Metrics
duration: 1 min
completed: 2026-01-15
---

# Phase 12 Plan 03: Convex Schema for Model Metrics Summary

**Added modelMetrics and overallMetrics tables to Convex with query/mutation functions for tracking ML model validation results**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-15T15:03:26Z
- **Completed:** 2026-01-15T15:04:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added modelMetrics table storing per-model validation metrics (MAE, RMSE, R2, accuracy percentage)
- Added overallMetrics table for aggregate model confidence summaries
- Created query functions: getOverallMetrics, getMetricsByPosition, getMetricsByModel, getAllMetrics
- Created upsert mutations for idempotent metric updates from backend validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Add modelMetrics table to Convex schema** - `4145d94` (feat)
2. **Task 2: Create modelMetrics query functions** - `45b38c3` (feat)

## Files Created/Modified
- `packages/frontend/convex/schema.ts` - Added modelMetrics and overallMetrics table definitions with indexes
- `packages/frontend/convex/modelMetrics.ts` - Query and mutation functions for metrics CRUD operations

## Decisions Made
- Used separate tables (modelMetrics vs overallMetrics) for efficient queries - per-model lookups don't need aggregate data
- Implemented upsert pattern for mutations to support idempotent updates from repeated validation runs
- Added by_position_target composite index for efficient model-specific lookups

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Schema and functions deployed to Convex successfully
- Ready for Phase 12 Plan 04 (prediction interval implementation) or backend integration
- Frontend can now consume model metrics via useQuery hooks

---
*Phase: 12-ml-pipeline-improvements*
*Completed: 2026-01-15*
