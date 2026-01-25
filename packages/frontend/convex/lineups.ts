import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Queries

/**
 * Get lineup for a specific week and season
 */
export const getByWeek = query({
  args: {
    week: v.number(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("lineups")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      )
      .first();
  },
});

/**
 * Get all lineups for a season
 */
export const getBySeason = query({
  args: { season: v.number() },
  handler: async (ctx, args) => {
    const lineups = await ctx.db
      .query("lineups")
      .filter((q) => q.eq(q.field("season"), args.season))
      .collect();
    return lineups.sort((a, b) => a.week - b.week);
  },
});

// Mutations

/**
 * Create or update a lineup for a specific week
 */
export const upsert = mutation({
  args: {
    week: v.number(),
    season: v.number(),
    slots: v.array(
      v.object({
        position: v.string(),
        playerId: v.optional(v.string()),
      })
    ),
    totalProjectedPoints: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("lineups")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      )
      .first();

    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        slots: args.slots,
        totalProjectedPoints: args.totalProjectedPoints,
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("lineups", {
      week: args.week,
      season: args.season,
      slots: args.slots,
      totalProjectedPoints: args.totalProjectedPoints,
      createdAt: now,
      updatedAt: now,
    });
  },
});

/**
 * Add a player to a specific slot in the lineup
 */
export const addPlayer = mutation({
  args: {
    week: v.number(),
    season: v.number(),
    slotIndex: v.number(),
    playerId: v.string(),
  },
  handler: async (ctx, args) => {
    const lineup = await ctx.db
      .query("lineups")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      )
      .first();

    if (!lineup) {
      throw new Error("Lineup not found for this week");
    }

    if (args.slotIndex < 0 || args.slotIndex >= lineup.slots.length) {
      throw new Error("Invalid slot index");
    }

    const updatedSlots = [...lineup.slots];
    updatedSlots[args.slotIndex] = {
      ...updatedSlots[args.slotIndex],
      playerId: args.playerId,
    };

    await ctx.db.patch(lineup._id, {
      slots: updatedSlots,
      updatedAt: Date.now(),
    });

    return lineup._id;
  },
});

/**
 * Remove a player from a specific slot in the lineup
 */
export const removePlayer = mutation({
  args: {
    week: v.number(),
    season: v.number(),
    slotIndex: v.number(),
  },
  handler: async (ctx, args) => {
    const lineup = await ctx.db
      .query("lineups")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      )
      .first();

    if (!lineup) {
      throw new Error("Lineup not found for this week");
    }

    if (args.slotIndex < 0 || args.slotIndex >= lineup.slots.length) {
      throw new Error("Invalid slot index");
    }

    const updatedSlots = [...lineup.slots];
    updatedSlots[args.slotIndex] = {
      ...updatedSlots[args.slotIndex],
      playerId: undefined,
    };

    await ctx.db.patch(lineup._id, {
      slots: updatedSlots,
      updatedAt: Date.now(),
    });

    return lineup._id;
  },
});

/**
 * Initialize an empty lineup with default slots for a week
 */
export const initialize = mutation({
  args: {
    week: v.number(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    // Check if lineup already exists
    const existing = await ctx.db
      .query("lineups")
      .withIndex("by_week_season", (q) =>
        q.eq("week", args.week).eq("season", args.season)
      )
      .first();

    if (existing) {
      return existing._id;
    }

    // Get lineup settings or use defaults
    const settings = await ctx.db.query("lineupSettings").first();
    const defaultSlots = settings?.slots ?? [
      { position: "QB", eligiblePositions: ["QB"] },
      { position: "RB", eligiblePositions: ["RB"] },
      { position: "RB", eligiblePositions: ["RB"] },
      { position: "WR", eligiblePositions: ["WR"] },
      { position: "WR", eligiblePositions: ["WR"] },
      { position: "TE", eligiblePositions: ["TE"] },
      { position: "FLEX", eligiblePositions: ["RB", "WR", "TE"] },
      { position: "K", eligiblePositions: ["K"] },
      { position: "DEF", eligiblePositions: ["DEF"] },
    ];

    const now = Date.now();
    return await ctx.db.insert("lineups", {
      week: args.week,
      season: args.season,
      slots: defaultSlots.map((slot) => ({
        position: slot.position,
        playerId: undefined,
      })),
      createdAt: now,
      updatedAt: now,
    });
  },
});
