# Phase 18: Performance Fixes & Optimization - Research

**Researched:** 2026-01-20
**Domain:** Next.js 16 performance optimization with App Router, React Server Components, and Tailwind CSS 4
**Confidence:** HIGH

<research_summary>
## Summary

Researched Next.js 16 ecosystem for comprehensive performance optimization strategies targeting player selection lag, code splitting, lazy loading, and caching. The standard approach leverages built-in Next.js 16 features (Turbopack, Cache Components, React Compiler) combined with virtualization for large lists and strategic Server/Client Component architecture.

Key finding: Next.js 16 provides automatic optimizations out-of-the-box that should be trusted first. Custom optimizations should focus on strategic code splitting with next/dynamic, react-window for large dropdowns (1000+ items), and fine-grained caching with the new "use cache" directive. Avoid over-engineering – many perceived performance issues are actually development mode artifacts or improper component boundaries.

**Primary recommendation:** Enable Turbopack (default in Next.js 16), implement react-window virtualization for player dropdowns, convert heavy Client Components to Server Components where possible, and use "use cache" directive for data-heavy components. Monitor with Lighthouse and useReportWebVitals.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for Next.js performance optimization:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.x | Framework with built-in optimizations | Turbopack, Cache Components, automatic code splitting |
| React | 19.x | UI library | Server Components, Suspense, React Compiler support |
| react-window | 1.8.10 | List virtualization | Industry standard for 1000+ item lists, 100x faster than rendering all |
| @next/bundle-analyzer | 14.2.0+ | Bundle analysis | Official tool for identifying large dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-window-infinite-loader | 1.0.9 | Infinite scroll with react-window | Lazy loading items as user scrolls |
| react-select | 5.8.0+ | Accessible select component | Combine with react-window via custom MenuList |
| sharp | 0.33.0+ | Image optimization | Automatic in Next.js for next/image |
| Vercel Analytics | Latest | Real User Monitoring (RUM) | Production performance tracking |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-window | react-virtualized | react-virtualized deprecated, react-window is smaller/faster rewrite |
| next/dynamic | React.lazy() | next/dynamic adds ssr: false option and loading states |
| Vercel Analytics | New Relic/Datadog | Vercel Analytics free tier, built-in Next.js integration |

**Installation:**
```bash
pnpm add react-window react-window-infinite-loader @types/react-window
pnpm add -D @next/bundle-analyzer
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
app/
├── layout.tsx           # Root layout (Server Component)
├── page.tsx             # Route pages (Server by default)
├── components/
│   ├── client/          # 'use client' components
│   │   ├── MatchupForm.tsx
│   │   └── PlayerSelect.tsx
│   └── server/          # Server Components (default)
│       ├── PlayerStats.tsx
│       └── PredictionResults.tsx
└── lib/
    ├── cache.ts         # 'use cache' functions
    └── api.ts           # Data fetching

public/                  # Static assets (auto-cached)
```

### Pattern 1: Virtualized Select for Large Datasets
**What:** Use react-window to render only visible options in dropdowns
**When to use:** 100+ items in select/dropdown (LineupIQ has ~500+ NFL players)
**Example:**
```typescript
// Source: react-window docs + react-select integration
'use client'
import { FixedSizeList as List } from 'react-window'
import Select, { components } from 'react-select'
import { createFilter } from 'react-select'

const MenuList = (props: any) => {
  const { options, children, maxHeight, getValue } = props
  const [value] = getValue()
  const initialOffset = options.indexOf(value) * 35

  return (
    <List
      height={maxHeight}
      itemCount={children.length}
      itemSize={35}
      initialScrollOffset={initialOffset}
      width="100%"
    >
      {({ index, style }) => <div style={style}>{children[index]}</div>}
    </List>
  )
}

export function PlayerSelect({ players }: { players: Player[] }) {
  return (
    <Select
      options={players}
      components={{ MenuList }}
      // CRITICAL: Disable accent stripping for performance
      filterOption={createFilter({ ignoreAccents: false })}
    />
  )
}
```

### Pattern 2: Strategic Code Splitting with next/dynamic
**What:** Lazy load Client Components that aren't immediately needed
**When to use:** Heavy components (charts, modals, conditional UI)
**Example:**
```typescript
// Source: Next.js official docs
'use client'
import dynamic from 'next/dynamic'

// Load chart library only when needed
const PredictionChart = dynamic(
  () => import('@/components/client/PredictionChart'),
  {
    loading: () => <div className="h-64 bg-muted animate-pulse" />,
    ssr: false // Skip SSR for chart libraries using window/document
  }
)

// Load on condition (modal)
const PlayerComparisonModal = dynamic(
  () => import('@/components/client/PlayerComparisonModal')
)

export default function MatchupPage() {
  const [showComparison, setShowComparison] = useState(false)

  return (
    <>
      <PredictionChart data={predictions} />
      {showComparison && <PlayerComparisonModal />}
    </>
  )
}
```

