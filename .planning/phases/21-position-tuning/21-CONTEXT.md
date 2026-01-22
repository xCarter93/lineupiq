# Phase 21: Position-Specific Tuning - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<vision>
## How This Should Work

This phase is about deep diving into each position separately - training, benchmarking, and iterating until we're satisfied with each position's model quality. This isn't a batch "retrain everything" job; it's a sequential, thoughtful optimization process where we focus on one position at a time.

After Phase 20 added weather and matchup features, we now retrain models position-by-position with these expanded features, analyze what improved, and iterate if needed before moving to the next position.

We prioritize high-impact positions first - QB and RB get attention first (highest fantasy impact), then WR/TE, then K/DEF. Each position gets the time and analysis it deserves.

**Injury data is NOT included in training.** Injury features should only be used at prediction time to adjust for who's out, who's replacing them, and who's questionable/doubtful. Training on historical injury data doesn't produce meaningful insights.

</vision>

<essential>
## What Must Be Nailed

**Position-specific optimization depth** - Each position is unique. QBs aren't RBs. The deep dive approach should surface position-specific insights that might not be obvious in a batch retrain. For example:
- Weather features might matter more for kickers than running backs
- Vegas lines might correlate differently with WR performance vs DEF scoring
- Matchup context (divisional games, home/away spreads) might affect QB decisions vs RB usage

The core of this phase is treating each position as its own optimization problem, not just running the same training script six times.

</essential>

<specifics>
## Specific Ideas

**Start with high-impact positions first:**
1. QB - Most points in fantasy, highest user interest
2. RB - Second-highest fantasy impact
3. WR/TE - Receiver positions (can train together or separately)
4. K/DEF - Lower-variance but still important

This prioritization means if we discover issues or need to adjust the approach, we learn early on positions that matter most to users.

**Iteration workflow:**
- Train position with new features (weather + matchup, NO injury)
- Run benchmarks to see R² improvements
- Analyze results (feature importance, error patterns)
- Adjust if needed (feature engineering, hyperparameters)
- Move to next position when satisfied

Not looking for perfection, but we should understand what the new features did for each position before calling it done.

**14 new features to evaluate:**
- 7 weather features: extreme_cold, freezing, extreme_heat, high_wind, precipitation, dome_game, temperature
- 5 matchup features: home_spread, total_points, is_divisional (+ any other Vegas/context features from Phase 20)
- 2 context features: game context or situational features

Combined with existing rolling stats from Phase 19.1 (5-game window, 2022-2025 training data).

</specifics>

<notes>
## Additional Context

**Why no injury training data:**
Historic injury data doesn't predict future performance well - a player who was injured in 2023 might be perfectly healthy in 2026. Injury impact is better handled at prediction time:
- Check current injury reports (Out/Doubtful/Questionable)
- Adjust predictions for affected players
- Predict backup players if starters are out
- This is a separate phase concern (real-time injury adjustment logic)

**Current baseline:**
Phase 19.1 models with 5-game rolling window, trained on 2022-2025 data, using LightGBM with 30 Optuna trials.

**The question this phase answers:**
"How much do weather and matchup features improve predictions for each position, and which features matter most for each position?"

</notes>

---

*Phase: 21-position-tuning*
*Context gathered: 2026-01-22*
