# Phase 8: Convex Backend - Research

**Researched:** 2026-01-15
**Domain:** Convex backend for Next.js with scoring configs and prediction storage
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Convex ecosystem for building a backend with scoring configurations, prediction storage, and app state management in a Next.js 16 application. Convex is a reactive database with automatic TypeScript type generation, real-time subscriptions, and transaction guarantees.

Key findings:
1. Schema-first approach with `defineSchema`/`defineTable` provides end-to-end type safety from database to UI
2. Use `v.id()` for table references, keep documents flat (not deeply nested)
3. Actions handle external API calls (our Python prediction API), mutations handle database writes
4. Real-time reactivity is automatic via `useQuery` - no manual refresh needed
5. Index everything you'll query by (foreign keys, common filters) from the start

**Primary recommendation:** Use standard Convex patterns with flat schema design, actions for Python API calls, and mutations that schedule actions for write-then-fetch workflows.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| convex | latest | Backend database + functions | The Convex package for React/Next.js |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @clerk/nextjs | v5+ | Authentication | If auth needed (optional for MVP) |
| zod | ^3.x | Additional validation | Complex validation beyond `v` validators |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Convex | Prisma + Postgres | Convex simpler, real-time built-in, no server to manage |
| Convex | Firebase | Convex has better TypeScript, transaction guarantees |
| Actions | Server Actions | Convex actions have scheduler, better retry logic |

**Installation:**
```bash
cd packages/frontend
pnpm add convex
npx convex dev  # Initialize project
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
packages/frontend/
├── convex/                    # Convex backend directory
│   ├── _generated/            # Auto-generated (gitignored)
│   ├── schema.ts              # Database schema
│   ├── scoringConfigs.ts      # Scoring config queries/mutations
│   ├── predictions.ts         # Prediction storage queries/mutations
│   ├── actions.ts             # External API actions (Python backend)
│   └── http.ts                # HTTP actions (webhooks if needed)
├── app/
│   ├── ConvexClientProvider.tsx  # Client provider wrapper
│   └── ...
```

### Pattern 1: Schema with Table References
**What:** Use `v.id()` for referencing documents in other tables
**When to use:** Any foreign key relationship
**Example:**
```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  scoringConfigs: defineTable({
    name: v.string(),
    isDefault: v.boolean(),
    // Scoring rules
    passingYardsPerPoint: v.number(),
    passingTdPoints: v.number(),
    interceptionPoints: v.number(),
    rushingYardsPerPoint: v.number(),
    rushingTdPoints: v.number(),
    receivingYardsPerPoint: v.number(),
    receivingTdPoints: v.number(),
    receptionPoints: v.number(),  // PPR
  }).index("by_default", ["isDefault"]),

  predictions: defineTable({
    position: v.union(v.literal("QB"), v.literal("RB"), v.literal("WR"), v.literal("TE")),
    playerId: v.string(),
    playerName: v.string(),
    opponent: v.string(),
    week: v.number(),
    season: v.number(),
    // Predicted stats
    predictedStats: v.object({
      passingYards: v.optional(v.number()),
      passingTds: v.optional(v.number()),
      rushingYards: v.optional(v.number()),
      rushingTds: v.optional(v.number()),
      receivingYards: v.optional(v.number()),
      receivingTds: v.optional(v.number()),
      receptions: v.optional(v.number()),
    }),
    // Calculated fantasy points (per scoring config)
    fantasyPoints: v.optional(v.number()),
    scoringConfigId: v.optional(v.id("scoringConfigs")),
    // Metadata
    fetchedAt: v.number(),
  })
    .index("by_player", ["playerId"])
    .index("by_position_week", ["position", "week", "season"])
    .index("by_week_season", ["week", "season"]),
});
```

