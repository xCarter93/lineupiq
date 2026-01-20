# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-15)

**Core value:** Accurate stat-level predictions from well-engineered features and properly trained models.
**Current focus:** v1.2 Platform Maturity — performance, ensemble models, and enhanced UI

## Current Position

Phase: 18 of 25 (Performance Fixes & Optimization)
Plan: Not started
Status: Ready to plan
Last activity: 2026-01-20 - Milestone v1.2 created

Progress: ░░░░░░░░░░ 0%

## Performance Metrics

**Velocity (v1.0 MVP):**
- Total plans completed: 30
- Average duration: 8.4 min
- Total execution time: 4.2 hours

**By Phase (v1.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3/3 | 15.5 min | 5.2 min |
| 02-data-pipeline | 2/2 | 5 min | 2.5 min |
| 03-data-processing | 3/3 | 10 min | 3.3 min |
| 04-feature-engineering | 3/3 | 6 min | 2.0 min |
| 05-model-development | 4/4 | 79 min | 19.8 min |
| 06-model-evaluation | 3/3 | 49 min | 16.3 min |
| 07-prediction-api | 3/3 | 30 min | 10.0 min |
| 08-convex-backend | 3/3 | 20 min | 6.7 min |
| 09-matchup-ui | 3/3 | 25 min | 8.3 min |
| 10-integration-polish | 3/3 | 32 min | 10.7 min |

## Accumulated Context

### Decisions

**v1.1 Decisions:**

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 11 | Prediction intervals highest priority | MAPIE CQR provides guarantees with ~100 LOC |
| 11 | LightGBM before ensembles | 7x speedup enables experimentation first |
| 11 | Defer KNN imputation | A/B test after baseline improvements |
| 12 | Separate modelMetrics/overallMetrics tables | Efficient queries for different access patterns |
| 12 | Split conformal over MAPIE wrapper | Works with existing trained models without retraining |
| 12 | 90% confidence intervals (alpha=0.1) | Informative bounds without excessive uncertainty |
| 12 | Accuracy % formula: 100*(1-MAE/mean) | Intuitive 0-100% scale for user trust |
| 12 | Three-tier confidence (High/Med/Low) | Simple user-facing metric based on R2 + accuracy |
| 12 | Convex-first with API fallback | Hook checks Convex cache first, fetches from API if null |
| 12 | ModelConfidence in page.tsx not form | MatchupForm is input-only, results render in page |
| 13 | LightGBM as default, keep XGBoost option | 7x speed + flexibility for comparison |
| 13 | Team-level defense (not individual) | Fantasy uses team DST, not individual defenders |
| 13 | Kicker predictions: FG by distance + XP | Match ESPN scoring granularity |
| 13 | Bundle audit improvements with K/DEF | Train everything together for consistency |
| 13-03 | Team defense uses schedule for points_allowed | nflreadpy team_stats lacks this field |
| 13-03 | FG buckets match ESPN scoring (0-39, 40-49, 50+) | Aligns with fantasy point tiers |
| 13-04 | ESPN Standard as default scoring | Industry standard, widely recognized |
| 13-04 | Expected value for kicker scoring | Accounts for success probability in predictions |
| 13-04 | 75% success rate for 50+ yard FGs | NFL average lower for long-distance attempts |
| 13-02 | Shift(1) for rolling feature leakage prevention | Only prior games used, never current game |
| 13-02 | CV (coeff of variation) for normalized volatility | Identifies boom/bust players across stat scales |
| 13-05 | LightGBM default for kicker models | 7x speedup from Phase 13-01 |
| 13-05 | 30 Optuna trials per kicker target | Balance training time vs optimization |
| 13-06 | Defense uses def_ prefix columns | nflreadpy team_stats column naming convention |
| 13-06 | 5 defense target models | Covers main fantasy DST scoring categories |
| 13-07 | LightGBM default for all skill positions | Consistent with 13-01, enables faster experimentation |
| 13-07 | train_receiver_models() convenience function | Easier to train WR + TE together |
| 13-08 | 2024 as holdout season for backtesting | 2025 data may be incomplete |
| 13-08 | K/DEF lower accuracy expected | High-variance events limit predictability |
| 13-08 | Convex metrics storage deferred | Optional, documented in BACKTEST_RESULTS.md |
| 14-01 | Column mapping in prepare_qb_data() | Keeps changes scoped to QB module vs pipeline-wide |
| 14-01 | 30 Optuna trials for QB models | Balance training time vs optimization |
| 14-01 | Non-negative clamping for count stats | Prevent negative interceptions/fumbles predictions |
| 14-02 | Combined fumbles_lost in prepare_rb_data() | Sum of rushing + receiving fumbles for fantasy scoring |
| 14-02 | Add fumble columns to ML_COLUMNS | Ensures data flows through cleaning pipeline |
| 14-02 | Non-negative guards for RB count stats | Consistent with 14-01 approach for TDs/fumbles |
| 14-03 | Map receiving_fumbles_lost to fumbles_lost | Consistent API naming across positions |
| 14-03 | Round fumbles_lost to 2 decimals | Rare events (~0.01-0.02/game) need precision |
| 14-04 | -2 pts per fumble (standard scoring) | Industry standard fantasy football scoring |
| 14-04 | Red text for negative stats in UI | Visual distinction for INTs/fumbles |
| 14-04 | Responsive grid layouts (2/4/6/7 cols) | Scale from mobile to full-width desktop |
| 15-01 | Height as int (inches) not string | nflreadpy returns height in inches |
| 15-01 | Filter null gsis_id from roster | Required for player history lookup |
| 15-01 | FANTASY_POSITIONS includes K | Roster display needs kickers, separate from ML |
| 15-02 | Optional enriched fields for players | Backward compatibility with existing data |
| 15-02 | by_player_id index for players table | O(1) lookups for efficient upserts |
| 15-02 | Three playerHistory indexes | Cover all expected query patterns |
| 15-03 | Height int→string conversion in hook | API returns int, Convex expects string |
| 15-03 | Batch size of 100 for Convex ops | Convex transaction limits, 100 is safe |
| 15-03 | Custom progress bar with Tailwind | Avoids adding Progress UI component |
| 15-04 | Custom tabs with Tailwind | No Tabs UI component in project |
| 15-04 | Cache-first data loading | Check Convex first, fetch API if empty |
| 15-04 | Display last 10 games per season | Balance completeness and UI scrollability |
| 16-01 | Direct recharts install (not shadcn/ui chart) | Avoids potential Tailwind v4 compatibility issues |
| 16-01 | module: esnext in tsconfig.base.json | Required for TypeScript dynamic import support |
| 16.1-01 | Player features computed from 2-season history | Sufficient data for reliable rolling stats |
| 16.1-01 | Merge player stats with position defaults | Ensures all 28 features present for model input |
| 16.1-01 | Neutral values for opponent/team strength | Future: look up actual rankings from cached data |
| 16.1-02 | No code changes for chart fix | Data flow correct; issue is seed data using fake player IDs |
| 16.1-02 | User must sync roster for real player IDs | Admin -> "Sync 2025 Roster" fetches real gsis_ids |
| 16.1-FIX | Explicit hex colors for Recharts | CSS variables use OKLCH which doesn't work with Recharts HSL wrapper |
| 16.1-FIX | AreaChart with gradient over LineChart | Better visual prominence for data trends |
| 17-01 | 28 FEATURE_DISPLAY_NAMES for human-readable explanations | Maps raw feature names to user-friendly display names |
| 17-01 | Contributions sorted by absolute SHAP value | Most impactful features shown first for decision support |
| 17-01 | Natural language summary with 2-3 positive, 1-2 negative factors | Concise explanation without overwhelming users |
| 17-02 | Plain img tag over Next/Image for NFL CDN | Simpler, no domain config needed |
| 17-02 | Top 5 contributions shown by default | Most impactful factors first, expandable for full list |
| 17-02 | Emerald/red for positive/negative SHAP | Consistent with ModelConfidence coloring |
| 17-03 | API client returns null on error | Graceful degradation for explainability panel |
| 17-03 | getPrimaryTarget maps position to stat | QB->passing_yards, RB->rushing_yards, WR/TE->receiving_yards |
| 17-03 | Dashboard 5-4-3 column split on lg | Fantasy hero (5), stats+history (4), explainability (3) |
| 17-03 | playerHeadshotUrl through MatchupData | Simplest data flow - form has selected player data |

**v1.0 Decisions:** See .planning/milestones/v1.0-ROADMAP.md

### Roadmap Evolution

- v1.0 MVP shipped: Foundation through polish, 10 phases (2026-01-15)
- Milestone v1.1 created: Model Confidence, 7 phases (Phase 11-17)
- Phase 16.1 inserted after Phase 16: Re-evaluate models and data visualization (URGENT)
- Milestone v1.2 created: Platform Maturity, 8 phases (Phase 18-25)

### Pending Todos

None

### Blockers/Concerns

None — ready to begin planning.

## Session Continuity

Last session: 2026-01-20
Stopped at: Milestone v1.2 initialization
Resume file: None
Next action: Plan Phase 18 (Performance Fixes & Optimization)
