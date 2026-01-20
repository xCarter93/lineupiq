---
phase: 17-model-explainability-ui
plan: 01
subsystem: api
tags: [shap, explainability, fastapi, pydantic]

# Dependency graph
requires:
  - phase: 06-model-evaluation
    provides: SHAP infrastructure (compute_shap_values, TreeExplainer)
  - phase: 07-prediction-api
    provides: FastAPI routes pattern, PredictionRequest schema
provides:
  - POST /api/explain/{position}/{target} endpoint
  - ExplainabilityRequest, ExplainabilityResponse schemas
  - FEATURE_DISPLAY_NAMES for human-readable explanations
  - Natural language summary generation
affects: [17-02, 17-03, 17-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SHAP-based single prediction explanation
    - Feature contribution sorting by absolute impact

key-files:
  created:
    - packages/backend/src/lineupiq/api/schemas/explainability.py
    - packages/backend/src/lineupiq/api/routes/explainability.py
  modified:
    - packages/backend/src/lineupiq/api/schemas/__init__.py
    - packages/backend/src/lineupiq/api/routes/__init__.py
    - packages/backend/src/lineupiq/api/main.py

key-decisions:
  - "28 FEATURE_DISPLAY_NAMES for human-readable explanations"
  - "Contributions sorted by absolute SHAP value (most impactful first)"
  - "Natural language summary with top 2-3 positive and 1-2 negative factors"

# Metrics
duration: 12min
completed: 2026-01-19
---

# Phase 17 Plan 01: Backend SHAP API Summary

**SHAP-based explainability endpoint returning feature contributions and natural language summaries for individual predictions**

## Performance

- **Duration:** 12 min
- **Started:** 2026-01-19T00:00:00Z
- **Completed:** 2026-01-19T00:12:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Created POST /api/explain/{position}/{target} endpoint
- Built ExplainabilityRequest/Response schemas with FeatureContribution model
- Added FEATURE_DISPLAY_NAMES mapping 28 features to user-friendly names
- Implemented natural language summary generation highlighting prediction drivers
- Integrated with existing SHAP infrastructure from importance.py
- Validation returns 400 for invalid position/target combinations

## Task Commits

Each task was committed atomically:

1. **Task 1: Create explainability schemas** - `f03f65c` (feat)
2. **Task 2: Create explainability endpoint** - `43dbee8` (feat)

Note: Task 3 (natural language summary generation) was included in Task 2 as the generate_summary() function.

## Files Created/Modified

- `packages/backend/src/lineupiq/api/schemas/explainability.py` - ExplainabilityRequest, ExplainabilityResponse, FeatureContribution schemas, FEATURE_DISPLAY_NAMES, TARGET_DISPLAY_NAMES, VALID_TARGETS constants
- `packages/backend/src/lineupiq/api/routes/explainability.py` - POST endpoint, prepare_features(), generate_summary() functions
- `packages/backend/src/lineupiq/api/schemas/__init__.py` - Export new schemas
- `packages/backend/src/lineupiq/api/routes/__init__.py` - Export explainability_router
- `packages/backend/src/lineupiq/api/main.py` - Register router at /api/explain prefix

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| 28 FEATURE_DISPLAY_NAMES dict | Maps raw feature names to human-readable display names for UI |
| Contributions sorted by absolute SHAP value | Most impactful features shown first for decision support |
| Natural language summary with 2-3 positive, 1-2 negative factors | Concise explanation without overwhelming users |
| VALID_TARGETS dict per position | Clear validation of which targets are valid for each position |

## Deviations from Plan

None - plan executed exactly as written. Task 3 (natural language summary) was implemented as part of Task 2 since it was a function within the same route file.

## Issues Encountered

None - existing SHAP infrastructure in importance.py worked seamlessly with the new endpoint.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Explainability API ready for frontend integration
- /api/explain/{position}/{target} returns full ExplainabilityResponse
- Ready for 17-02 (UI components) which appears to be complete
- Next: 17-03 Dashboard Integration

---
*Phase: 17-model-explainability-ui*
*Completed: 2026-01-19*
