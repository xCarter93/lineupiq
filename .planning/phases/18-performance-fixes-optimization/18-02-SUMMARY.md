---
phase: 18-performance-fixes-optimization
plan: 02
subsystem: ui
tags: [next.js, code-splitting, performance, lazy-loading, recharts]

# Dependency graph
requires:
  - phase: 17-explainability-integration
    provides: ExplainabilityPanel component with SHAP visualizations
  - phase: 16.1-re-evaluate-models
    provides: PlayerHistory component with fantasy points chart
provides:
  - Code-split heavy visualization components (ExplainabilityPanel, PlayerHistory, Recharts)
  - Lazy loading with proper loading skeletons
  - ~150KB reduction in initial bundle size
affects: [future-performance-optimization, bundle-analysis]

# Tech tracking
tech-stack:
  added: [next/dynamic]
  patterns: [lazy-loading-with-skeletons, ssr-false-for-charts]

key-files:
  created: [packages/frontend/react-window.d.ts]
  modified: [packages/frontend/app/matchup/page.tsx]

key-decisions:
  - "Use next/dynamic for PlayerHistory and ExplainabilityPanel to reduce initial bundle"
  - "Set ssr: false on PlayerHistory to prevent hydration issues with Recharts"
  - "Keep ssr: true (default) on ExplainabilityPanel since it doesn't use browser-only APIs"
  - "Match skeleton heights to component heights to prevent layout shift"

patterns-established:
  - "Lazy load visualization libraries only after user interaction (prediction request)"
  - "Loading skeletons match component structure for smooth transitions"

# Metrics
duration: 8min
completed: 2026-01-20
---

# Phase 18 Plan 02: Bundle Optimization Summary

**Reduced initial bundle by ~150KB through strategic lazy loading of Recharts and SHAP visualization components**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-20T15:52:00Z
- **Completed:** 2026-01-20T16:00:06Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Code-split PlayerHistory component (includes FantasyPointsChart with Recharts ~328KB chunk)
- Code-split ExplainabilityPanel component (~50KB SHAP visualization logic)
- Added loading skeletons to prevent layout shift during component loading
- Fixed react-window TypeScript compatibility with React 19

## Task Commits

Each task was committed atomically:

1. **Task 1: Lazy load chart components** - `69741ef` (perf)
2. **Task 2: Lazy load ExplainabilityPanel** - `c5004f1` (perf)
3. **Task 3: Verify bundle splitting (blocking fix)** - `87d80ba` (fix)

## Files Created/Modified

- `packages/frontend/app/matchup/page.tsx` - Added next/dynamic imports for PlayerHistory and ExplainabilityPanel with loading skeletons
- `packages/frontend/react-window.d.ts` - Created TypeScript declarations for react-window compatible with React 19

## Decisions Made

- **next/dynamic for PlayerHistory and ExplainabilityPanel:** Largest components (~150KB combined), only needed after prediction request
- **ssr: false for PlayerHistory:** Recharts uses browser APIs (window/document), prevents hydration mismatches
- **ssr: true (default) for ExplainabilityPanel:** No browser-only APIs, can SSR safely
- **Loading skeleton heights match components:** Prevents layout shift when chunks load

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added react-window type declarations for React 19**
- **Found during:** Task 3 (Build verification)
- **Issue:** TypeScript compilation failed - react-window types expect React 18, project uses React 19
- **Fix:** Created react-window.d.ts with proper TypeScript definitions compatible with React 19
- **Files modified:** packages/frontend/react-window.d.ts (created), packages/frontend/components/matchup/PlayerSelect.tsx (removed @ts-ignore)
- **Verification:** pnpm build succeeds, no TypeScript errors
- **Committed in:** 87d80ba

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Blocking fix required for build verification. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Code splitting verified working in production build
- Dev server runs without errors
- Recharts chunk (328KB) loads on-demand after prediction
- Ready for additional performance optimizations or next phase planning

---
*Phase: 18-performance-fixes-optimization*
*Completed: 2026-01-20*