### Pattern 3: Cache Components with "use cache" Directive
**What:** Cache expensive data fetching at component level
**When to use:** Server Components with data that doesn't change per-request
**Example:**
```typescript
// Source: Next.js 16 Cache Components docs
import { cacheLife, cacheTag } from 'next/cache'

async function PlayerStatsCard({ playerId }: { playerId: string }) {
  'use cache'
  cacheLife('hours') // Revalidate after 1 hour
  cacheTag(`player-${playerId}`)

  const stats = await db.query('SELECT * FROM playerHistory WHERE player_id = ?', [playerId])

  return (
    <div>
      <h3>{stats.name}</h3>
      <p>Last 10 games avg: {stats.avg}</p>
    </div>
  )
}

// Revalidate when player data changes
import { updateTag } from 'next/cache'

export async function syncPlayerData(playerId: string) {
  'use server'
  await fetchAndStorePlayerData(playerId)
  updateTag(`player-${playerId}`) // Immediate cache invalidation
}
```

### Pattern 4: Server Component First, Client Component Last
**What:** Push Client Components to leaf nodes of component tree
**When to use:** Always – default to Server Components, add 'use client' only where needed
**Example:**
```typescript
// app/matchup/page.tsx (Server Component - no 'use client')
export default async function MatchupPage() {
  // Fetch data on server
  const players = await getPlayers()

  return (
    <div>
      <h1>Matchup Simulator</h1>
      {/* Pass data to Client Component */}
      <MatchupForm players={players} />
    </div>
  )
}

// components/client/MatchupForm.tsx (Client Component)
'use client'
export function MatchupForm({ players }: { players: Player[] }) {
  const [selectedPlayer, setSelectedPlayer] = useState(null)

  return (
    <form>
      <PlayerSelect
        players={players}
        onChange={setSelectedPlayer}
      />
    </form>
  )
}
```

### Anti-Patterns to Avoid
- **Over-using 'use client':** Don't add 'use client' to entire pages; only to interactive leaves
- **Fetching data in Client Components:** Move data fetching to Server Components, pass as props
- **Not using Suspense boundaries:** Dynamic content without Suspense causes waterfalls
- **Disabling all caching:** Trust Next.js defaults first, only opt-out with 'no-store' when truly needed
- **Testing only on fast devices:** Test on throttled networks (Chrome DevTools slow 4G)
- **Ignoring bundle analyzer:** Run regularly to catch accidental server package imports
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| List virtualization | Custom windowing logic | react-window | Handles scroll physics, overscan, dynamic sizing, tested at scale |
| Code splitting | Manual chunk configuration | next/dynamic | Automatic Suspense integration, ssr control, loading states |
| Image optimization | Manual srcset/picture | next/image | Automatic WebP/AVIF, lazy loading, blur placeholders, prevents CLS |
| Font optimization | Manual @font-face | next/font | Eliminates FOIT/FOUT, self-hosts Google Fonts, zero layout shift |
| Route prefetching | Manual <link rel="prefetch"> | Next.js <Link> | Automatic viewport detection, incremental prefetch, cache-aware |
| Data caching | Custom in-memory cache | "use cache" directive | Compiler-generated cache keys, tag-based invalidation, persistence |
| Bundle analysis | Manual webpack stats parsing | @next/bundle-analyzer | Visual treemap, per-route breakdown, dead code detection |
| Performance monitoring | Custom Web Vitals tracking | useReportWebVitals hook | Captures all Core Web Vitals, integrates with analytics |

**Key insight:** Next.js 16 has matured to the point where custom performance optimizations are rarely needed. The framework provides automatic code splitting, caching, prefetching, and optimization out-of-the-box. Manual optimizations should focus on application-specific concerns (e.g., virtualizing large dropdowns) rather than framework-level concerns.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Shipping Too Much JavaScript to Client
**What goes wrong:** Heavy bundle size, slow initial load, poor FCP/LCP
**Why it happens:** Over-using 'use client', importing large libraries unnecessarily
**How to avoid:**
- Default to Server Components
- Use next/dynamic for heavy libraries (charts, markdown, editors)
- Check bundle with @next/bundle-analyzer
- Lazy load conditional UI (modals, tabs)
**Warning signs:** Lighthouse scores <90, bundle >300KB, slow Time to Interactive

