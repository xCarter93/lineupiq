# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-15)

**Core value:** Accurate stat-level predictions from well-engineered features and properly trained models.
**Current focus:** v1.2 Platform Maturity — performance, ensemble models, and enhanced UI

## Current Position

Phase: 20 of 25 (Performance Optimization)
Plan: Ready to plan
Status: Ready
Last activity: 2026-01-20 - Phase 19.2.1 complete (player-specific prediction bug fixed)

Progress: ███░░░░░░░ 20%

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
| 12 | Accuracy % formula: 100*(1-MAE/mean) | ~~Intuitive 0-100% scale for user trust~~ → SUPERSEDED by 19.2-02 |
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
| 18-01 | react-window for player dropdown virtualization | Industry standard, 6KB bundle, renders only visible items |
| 18-01 | 48px item height for player dropdown | Matches existing avatar design, renders ~6 items in 300px dropdown |
| 18-01 | Filter before virtualization | Preserves existing useMemo search logic, clean separation of concerns |
| 18-02 | next/dynamic for PlayerHistory and ExplainabilityPanel | Largest components (~150KB combined), only needed after prediction |
| 18-02 | ssr: false for PlayerHistory (chart component) | Recharts uses browser APIs, prevents hydration mismatches |
| 18-02 | ssr: true for ExplainabilityPanel | No browser-only APIs, can SSR safely |
| 18-02 | Loading skeletons match component heights | Prevents layout shift when code-split chunks load |
| 18-03 | Verification over new features for Task 1 | All loading states already implemented; focused on confirming smooth UX |
| 18-03 | Development-only Web Vitals logging | Simple implementation; production analytics deferred to later |
| 18-03 | ANALYZE=true environment flag for bundle analyzer | Only runs when explicitly needed, doesn't affect normal builds |
| 19-01 | 30 Optuna trials for XGBoost models | Consistent with Phase 13-01 LightGBM decision |
| 19-01 | _xgb.joblib suffix for XGBoost models | Clear distinction from LightGBM models |
| 19-01 | Mirror LightGBM training function patterns | XGBoost functions follow same structure with model_type parameter |
| 19-02 | VotingRegressor for simple/weighted averaging | Standard sklearn approach for ensemble averaging |
| 19-02 | Ridge(alpha=1.0) for stacking meta-learner | Prevents overfitting on correlated base predictions |
| 19-02 | cv=5 default for stacking | Generates out-of-fold predictions to avoid data leakage |
| 19-02 | passthrough=False in stacking | Use only base predictions, not original features |
| 19-02 | Ensemble naming: {position}_{target}_{ensemble_type}.joblib | Consistent with existing persistence patterns |
| 19-03 | Do NOT adopt ensemble models | Benchmarked 21 stats: ensembles only beat single models on 1 stat (4.8%) |
| 19-03 | High correlation (0.890) indicates insufficient diversity | LightGBM/XGBoost predictions too similar to benefit from averaging |
| 19-03 | Keep LightGBM as production default | Wins 17/21 stats (81%), already performing well without ensemble overhead |
| 19-04 | keep-single integration strategy | API continues using LightGBM/XGBoost single models, no ensemble complexity |
| 19-04 | Document architectural decisions in code | Added NOTE in models_loader.py explaining ensemble rejection with benchmark reference |
| 19.1-01 | Keep single models with 2022-2025 training data | Avoid COVID-era noise (2020-2021) while maximizing recency for 2026 predictions |
| 19.1-01 | Reject ensemble models despite 2025 benchmark | 2024 benchmark more reliable; matches production setup; simpler architecture |
| 19.1-01 | 4-year training window (2022-2025) | Balance between volume and recency; includes most recent 2025 season data |
| 19.1-02 | Expand rolling window from 3 to 5 games | Captures recent trends better; TD prediction focus; includes shift(1) for leakage prevention |
| 19.1-02 | Add shift(1) to all rolling stats | Prevents data leakage by excluding current game from rolling averages |
| 19.1-03 | Adopt 5-game rolling window as standard | Benchmarked 21 stats with avg R² 0.332; TD models avg R² 0.261; acceptable performance |
| 19.1-03 | Rolling features consistently top predictors | SHAP analysis shows rolling stats appear in top 5 for majority of models |
| 19.2-01 | Replace accuracy_pct with R²-based formula | Current formula 100*(1-MAE/mean) is scale-dependent; R²-based (100*R²) correlates with model quality |
| 19.2-01 | Confidence tiers based on R² thresholds | High (R²>0.5), Medium (R²0.3-0.5), Low (R²<0.3); fixes 10 models showing 0% accuracy |
| 19.2-02 | Implemented accuracy_pct = max(0, min(100, 100*R²)) | Fixes scale-dependent accuracy; clamped to [0,100] for negative R² edge cases |
| 19.2-02 | Simplified confidence_rating to R²-only | Removed accuracy_pct parameter; single metric aligns with ML standards |
| 19.2-03 | Updated ModelConfidence tooltip to explain R²-based accuracy | Tooltip shows "variance explained by the model" to help users understand R²-based metric |
| 19.2.1-01 | Root cause: window parameter mismatch (3 vs 5) | Models trained with roll5 features, API computes roll3; dict.update() doesn't overwrite → all players use defaults |
| 19.2.1-02 | Fixed window parameter in roster.py (3→5) | Updated _compute_rolling_stats_for_player and _compute_volatility_for_player to window=5; enables player-specific predictions |

**v1.0 Decisions:** See .planning/milestones/v1.0-ROADMAP.md

### Roadmap Evolution

- v1.0 MVP shipped: Foundation through polish, 10 phases (2026-01-15)
- Milestone v1.1 created: Model Confidence, 7 phases (Phase 11-17)
- Phase 16.1 inserted after Phase 16: Re-evaluate models and data visualization (URGENT)
- Milestone v1.2 created: Platform Maturity, 8 phases (Phase 18-25)
- Phase 19.1 inserted after Phase 19: Re-evaluate recent performance metrics (URGENT)
- Phase 19.2 inserted after Phase 19.1: Improve model confidence & accuracy - address 49% accuracy issue (URGENT)
- Phase 19.2.1 inserted after Phase 19.2: Different players showing same predicted stats - fix player-specific feature computation (URGENT)

### Pending Todos

None

### Blockers/Concerns

None

## Session Continuity

Last session: 2026-01-20
Stopped at: Phase 19.2.1 complete (player-specific prediction bug fixed)
Resume file: None
Next action: Ready for Phase 20 (Performance Optimization)
