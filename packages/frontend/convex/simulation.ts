import { query, mutation } from "./_generated/server";
import { v } from "convex/values";
import { getCurrentSeason } from "../lib/season";

// Queries

/**
 * Get the current simulation state for a target season
 * Returns the most recent simulation for the given season, or null if none exists
 */
export const getSimulationState = query({
  args: { targetSeason: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const season = args.targetSeason ?? getCurrentSeason();
    const simulation = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", season))
      .first();
    return simulation;
  },
});

/**
 * List all simulations
 */
export const list = query({
  args: {},
  handler: async (ctx) => {
    const simulations = await ctx.db.query("simulationState").collect();
    return simulations.sort((a, b) => b.createdAt - a.createdAt);
  },
});

// Mutations

/**
 * Initialize a new simulation
 * Creates a simulation state record starting at week 0 (pre-season)
 */
export const initializeSimulation = mutation({
  args: {
    name: v.optional(v.string()),
    targetSeason: v.number(),
    trainingSeasons: v.array(v.number()),
  },
  handler: async (ctx, args) => {
    // Check if simulation already exists for this season
    const existing = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", args.targetSeason))
      .first();

    if (existing) {
      // Delete existing simulation to start fresh
      await ctx.db.delete(existing._id);
    }

    const now = Date.now();
    const name = args.name ?? `${args.targetSeason} Season Simulation`;

    return await ctx.db.insert("simulationState", {
      name,
      targetSeason: args.targetSeason,
      trainingSeasons: args.trainingSeasons,
      currentWeek: 0, // Pre-season state
      status: "ready",
      createdAt: now,
      updatedAt: now,
    });
  },
});

/**
 * Update the simulation status
 * Used during training/prediction workflows to show progress
 */
export const updateStatus = mutation({
  args: {
    targetSeason: v.number(),
    status: v.union(
      v.literal("ready"),
      v.literal("training"),
      v.literal("predicting"),
      v.literal("advancing")
    ),
    lastTrainedAt: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const simulation = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", args.targetSeason))
      .first();

    if (!simulation) {
      throw new Error(`No simulation found for season ${args.targetSeason}`);
    }

    const updates: Record<string, unknown> = {
      status: args.status,
      updatedAt: Date.now(),
    };

    if (args.lastTrainedAt !== undefined) {
      updates.lastTrainedAt = args.lastTrainedAt;
    }

    await ctx.db.patch(simulation._id, updates);
    return simulation._id;
  },
});

/**
 * Advance the simulation to the next week
 * Increments currentWeek and sets status to ready
 */
export const advanceWeek = mutation({
  args: {
    targetSeason: v.number(),
    toWeek: v.optional(v.number()), // If provided, advances to specific week
  },
  handler: async (ctx, args) => {
    const simulation = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", args.targetSeason))
      .first();

    if (!simulation) {
      throw new Error(`No simulation found for season ${args.targetSeason}`);
    }

    const newWeek = args.toWeek ?? simulation.currentWeek + 1;

    if (newWeek < 0 || newWeek > 18) {
      throw new Error(`Invalid week: ${newWeek}. Must be between 0 and 18.`);
    }

    if (newWeek <= simulation.currentWeek) {
      throw new Error(
        `Cannot advance backwards. Current week: ${simulation.currentWeek}, requested: ${newWeek}`
      );
    }

    await ctx.db.patch(simulation._id, {
      currentWeek: newWeek,
      status: "ready",
      updatedAt: Date.now(),
    });

    return newWeek;
  },
});

/**
 * Reset simulation to week 0 (pre-season state)
 */
export const resetSimulation = mutation({
  args: { targetSeason: v.number() },
  handler: async (ctx, args) => {
    const simulation = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", args.targetSeason))
      .first();

    if (!simulation) {
      throw new Error(`No simulation found for season ${args.targetSeason}`);
    }

    await ctx.db.patch(simulation._id, {
      currentWeek: 0,
      status: "ready",
      lastTrainedAt: undefined,
      updatedAt: Date.now(),
    });

    return simulation._id;
  },
});

/**
 * Delete a simulation entirely
 */
export const deleteSimulation = mutation({
  args: { targetSeason: v.number() },
  handler: async (ctx, args) => {
    const simulation = await ctx.db
      .query("simulationState")
      .withIndex("by_target_season", (q) => q.eq("targetSeason", args.targetSeason))
      .first();

    if (!simulation) {
      throw new Error(`No simulation found for season ${args.targetSeason}`);
    }

    await ctx.db.delete(simulation._id);
  },
});
