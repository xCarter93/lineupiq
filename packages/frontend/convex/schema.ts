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
    playerId: v.string(), // Unique player ID
    name: v.string(), // Display name
    position: v.string(), // "QB", "RB", "WR", "TE"
    team: v.string(), // Team abbreviation
  })
    .index("by_position", ["position"])
    .index("by_team", ["team"]),
});