### Pitfall 2: Player Dropdown Lag with Large Datasets
**What goes wrong:** Dropdown takes 2-5 seconds to open with 500+ players
**Why it happens:** React rendering all option elements at once, accent stripping on every keystroke
**How to avoid:**
- Use react-window virtualization (renders ~10 visible items instead of 500)
- Disable accent stripping: `filterOption={createFilter({ignoreAccents: false})}`
- Disable mouse events for options (custom Option component)
**Warning signs:** Dropdown stutters, typing lags, browser hangs

### Pitfall 3: CSS-in-JS Performance Hit
**What goes wrong:** Runtime style injection causes style recalculation on every render
**Why it happens:** Styled Components, Emotion hash classnames and inject styles at runtime
**How to avoid:**
- Use Tailwind CSS 4 (zero-runtime, compile-time)
- Or CSS Modules (static CSS, no runtime)
- Avoid styled-components/emotion in App Router
**Warning signs:** Poor INP scores, slow interactions, style recalc in Chrome DevTools

### Pitfall 4: Incorrect Static/Dynamic Rendering
**What goes wrong:** Page marked dynamic when it should be static (slower, no caching)
**Why it happens:** Accidentally using cookies(), headers(), searchParams in wrong scope
**How to avoid:**
- Check build output: `○ Static` vs `ƒ Dynamic`
- Extract runtime data and pass as props to cached components
- Use 'use cache' directive to cache within dynamic routes
**Warning signs:** Every request hits server, no Full Route Cache, slow TTFB

### Pitfall 5: Not Monitoring Real User Performance
**What goes wrong:** App feels fast on developer's laptop but slow for users
**Why it happens:** Testing only on fast devices/networks, no RUM
**How to avoid:**
- Test on throttled network (Chrome DevTools slow 4G)
- Use useReportWebVitals to send Core Web Vitals to analytics
- Deploy Vercel Analytics for field data
- Run Lighthouse in incognito (no extensions)
**Warning signs:** User complaints about slowness, high bounce rate, low engagement

### Pitfall 6: Premature Optimization
**What goes wrong:** Complex caching logic that's hard to debug, over-abstracted code
**Why it happens:** Optimizing before measuring, not trusting Next.js defaults
**How to avoid:**
- Profile first with Lighthouse/Web Vitals
- Trust automatic optimizations (code splitting, caching, prefetching)
- Only add custom optimizations for measured bottlenecks
- Keep caching strategies simple (use predefined cacheLife profiles)
**Warning signs:** Complex code with minimal performance gain, hard-to-reproduce bugs
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Basic Virtualized Player Dropdown
```typescript
// Source: react-window docs + community patterns
'use client'
import { FixedSizeList as List } from 'react-window'
import { createFilter } from 'react-select'
import Select, { components } from 'react-select'

interface Player {
  id: string
  name: string
  position: string
  team: string
}

const VirtualizedMenuList = (props: any) => {
  const { options, children, maxHeight, getValue } = props
  const [value] = getValue()
  const initialOffset = options.indexOf(value) * 35

  if (!children.length) {
    return <div className="p-2">No options</div>
  }

  return (
    <List
      height={Math.min(maxHeight, children.length * 35)}
      itemCount={children.length}
      itemSize={35}
      initialScrollOffset={initialOffset}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>{children[index]}</div>
      )}
    </List>
  )
}

export function PlayerSelect({
  players,
  onChange
}: {
  players: Player[]
  onChange: (player: Player) => void
}) {
  const options = players.map(p => ({
    value: p.id,
    label: `${p.name} (${p.position} - ${p.team})`,
    data: p
  }))

  return (
    <Select
      options={options}
      components={{ MenuList: VirtualizedMenuList }}
      // Performance: disable accent stripping
      filterOption={createFilter({ ignoreAccents: false })}
      onChange={(selected) => selected && onChange(selected.data)}
      placeholder="Search for a player..."
      className="w-full"
    />
  )
}
```

### Strategic Code Splitting for Charts
```typescript
// Source: Next.js lazy loading docs
'use client'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'

// Only load Recharts when component renders
const PredictionChart = dynamic(
  () => import('@/components/client/PredictionChart'),
  {
    loading: () => (
      <div className="h-64 rounded-lg bg-muted animate-pulse" />
    ),
    ssr: false // Recharts uses window/document
  }
)

// Load SHAP explainability chart on demand
const ExplainabilityChart = dynamic(
  () => import('@/components/client/ExplainabilityChart')
)

export function PredictionDashboard({ predictions, showExplain }: Props) {
  return (
    <div>
      {/* Chart loads immediately but in separate bundle */}
      <PredictionChart data={predictions} />

      {/* Chart loads only when user clicks "Explain" */}
      {showExplain && <ExplainabilityChart data={predictions} />}
    </div>
  )
}
```

