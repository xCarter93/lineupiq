import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // User scoring configurations for fantasy points calculation
  scoringConfigs: defineTable({
    name: v.string(), // e.g., "Standard", "PPR", "Half-PPR"
    preset: v.optional(v.union(v.literal("standard"), v.literal("half_ppr"), v.literal("full_ppr"), v.literal("custom"))),
    isDefault: v.boolean(), // Whether this is the active config
    passing: v.object({
      yardsPerPoint: v.number(), // e.g., 25 (1 pt per 25 yards)
      tdPoints: v.number(), // e.g., 4
      intPoints: v.number(), // e.g., -2
      twoPtConversion: v.optional(v.number()), // e.g., 2
    }),
    rushing: v.object({
      yardsPerPoint: v.number(), // e.g., 10
      tdPoints: v.number(), // e.g., 6
      twoPtConversion: v.optional(v.number()), // e.g., 2
    }),
    receiving: v.object({
      yardsPerPoint: v.number(), // e.g., 10
      tdPoints: v.number(), // e.g., 6
      receptionPoints: v.number(), // e.g., 0 (standard) or 1 (PPR)
      twoPtConversion: v.optional(v.number()), // e.g., 2
    }),
    kicking: v.optional(v.object({
      fgPoints: v.number(), // e.g., 3
      fg40_49Points: v.number(), // e.g., 4
      fg50PlusPoints: v.number(), // e.g., 5
      patPoints: v.number(), // e.g., 1
      missPoints: v.number(), // e.g., -1
    })),
    defense: v.optional(v.object({
      sackPoints: v.number(), // e.g., 1
      intPoints: v.number(), // e.g., 2
      fumbleRecPoints: v.number(), // e.g., 2
      tdPoints: v.number(), // e.g., 6
      safetyPoints: v.number(), // e.g., 2
      ptsAllowed0: v.optional(v.number()), // Points for 0 pts allowed
      ptsAllowed1_6: v.optional(v.number()),
      ptsAllowed7_13: v.optional(v.number()),
      ptsAllowed14_20: v.optional(v.number()),
      ptsAllowed21_27: v.optional(v.number()),
      ptsAllowed28_34: v.optional(v.number()),
      ptsAllowed35Plus: v.optional(v.number()),
    })),
  }).index("by_default", ["isDefault"]),

  // Weekly batch predictions, one row per (player, season, week, target).
  // Written only by the Python batch job via the /ingest-predictions HTTP action.
  cachedPredictions: defineTable({
    playerId: v.string(), // gsis_id, or "DEF_{TEAM}" for team defense
    playerName: v.string(), // denormalized so the weekly grid needs no join
    position: v.string(), // "QB", "RB", "WR", "TE", "K", "DEF"
    team: v.string(),
    opponent: v.optional(v.string()),
    isHome: v.optional(v.boolean()),
    season: v.number(),
    week: v.number(),
    target: v.string(), // "passing_yards", "receiving_tds", etc.
    predictedValue: v.number(),
    source: v.union(v.literal("model"), v.literal("baseline")),
    modelVersion: v.optional(v.string()), // absent for baseline predictions
    runId: v.string(), // one id per generate_predictions.py run
    generatedAt: v.number(),
  })
    .index("by_season_week", ["season", "week"])
    .index("by_player_week", ["playerId", "season", "week"])
    .index("by_position_week", ["position", "season", "week"])
    .index("by_run", ["runId"]),

  // Player metadata for selection UI
  players: defineTable({
    playerId: v.string(), // gsis_id from nflreadpy
    name: v.string(), // Display name (full_name)
    position: v.string(), // "QB", "RB", "WR", "TE", "K", "DEF"
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

  // Cached weekly player stats for historical display
  playerHistory: defineTable({
    playerId: v.string(), // gsis_id
    season: v.number(),
    week: v.number(),
    opponentTeam: v.optional(v.string()),
    // Stats (all optional - not all positions have all stats)
    passingYards: v.optional(v.number()),
    passingTds: v.optional(v.number()),
    interceptions: v.optional(v.number()),
    rushingYards: v.optional(v.number()),
    rushingTds: v.optional(v.number()),
    carries: v.optional(v.number()),
    receivingYards: v.optional(v.number()),
    receivingTds: v.optional(v.number()),
    receptions: v.optional(v.number()),
    fantasyPoints: v.optional(v.number()),
    // Metadata
    updatedAt: v.number(),
  })
    .index("by_player", ["playerId"])
    .index("by_player_season", ["playerId", "season"])
    .index("by_player_week", ["playerId", "season", "week"]),

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

  // 2025 validation predictions for predicted vs actual comparisons
  validationPredictions: defineTable({
    playerId: v.string(),
    playerName: v.string(),
    position: v.string(), // QB, RB, WR, TE, K, DEF
    season: v.number(),
    week: v.number(),
    target: v.string(), // passing_yards, rushing_yards, receiving_yards, etc.
    predictedValue: v.number(),
    actualValue: v.number(),
    error: v.number(), // predictedValue - actualValue
    absoluteError: v.number(), // Math.abs(error)
  })
    .index("by_player_week", ["playerId", "season", "week"])
    .index("by_position_week", ["position", "season", "week"])
    .index("by_season_week", ["season", "week"]),

  // User lineup for a given week
  lineups: defineTable({
    week: v.number(),
    season: v.number(),
    slots: v.array(v.object({
      position: v.string(), // "QB", "RB", "WR", "TE", "FLEX", "K", "DEF"
      playerId: v.optional(v.string()),
    })),
    totalProjectedPoints: v.optional(v.number()),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_week_season", ["week", "season"]),

  // Configurable roster slots for lineup
  lineupSettings: defineTable({
    slots: v.array(v.object({
      position: v.string(), // "QB", "RB", "WR", "TE", "FLEX", "K", "DEF"
      eligiblePositions: v.array(v.string()), // e.g., ["RB", "WR", "TE"] for FLEX
    })),
    updatedAt: v.number(),
  }),

  // Recently viewed players for sidebar
  recentPlayers: defineTable({
    playerIds: v.array(v.string()),
    timestamps: v.array(v.number()),
    updatedAt: v.number(),
  }),

  // Season simulation state for backtesting
  simulationState: defineTable({
    name: v.string(), // e.g., "2025 Season Simulation"
    targetSeason: v.number(), // Season being simulated (e.g., 2025)
    trainingSeasons: v.array(v.number()), // Base seasons for training (e.g., [2022, 2023, 2024])
    currentWeek: v.number(), // 0 = pre-season, 1-18 = active
    status: v.union(
      v.literal("ready"),
      v.literal("training"),
      v.literal("predicting"),
      v.literal("advancing")
    ),
    lastTrainedAt: v.optional(v.string()), // ISO timestamp of last training
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_target_season", ["targetSeason"]),

  // Cached player features from ML backend for detail views
  playerFeatures: defineTable({
    playerId: v.string(),
    week: v.number(),
    season: v.number(),
    weather: v.optional(v.object({
      temperature: v.optional(v.number()),
      windSpeed: v.optional(v.number()),
      precipitation: v.optional(v.number()),
      isDome: v.optional(v.boolean()),
    })),
    vegas: v.optional(v.object({
      spread: v.optional(v.number()),
      overUnder: v.optional(v.number()),
      impliedTotal: v.optional(v.number()),
    })),
    opponentDefense: v.optional(v.object({
      rank: v.optional(v.number()),
      passingYardsAllowed: v.optional(v.number()),
      rushingYardsAllowed: v.optional(v.number()),
      pointsAllowed: v.optional(v.number()),
    })),
    usage: v.optional(v.object({
      snapPct: v.optional(v.number()),
      targetShare: v.optional(v.number()),
      carryShare: v.optional(v.number()),
      redZoneOpportunities: v.optional(v.number()),
    })),
    updatedAt: v.number(),
  })
    .index("by_player_week", ["playerId", "week", "season"]),
});
