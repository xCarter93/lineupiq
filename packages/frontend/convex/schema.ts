import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // User scoring configurations for fantasy points calculation
  scoringConfigs: defineTable({
    name: v.string(), // e.g., "Standard", "PPR", "Half-PPR"
    isDefault: v.boolean(), // Whether this is the active config
    passing: v.object({
      yardsPerPoint: v.number(), // e.g., 25 (1 pt per 25 yards)
      tdPoints: v.number(), // e.g., 4
      intPoints: v.number(), // e.g., -2
    }),
    rushing: v.object({
      yardsPerPoint: v.number(), // e.g., 10
      tdPoints: v.number(), // e.g., 6
    }),
    receiving: v.object({
      yardsPerPoint: v.number(), // e.g., 10
      tdPoints: v.number(), // e.g., 6
      receptionPoints: v.number(), // e.g., 0 (standard) or 1 (PPR)
    }),
  }).index("by_default", ["isDefault"]),

  // Cached predictions from Python ML API
  cachedPredictions: defineTable({
    playerId: v.string(), // Player identifier
    position: v.string(), // "QB", "RB", "WR", "TE"
    week: v.number(), // NFL week number
    season: v.number(), // NFL season year
    predictions: v.any(), // Position-specific predictions (flexible structure)
    createdAt: v.number(), // Timestamp for cache invalidation
  })
    .index("by_player", ["playerId"])
    .index("by_player_week", ["playerId", "week", "season"]),

  // Player metadata for selection UI
  players: defineTable({
    playerId: v.string(), // gsis_id from nflreadpy
    name: v.string(), // Display name (full_name)
    position: v.string(), // "QB", "RB", "WR", "TE", "K"
    team: v.string(), // Team abbreviation
    // Enriched fields (optional for backward compatibility)
    jerseyNumber: v.optional(v.number()),
    height: v.optional(v.string()), // e.g., "6-2"
    weight: v.optional(v.number()),
    college: v.optional(v.string()),
    yearsExp: v.optional(v.number()),
    headshotUrl: v.optional(v.string()),
  })
    .index("by_position", ["position"])
    .index("by_team", ["team"])
    .index("by_player_id", ["playerId"]),

  // Model validation metrics (from backtesting)
  modelMetrics: defineTable({
    position: v.string(), // "QB", "RB", "WR", "TE"
    target: v.string(), // "passing_yards", "rushing_tds", etc.
    season: v.number(), // Season validated against (e.g., 2025)
    accuracyPct: v.number(), // 0-100 accuracy percentage
    confidence: v.string(), // "High", "Medium", "Low"
    mae: v.number(), // Mean Absolute Error
    rmse: v.number(), // Root Mean Squared Error
    r2: v.number(), // R-squared
    sampleCount: v.number(), // Number of predictions validated
    updatedAt: v.number(), // Timestamp of last update
  })
    .index("by_position", ["position"])
    .index("by_position_target", ["position", "target"])
    .index("by_season", ["season"]),

  // Overall model confidence summary
  overallMetrics: defineTable({
    season: v.number(), // Season validated against
    overallAccuracyPct: v.number(),
    overallConfidence: v.string(),
    modelCount: v.number(), // Number of models included
    updatedAt: v.number(),
  }).index("by_season", ["season"]),
});
