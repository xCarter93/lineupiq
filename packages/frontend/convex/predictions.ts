import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Get most recent prediction for a player
// If week/season provided, get specific prediction; otherwise get most recent
export const getByPlayer = query({
  args: {
    playerId: v.string(),
    week: v.optional(v.number()),
    season: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    if (args.week !== undefined && args.season !== undefined) {
      // Get specific prediction
      return await ctx.db
        .query("cachedPredictions")
        .withIndex("by_player_week", (q) =>
          q
            .eq("playerId", args.playerId)
            .eq("week", args.week!)
            .eq("season", args.season!)
        )
        .first();
    }

    // Get most recent by createdAt
    const predictions = await ctx.db
      .query("cachedPredictions")
      .withIndex("by_player", (q) => q.eq("playerId", args.playerId))
      .collect();

    if (predictions.length === 0) return null;

    // Sort by createdAt descending and return first
    return predictions.sort((a, b) => b.createdAt - a.createdAt)[0];
  },
});

// Get prediction for specific player/week/season
export const getByPlayerWeek = query({
  args: {
    playerId: v.string(),
    week: v.number(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("cachedPredictions")
      .withIndex("by_player_week", (q) =>
        q
          .eq("playerId", args.playerId)
          .eq("week", args.week)
          .eq("season", args.season)
      )
      .first();
  },
});

// Get N most recent predictions
export const listRecent = query({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 10;

    const predictions = await ctx.db.query("cachedPredictions").collect();

    // Sort by createdAt descending and return limited results
    return predictions.sort((a, b) => b.createdAt - a.createdAt).slice(0, limit);
  },
});

// Store or update a prediction
export const store = mutation({
  args: {
    playerId: v.string(),
    position: v.string(),
    week: v.number(),
    season: v.number(),
    predictions: v.any(),
  },
  handler: async (ctx, args) => {
    // Check if prediction exists for this player/week/season
    const existing = await ctx.db
      .query("cachedPredictions")
      .withIndex("by_player_week", (q) =>
        q
          .eq("playerId", args.playerId)
          .eq("week", args.week)
          .eq("season", args.season)
      )
      .first();

    const now = Date.now();

    if (existing) {
      // Update existing prediction
      await ctx.db.patch(existing._id, {
        predictions: args.predictions,
        createdAt: now,
        position: args.position,
      });
      return existing._id;
    }

    // Insert new prediction
    return await ctx.db.insert("cachedPredictions", {
      playerId: args.playerId,
      position: args.position,
      week: args.week,
      season: args.season,
      predictions: args.predictions,
      createdAt: now,
    });
  },
});

// Delete a prediction
export const remove = mutation({
  args: {
    id: v.id("cachedPredictions"),
  },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// Clear predictions older than N days
export const clearOld = mutation({
  args: {
    daysOld: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const daysOld = args.daysOld ?? 7;
    const cutoffTime = Date.now() - daysOld * 24 * 60 * 60 * 1000;

    const oldPredictions = await ctx.db
      .query("cachedPredictions")
      .filter((q) => q.lt(q.field("createdAt"), cutoffTime))
      .collect();

    for (const prediction of oldPredictions) {
      await ctx.db.delete(prediction._id);
    }

    return oldPredictions.length;
  },
});
