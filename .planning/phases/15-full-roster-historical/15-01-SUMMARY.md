---
phase: 15-full-roster-historical
plan: 01
subsystem: api
tags: [nflreadpy, fastapi, pydantic, roster, polars]

# Dependency graph
requires:
  - phase: 07-prediction-api
    provides: FastAPI app structure, route patterns
provides:
  - GET /api/roster endpoint for full NFL roster
  - GET /api/player/{id}/history endpoint for player stats
  - fetch_rosters() and fetch_player_history() data functions
affects: [15-03, 15-04, 16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Polars DataFrame for roster data filtering
    - nflreadpy roster API integration

key-files:
  created:
    - packages/backend/src/lineupiq/api/schemas/roster.py
    - packages/backend/src/lineupiq/api/routes/roster.py
  modified:
    - packages/backend/src/lineupiq/data/fetchers.py
    - packages/backend/src/lineupiq/api/schemas/__init__.py
    - packages/backend/src/lineupiq/api/routes/__init__.py
    - packages/backend/src/lineupiq/api/main.py

key-decisions:
  - "Height stored as integer (inches) not string - nflreadpy returns inches"
  - "Filter players without gsis_id - required for player history lookup"
  - "FANTASY_POSITIONS includes K for roster display (vs SKILL_POSITIONS)"

# Metrics
duration: 12 min
completed: 2026-01-15
---

# Phase 15 Plan 01: Backend Roster + Player History API Summary

**Two new API endpoints for fetching NFL roster and player game-by-game history from nflreadpy**

## Performance

- **Duration:** 12 min
- **Started:** 2026-01-15T16:20:00Z
- **Completed:** 2026-01-15T16:32:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- fetch_rosters() returns ~1020 fantasy-relevant players (QB/RB/WR/TE/K)
- fetch_player_history() returns weekly stats for any player by gsis_id
- GET /api/roster?season=2025 returns full roster with player bio data
- GET /api/player/{player_id}/history?seasons=3 returns game-by-game stats
- 404 returned for unknown player_id

## Task Commits

Each task was committed atomically:

1. **Task 1: Add roster fetcher to data module** - `3d5a751` (feat)
2. **Task 2: Create roster API schemas** - `ebd34c7` (feat)
3. **Task 3: Create roster API routes** - `3af6657` (feat)
4. **Bug fix: Data types and filtering** - `cf9784c` (fix)

## Files Created/Modified

- `packages/backend/src/lineupiq/data/fetchers.py` - Added fetch_rosters() and fetch_player_history()
- `packages/backend/src/lineupiq/api/schemas/roster.py` - PlayerRoster, RosterResponse, WeeklyStats, PlayerHistoryResponse models
- `packages/backend/src/lineupiq/api/routes/roster.py` - /api/roster and /api/player/{id}/history endpoints
- `packages/backend/src/lineupiq/api/schemas/__init__.py` - Export new schemas
- `packages/backend/src/lineupiq/api/routes/__init__.py` - Export roster_router
- `packages/backend/src/lineupiq/api/main.py` - Register roster_router

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Height as int (inches) | nflreadpy returns height in inches, not as formatted string |
| Filter null gsis_id | Players without gsis_id can't be looked up in player history |
| FANTASY_POSITIONS includes K | Roster display needs kickers, separate from SKILL_POSITIONS for ML |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Changed height field type from str to int**
- **Found during:** Verification (API test returned 500)
- **Issue:** Plan specified height as str (e.g., "6-2"), but nflreadpy returns int (inches)
- **Fix:** Updated PlayerRoster.height type to `int | None`
- **Files modified:** packages/backend/src/lineupiq/api/schemas/roster.py
- **Verification:** API now returns valid JSON with integer heights
- **Committed in:** cf9784c

**2. [Rule 3 - Blocking] Filter out players with null gsis_id**
- **Found during:** Verification (API test returned 500)
- **Issue:** One player in roster had null gsis_id, causing Pydantic validation error
- **Fix:** Added filter in fetch_rosters() to exclude players without gsis_id
- **Files modified:** packages/backend/src/lineupiq/data/fetchers.py
- **Verification:** API now returns 1020 players without validation errors
- **Committed in:** cf9784c

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correct API operation. No scope creep.

## Issues Encountered

None - deviations were discovered during verification and fixed immediately.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Roster and history endpoints ready for frontend consumption
- Ready for 15-02 (Convex Schema Enhancements) - already completed
- Ready for 15-03 (Frontend Roster Sync + Admin Page)

---
*Phase: 15-full-roster-historical*
*Completed: 2026-01-15*
