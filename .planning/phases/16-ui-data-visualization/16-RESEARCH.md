# Phase 16: UI Data Visualization - Research

**Researched:** 2026-01-15
**Domain:** Recharts data visualization for fantasy football stats
**Confidence:** HIGH

<research_summary>
## Summary

Researched the React charting ecosystem for visualizing fantasy football stats and player history. The clear recommendation is **Recharts via shadcn/ui charts**, which is already compatible with the project's existing shadcn/ui + Tailwind stack.

Key findings:
1. **shadcn/ui has official Recharts integration** - 53 pre-built chart components with automatic light/dark mode support
2. **Recharts v3.6.0 is current** with React 19 support (stable as of late 2024)
3. **Next.js SSR requires dynamic imports** with `ssr: false` to avoid hydration mismatches
4. **Sports data visualization best practices** favor line charts for trends and bar charts for comparisons

**Primary recommendation:** Install shadcn/ui chart component (uses Recharts under the hood), implement with dynamic imports for Next.js SSR compatibility. Focus on line charts for week-over-week trends and bar charts for stat comparisons.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | 3.6.0 | React charting library | Composable components, SVG-based, shadcn/ui integration |
| @shadcn/ui chart | N/A | Chart wrapper component | Pre-styled, theming, ChartConfig pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| next/dynamic | Built-in | Dynamic imports | Required for SSR-safe chart loading |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Recharts | Nivo | More chart types, larger bundle, more complex API |
| Recharts | Victory | Better accessibility, React Native support, fewer chart types |
| Recharts | Chart.js | Canvas-based (faster for huge datasets), not React-native |

**Why Recharts wins for this project:**
- shadcn/ui already uses Recharts - matches existing component patterns
- Composable React components - familiar DX
- SVG-based - crisp rendering, easy styling
- Moderate bundle size (~70KB gzipped)
- Active maintenance, React 19 support

**Installation:**
```bash
# Add shadcn/ui chart component (includes recharts)
cd packages/frontend
npx shadcn@latest add chart
```

Or manual:
```bash
pnpm add recharts
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Component Structure
```
components/
├── charts/                   # Chart components
│   ├── PlayerStatsChart.tsx  # Line chart for week-over-week stats
│   ├── StatComparisonBar.tsx # Bar chart for stat comparisons
│   └── FantasyPointsArea.tsx # Area chart for fantasy points trend
└── matchup/
    └── PlayerHistory.tsx     # Updated to include charts
```

### Pattern 1: SSR-Safe Chart Loading
**What:** Use Next.js dynamic imports with ssr: false for all chart components
**When to use:** Always - Recharts uses browser APIs that break SSR
**Example:**
```typescript
"use client";
import dynamic from "next/dynamic";

// Dynamic import with SSR disabled
const StatsLineChart = dynamic(
  () => import("@/components/charts/StatsLineChart"),
  {
    ssr: false,
    loading: () => (
      <div className="h-[300px] flex items-center justify-center bg-muted/30 rounded-lg">
        <span className="text-muted-foreground">Loading chart...</span>
      </div>
    ),
  }
);

export function PlayerHistory() {
  return <StatsLineChart data={games} />;
}
```

### Pattern 2: shadcn/ui ChartConfig Pattern
**What:** Define chart configuration object for colors and labels
**When to use:** All charts using shadcn/ui chart component
**Example:**
```typescript
import { ChartConfig, ChartContainer } from "@/components/ui/chart";
import { LineChart, Line, XAxis, YAxis } from "recharts";

