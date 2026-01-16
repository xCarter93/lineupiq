import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Return all players, ordered by name
export const list = query({
  args: {},
  handler: async (ctx) => {
    const players = await ctx.db.query("players").collect();
    return players.sort((a, b) => a.name.localeCompare(b.name));
  },
});

// Get players for a position
export const getByPosition = query({
  args: {
    position: v.union(
      v.literal("QB"),
      v.literal("RB"),
      v.literal("WR"),
      v.literal("TE")
    ),
  },
  handler: async (ctx, args) => {
    const players = await ctx.db
      .query("players")
      .withIndex("by_position", (q) => q.eq("position", args.position))
      .collect();
    return players.sort((a, b) => a.name.localeCompare(b.name));
  },
});

// Get players on a team
export const getByTeam = query({
  args: {
    team: v.string(),
  },
  handler: async (ctx, args) => {
    const players = await ctx.db
      .query("players")
      .withIndex("by_team", (q) => q.eq("team", args.team))
      .collect();
    return players.sort((a, b) => a.name.localeCompare(b.name));
  },
});

// Search players by name
export const search = query({
  args: {
    query: v.string(),
  },
  handler: async (ctx, args) => {
    const searchQuery = args.query.toLowerCase();

    // Get all players and filter by name
    const players = await ctx.db.query("players").collect();

    const matches = players.filter((player) =>
      player.name.toLowerCase().includes(searchQuery)
    );

    // Sort by name and limit to 20 results
    return matches.sort((a, b) => a.name.localeCompare(b.name)).slice(0, 20);
  },
});

// Get player by playerId
export const getByPlayerId = query({
  args: { playerId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("players")
      .withIndex("by_player_id", (q) => q.eq("playerId", args.playerId))
      .first();
  },
});

// Create or update player
export const upsert = mutation({
  args: {
    playerId: v.string(),
    name: v.string(),
    position: v.string(),
    team: v.string(),
    // Optional enriched fields
    jerseyNumber: v.optional(v.number()),
    height: v.optional(v.string()),
    weight: v.optional(v.number()),
    college: v.optional(v.string()),
    yearsExp: v.optional(v.number()),
    headshotUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Use by_player_id index for efficient lookup
    const existing = await ctx.db
      .query("players")
      .withIndex("by_player_id", (q) => q.eq("playerId", args.playerId))
      .first();

    const data = {
      playerId: args.playerId,
      name: args.name,
      position: args.position,
      team: args.team,
      jerseyNumber: args.jerseyNumber,
      height: args.height,
      weight: args.weight,
      college: args.college,
      yearsExp: args.yearsExp,
      headshotUrl: args.headshotUrl,
    };

    if (existing) {
      await ctx.db.patch(existing._id, data);
      return existing._id;
    }

    return await ctx.db.insert("players", data);
  },
});

// Upsert multiple players with enriched data
export const bulkUpsert = mutation({
  args: {
    players: v.array(
      v.object({
        playerId: v.string(),
        name: v.string(),
        position: v.string(),
        team: v.string(),
        // Optional enriched fields
        jerseyNumber: v.optional(v.number()),
        height: v.optional(v.string()),
        weight: v.optional(v.number()),
        college: v.optional(v.string()),
        yearsExp: v.optional(v.number()),
        headshotUrl: v.optional(v.string()),
      })
    ),
  },
  handler: async (ctx, args) => {
    // Use by_player_id index for faster lookups
    let count = 0;

    for (const player of args.players) {
      const existing = await ctx.db
        .query("players")
        .withIndex("by_player_id", (q) => q.eq("playerId", player.playerId))
        .first();

      const data = {
        playerId: player.playerId,
        name: player.name,
        position: player.position,
        team: player.team,
        jerseyNumber: player.jerseyNumber,
        height: player.height,
        weight: player.weight,
        college: player.college,
        yearsExp: player.yearsExp,
        headshotUrl: player.headshotUrl,
      };

      if (existing) {
        await ctx.db.patch(existing._id, data);
      } else {
        await ctx.db.insert("players", data);
      }
      count++;
    }

    return count;
  },
});

// Delete player
export const remove = mutation({
  args: {
    id: v.id("players"),
  },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
