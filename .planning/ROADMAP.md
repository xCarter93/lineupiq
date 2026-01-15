# Roadmap: LineupIQ

## Overview

Build a fantasy football prediction app from the ground up: establish a Python/Next.js monorepo, create a robust data pipeline from nflreadpy, engineer high-signal features, train ML models that predict individual player stats, expose predictions via API, store app state in Convex, and deliver a matchup simulation UI. Each phase builds on the previous, prioritizing model accuracy over UI polish.

## Milestones

- ✅ **[v1.0 MVP](milestones/v1.0-ROADMAP.md)** — Phases 1-10 (shipped 2026-01-15)
- 🚧 **v1.1 Model Confidence** — Phases 11-17 (in progress)

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

### 🚧 v1.1 Model Confidence (In Progress)

**Milestone Goal:** Research-first ML improvements, expand to all positions (K/DEF), and build user trust through data-rich visualizations.

#### Phase 11: ML Pipeline Audit & Research

**Goal**: Review current ML practices, research alternatives, document recommendations
**Depends on**: v1.0 MVP complete
**Research**: Likely (explicit research phase)
**Research topics**: Data cleaning best practices, null handling strategies, feature completeness audit, model architecture options (XGBoost vs ensemble vs neural nets), sports analytics papers

Plans:
- [x] 11-01: ML Pipeline Audit (AUDIT-REPORT.md) — completed 2026-01-15

#### Phase 12: ML Pipeline Improvements

**Goal**: Implement research findings (data cleaning, features, model architecture)
**Depends on**: Phase 11
**Research**: Unlikely (implementing findings from research phase)

Plans:
- [ ] 12-01: TBD

#### Phase 13: K/DEF Models

**Goal**: Add kicker and defense position predictions
**Depends on**: Phase 12
**Research**: Likely (new model architecture decisions)
**Research topics**: Kicker modeling (team-based vs individual), defense stat predictions, fantasy scoring for special teams

Plans:
- [ ] 13-01: TBD

#### Phase 14: Complete Fantasy Stats

**Goal**: Add missing stats to scoring calculations and UI display
**Depends on**: Phase 13
**Research**: Unlikely (extending existing patterns)

Plans:
- [ ] 14-01: TBD

#### Phase 15: Full Roster + Historical Data

**Goal**: Import current 2025-26 roster, add 3-year historical display
**Depends on**: Phase 14
**Research**: Unlikely (nflreadpy already in codebase)

Plans:
- [ ] 15-01: TBD

#### Phase 16: UI Data Visualization

**Goal**: Recharts integration for stats and history visualization
**Depends on**: Phase 15
**Research**: Likely (new library integration)
**Research topics**: Recharts API, chart types for sports data, responsive charting patterns

Plans:
- [ ] 16-01: TBD

#### Phase 17: Model Explainability UI

**Goal**: Feature contribution bars and prediction context
**Depends on**: Phase 16
**Research**: Unlikely (implementing known pattern)

Plans:
- [ ] 17-01: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1-10 | v1.0 MVP | 30/30 | ✅ Complete | 2026-01-15 |
| 11. ML Pipeline Audit | v1.1 | 1/1 | ✅ Complete | 2026-01-15 |
| 12. ML Pipeline Improvements | v1.1 | 0/? | Not started | - |
| 13. K/DEF Models | v1.1 | 0/? | Not started | - |
| 14. Complete Fantasy Stats | v1.1 | 0/? | Not started | - |
| 15. Full Roster + Historical | v1.1 | 0/? | Not started | - |
| 16. UI Data Visualization | v1.1 | 0/? | Not started | - |
| 17. Model Explainability UI | v1.1 | 0/? | Not started | - |

---

**Project Status:** v1.1 Model Confidence in progress
