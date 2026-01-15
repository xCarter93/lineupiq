---
phase: 04-feature-engineering
plan: 02
subsystem: features
tags: [polars, opponent-strength, defensive-rankings, matchup-features, ml-features]

# Dependency graph
requires:
  - phase: 03-data-processing
    provides: Processed player stats with opponent column from schedule join
provides:
  - add_opponent_strength: Main entry point for opponent defensive features
  - compute_defensive_stats: Aggregate stats allowed by each defense
  - compute_defensive_rankings: Season-to-date rankings without data leakage
affects: [05-model-development, 06-model-evaluation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Defensive stats computed by grouping on opponent (team being scored against)
    - Rankings use only prior weeks to avoid data leakage
    - Normalization to 0-1 scale: (rank-1)/(N-1) where 0=best defense

key-files:
  created:
    - packages/backend/src/lineupiq/features/opponent_features.py
    - packages/backend/tests/test_opponent_features.py
  modified:
    - packages/backend/src/lineupiq/features/__init__.py

key-decisions:
  - "Rank 1 = best defense (fewest yards allowed)"
  - "Normalize to 0-1 where 0=best (hardest matchup), 1=worst (easiest matchup)"
  - "Week N rankings use only weeks 1 to N-1 to avoid data leakage"
  - "Week 1 has null rankings (no prior data)"

patterns-established:
  - "Opponent features joined on opponent + season + week"
  - "Defensive stats = stats scored AGAINST a team"

# Metrics
duration: 3 min
completed: 2026-01-15
---

# Phase 4 Plan 2: Opponent Defensive Strength Metrics Summary

**Opponent defensive strength features computing season-to-date rankings from prior weeks only, with 0-1 normalization where 0=best defense (hardest matchup) and 1=worst defense (easiest matchup)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-15T00:25:21Z
- **Completed:** 2026-01-15T00:28:28Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created opponent_features.py module with defensive strength computation
- compute_defensive_stats aggregates yards allowed by each defense per week
- compute_defensive_rankings computes season-to-date rankings using ONLY prior weeks (no leakage)
- add_opponent_strength is main entry point that orchestrates stats -> rankings -> join
- Normalized rankings to 0-1 scale: 0=best defense (rank 1), 1=worst defense (rank 32)
- 11 unit tests covering aggregation, ordering, leakage prevention, normalization, and joins
- Verified with real 2024 data: 6123 rows processed, all strength values in [0, 1] range

## Task Commits

Each task was committed atomically:

1. **Task 1: Create opponent_features module** - `4c8decf` (feat)
2. **Task 2: Add unit tests** - `5cf650e` (test)

## Files Created/Modified

- `packages/backend/src/lineupiq/features/opponent_features.py` - Main module with 3 functions
- `packages/backend/tests/test_opponent_features.py` - 11 comprehensive tests
- `packages/backend/src/lineupiq/features/__init__.py` - Updated exports

## Decisions Made

- **Rank interpretation:** Rank 1 = best defense (allows fewest yards), helps model understand matchup difficulty
- **Normalization scale:** 0-1 where 0 is hardest matchup (best defense), 1 is easiest matchup (worst defense)
- **Data leakage prevention:** Week N rankings computed from weeks 1 to N-1 only
- **Week 1 handling:** Null values for week 1 since no prior data exists

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Opponent strength features ready for model consumption
- opp_pass_defense_strength and opp_rush_defense_strength available
- Rankings correctly avoid data leakage
- Ready for 04-03 (Weather and venue features)

---
*Phase: 04-feature-engineering*
*Completed: 2026-01-15*
