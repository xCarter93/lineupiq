import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Queries

/**
 * List all scoring configs, ordered by name
 */
export const list = query({
  args: {},
  handler: async (ctx) => {
    const configs = await ctx.db.query("scoringConfigs").collect();
    return configs.sort((a, b) => a.name.localeCompare(b.name));
  },
});

/**
 * Get the default scoring config
 */
export const getDefault = query({
  args: {},
  handler: async (ctx) => {
    const config = await ctx.db
      .query("scoringConfigs")
      .withIndex("by_default", (q) => q.eq("isDefault", true))
      .first();
    return config;
  },
});

/**
 * Get a single scoring config by ID
 */
export const getById = query({
  args: { id: v.id("scoringConfigs") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Mutations

/**
 * Create a new scoring config
 * If isDefault is true, clears default flag from all other configs first
 */
export const create = mutation({
  args: {
    name: v.string(),
    passing: v.object({
      yardsPerPoint: v.number(),
      tdPoints: v.number(),
      intPoints: v.number(),
    }),
    rushing: v.object({
      yardsPerPoint: v.number(),
      tdPoints: v.number(),
    }),
    receiving: v.object({
      yardsPerPoint: v.number(),
      tdPoints: v.number(),
      receptionPoints: v.number(),
    }),
    isDefault: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    // If setting as default, clear other defaults first
    if (args.isDefault) {
      const currentDefault = await ctx.db
        .query("scoringConfigs")
        .withIndex("by_default", (q) => q.eq("isDefault", true))
        .first();
      if (currentDefault) {
        await ctx.db.patch(currentDefault._id, { isDefault: false });
      }
    }

    return await ctx.db.insert("scoringConfigs", {
      name: args.name,
      passing: args.passing,
      rushing: args.rushing,
      receiving: args.receiving,
      isDefault: args.isDefault ?? false,
    });
  },
});

/**
 * Update an existing scoring config
 * If setting isDefault to true, clears default flag from all other configs first
 */
export const update = mutation({
  args: {
    id: v.id("scoringConfigs"),
    name: v.optional(v.string()),
    passing: v.optional(
      v.object({
        yardsPerPoint: v.number(),
        tdPoints: v.number(),
        intPoints: v.number(),
      })
    ),
    rushing: v.optional(
      v.object({
        yardsPerPoint: v.number(),
        tdPoints: v.number(),
      })
    ),
    receiving: v.optional(
      v.object({
        yardsPerPoint: v.number(),
        tdPoints: v.number(),
        receptionPoints: v.number(),
      })
    ),
    isDefault: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;

    // If setting as default, clear other defaults first
    if (updates.isDefault) {
      const currentDefault = await ctx.db
        .query("scoringConfigs")
        .withIndex("by_default", (q) => q.eq("isDefault", true))
        .first();
      if (currentDefault && currentDefault._id !== id) {
        await ctx.db.patch(currentDefault._id, { isDefault: false });
      }
    }

    // Filter out undefined values
    const filteredUpdates: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(updates)) {
      if (value !== undefined) {
        filteredUpdates[key] = value;
      }
    }

    await ctx.db.patch(id, filteredUpdates);
    return id;
  },
});

/**
 * Remove a scoring config
 * Prevents deleting the default config
 */
export const remove = mutation({
  args: { id: v.id("scoringConfigs") },
  handler: async (ctx, args) => {
    const config = await ctx.db.get(args.id);
    if (!config) {
      throw new Error("Scoring config not found");
    }
    if (config.isDefault) {
      throw new Error("Cannot delete the default scoring config");
    }
    await ctx.db.delete(args.id);
  },
});

/**
 * Set a specific config as the default
 * Clears default flag from all other configs
 */
export const setDefault = mutation({
  args: { id: v.id("scoringConfigs") },
  handler: async (ctx, args) => {
    // Clear all defaults
    const allConfigs = await ctx.db.query("scoringConfigs").collect();
    for (const config of allConfigs) {
      if (config.isDefault) {
        await ctx.db.patch(config._id, { isDefault: false });
      }
    }

    // Set new default
    await ctx.db.patch(args.id, { isDefault: true });
  },
});

/**
 * Seed default scoring presets if none exist
 * Creates Standard (default), PPR, and Half-PPR configs
 * Idempotent - only runs if no configs exist
 */
export const seedDefaults = mutation({
  args: {},
  handler: async (ctx) => {
    // Check if any configs exist
    const existing = await ctx.db.query("scoringConfigs").first();
    if (existing) {
      return; // Already seeded
    }

    // Standard scoring (default)
    await ctx.db.insert("scoringConfigs", {
      name: "Standard",
      isDefault: true,
      passing: {
        yardsPerPoint: 25, // 1 pt per 25 yards
        tdPoints: 4,
        intPoints: -2,
      },
      rushing: {
        yardsPerPoint: 10, // 1 pt per 10 yards
        tdPoints: 6,
      },
      receiving: {
        yardsPerPoint: 10, // 1 pt per 10 yards
        tdPoints: 6,
        receptionPoints: 0, // No points per reception
      },
    });

    // PPR scoring
    await ctx.db.insert("scoringConfigs", {
      name: "PPR",
      isDefault: false,
      passing: {
        yardsPerPoint: 25,
        tdPoints: 4,
        intPoints: -2,
      },
      rushing: {
        yardsPerPoint: 10,
        tdPoints: 6,
      },
      receiving: {
        yardsPerPoint: 10,
        tdPoints: 6,
        receptionPoints: 1, // 1 point per reception
      },
    });

    // Half-PPR scoring
    await ctx.db.insert("scoringConfigs", {
      name: "Half-PPR",
      isDefault: false,
      passing: {
        yardsPerPoint: 25,
        tdPoints: 4,
        intPoints: -2,
      },
      rushing: {
        yardsPerPoint: 10,
        tdPoints: 6,
      },
      receiving: {
        yardsPerPoint: 10,
        tdPoints: 6,
        receptionPoints: 0.5, // 0.5 points per reception
      },
    });
  },
});