### Pattern 2: Action for External API Call
**What:** Use actions to call Python prediction API, mutations to store results
**When to use:** Fetching predictions from FastAPI backend
**Example:**
```typescript
// convex/actions.ts
import { action } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

export const fetchPrediction = action({
  args: {
    position: v.union(v.literal("QB"), v.literal("RB"), v.literal("WR"), v.literal("TE")),
    features: v.object({
      // Feature fields matching Python API
    }),
  },
  handler: async (ctx, args) => {
    const apiUrl = process.env.PREDICTION_API_URL ?? "http://localhost:8000";

    const response = await fetch(`${apiUrl}/predict/${args.position.toLowerCase()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args.features),
    });

    if (!response.ok) {
      throw new Error(`Prediction API error: ${response.status}`);
    }

    const prediction = await response.json();

    // Store in database via mutation
    await ctx.runMutation(internal.predictions.storePrediction, {
      position: args.position,
      prediction,
    });

    return prediction;
  },
});
```

### Pattern 3: ConvexClientProvider for Next.js App Router
**What:** Client component wrapper for Convex provider
**When to use:** Always, for Next.js App Router
**Example:**
```typescript
// app/ConvexClientProvider.tsx
"use client";
import { ConvexProvider, ConvexReactClient } from "convex/react";
import { ReactNode } from "react";

const convex = new ConvexReactClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  return <ConvexProvider client={convex}>{children}</ConvexProvider>;
}

// app/layout.tsx
import { ConvexClientProvider } from "./ConvexClientProvider";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html>
      <body>
        <ConvexClientProvider>{children}</ConvexClientProvider>
      </body>
    </html>
  );
}
```

### Pattern 4: Query with Index
**What:** Use `.withIndex()` for efficient filtered queries
**When to use:** Any query filtering by non-primary key
**Example:**
```typescript
// convex/predictions.ts
import { query } from "./_generated/server";
import { v } from "convex/values";

