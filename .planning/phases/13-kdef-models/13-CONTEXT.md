# Phase 13 Context: K/DEF Models + Training Improvements

## Expanded Scope

This phase bundles three major work streams:
1. **Training Pipeline Improvements** (from Phase 11 audit)
2. **K/DEF Models** (new positions)
3. **Complete Fantasy Scoring** (all position types)

## Data Availability (from nflreadpy exploration)

### Kicker Data (`load_player_stats`)
Available columns for K position (569 rows in 2024):
- `fg_made`, `fg_att`, `fg_missed`, `fg_blocked`
- `fg_made_0_19`, `fg_made_20_29`, `fg_made_30_39`, `fg_made_40_49`, `fg_made_50_59`, `fg_made_60_`
- Same breakdown for `fg_missed_*`
- `pat_made`, `pat_att`, `pat_missed`, `pat_blocked`
- `fg_pct`, `pat_pct`

### Team Defense Data (`load_team_stats`)
102 columns including:
- Defensive stats: `def_sacks`, `def_interceptions`, `def_tds`, `def_fumbles_forced`, `def_fumbles`, `def_safeties`
- Special teams: `special_teams_tds`, `punt_returns`, `punt_return_yards`, `kickoff_returns`, `kickoff_return_yards`
- Points allowed: computed from `home_score`/`away_score` in schedules

## ESPN Standard Scoring Reference

### Kicking
| Stat | Points |
|------|--------|
| FG 0-39 yards | 3 |
| FG 40-49 yards | 4 |
| FG 50+ yards | 5 |
| XP Made | 1 |
| XP Missed | -1 |
| FG Missed 0-39 | 0 |
| FG Missed 40-49 | -1 |
| FG Missed 50+ | 0 |

### Team Defense/Special Teams
| Stat | Points |
|------|--------|
| Sack | 1 |
| Interception | 2 |
| Fumble Recovery | 2 |
| Defensive TD | 6 |
| Safety | 2 |
| Blocked Kick | 2 |
| Kick/Punt Return TD | 6 |

**Points Allowed Tiers:**
| Points Allowed | Fantasy Points |
|----------------|----------------|
| 0 | 10 |
| 1-6 | 7 |
| 7-13 | 4 |
| 14-20 | 1 |
| 21-27 | 0 |
| 28-34 | -1 |
| 35+ | -4 |

### Missing from Current Skill Position Scoring
- QB: interceptions (-2), fumbles lost (-2)
- RB: fumbles lost (-2), receiving TDs (+6)
- WR/TE: fumbles lost (-2)
- All: 2-pt conversions (+2)

## Phase 11 Audit Recommendations to Implement

### Priority 1: LightGBM Migration
- 7x faster training enables more Optuna trials
- Native categorical handling for team IDs
- Add `get_lgb_params()` to training.py

### Priority 2: New Features
**Team Strength Features:**
- Offense points per game (rolling)
- Total yards per game (rolling)
- Pace of play indicator

**Player Volatility Metrics:**
- Rolling standard deviation of stats
- Coefficient of variation (CV = std/mean)

## Backtest Baseline (from conversation)

Current model accuracy on 2025 holdout:
- Overall: 60.3% accuracy
- Strong: QB passing_yards (72.8%), RB carries (70.0%)
- Weak: TD predictions (0-7.7% accuracy)

## Plan Structure

**Wave 1 (parallel - infrastructure):**
- 13-01: LightGBM Migration
- 13-02: Team Strength & Volatility Features
- 13-03: K/DEF Data Pipeline
- 13-04: Complete Fantasy Scoring Config

**Wave 2 (parallel - model training):**
- 13-05: Kicker Models + API
- 13-06: Defense Models + API
- 13-07: Retrain Skill Position Models

**Wave 3:**
- 13-08: Backtest All Models & Calibrate Intervals

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| LightGBM as default, keep XGBoost option | Speed + flexibility for comparison |
| Team-level defense prediction (not individual) | Fantasy uses team DST, not individual defenders |
| Kicker predictions: FG attempts by distance + XP | Match scoring granularity |
| Include all ESPN standard scoring stats | Comprehensive coverage for future user customization |
