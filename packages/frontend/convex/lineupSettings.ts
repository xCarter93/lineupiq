import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Default lineup slots configuration
const DEFAULT_SLOTS = [
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

// Queries

/**
 * Get current lineup settings
 * Returns default settings if none exist
 */
export const get = query({
  args: {},
  handler: async (ctx) => {
    const settings = await ctx.db.query("lineupSettings").first();
    if (settings) {
      return settings;
    }
    // Return default structure without persisting
    return {
      slots: DEFAULT_SLOTS,
      updatedAt: Date.now(),
    };
  },
});

// Mutations

/**
 * Update lineup settings (creates if doesn't exist)
 */
export const update = mutation({
  args: {
    slots: v.array(
      v.object({
        position: v.string(),
        eligiblePositions: v.array(v.string()),
      })
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("lineupSettings").first();
    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        slots: args.slots,
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("lineupSettings", {
      slots: args.slots,
      updatedAt: now,
    });
  },
});

/**
 * Add a new slot to the lineup
 */
export const addSlot = mutation({
  args: {
    position: v.string(),
    eligiblePositions: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("lineupSettings").first();
    const now = Date.now();

    const newSlot = {
      position: args.position,
      eligiblePositions: args.eligiblePositions,
    };

    if (existing) {
      await ctx.db.patch(existing._id, {
        slots: [...existing.slots, newSlot],
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("lineupSettings", {
      slots: [...DEFAULT_SLOTS, newSlot],
      updatedAt: now,
    });
  },
});

/**
 * Remove a slot from the lineup by index
 */
export const removeSlot = mutation({
  args: { slotIndex: v.number() },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("lineupSettings").first();

    if (!existing) {
      throw new Error("No lineup settings found");
    }

    if (args.slotIndex < 0 || args.slotIndex >= existing.slots.length) {
      throw new Error("Invalid slot index");
    }

    const updatedSlots = existing.slots.filter(
      (_, index) => index !== args.slotIndex
    );

    await ctx.db.patch(existing._id, {
      slots: updatedSlots,
      updatedAt: Date.now(),
    });

    return existing._id;
  },
});

/**
 * Update a specific slot's eligible positions
 */
export const updateSlot = mutation({
  args: {
    slotIndex: v.number(),
    position: v.optional(v.string()),
    eligiblePositions: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("lineupSettings").first();

    if (!existing) {
      throw new Error("No lineup settings found");
    }

    if (args.slotIndex < 0 || args.slotIndex >= existing.slots.length) {
      throw new Error("Invalid slot index");
    }

    const updatedSlots = [...existing.slots];
    updatedSlots[args.slotIndex] = {
      position: args.position ?? updatedSlots[args.slotIndex].position,
      eligiblePositions:
        args.eligiblePositions ??
        updatedSlots[args.slotIndex].eligiblePositions,
    };

    await ctx.db.patch(existing._id, {
      slots: updatedSlots,
      updatedAt: Date.now(),
    });

    return existing._id;
  },
});

/**
 * Reset lineup settings to defaults
 */
export const resetToDefaults = mutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db.query("lineupSettings").first();
    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        slots: DEFAULT_SLOTS,
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("lineupSettings", {
      slots: DEFAULT_SLOTS,
      updatedAt: now,
    });
  },
});
