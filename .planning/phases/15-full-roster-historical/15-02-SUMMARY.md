---
phase: 15-full-roster-historical
plan: 02
subsystem: database
tags: [convex, schema, players, history]

# Dependency graph
requires:
  - phase: 08-convex-backend
    provides: Initial Convex schema with players table
provides:
  - Extended players table with enriched metadata fields
  - playerHistory table for weekly stats caching
  - Efficient indexed lookups for player data
affects: [15-03, 15-04, historical-display, player-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Indexed upsert pattern for efficient bulk operations
    - Optional fields for backward-compatible schema extension

key-files:
  created:
    - packages/frontend/convex/playerHistory.ts
  modified:
    - packages/frontend/convex/schema.ts
    - packages/frontend/convex/players.ts

key-decisions:
  - "Optional enriched fields maintain backward compatibility"
  - "by_player_id index enables efficient upsert lookups"
  - "Three playerHistory indexes cover all query patterns"

patterns-established:
  - "Indexed lookup before upsert for efficient bulk operations"
  - "Optional fields for extensibility without breaking existing data"

# Metrics
duration: 2min
completed: 2026-01-16
---

# Phase 15 Plan 02: Convex Schema Extension Summary

**Extended Convex schema with enriched player metadata and playerHistory table for weekly stats caching**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-16T00:29:24Z
- **Completed:** 2026-01-16T00:31:36Z
- **Tasks:** 4
- **Files modified:** 3

## Accomplishments
- Extended players table with optional enriched fields (jerseyNumber, height, weight, college, yearsExp, headshotUrl)
- Created playerHistory table with indexes for player, season, and week queries
- Updated all player mutations to support enriched data
- Created comprehensive playerHistory CRUD operations

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend players table schema** - `5c5a9bd` (feat)
2. **Task 2: Add playerHistory table to schema** - `4bebfdc` (feat)
3. **Task 3: Update players.ts mutations for enriched data** - `d757296` (feat)
4. **Task 4: Create playerHistory.ts mutations and queries** - `8049a61` (feat)

## Files Created/Modified
- `packages/frontend/convex/schema.ts` - Extended players table, added playerHistory table
- `packages/frontend/convex/players.ts` - Updated upsert/bulkUpsert, added getByPlayerId
- `packages/frontend/convex/playerHistory.ts` - New file with CRUD operations

## Decisions Made
- Optional enriched fields maintain backward compatibility with existing player data
- by_player_id index enables O(1) lookups instead of full table scan for upserts
- Three playerHistory indexes (by_player, by_player_season, by_player_week) cover all expected query patterns

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Schema extended and ready for data population
- playerHistory table ready for weekly stats import
- Ready for 15-03-PLAN.md (Backend Roster + History Fetchers)

---
*Phase: 15-full-roster-historical*
*Completed: 2026-01-16*