export const getByWeek = query({
  args: {
    week: v.number(),
    season: v.number(),
    position: v.optional(v.union(v.literal("QB"), v.literal("RB"), v.literal("WR"), v.literal("TE"))),
  },
  handler: async (ctx, args) => {
    let q = ctx.db
      .query("predictions")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      );

    if (args.position) {
      q = q.filter((q) => q.eq(q.field("position"), args.position));
    }

    return await q.collect();
  },
});
```

### Anti-Patterns to Avoid
- **Deeply nested documents:** Don't nest arrays of objects. Use separate tables with references.
- **Manual data refresh:** Don't call mutations then manually refetch. `useQuery` auto-updates.
- **Unindexed filters:** Don't use `.filter()` on large tables. Create indexes.
- **Client-only auth:** Don't check auth only in UI. Validate in mutations/queries.
- **Multiple sequential `runMutation`:** Batch into single mutation for atomicity.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Real-time updates | Custom WebSocket/polling | Convex `useQuery` | Automatic subscriptions, optimized invalidation |
| Type generation | Manual interfaces | Convex schema + codegen | `npx convex dev` generates types automatically |
| Transaction handling | Custom locking | Convex mutations | Built-in ACID transactions |
| Data validation | Custom validators | `v` validators in args | Validated on server, generates TypeScript types |
| Caching | Custom cache layer | Convex query caching | Automatic, invalidated on mutation |
| Foreign key refs | String IDs | `v.id("tableName")` | Type-safe references, validated existence |

**Key insight:** Convex provides reactive data out of the box. The `useQuery` hook automatically subscribes to changes and re-renders components. Don't build custom sync/refresh logic - it negates Convex's core value proposition.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Not Awaiting Promises
**What goes wrong:** Scheduled functions don't run, database writes silently fail
**Why it happens:** Forgetting `await` on `ctx.scheduler.runAfter`, `ctx.db.patch`, etc.
**How to avoid:** Enable `no-floating-promises` ESLint rule
**Warning signs:** Functions appear to "do nothing", inconsistent state

### Pitfall 2: Using `.filter()` on Large Tables
**What goes wrong:** Slow queries, timeout errors
**Why it happens:** `.filter()` scans entire table, no index used
**How to avoid:** Define indexes in schema, use `.withIndex()` instead of `.filter()`
**Warning signs:** Queries get slower as data grows

### Pitfall 3: Deeply Nested Objects
**What goes wrong:** Updating specific nested items is painful, poor performance
**Why it happens:** Treating Convex like MongoDB, nesting everything
**How to avoid:** Keep documents flat, use table references
**Warning signs:** Complex update logic, `$set` on nested paths

### Pitfall 4: Manual Refresh After Mutation
**What goes wrong:** Unnecessary complexity, wasted requests
**Why it happens:** Habit from REST APIs, not trusting reactivity
**How to avoid:** Trust `useQuery` - it auto-updates when underlying data changes
**Warning signs:** Calling `refetch()` or using `useEffect` to refresh after mutation

### Pitfall 5: Frontend-Only Auth Checks
**What goes wrong:** Data exposed to malicious users
**Why it happens:** Only hiding UI buttons, not validating in backend
**How to avoid:** Always use `ctx.auth.getUserIdentity()` in mutations/queries
**Warning signs:** Auth checks only in components, not in Convex functions

### Pitfall 6: Circular Imports in Schema
**What goes wrong:** Validators are undefined, cryptic runtime errors
**Why it happens:** Importing from schema.ts in files that schema.ts imports
**How to avoid:** Keep validators in separate files, import into schema.ts
**Warning signs:** "Validator undefined" errors, import cycles
</common_pitfalls>

<code_examples>
## Code Examples

### Basic Mutation (Create Scoring Config)
```typescript
// convex/scoringConfigs.ts
import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    name: v.string(),
    passingYardsPerPoint: v.number(),
    passingTdPoints: v.number(),
    interceptionPoints: v.number(),
    rushingYardsPerPoint: v.number(),
    rushingTdPoints: v.number(),
    receivingYardsPerPoint: v.number(),
    receivingTdPoints: v.number(),
    receptionPoints: v.number(),
  },
  handler: async (ctx, args) => {
    const configId = await ctx.db.insert("scoringConfigs", {
      ...args,
      isDefault: false,
    });
    return configId;
  },
});

export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("scoringConfigs").collect();
  },
});

export const getDefault = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("scoringConfigs")
      .withIndex("by_default", (q) => q.eq("isDefault", true))
      .first();
  },
});
```

### Using Queries in React
```typescript
// app/scoring/page.tsx
"use client";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";

export default function ScoringPage() {
  const configs = useQuery(api.scoringConfigs.list);
  const createConfig = useMutation(api.scoringConfigs.create);

  if (configs === undefined) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Scoring Configurations</h1>
      <ul>
        {configs.map((config) => (
          <li key={config._id}>{config.name}</li>
        ))}
      </ul>
      <button
        onClick={() => createConfig({
          name: "Standard PPR",
          passingYardsPerPoint: 25,
          passingTdPoints: 4,
          interceptionPoints: -2,
          rushingYardsPerPoint: 10,
          rushingTdPoints: 6,
          receivingYardsPerPoint: 10,
          receivingTdPoints: 6,
          receptionPoints: 1,
        })}
      >
        Add Standard PPR
      </button>
    </div>
  );
}
```

### Internal Mutation (Called from Action)
```typescript
// convex/predictions.ts
import { internalMutation } from "./_generated/server";
import { v } from "convex/values";

