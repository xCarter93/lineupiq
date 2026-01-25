import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Queries

/**
 * Get player features for a specific week
 */
export const getByPlayerWeek = query({
  args: {
    playerId: v.string(),
    week: v.number(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("playerFeatures")
      .withIndex("by_player_week", (q) =>
        q
          .eq("playerId", args.playerId)
          .eq("week", args.week)
          .eq("season", args.season)
      )
      .first();
  },
});

/**
 * Get all features for a player across weeks
 */
export const getByPlayer = query({
  args: {
    playerId: v.string(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    const features = await ctx.db
      .query("playerFeatures")
      .filter((q) =>
        q.and(
          q.eq(q.field("playerId"), args.playerId),
          q.eq(q.field("season"), args.season)
        )
      )
      .collect();
    return features.sort((a, b) => a.week - b.week);
  },
});

// Mutations

/**
 * Upsert player features for a specific week
 */
export const upsert = mutation({
  args: {
    playerId: v.string(),
    week: v.number(),
    season: v.number(),
    weather: v.optional(
      v.object({
        temperature: v.optional(v.number()),
        windSpeed: v.optional(v.number()),
        precipitation: v.optional(v.number()),
        isDome: v.optional(v.boolean()),
      })
    ),
    vegas: v.optional(
      v.object({
        spread: v.optional(v.number()),
        overUnder: v.optional(v.number()),
        impliedTotal: v.optional(v.number()),
      })
    ),
    opponentDefense: v.optional(
      v.object({
        rank: v.optional(v.number()),
        passingYardsAllowed: v.optional(v.number()),
        rushingYardsAllowed: v.optional(v.number()),
        pointsAllowed: v.optional(v.number()),
      })
    ),
    usage: v.optional(
      v.object({
        snapPct: v.optional(v.number()),
        targetShare: v.optional(v.number()),
        carryShare: v.optional(v.number()),
        redZoneOpportunities: v.optional(v.number()),
      })
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("playerFeatures")
      .withIndex("by_player_week", (q) =>
        q
          .eq("playerId", args.playerId)
          .eq("week", args.week)
          .eq("season", args.season)
      )
      .first();

    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        weather: args.weather ?? existing.weather,
        vegas: args.vegas ?? existing.vegas,
        opponentDefense: args.opponentDefense ?? existing.opponentDefense,
        usage: args.usage ?? existing.usage,
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("playerFeatures", {
      playerId: args.playerId,
      week: args.week,
      season: args.season,
      weather: args.weather,
      vegas: args.vegas,
      opponentDefense: args.opponentDefense,
      usage: args.usage,
      updatedAt: now,
    });
  },
});

/**
 * Batch upsert player features
 */
export const batchUpsert = mutation({
  args: {
    features: v.array(
      v.object({
        playerId: v.string(),
        week: v.number(),
        season: v.number(),
        weather: v.optional(
          v.object({
            temperature: v.optional(v.number()),
            windSpeed: v.optional(v.number()),
            precipitation: v.optional(v.number()),
            isDome: v.optional(v.boolean()),
          })
        ),
        vegas: v.optional(
          v.object({
            spread: v.optional(v.number()),
            overUnder: v.optional(v.number()),
            impliedTotal: v.optional(v.number()),
          })
        ),
        opponentDefense: v.optional(
          v.object({
            rank: v.optional(v.number()),
            passingYardsAllowed: v.optional(v.number()),
            rushingYardsAllowed: v.optional(v.number()),
            pointsAllowed: v.optional(v.number()),
          })
        ),
        usage: v.optional(
          v.object({
            snapPct: v.optional(v.number()),
            targetShare: v.optional(v.number()),
            carryShare: v.optional(v.number()),
            redZoneOpportunities: v.optional(v.number()),
          })
        ),
      })
    ),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    const results = [];

    for (const feature of args.features) {
      const existing = await ctx.db
        .query("playerFeatures")
        .withIndex("by_player_week", (q) =>
          q
            .eq("playerId", feature.playerId)
            .eq("week", feature.week)
            .eq("season", feature.season)
        )
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, {
          weather: feature.weather ?? existing.weather,
          vegas: feature.vegas ?? existing.vegas,
          opponentDefense: feature.opponentDefense ?? existing.opponentDefense,
          usage: feature.usage ?? existing.usage,
          updatedAt: now,
        });
        results.push(existing._id);
      } else {
        const id = await ctx.db.insert("playerFeatures", {
          playerId: feature.playerId,
          week: feature.week,
          season: feature.season,
          weather: feature.weather,
          vegas: feature.vegas,
          opponentDefense: feature.opponentDefense,
          usage: feature.usage,
          updatedAt: now,
        });
        results.push(id);
      }
    }

    return results;
  },
});
