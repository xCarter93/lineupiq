---
phase: 08-convex-backend
plan: 01
subsystem: database
tags: [convex, react, next.js, backend-as-a-service]

# Dependency graph
requires:
  - phase: 07-prediction-api
    provides: Python ML prediction endpoints for QB/RB/WR/TE stats
provides:
  - Convex initialization with dev environment
  - Schema with scoringConfigs, cachedPredictions, players tables
  - ConvexClientProvider for React hooks access
affects: [08-convex-backend/02, 08-convex-backend/03, 08-convex-backend/04]

# Tech tracking
tech-stack:
  added: [convex v1.31.4]
  patterns: [ConvexClientProvider wrapping app, schema-first database design]

key-files:
  created:
    - packages/frontend/convex/schema.ts
    - packages/frontend/app/providers/ConvexClientProvider.tsx
  modified:
    - packages/frontend/app/layout.tsx
    - packages/frontend/package.json

key-decisions:
  - "Use v.any() for predictions field to support flexible position-specific data"
  - "Initialize Convex client at module level in provider for singleton pattern"

patterns-established:
  - "ConvexClientProvider: Client component wrapping app for hooks access"
  - "Schema indexes: by_default for configs, by_player_week for predictions, by_position/team for players"

# Metrics
duration: 8min
completed: 2026-01-15
---

# Phase 08-01: Convex Initialization Summary

**Convex backend initialized with schema for scoring configs, prediction caching, and player metadata**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-15T14:30:00Z
- **Completed:** 2026-01-15T14:38:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Convex project initialized with dev environment connected to cloud
- Schema defines three tables with appropriate indexes for efficient queries
- ConvexClientProvider enables React hooks throughout the app
- Build passes with Convex integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Convex and initialize project** - `e2d2b0f` (feat)
2. **Task 2: Create Convex schema with tables** - `731009b` (feat)
3. **Task 3: Create ConvexClientProvider and integrate into layout** - `d68d65b` (feat)

## Files Created/Modified
- `packages/frontend/convex/schema.ts` - Defines scoringConfigs, cachedPredictions, players tables with indexes
- `packages/frontend/app/providers/ConvexClientProvider.tsx` - Client-side provider for Convex React hooks
- `packages/frontend/app/layout.tsx` - Updated to wrap children with ConvexClientProvider
- `packages/frontend/package.json` - Added convex dependency

## Decisions Made
- Used `v.any()` for the predictions field in cachedPredictions to allow flexible position-specific data structures
- Created ConvexReactClient as module-level singleton to avoid re-instantiation on re-renders

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required

The user manually completed Convex project initialization via `pnpm dlx convex dev`:
- Authenticated with Convex account
- Created project "lineupiq"
- `.env.local` auto-generated with `NEXT_PUBLIC_CONVEX_URL`

## Next Phase Readiness
- Convex foundation complete, ready for query and mutation functions
- Schema deployed to Convex dev environment
- Next plan (08-02) will add query functions for reading data

---
*Phase: 08-convex-backend*
*Completed: 2026-01-15*
