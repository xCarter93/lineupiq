import { v } from "convex/values";
import { query, mutation } from "./_generated/server";

// Query: Get predictions for a specific player across all weeks
export const getPlayerValidationPredictions = query({
  args: { playerId: v.string(), season: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("validationPredictions")
      .withIndex("by_player_week", (q) =>
        q.eq("playerId", args.playerId).eq("season", args.season)
      )
      .collect();
  },
});

// Query: Get aggregate accuracy metrics for a position
export const getPositionAccuracyMetrics = query({
  args: { position: v.string(), season: v.number() },
  handler: async (ctx, args) => {
    const predictions = await ctx.db
      .query("validationPredictions")
      .withIndex("by_position_week", (q) =>
        q.eq("position", args.position).eq("season", args.season)
      )
      .collect();

    if (predictions.length === 0) {
      return { count: 0, mae: 0, mape: 0 };
    }

    const totalAE = predictions.reduce((sum, p) => sum + p.absoluteError, 0);
    const mae = totalAE / predictions.length;

    // MAPE: Mean Absolute Percentage Error
    const totalAPE = predictions.reduce(
      (sum, p) => sum + (p.actualValue !== 0 ? Math.abs(p.error / p.actualValue) * 100 : 0),
      0
    );
    const mape = totalAPE / predictions.length;

    return { count: predictions.length, mae, mape };
  },
});

// Query: Get all positions with available validation data
export const getAvailableValidationPositions = query({
  args: { season: v.number() },
  handler: async (ctx, args) => {
    const predictions = await ctx.db
      .query("validationPredictions")
      .filter((q) => q.eq(q.field("season"), args.season))
      .collect();

    const positions = new Set(predictions.map((p) => p.position));
    return Array.from(positions).sort();
  },
});

// Mutation: Bulk upsert predictions (for upload script)
export const upsertValidationPredictions = mutation({
  args: {
    predictions: v.array(
      v.object({
        playerId: v.string(),
        playerName: v.string(),
        position: v.string(),
        season: v.number(),
        week: v.number(),
        target: v.string(),
        predictedValue: v.number(),
        actualValue: v.number(),
      })
    ),
  },
  handler: async (ctx, args) => {
    let inserted = 0;
    let updated = 0;

    for (const pred of args.predictions) {
      const error = pred.predictedValue - pred.actualValue;
      const absoluteError = Math.abs(error);

      // Check if prediction already exists
      const existing = await ctx.db
        .query("validationPredictions")
        .withIndex("by_player_week", (q) =>
          q
            .eq("playerId", pred.playerId)
            .eq("season", pred.season)
            .eq("week", pred.week)
        )
        .filter((q) => q.eq(q.field("target"), pred.target))
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, {
          ...pred,
          error,
          absoluteError,
        });
        updated++;
      } else {
        await ctx.db.insert("validationPredictions", {
          ...pred,
          error,
          absoluteError,
        });
        inserted++;
      }
    }

    return { inserted, updated };
  },
});
