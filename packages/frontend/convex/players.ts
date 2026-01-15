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

// Create or update player
export const upsert = mutation({
  args: {
    playerId: v.string(),
    name: v.string(),
    position: v.string(),
    team: v.string(),
  },
  handler: async (ctx, args) => {
    // Check if playerId exists
    const players = await ctx.db.query("players").collect();
    const existing = players.find((p) => p.playerId === args.playerId);

    if (existing) {
      // Update existing player
      await ctx.db.patch(existing._id, {
        name: args.name,
        position: args.position,
        team: args.team,
      });
      return existing._id;
    }

    // Insert new player
    return await ctx.db.insert("players", {
      playerId: args.playerId,
      name: args.name,
      position: args.position,
      team: args.team,
    });
  },
});

// Upsert multiple players
export const bulkUpsert = mutation({
  args: {
    players: v.array(
      v.object({
        playerId: v.string(),
        name: v.string(),
        position: v.string(),
        team: v.string(),
      })
    ),
  },
  handler: async (ctx, args) => {
    // Get all existing players for lookup
    const existingPlayers = await ctx.db.query("players").collect();
    const existingByPlayerId = new Map(
      existingPlayers.map((p) => [p.playerId, p])
    );

    let count = 0;

    for (const player of args.players) {
      const existing = existingByPlayerId.get(player.playerId);

      if (existing) {
        await ctx.db.patch(existing._id, {
          name: player.name,
          position: player.position,
          team: player.team,
        });
      } else {
        await ctx.db.insert("players", {
          playerId: player.playerId,
          name: player.name,
          position: player.position,
          team: player.team,
        });
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
