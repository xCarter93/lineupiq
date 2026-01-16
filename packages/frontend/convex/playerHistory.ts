import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Get all history for a player
export const getByPlayer = query({
  args: { playerId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("playerHistory")
      .withIndex("by_player", (q) => q.eq("playerId", args.playerId))
      .collect();
  },
});

// Get history for a player's specific season
export const getByPlayerSeason = query({
  args: {
    playerId: v.string(),
    season: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("playerHistory")
      .withIndex("by_player_season", (q) =>
        q.eq("playerId", args.playerId).eq("season", args.season)
      )
      .collect();
  },
});

// Get most recent N games for a player
export const getRecentGames = query({
  args: {
    playerId: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 10;
    const games = await ctx.db
      .query("playerHistory")
      .withIndex("by_player", (q) => q.eq("playerId", args.playerId))
      .collect();

    // Sort by season desc, week desc and take limit
    return games
      .sort((a, b) => {
        if (b.season !== a.season) return b.season - a.season;
        return b.week - a.week;
      })
      .slice(0, limit);
  },
});

// Bulk upsert history records
export const bulkUpsert = mutation({
  args: {
    games: v.array(
      v.object({
        playerId: v.string(),
        season: v.number(),
        week: v.number(),
        opponentTeam: v.optional(v.string()),
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
      })
    ),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    let count = 0;

    for (const game of args.games) {
      // Check if record exists for this player/season/week
      const existing = await ctx.db
        .query("playerHistory")
        .withIndex("by_player_week", (q) =>
          q
            .eq("playerId", game.playerId)
            .eq("season", game.season)
            .eq("week", game.week)
        )
        .first();

      const data = { ...game, updatedAt: now };

      if (existing) {
        await ctx.db.patch(existing._id, data);
      } else {
        await ctx.db.insert("playerHistory", data);
      }
      count++;
    }

    return count;
  },
});

// Clear history for a player (for re-import)
export const clearByPlayer = mutation({
  args: { playerId: v.string() },
  handler: async (ctx, args) => {
    const records = await ctx.db
      .query("playerHistory")
      .withIndex("by_player", (q) => q.eq("playerId", args.playerId))
      .collect();

    for (const record of records) {
      await ctx.db.delete(record._id);
    }

    return records.length;
  },
});