const chartConfig = {
  passingYards: {
    label: "Pass Yards",
    color: "hsl(var(--chart-1))",
  },
  rushingYards: {
    label: "Rush Yards",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

function StatsChart({ data }: { data: GameData[] }) {
  return (
    <ChartContainer config={chartConfig} className="min-h-[300px]">
      <LineChart data={data}>
        <XAxis dataKey="week" />
        <YAxis />
        <Line dataKey="passingYards" stroke="var(--color-passingYards)" />
        <Line dataKey="rushingYards" stroke="var(--color-rushingYards)" />
      </LineChart>
    </ChartContainer>
  );
}
```

### Pattern 3: ResponsiveContainer for Fluid Charts
**What:** Wrap charts in ResponsiveContainer for automatic resizing
**When to use:** All charts that need to fill available width
**Example:**
```typescript
import { ResponsiveContainer, LineChart } from "recharts";

function ResponsiveChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        {/* Chart content */}
      </LineChart>
    </ResponsiveContainer>
  );
}
```
**Note:** Parent container MUST have defined dimensions (min-height required).

### Anti-Patterns to Avoid
- **Importing Recharts in server components:** Always use dynamic imports with ssr: false
- **Missing min-height on ChartContainer:** Charts won't render without defined height
- **Animations on large datasets:** Disable with `isAnimationActive={false}` for >100 data points
- **Creating charts in render loop:** Define chart config outside component or with useMemo
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Responsive charts | Manual resize listeners | ResponsiveContainer | Debouncing, performance, edge cases |
| Custom tooltips | DIY positioning logic | Recharts Tooltip + content prop | SVG positioning is complex |
| Axis formatting | String manipulation | tickFormatter prop | Handles scales, intervals |
| Data aggregation | Manual loops | Transform data before passing | Recharts expects flat array |
| Animation | Custom transitions | Built-in isAnimationActive | Performance optimized |
| Dark mode colors | Manual CSS | shadcn/ui ChartConfig | Uses CSS variables automatically |

**Key insight:** Recharts is already a high-level abstraction. Don't try to fight it. Transform your data to match what Recharts expects (flat array of objects with consistent keys) rather than trying to make Recharts handle complex data structures.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: SSR Hydration Mismatch
**What goes wrong:** "Hydration failed because the server rendered HTML didn't match the client"
**Why it happens:** Recharts uses browser APIs (window, document) unavailable during SSR
**How to avoid:** Always use `dynamic(() => import(...), { ssr: false })`
**Warning signs:** Console hydration errors, charts flashing on load

### Pitfall 2: Charts Not Rendering (Blank Space)
**What goes wrong:** Chart area is empty, no errors
**Why it happens:** Parent container has no defined height
**How to avoid:** Add `min-h-[300px]` to ChartContainer or parent div
**Warning signs:** ResponsiveContainer logs warning about 0 width/height

### Pitfall 3: Performance Degradation with Large Datasets
**What goes wrong:** Chart becomes sluggish, page freezes on resize
**Why it happens:** SVG rendering + animations with 1000+ data points
**How to avoid:**
  - Disable animations: `isAnimationActive={false}`
  - Sample/aggregate data to <100 points
  - Use debounce on ResponsiveContainer (prop available)
**Warning signs:** Slow initial render, janky resize behavior

### Pitfall 4: Tooltip Position Issues
**What goes wrong:** Tooltip appears in wrong location or clips off screen
**Why it happens:** Default positioning doesn't account for container bounds
**How to avoid:** Use portal rendering (Recharts 3.0+) or custom positioning
**Warning signs:** Tooltip partially hidden at chart edges

### Pitfall 5: Z-Index/Layering Problems
**What goes wrong:** Tooltip hidden behind other chart elements
**Why it happens:** SVG doesn't support z-index; layer order = render order
**How to avoid:** Order JSX elements correctly (Tooltip after other elements)
**Warning signs:** Interactive elements not responding, tooltips obscured
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns for LineupIQ fantasy football visualization:

### Week-over-Week Fantasy Points Line Chart
```typescript
// Source: Recharts + shadcn/ui patterns
"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface GameData {
  week: number;
  fantasyPoints: number;
}

export function FantasyPointsChart({ data }: { data: GameData[] }) {
  // Sort by week ascending for proper line rendering
  const sortedData = [...data].sort((a, b) => a.week - b.week);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={sortedData}>
        <XAxis
          dataKey="week"
          tickFormatter={(w) => `Wk ${w}`}
          fontSize={12}
        />
        <YAxis
          domain={[0, 'auto']}
          fontSize={12}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            return (
              <div className="bg-white border rounded-lg shadow-sm p-2">
                <p className="text-sm font-medium">
                  Week {payload[0].payload.week}
                </p>
                <p className="text-sm text-muted-foreground">
                  {payload[0].value?.toFixed(1)} pts
                </p>
              </div>
            );
          }}
        />
        <Line
          type="monotone"
          dataKey="fantasyPoints"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Position-Specific Stat Bar Chart
```typescript
// Source: Recharts patterns for stat comparison
"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface StatData {
  name: string;
  value: number;
}

export function StatComparisonChart({
  stats,
  color = "hsl(var(--primary))"
}: {
  stats: StatData[];
  color?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={stats} layout="vertical">
        <XAxis type="number" fontSize={12} />
        <YAxis
          type="category"
          dataKey="name"
          width={80}
          fontSize={12}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            return (
              <div className="bg-white border rounded-lg shadow-sm p-2">
                <p className="text-sm font-medium">
                  {payload[0].payload.name}
                </p>
                <p className="text-sm">
                  {payload[0].value}
                </p>
              </div>
            );
          }}
        />
        <Bar
          dataKey="value"
          fill={color}
          radius={[0, 4, 4, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### Dynamic Import Wrapper Pattern
```typescript
// components/charts/index.tsx
// Centralized dynamic exports for SSR safety
"use client";

import dynamic from "next/dynamic";

const ChartLoader = () => (
  <div className="h-[200px] flex items-center justify-center bg-muted/30 rounded-lg animate-pulse">
    <span className="text-sm text-muted-foreground">Loading chart...</span>
  </div>
);

export const FantasyPointsChart = dynamic(
  () => import("./FantasyPointsChart").then((mod) => mod.FantasyPointsChart),
  { ssr: false, loading: ChartLoader }
);

