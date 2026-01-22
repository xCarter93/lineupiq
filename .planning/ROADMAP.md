# Roadmap: LineupIQ

## Overview

Build a fantasy football prediction app from the ground up: establish a Python/Next.js monorepo, create a robust data pipeline from nflreadpy, engineer high-signal features, train ML models that predict individual player stats, expose predictions via API, store app state in Convex, and deliver a matchup simulation UI. Each phase builds on the previous, prioritizing model accuracy over UI polish.

## Milestones

- ✅ **[v1.0 MVP](milestones/v1.0-ROADMAP.md)** — Phases 1-10 (shipped 2026-01-15)
- ✅ **v1.1 Model Confidence** — Phases 11-17 (shipped 2026-01-19)
- 🚧 **v1.2 Platform Maturity** — Phases 18-25 (in progress)

## Completed Milestones

<details>
<summary>✅ v1.0 MVP (Phases 1-10) — SHIPPED 2026-01-15</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-01-14
- [x] Phase 2: Data Pipeline (2/2 plans) — completed 2026-01-14
- [x] Phase 3: Data Processing (3/3 plans) — completed 2026-01-15
- [x] Phase 4: Feature Engineering (3/3 plans) — completed 2026-01-15
- [x] Phase 5: Model Development (4/4 plans) — completed 2026-01-15
- [x] Phase 6: Model Evaluation (3/3 plans) — completed 2026-01-15
- [x] Phase 7: Prediction API (3/3 plans) — completed 2026-01-15
- [x] Phase 8: Convex Backend (3/3 plans) — completed 2026-01-15
- [x] Phase 9: Matchup UI (3/3 plans) — completed 2026-01-15
- [x] Phase 10: Integration & Polish (3/3 plans) — completed 2026-01-15

