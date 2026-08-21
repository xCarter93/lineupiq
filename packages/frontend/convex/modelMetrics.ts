import { v } from "convex/values";
import { query, mutation } from "./_generated/server";
import { getLastCompletedSeason } from "../lib/season";

// Query: Get overall model confidence for display in UI
export const getOverallMetrics = query({
  args: { season: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const season = args.season ?? getLastCompletedSeason();
    return await ctx.db
      .query("overallMetrics")
      .withIndex("by_season", (q) => q.eq("season", season))
      .first();
  },
});

// Query: Get metrics for specific position
export const getMetricsByPosition = query({
  args: { position: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("modelMetrics")
      .withIndex("by_position", (q) => q.eq("position", args.position))
      .collect();
  },
});

// Query: Get metrics for specific model
export const getMetricsByModel = query({
  args: { position: v.string(), target: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("modelMetrics")
      .withIndex("by_position_target", (q) =>
        q.eq("position", args.position).eq("target", args.target)
      )
      .first();
  },
});

// Query: Get all model metrics
export const getAllMetrics = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("modelMetrics").collect();
  },
});

// Mutation: Upsert model metrics (called from backend after validation)
export const upsertModelMetrics = mutation({
  args: {
    position: v.string(),
    target: v.string(),
    season: v.number(),
    accuracyPct: v.number(),
    confidence: v.string(),
    mae: v.number(),
    rmse: v.number(),
    r2: v.number(),
    sampleCount: v.number(),
  },
  handler: async (ctx, args) => {
    // Check if exists
    const existing = await ctx.db
      .query("modelMetrics")
      .withIndex("by_position_target", (q) =>
        q.eq("position", args.position).eq("target", args.target)
      )
      .filter((q) => q.eq(q.field("season"), args.season))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        accuracyPct: args.accuracyPct,
        confidence: args.confidence,
        mae: args.mae,
        rmse: args.rmse,
        r2: args.r2,
        sampleCount: args.sampleCount,
        updatedAt: Date.now(),
      });
      return existing._id;
    } else {
      return await ctx.db.insert("modelMetrics", {
        ...args,
        updatedAt: Date.now(),
      });
    }
  },
});

// Mutation: Upsert overall metrics
export const upsertOverallMetrics = mutation({
  args: {
    season: v.number(),
    overallAccuracyPct: v.number(),
    overallConfidence: v.string(),
    modelCount: v.number(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("overallMetrics")
      .withIndex("by_season", (q) => q.eq("season", args.season))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        overallAccuracyPct: args.overallAccuracyPct,
        overallConfidence: args.overallConfidence,
        modelCount: args.modelCount,
        updatedAt: Date.now(),
      });
      return existing._id;
    } else {
      return await ctx.db.insert("overallMetrics", {
        ...args,
        updatedAt: Date.now(),
      });
    }
  },
});
