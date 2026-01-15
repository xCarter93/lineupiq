import { mutation } from "./_generated/server";

// Sample NFL players for testing the matchup UI
const SAMPLE_PLAYERS = [
  // QBs
  { playerId: "mahomes-patrick", name: "Patrick Mahomes", position: "QB", team: "KC" },
  { playerId: "allen-josh", name: "Josh Allen", position: "QB", team: "BUF" },
  { playerId: "hurts-jalen", name: "Jalen Hurts", position: "QB", team: "PHI" },
  { playerId: "burrow-joe", name: "Joe Burrow", position: "QB", team: "CIN" },
  { playerId: "jackson-lamar", name: "Lamar Jackson", position: "QB", team: "BAL" },
  { playerId: "herbert-justin", name: "Justin Herbert", position: "QB", team: "LAC" },

  // RBs
  { playerId: "mccaffrey-christian", name: "Christian McCaffrey", position: "RB", team: "SF" },
  { playerId: "henry-derrick", name: "Derrick Henry", position: "RB", team: "BAL" },
  { playerId: "chubb-nick", name: "Nick Chubb", position: "RB", team: "CLE" },
  { playerId: "barkley-saquon", name: "Saquon Barkley", position: "RB", team: "PHI" },
  { playerId: "taylor-jonathan", name: "Jonathan Taylor", position: "RB", team: "IND" },
  { playerId: "jacobs-josh", name: "Josh Jacobs", position: "RB", team: "GB" },

  // WRs
  { playerId: "hill-tyreek", name: "Tyreek Hill", position: "WR", team: "MIA" },
  { playerId: "jefferson-justin", name: "Justin Jefferson", position: "WR", team: "MIN" },
  { playerId: "chase-jamarr", name: "Ja'Marr Chase", position: "WR", team: "CIN" },
  { playerId: "lamb-ceedee", name: "CeeDee Lamb", position: "WR", team: "DAL" },
  { playerId: "brown-aj", name: "A.J. Brown", position: "WR", team: "PHI" },
  { playerId: "diggs-stefon", name: "Stefon Diggs", position: "WR", team: "HOU" },

  // TEs
  { playerId: "kelce-travis", name: "Travis Kelce", position: "TE", team: "KC" },
  { playerId: "andrews-mark", name: "Mark Andrews", position: "TE", team: "BAL" },
  { playerId: "kittle-george", name: "George Kittle", position: "TE", team: "SF" },
  { playerId: "hockenson-tj", name: "T.J. Hockenson", position: "TE", team: "MIN" },
  { playerId: "goedert-dallas", name: "Dallas Goedert", position: "TE", team: "PHI" },
  { playerId: "waller-darren", name: "Darren Waller", position: "TE", team: "NYG" },
];

// Seed sample players for UI testing
export const seedSamplePlayers = mutation({
  args: {},
  handler: async (ctx) => {
    // Check if already seeded
    const existing = await ctx.db.query("players").first();
    if (existing) {
      return { status: "already_seeded", count: 0 };
    }

    // Insert all sample players
    for (const player of SAMPLE_PLAYERS) {
      await ctx.db.insert("players", player);
    }

    return { status: "seeded", count: SAMPLE_PLAYERS.length };
  },
});

// Clear all players (for testing)
export const clearPlayers = mutation({
  args: {},
  handler: async (ctx) => {
    const players = await ctx.db.query("players").collect();
    for (const player of players) {
      await ctx.db.delete(player._id);
    }
    return { cleared: players.length };
  },
});