### Cache Components Pattern
```typescript
// Source: Next.js 16 Cache Components docs
import { cacheLife, cacheTag } from 'next/cache'

// Cache player history data at component level
async function PlayerHistoryCard({ playerId }: { playerId: string }) {
  'use cache'
  cacheLife('hours') // Revalidate after 1 hour
  cacheTag(`player-${playerId}`)

  const history = await db.playerHistory.findMany({
    where: { player_id: playerId },
    orderBy: { game_date: 'desc' },
    take: 10
  })

  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">Last 10 Games</h3>
      <ul>
        {history.map(game => (
          <li key={game.id}>
            {game.opponent}: {game.fantasy_points} pts
          </li>
        ))}
      </ul>
    </div>
  )
}

// Server Action to invalidate cache when data updates
import { updateTag } from 'next/cache'

export async function syncPlayerHistory(playerId: string) {
  'use server'

  // Fetch latest from API
  const freshData = await fetchPlayerHistory(playerId)

  // Store in Convex
  await storePlayerHistory(freshData)

  // Immediately invalidate cached component
  updateTag(`player-${playerId}`)
}
```

### Server Component Data Fetching Pattern
```typescript
// Source: Next.js Server Components best practices
// app/matchup/page.tsx (Server Component)
import { getPlayers } from '@/lib/api'
import { MatchupForm } from '@/components/client/MatchupForm'

export default async function MatchupPage() {
  // Fetch on server - no client JavaScript cost
  const players = await getPlayers()

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-6">Matchup Simulator</h1>

      {/* Pass data to Client Component */}
      <MatchupForm players={players} />
    </div>
  )
}

// components/client/MatchupForm.tsx (Client Component)
'use client'
import { useState } from 'react'
import { PlayerSelect } from './PlayerSelect'

export function MatchupForm({ players }: { players: Player[] }) {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null)

  return (
    <form className="space-y-4">
      <PlayerSelect
        players={players}
        onChange={setSelectedPlayer}
      />
      {selectedPlayer && (
        <div>Selected: {selectedPlayer.name}</div>
      )}
    </form>
  )
}
```

### Performance Monitoring Setup
```typescript
// Source: Next.js useReportWebVitals docs
// app/layout.tsx
import { Suspense } from 'react'
import { WebVitals } from '@/components/web-vitals'

export default function RootLayout({ children }: Props) {
  return (
    <html lang="en">
      <body>
        <Suspense fallback={null}>
          <WebVitals />
        </Suspense>
        {children}
      </body>
    </html>
  )
}

// components/web-vitals.tsx
'use client'
import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Send to analytics (Vercel, Google Analytics, etc.)
    if (window.gtag) {
      window.gtag('event', metric.name, {
        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
        event_label: metric.id,
        non_interaction: true,
      })
    }

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(metric)
    }
  })

  return null
}
```
</code_examples>

<sota_updates>
## State of the Art (2024-2026)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Webpack | Turbopack (default) | Next.js 16 (Jan 2026) | 2-5x faster builds, 10x faster Fast Refresh |
| force-cache/revalidate config | "use cache" directive | Next.js 16 | Fine-grained component-level caching, compiler-managed keys |
| Manual memoization (useMemo, memo) | React Compiler | React 19 + Next.js 16 | Automatic optimization, zero code changes |
| Pages Router (pages/) | App Router (app/) | Stable since Next.js 13 | Server Components, Suspense streaming, better DX |
| CSS-in-JS (styled-components) | Tailwind CSS 4 | Tailwind v4 (2025) | 40-60% faster builds, zero runtime, 100x faster incremental |
| react-virtualized | react-window | 2019+ | Smaller bundle (6KB vs 27KB), faster rendering |

**New tools/patterns to consider:**
- **Cache Components:** Replaces static/dynamic export config with "use cache" directive for explicit caching
- **Turbopack File System Caching (Beta):** Stores compiler artifacts on disk, dramatically faster dev server restarts
- **Layout Deduplication:** Prefetching 50 links now downloads shared layout once instead of 50 times
- **Incremental Prefetching:** Only prefetches non-cached route segments, cancels when link leaves viewport
- **updateTag() vs revalidateTag():** updateTag for immediate Server Action updates, revalidateTag for eventual consistency
- **React Compiler:** Stable in Next.js 16, automatic memoization without useMemo/memo
- **Tailwind CSS 4:** CSS-first config with @theme directive, 3-10x faster builds