export const storePrediction = internalMutation({
  args: {
    position: v.union(v.literal("QB"), v.literal("RB"), v.literal("WR"), v.literal("TE")),
    prediction: v.object({
      playerId: v.string(),
      playerName: v.string(),
      opponent: v.string(),
      week: v.number(),
      season: v.number(),
      predictions: v.any(),
    }),
  },
  handler: async (ctx, args) => {
    // Check if prediction already exists
    const existing = await ctx.db
      .query("predictions")
      .withIndex("by_player", (q) => q.eq("playerId", args.prediction.playerId))
      .filter((q) =>
        q.and(
          q.eq(q.field("week"), args.prediction.week),
          q.eq(q.field("season"), args.prediction.season)
        )
      )
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        predictedStats: args.prediction.predictions,
        fetchedAt: Date.now(),
      });
      return existing._id;
    }

    return await ctx.db.insert("predictions", {
      position: args.position,
      playerId: args.prediction.playerId,
      playerName: args.prediction.playerName,
      opponent: args.prediction.opponent,
      week: args.prediction.week,
      season: args.prediction.season,
      predictedStats: args.prediction.predictions,
      fetchedAt: Date.now(),
    });
  },
});
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pages Router setup | App Router + ConvexClientProvider | Next.js 13+ | Requires "use client" wrapper component |
| `@app.on_event` | `lifespan` context manager | FastAPI 0.100+ | Our prediction API already uses lifespan |
| Manual type syncing | Convex codegen | Always in Convex | `npx convex dev` generates types automatically |

**New tools/patterns to consider:**
- **Convex Components:** Pre-built components for common patterns (rate limiting, aggregates)
- **HTTP Actions with Hono:** Advanced routing if needed beyond basic patterns
- **Preloading:** `preloadQuery` for server components to preload data

**Deprecated/outdated:**
- **Manual refresh patterns:** Don't use `refetch()` or state management for Convex data
- **String IDs for references:** Use `v.id("tableName")` for type-safe foreign keys
</sota_updates>

<open_questions>
## Open Questions

1. **Authentication Approach**
   - What we know: Convex supports Clerk, Auth0, custom JWT
   - What's unclear: Whether MVP needs auth or if we start without it
   - Recommendation: Start without auth for MVP, add later if needed

2. **Prediction Caching Strategy**
   - What we know: Convex has automatic query caching, our Python API has its own cache
   - What's unclear: How long to cache predictions in Convex vs relying on Python cache
   - Recommendation: Store predictions in Convex with `fetchedAt` timestamp, refresh on demand
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Convex Schemas](https://docs.convex.dev/database/schemas) - Schema definition patterns
- [Convex Best Practices](https://docs.convex.dev/understanding/best-practices/) - Official best practices
- [Convex Query Functions](https://docs.convex.dev/functions/query-functions) - Query patterns
- [Convex Mutation Functions](https://docs.convex.dev/functions/mutation-functions) - Mutation patterns
- [Convex Actions](https://docs.convex.dev/functions/actions) - External API integration
- [Convex HTTP Actions](https://docs.convex.dev/functions/http-actions) - HTTP routing
- [Convex Next.js App Router](https://docs.convex.dev/client/nextjs/app-router/) - Next.js integration
- [Convex Next.js Quickstart](https://docs.convex.dev/quickstart/nextjs) - Setup guide

### Secondary (MEDIUM confidence)
- [10 Tips for Convex Developers](https://www.schemets.com/blog/10-convex-developer-tips-pitfalls-productivity) - Community pitfalls
- [Convex Transaction Throughput](https://stack.convex.dev/high-throughput-mutations-via-precise-queries) - Performance patterns

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official docs
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Convex database + functions
- Ecosystem: Convex React hooks, schema, actions
- Patterns: Schema design, mutations, queries, external API calls
- Pitfalls: Await promises, indexes, nested objects, auth, manual refresh

**Confidence breakdown:**
- Standard stack: HIGH - Single package, well-documented
- Architecture: HIGH - Patterns from official docs and examples
- Pitfalls: HIGH - Documented in official best practices
- Code examples: HIGH - Based on official documentation patterns

**Research date:** 2026-01-15
**Valid until:** 2026-02-15 (30 days - Convex ecosystem stable)
</metadata>

---

*Phase: 08-convex-backend*
*Research completed: 2026-01-15*
*Ready for planning: yes*
