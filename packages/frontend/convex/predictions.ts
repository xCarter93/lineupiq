import { v } from "convex/values";
import { query, internalMutation } from "./_generated/server";

// Query: All predictions for a season/week (the weekly grid reads this once and
// groups by playerId client-side)
export const byWeek = query({
  args: { season: v.number(), week: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cachedPredictions")
      .withIndex("by_season_week", (q) =>
        q.eq("season", args.season).eq("week", args.week)
      )
      .collect();
  },
});

// Query: Every target predicted for one player in one week
export const byPlayerWeek = query({
  args: { playerId: v.string(), season: v.number(), week: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cachedPredictions")
      .withIndex("by_player_week", (q) =>
        q
          .eq("playerId", args.playerId)
          .eq("season", args.season)
          .eq("week", args.week)
      )
      .collect();
  },
});

// Internal mutation: idempotent upsert on the natural key
// (playerId, season, week, target). Reached only through the
// /ingest-predictions HTTP action. The batch job sends chunks of 100 rows.
export const upsertBatch = internalMutation({
  args: {
    rows: v.array(
      v.object({
        playerId: v.string(),
        playerName: v.string(),
        position: v.string(),
        team: v.string(),
        opponent: v.optional(v.string()),
        isHome: v.optional(v.boolean()),
        season: v.number(),
        week: v.number(),
        target: v.string(),
        predictedValue: v.number(),
        source: v.union(v.literal("model"), v.literal("baseline")),
        modelVersion: v.optional(v.string()),
        runId: v.string(),
      })
    ),
  },
  handler: async (ctx, args) => {
    let inserted = 0;
    let updated = 0;
    const generatedAt = Date.now();

    for (const row of args.rows) {
      const existing = await ctx.db
        .query("cachedPredictions")
        .withIndex("by_player_week", (q) =>
          q
            .eq("playerId", row.playerId)
            .eq("season", row.season)
            .eq("week", row.week)
        )
        .filter((q) => q.eq(q.field("target"), row.target))
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, { ...row, generatedAt });
        updated++;
      } else {
        await ctx.db.insert("cachedPredictions", { ...row, generatedAt });
        inserted++;
      }
    }

    return { inserted, updated };
  },
});

// Internal mutation: drop every row a single run wrote, for rolling back a bad run
export const deleteByRun = internalMutation({
  args: { runId: v.string() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("cachedPredictions")
      .withIndex("by_run", (q) => q.eq("runId", args.runId))
      .collect();

    for (const row of rows) {
      await ctx.db.delete(row._id);
    }

    return rows.length;
  },
});