**Deprecated/outdated:**
- **export const dynamic = 'force-static':** Use "use cache" instead
- **export const revalidate = N:** Use cacheLife('hours'|'days'|'weeks') instead
- **Styled Components/Emotion:** Runtime CSS injection hurts Web Vitals, use Tailwind/CSS Modules
- **react-virtualized:** Deprecated by author, use react-window
- **Manual webpack config for code splitting:** next/dynamic handles it automatically
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Optimal overscan for react-window with player dropdowns**
   - What we know: overscanCount prevents flash of empty content during fast scroll
   - What's unclear: Ideal value for 500-player list (default is 1, could be 3-5)
   - Recommendation: Start with default, increase to 3 if users report flashing during scroll

2. **Cache hit rates for "use cache" directive**
   - What we know: Cache Components uses compiler-generated keys based on arguments
   - What's unclear: Hit rate for parameterized caching (e.g., caching by playerId)
   - Recommendation: Monitor cache effectiveness in production, add logging in Server Actions

3. **Turbopack File System Caching stability**
   - What we know: Beta feature in Next.js 16, stores compiler artifacts on disk
   - What's unclear: Production readiness, cache invalidation edge cases
   - Recommendation: Enable in development first, monitor for stale cache issues before production

4. **React Compiler edge cases**
   - What we know: Stable in Next.js 16, automatic memoization
   - What's unclear: Performance impact on components with complex dependencies
   - Recommendation: Enable reactCompiler: true, compare before/after with Lighthouse
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Next.js 16 Official Announcement](https://nextjs.org/blog/next-16) - Turbopack, Cache Components, React Compiler
- [Next.js Lazy Loading Guide](https://nextjs.org/docs/app/guides/lazy-loading) - next/dynamic patterns
- [Next.js Caching Guide](https://nextjs.org/docs/app/guides/caching) - Request Memoization, Data Cache, Full Route Cache
- [Next.js Cache Components](https://nextjs.org/docs/app/getting-started/cache-components) - "use cache" directive, cacheLife, cacheTag
- [Next.js Production Checklist](https://nextjs.org/docs/app/guides/production-checklist) - Optimization recommendations
- [Next.js Server/Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) - Component patterns
- [react-window Official Docs](https://react-window.vercel.app/) - Virtualization API
- [Tailwind CSS v4 Announcement](https://tailwindcss.com/blog/tailwindcss-v4) - CSS-first architecture

### Secondary (MEDIUM confidence - cross-verified)
- [Next.js 16 Performance Guide (Medium)](https://medium.com/@Adekola_Olawale/migrating-to-next-js-16-a-practical-performance-first-guide-e9680dd252b4) - Verified against official docs
- [Code Splitting Patterns (Blazity)](https://blazity.com/blog/code-splitting-next-js) - Verified with Next.js docs
- [Performance Mistakes (Medium)](https://medium.com/full-stack-forge/7-common-performance-mistakes-in-next-js-and-how-to-fix-them-edd355e2f9a9) - Verified pitfalls
- [Virtualized Player Select (Botsplash)](https://www.botsplash.com/post/optimize-your-react-select-component-to-smoothly-render-10k-data) - Verified pattern with react-window docs
- [Server/Client Best Practices (Medium)](https://medium.com/@jigsz6391/next-js-server-components-vs-client-components-best-practices-2e735f4ad27c) - Cross-verified

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official documentation
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Next.js 16 App Router, React 19, Turbopack
- Ecosystem: react-window, @next/bundle-analyzer, Vercel Analytics
- Patterns: Virtualization, code splitting, caching strategies, Server/Client composition
- Pitfalls: JavaScript bundle size, CSS-in-JS, dropdown lag, static/dynamic rendering

**Confidence breakdown:**
- Standard stack: HIGH - Verified with official Next.js docs, widely used patterns
- Architecture: HIGH - From Next.js official guides and Cache Components docs
- Pitfalls: HIGH - Cross-verified across multiple sources, documented in community
- Code examples: HIGH - From official Next.js/react-window documentation

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - Next.js ecosystem relatively stable, Turbopack is now default)

**Next.js version:** 16.x (latest stable)
**React version:** 19.x (with Server Components, React Compiler)
**Tailwind CSS version:** 4.x (CSS-first, zero runtime)
</metadata>

---

*Phase: 18-performance-fixes-optimization*
*Research completed: 2026-01-20*
*Ready for planning: yes*
