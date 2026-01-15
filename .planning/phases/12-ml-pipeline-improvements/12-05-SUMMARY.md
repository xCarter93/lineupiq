---
phase: 12-ml-pipeline-improvements
plan: 05
subsystem: frontend
tags: [ui, model-confidence, validation-metrics, react]

# Dependency graph
requires:
  - phase: 12-03
    provides: Convex schema for model metrics storage
  - phase: 12-04
    provides: Backend validation metrics computation
provides:
  - ModelConfidence component for displaying accuracy
  - useModelMetrics hook for data access
  - Validation API client in prediction-api.ts
affects: [17-model-explainability-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Convex-first with API fallback pattern in hooks
    - Color-coded confidence tiers for trust signals

key-files:
  created:
    - packages/frontend/hooks/useModelMetrics.ts
    - packages/frontend/components/matchup/ModelConfidence.tsx
  modified:
    - packages/frontend/lib/prediction-api.ts
    - packages/frontend/app/matchup/page.tsx

key-decisions:
  - "Added validation API to prediction-api.ts rather than creating separate api.ts"
  - "Integrated ModelConfidence in page.tsx not MatchupForm.tsx (form is input-only)"
  - "Three-tier color coding: emerald (High), amber (Medium), muted (Low)"

patterns-established:
  - "Hook pattern: Convex query first, API fallback if null"

# Metrics
duration: 5 min
completed: 2026-01-15
---

# Phase 12 Plan 05: Model Confidence UI Summary

**Display model confidence in the matchup UI to build user trust by showing how confident the model is in its predictions.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-15
- **Completed:** 2026-01-15
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Added validation metrics API client (types + fetch function) to prediction-api.ts
- Created useModelMetrics hook with Convex-first, API-fallback pattern
- Built ModelConfidence component with color-coded accuracy display
- Integrated confidence indicator into matchup page results section

## Task Commits

Each task was committed atomically:

1. **Task 1: Add API client for validation metrics** - `74dd2f1` (feat)
2. **Task 2: Create useModelMetrics hook** - `f9a16b0` (feat)
3. **Task 3: Create ModelConfidence component and integrate** - `6fc8153` (feat)

## Files Created/Modified

- `packages/frontend/lib/prediction-api.ts` - Added ValidationResponse types and fetchValidationMetrics function
- `packages/frontend/hooks/useModelMetrics.ts` - Hook for accessing model metrics with caching
- `packages/frontend/components/matchup/ModelConfidence.tsx` - UI component for confidence display
- `packages/frontend/app/matchup/page.tsx` - Integrated ModelConfidence in results section

## Decisions Made

- Added validation API functions to existing prediction-api.ts rather than creating new api.ts file (consolidates API client code)
- Integrated ModelConfidence in matchup/page.tsx where predictions are rendered, not in MatchupForm.tsx (which is purely input)
- Used three-tier color scheme: emerald-600 (High), amber-600 (Medium), muted-foreground (Low)

## Deviations from Plan

- Plan suggested modifying MatchupForm.tsx, but integration in page.tsx is architecturally correct since MatchupForm only handles input
- Used existing prediction-api.ts instead of creating new api.ts file

## Issues Encountered

None

## User Setup Required

None - requires backend validation endpoint from plan 12-04 to show actual metrics

## Next Phase Readiness

- ModelConfidence displays loading state when metrics unavailable
- Component gracefully returns null if no data
- Ready for Phase 13+ when validation endpoint is deployed

---
*Phase: 12-ml-pipeline-improvements*
*Completed: 2026-01-15*