export const StatComparisonChart = dynamic(
  () => import("./StatComparisonChart").then((mod) => mod.StatComparisonChart),
  { ssr: false, loading: ChartLoader }
);
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recharts 2.x | Recharts 3.6.0 | Oct 2024 | New state management, custom components, accessibility default |
| Manual React 19 workarounds | Native React 19 support | Late 2024 | No more react-is overrides needed |
| Customized component for custom content | Direct custom components in tree | Recharts 3.0 | Simpler composition |
| recharts-scale dependency | Built-in scales | Recharts 3.0 | Smaller bundle, maintained internally |

**New tools/patterns to consider:**
- **Recharts 3.0+ Tooltip Portal:** Renders tooltips outside SVG for better positioning
- **accessibilityLayer (default true):** Built-in a11y support in Recharts 3.0+
- **width="auto" on YAxis:** Auto-width calculation for axis labels

**Deprecated/outdated:**
- **alwaysShow prop on Reference elements:** Removed in 3.0
- **activeIndex prop:** Removed, use Tooltip interaction instead
- **CategoricalChartState access:** No longer exposed in handlers
</sota_updates>

<fantasy_football_specific>
## Fantasy Football Chart Recommendations

### Chart Types by Use Case

| Use Case | Chart Type | X-Axis | Y-Axis | Notes |
|----------|------------|--------|--------|-------|
| Week-over-week performance | Line | Week number | Fantasy points | Sort ascending |
| Stat breakdown (single game) | Horizontal Bar | Stat name | Value | Good for QB with many stats |
| Season comparison | Grouped Bar | Season | Avg points | Compare 2022 vs 2023 vs 2024 |
| Scoring category breakdown | Stacked Bar | Category | Points | Visualize passing/rushing/receiving split |
| Trend with projection | Area + Line | Week | Points | Area for historical, line for projected |

### Data Transformation for Existing PlayerHistory

The current `HistoryGame` interface maps well to Recharts:

```typescript
// Current data structure
interface HistoryGame {
  season: number;
  week: number;
  fantasyPoints?: number;
  passingYards?: number;
  // ... other stats
}

// Transform for LineChart (no changes needed!)
const chartData = games
  .filter(g => g.season === selectedSeason)
  .sort((a, b) => a.week - b.week);

// Use directly:
<LineChart data={chartData}>
  <Line dataKey="fantasyPoints" />
</LineChart>
```

### Color Palette Recommendation
Use shadcn/ui chart colors which adapt to light/dark mode:
- `hsl(var(--chart-1))` - Primary (fantasy points)
- `hsl(var(--chart-2))` - Secondary (yards)
- `hsl(var(--chart-3))` - Tertiary (TDs)
- `hsl(var(--chart-4))` - Quaternary (negative stats like INTs)
</fantasy_football_specific>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Exact shadcn/ui chart compatibility with Tailwind v4**
   - What we know: shadcn/ui supports Tailwind, project uses Tailwind v4
   - What's unclear: Whether chart component needs any v4-specific adjustments
   - Recommendation: Install and test; likely works since shadcn/ui is actively maintained

2. **React 19 + Recharts 3.6 stability in production**
   - What we know: React 19 support was added in Recharts alpha, now stable in 3.x
   - What's unclear: Any edge cases specific to Next.js 16 + React 19.2
   - Recommendation: Start with simple charts, monitor for hydration issues
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Recharts GitHub Releases](https://github.com/recharts/recharts/releases) - Version 3.6.0 verified
- [Recharts 3.0 Migration Guide](https://github.com/recharts/recharts/wiki/3.0-migration-guide) - Breaking changes documented
- [shadcn/ui Charts](https://ui.shadcn.com/docs/components/chart) - Integration patterns

### Secondary (MEDIUM confidence)
- [LogRocket: Best React Chart Libraries 2025](https://blog.logrocket.com/best-react-chart-libraries-2025/) - Comparison verified against docs
- [Sports Data Visualization Best Practices](https://www.entitysport.com/data-visualization-techniques-in-sports-analytics/) - General patterns, not library-specific
- [Sebastian Silbermann X Post](https://x.com/sebsilbermann/status/1795417336809136441) - React 19 alpha support confirmation

### Tertiary (LOW confidence - needs validation)
- Fantasy football player comparison tools (various) - UI inspiration only
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Recharts 3.x with React 19 + Next.js 16
- Ecosystem: shadcn/ui chart component, dynamic imports
- Patterns: SSR-safe loading, ResponsiveContainer, ChartConfig
- Pitfalls: Hydration, performance, height requirements

**Confidence breakdown:**
- Standard stack: HIGH - shadcn/ui official integration, verified versions
- Architecture: HIGH - Patterns from official docs and migration guide
- Pitfalls: HIGH - Documented in GitHub issues and guides
- Code examples: MEDIUM - Adapted from patterns, not copy-paste from production

**Research date:** 2026-01-15
**Valid until:** 2026-02-15 (30 days - Recharts ecosystem stable)
</metadata>

---

*Phase: 16-ui-data-visualization*
*Research completed: 2026-01-15*
*Ready for planning: yes*
