# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-14)

**Core value:** Accurate stat-level predictions from well-engineered features and properly trained models.
**Current focus:** Phase 6 — Model Evaluation (in progress)

## Current Position

Phase: 6 of 10 (Model Evaluation)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-01-15 — Completed 06-02-PLAN.md

Progress: ██████████████████████████████████████████████████ 53%

## Performance Metrics

**Velocity:**
- Total plans completed: 16
- Average duration: 8.3 min
- Total execution time: 2.08 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3/3 | 15.5 min | 5.2 min |
| 02-data-pipeline | 2/2 | 5 min | 2.5 min |
| 03-data-processing | 3/3 | 10 min | 3.3 min |
| 04-feature-engineering | 3/3 | 6 min | 2.0 min |
| 05-model-development | 4/4 | 79 min | 19.8 min |
| 06-model-evaluation | 2/3 | 9 min | 4.5 min |

**Recent Trend:**
- Last 5 plans: 05-02 (10 min), 05-03 (27 min), 05-04 (35 min), 06-01 (est), 06-02 (9 min)
- Trend: Model evaluation infrastructure with feature importance analysis

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 01-01 | pnpm@9.15.4 as package manager | Latest stable with workspace support |
| 01-01 | Node 20 LTS | Consistent tooling across team |
| 01-01 | ES2022 target in tsconfig | Modern Next.js compatibility |
| 01-02 | hatchling build backend | Modern, fast build system that works well with uv |
| 01-02 | src layout for Python | Standard packaging layout for better testability |
| 01-02 | Python 3.11 minimum | Required for modern typing features |
| 01-03 | radix-mira style preset | Modern, accessible component design |
| 01-03 | JetBrains Mono font | Monospace developer aesthetic |
| 01-03 | Zinc base + emerald accent | Per PROJECT.md theme requirements |
| 02-01 | Return Polars DataFrames natively | nflreadpy returns Polars, avoid conversion overhead |
| 02-01 | SeasonList type alias | Consistent typing for seasons parameter across functions |
| 02-02 | Parquet format for storage | Efficient columnar format, preserves types, fast reads |
| 02-02 | Per-season caching strategy | Independent cache per season enables incremental updates |
| 02-02 | 7-day cache freshness default | Balance fresh data vs network calls |
| 03-01 | Cap yards at 600, TDs at 8 | Conservative outlier boundaries based on NFL records |
| 03-01 | is_dome boolean from roof column | Simplified weather feature logic |
| 03-01 | Default dome temp/wind to 65/5 | Reasonable indoor conditions when data missing |
| 03-02 | Map historical teams to current | OAK->LV, STL->LA, SD->LAC, PHO->ARI |
| 03-02 | Group FB with RB | Fullbacks grouped with running backs for fantasy |
| 03-02 | Create lowercase player_key | Enables case-insensitive player matching |
| 03-03 | temp_normalized = (temp-65)/20 | Center around comfortable temp, scale to ~[-2, 2] |
| 03-03 | wind_normalized = wind/15 | Scale to ~[0, 2] for typical conditions |
| 03-03 | Support both 'team' and 'recent_team' | Flexibility for different data source naming |
| 04-02 | Rank 1 = best defense | Fewest yards allowed = best, helps model understand matchup difficulty |
| 04-02 | opp_strength 0=best, 1=worst | 0=hardest matchup (best defense), 1=easiest matchup |
| 04-02 | Rankings use prior weeks only | Avoid data leakage - week N uses weeks 1 to N-1 |
| 04-03 | 17 ML feature columns total | 8 rolling + 5 opponent + 2 weather + 2 context |
| 04-03 | Removed interceptions from features | Not available in cleaned data |
| 05-01 | shap>=0.50.0 with prerelease deps | Required for Python 3.11 compatibility |
| 05-01 | TimeSeriesSplit n_splits=5 default | Standard temporal CV avoiding leakage |
| 05-01 | Models stored in packages/backend/models/ | Separate from source code, gitignored |
| 05-02 | 6 seasons training data (2019-2024) | Provides ~3,770 QB samples for robust training |
| 05-02 | max_depth=3 optimal for QB models | Low complexity prevents overfitting on sports data |
| 05-02 | Tests allow small negative predictions | XGBoost regression behavior on synthetic data |
| 05-03 | 5 RB targets trained | rushing_yards, rushing_tds, carries, receiving_yards, receptions |
| 05-03 | 50 Optuna trials per target | Balance training time vs optimization quality |
| 05-04 | Separate WR and TE models | Different stat distributions require position-specific models |
| 05-04 | 6 receiver targets total | 3 WR + 3 TE models for receiving_yards, receiving_tds, receptions |
| 06-02 | SHAP TreeExplainer for XGBoost | Optimized explainer for tree-based models |
| 06-02 | Normalized importance values | All importance dicts sum to 1.0 for comparability |
| 06-02 | Optional SHAP analysis | Works in XGBoost-only mode when X_sample not provided |

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-01-15T01:50:31Z
Stopped at: Completed 06-02-PLAN.md - Feature importance analysis
Resume file: None
