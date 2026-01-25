import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

const MAX_RECENT_PLAYERS = 5;

// Queries

/**
 * Get recently viewed players
 * Returns player IDs sorted by most recent first
 */
export const get = query({
  args: {},
  handler: async (ctx) => {
    const recent = await ctx.db.query("recentPlayers").first();
    if (!recent) {
      return { playerIds: [], timestamps: [] };
    }
    return {
      playerIds: recent.playerIds,
      timestamps: recent.timestamps,
    };
  },
});

/**
 * Get recently viewed players with full player data
 */
export const getWithDetails = query({
  args: {},
  handler: async (ctx) => {
    const recent = await ctx.db.query("recentPlayers").first();
    if (!recent || recent.playerIds.length === 0) {
      return [];
    }

    const players = await Promise.all(
      recent.playerIds.map(async (playerId) => {
        const player = await ctx.db
          .query("players")
          .withIndex("by_player_id", (q) => q.eq("playerId", playerId))
          .first();
        return player;
      })
    );

    // Filter out any null results (deleted players)
    return players.filter((p) => p !== null);
  },
});

// Mutations

/**
 * Add a player to recent players list
 * Moves player to front if already exists
 * Maintains max of 5 recent players
 */
export const add = mutation({
  args: { playerId: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("recentPlayers").first();
    const now = Date.now();

    if (existing) {
      // Remove player if already in list
      const existingIndex = existing.playerIds.indexOf(args.playerId);
      let playerIds = [...existing.playerIds];
      let timestamps = [...existing.timestamps];

      if (existingIndex !== -1) {
        playerIds.splice(existingIndex, 1);
        timestamps.splice(existingIndex, 1);
      }

      // Add to front
      playerIds.unshift(args.playerId);
      timestamps.unshift(now);

      // Trim to max size
      if (playerIds.length > MAX_RECENT_PLAYERS) {
        playerIds = playerIds.slice(0, MAX_RECENT_PLAYERS);
        timestamps = timestamps.slice(0, MAX_RECENT_PLAYERS);
      }

      await ctx.db.patch(existing._id, {
        playerIds,
        timestamps,
        updatedAt: now,
      });
      return existing._id;
    }

    return await ctx.db.insert("recentPlayers", {
      playerIds: [args.playerId],
      timestamps: [now],
      updatedAt: now,
    });
  },
});

/**
 * Clear all recent players
 */
export const clear = mutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db.query("recentPlayers").first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        playerIds: [],
        timestamps: [],
        updatedAt: Date.now(),
      });
    }
  },
});