**Full details:** [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 Model Confidence (Phases 11-17) — SHIPPED 2026-01-19</summary>

- [x] Phase 11: ML Pipeline Audit (1/1 plan) — completed 2026-01-15
- [x] Phase 12: ML Pipeline Improvements (5/5 plans) — completed 2026-01-15
- [x] Phase 13: K/DEF + Training Improvements (8/8 plans) — completed 2026-01-15
- [x] Phase 14: Complete Fantasy Stats (4/4 plans) — completed 2026-01-15
- [x] Phase 15: Full Roster + Historical (4/4 plans) — completed 2026-01-16
- [x] Phase 16: UI Data Visualization (1/1 plan) — completed 2026-01-15
- [x] Phase 16.1: Re-evaluate Models & Viz (3/3 plans) — completed 2026-01-20
- [x] Phase 17: Model Explainability UI (4/4 plans) — completed 2026-01-19

**Full details:** [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

### 🚧 v1.2 Platform Maturity (In Progress)

**Milestone Goal:** Mature the platform with performance optimizations, ensemble models, advanced features, and enhanced UI capabilities for production readiness.

#### Phase 18: Performance Fixes & Optimization

**Goal**: Fix player selection lag and optimize frontend/API performance through code splitting, lazy loading, and smarter caching
**Depends on**: Previous milestone complete
**Research**: Complete (18-RESEARCH.md)
**Plans**: 3/3 complete

Plans:
- [x] 18-01: Virtualize player dropdown with react-window — completed 2026-01-20
- [x] 18-02: Lazy load heavy components with next/dynamic — completed 2026-01-20
- [x] 18-03: Loading UX polish + Web Vitals monitoring — completed 2026-01-20

#### Phase 19: Ensemble Models & XGBoost Parity

**Goal**: Combine LightGBM + XGBoost models using stacking/voting ensembles for improved prediction accuracy
**Depends on**: Phase 18
**Research**: Complete (19-RESEARCH.md)
**Plans**: 4/4 complete

Plans:
- [x] 19-01: Train XGBoost models for all positions — completed 2026-01-20
- [x] 19-02: Implement ensemble strategies (voting, stacking) — completed 2026-01-20
- [x] 19-03: Benchmark ensembles vs single models on 2024 holdout — completed 2026-01-20
- [x] 19-04: Integration decision (keep-single models) — completed 2026-01-20

**Outcome**: Ensembles NOT adopted. Benchmarking showed single models win 20/21 stats (95.2%). LightGBM remains production default.

#### Phase 19.1: Re-evaluate Recent Performance Metrics (INSERTED)

**Goal**: Improve model accuracy by fixing data leakage, expanding training data window to 2022-2025, and increasing rolling window from 3 to 5 games
**Depends on**: Phase 19
**Research**: Complete (19.1-CONTEXT.md)
**Plans**: 3/3 complete

Plans:
- [x] 19.1-01: Expand training data window from 2-year to 4-year (2022-2025) and re-benchmark ensembles — completed 2026-01-20
- [x] 19.1-02: Expand rolling window from 3 to 5 games with shift(1) data leakage fix — completed 2026-01-20
- [x] 19.1-03: Validate 5-game rolling window improvements with comprehensive benchmarking — completed 2026-01-20

**Outcome**: 5-game rolling window adopted as new standard. Data leakage fixed with shift(1). Models trained on 2022-2025 data excluding COVID-era noise.

#### Phase 19.2: Improve Model Confidence & Accuracy (INSERTED)

**Goal**: Fix scale-dependent accuracy formula (100*(1-MAE/mean)) with R²-based calculation to properly reflect model quality
**Depends on**: Phase 19.1
**Research**: Complete (19.2-CONTEXT.md - accuracy audit)
**Plans**: 3/3 complete

Plans:
- [x] 19.2-01: Audit current accuracy formula and evaluate alternatives (R²-based, MAPE, skill score) — completed 2026-01-20
- [x] 19.2-02: Implement R²-based accuracy calculation and simplified confidence tiers — completed 2026-01-20
- [x] 19.2-03: Update UI to reflect R²-based accuracy and verify display — completed 2026-01-20

**Outcome**: R²-based accuracy (100*R²) replaces MAE/mean formula. Confidence tiers simplified to R²-only thresholds (High: >0.5, Medium: 0.3-0.5, Low: <0.3). Fixes "49% accuracy for R² 0.545" problem. UI tooltip explains "variance explained by the model".

#### Phase 19.2.1: Different Players Showing Same Stats (INSERTED)

**Goal**: Fix bug where different players in the same position show identical predicted stats instead of player-specific predictions
**Depends on**: Phase 19.2
**Research**: Complete (19.2.1-CONTEXT.md - window parameter mismatch investigation)
**Plans**: 2/2 complete

Plans:
- [x] 19.2.1-01: Diagnose window parameter mismatch in player feature computation — completed 2026-01-20
- [x] 19.2.1-02: Fix window parameter (3→5) in roster.py and verify player-specific predictions — completed 2026-01-20

**Outcome**: Fixed window parameter mismatch. Models trained with window=5 (Phase 19.1-02) but API computed window=3 features, causing key mismatch (roll3 vs roll5). When dict.update() merged player features with defaults, roll3 keys didn't overwrite roll5 defaults → all players received identical position-typical predictions. Fix: Updated _compute_rolling_stats_for_player and _compute_volatility_for_player to window=5. Different players now produce different predictions based on individual performance history.

#### Phase 20: Advanced Features

**Goal**: Expand feature engineering with weather data, injury reports, and matchup-specific signals
**Depends on**: Phase 19.2.1
**Research**: Complete (20-RESEARCH.md)
**Plans**: 3/3 complete

Plans:
- [x] 20-01: Enhanced Weather Features (Visual Crossing API) — completed 2026-01-21
- [x] 20-02: Injury Status Features (nflreadpy injury reports) — completed 2026-01-21
- [x] 20-03: Vegas Lines & Matchup Features (The Odds API) — completed 2026-01-21

**Outcome**: Added 16 new ML features (7 weather, 2 injury, 5 matchup). Visual Crossing and The Odds API integrated with caching/graceful degradation. Models ready for retraining with expanded feature set.

#### Phase 21: Position-Specific Tuning

**Goal**: Deep hyperparameter optimization for each position (QB, RB, WR, TE, K, DEF) with position-specific feature sets
**Depends on**: Phase 20
**Research**: Unlikely (extends existing Optuna tuning patterns)
**Plans**: TBD

Plans:
- [ ] 21-01: TBD

#### Phase 22: Multi-Player Comparison UI

**Goal**: Build side-by-side player comparison interface for lineup decision support
**Depends on**: Phase 21
**Research**: Unlikely (internal UI patterns)
**Plans**: TBD

Plans:
- [ ] 22-01: TBD

#### Phase 23: Season-Long View UI

**Goal**: Display weekly projections across full season with playoff scheduling support
**Depends on**: Phase 22
**Research**: Unlikely (data visualization with existing Recharts)
**Plans**: TBD

Plans:
- [ ] 23-01: TBD

#### Phase 24: Real-Time Data Updates

**Goal**: Sync with latest NFL data for injuries and roster changes in real-time
**Depends on**: Phase 23
**Research**: Likely (new integration with real-time data sources)
**Research topics**: NFL injury/roster APIs, polling vs webhooks, cache invalidation strategies
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

#### Phase 25: Advanced Stats Pipeline

**Goal**: Add target share, snap counts, and red zone usage metrics to feature pipeline
**Depends on**: Phase 24
**Research**: Likely (new data sources for advanced stats)
**Research topics**: Target share data availability, snap count APIs, red zone metrics sources
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-01-14 |
| 2. Data Pipeline | v1.0 | 2/2 | Complete | 2026-01-14 |
| 3. Data Processing | v1.0 | 3/3 | Complete | 2026-01-15 |
| 4. Feature Engineering | v1.0 | 3/3 | Complete | 2026-01-15 |
| 5. Model Development | v1.0 | 4/4 | Complete | 2026-01-15 |
| 6. Model Evaluation | v1.0 | 3/3 | Complete | 2026-01-15 |
| 7. Prediction API | v1.0 | 3/3 | Complete | 2026-01-15 |
| 8. Convex Backend | v1.0 | 3/3 | Complete | 2026-01-15 |
| 9. Matchup UI | v1.0 | 3/3 | Complete | 2026-01-15 |
| 10. Integration & Polish | v1.0 | 3/3 | Complete | 2026-01-15 |
| 11. ML Pipeline Audit | v1.1 | 1/1 | Complete | 2026-01-15 |
| 12. ML Pipeline Improvements | v1.1 | 5/5 | Complete | 2026-01-15 |
| 13. K/DEF + Training | v1.1 | 8/8 | Complete | 2026-01-15 |
| 14. Complete Fantasy Stats | v1.1 | 4/4 | Complete | 2026-01-15 |
| 15. Full Roster + Historical | v1.1 | 4/4 | Complete | 2026-01-16 |
| 16. UI Data Visualization | v1.1 | 1/1 | Complete | 2026-01-15 |
| 16.1. Re-evaluate Models & Viz | v1.1 | 3/3 | Complete | 2026-01-20 |
| 17. Model Explainability UI | v1.1 | 4/4 | Complete | 2026-01-19 |
| 18. Performance Fixes | v1.2 | 3/3 | Complete | 2026-01-20 |
| 19. Ensemble Models | v1.2 | 4/4 | Complete | 2026-01-20 |
| 19.1. Re-evaluate Performance | v1.2 | 3/3 | Complete | 2026-01-20 |
| 19.2. Improve Model Confidence | v1.2 | 3/3 | Complete | 2026-01-20 |
| 19.2.1. Different Players Same Stats | v1.2 | 2/2 | Complete | 2026-01-20 |
| 20. Advanced Features | v1.2 | 3/3 | Complete | 2026-01-21 |
| 21. Position Tuning | v1.2 | 0/? | Not started | - |
| 22. Multi-Player Comparison | v1.2 | 0/? | Not started | - |
| 23. Season-Long View | v1.2 | 0/? | Not started | - |
| 24. Real-Time Updates | v1.2 | 0/? | Not started | - |
| 25. Advanced Stats | v1.2 | 0/? | Not started | - |

---

**Project Status:** v1.2 Platform Maturity — Phase 20 complete, Phase 21 (Position-Specific Tuning) ready to plan
