# Roadmap: LineupIQ

## Overview

Build a fantasy football prediction app from the ground up: establish a Python/Next.js monorepo, create a robust data pipeline from nflreadpy, engineer high-signal features, train ML models that predict individual player stats, expose predictions via API, store app state in Convex, and deliver a matchup simulation UI. Each phase builds on the previous, prioritizing model accuracy over UI polish.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Monorepo structure, package setup, dev environment
- [x] **Phase 2: Data Pipeline** - nflreadpy integration, data fetching, raw data storage
- [x] **Phase 3: Data Processing** - Cleaning, transformations, player/team normalization
- [x] **Phase 4: Feature Engineering** - Rolling stats, opponent strength, weather features
- [x] **Phase 5: Model Development** - Training pipeline, model architecture, cross-validation
- [x] **Phase 6: Model Evaluation** - Performance metrics, feature importance, overfitting checks
- [x] **Phase 7: Prediction API** - Python API endpoints, inference pipeline, caching
- [x] **Phase 8: Convex Backend** - Schema, scoring configs, prediction storage
- [x] **Phase 9: Matchup UI** - Player selection, opponent selection, stat display
- [x] **Phase 10: Integration & Polish** - End-to-end flow, error handling, UX refinement

## Phase Details

### Phase 1: Foundation
**Goal**: Establish monorepo with Python ML backend and Next.js frontend, all tooling configured
**Depends on**: Nothing (first phase)
**Research**: Unlikely (standard monorepo setup)
**Plans**: TBD

Plans:
- [x] 01-01: Monorepo structure with pnpm workspaces
- [x] 01-02: Python backend setup with uv
- [x] 01-03: Next.js frontend with Shadcn preset

### Phase 2: Data Pipeline
**Goal**: Fetch and store historical NFL data from nflreadpy (1999-2025)
**Depends on**: Phase 1
**Research**: Likely (nflreadpy API patterns)
**Research topics**: nflreadpy function signatures, data schemas, best practices for large dataset handling
**Plans**: TBD

Plans:
- [x] 02-01: nflreadpy integration and data fetching scripts
- [x] 02-02: Raw data storage structure and caching

### Phase 3: Data Processing
**Goal**: Clean, transform, and normalize raw NFL data for ML consumption
**Depends on**: Phase 2
**Research**: Unlikely (standard pandas/data work)
**Plans**: TBD

Plans:
- [x] 03-01: Data cleaning and validation
- [x] 03-02: Player/team ID normalization
- [x] 03-03: Weekly stat aggregations

### Phase 4: Feature Engineering
**Goal**: Create ML-ready features: rolling stats, opponent strength, weather factors
**Depends on**: Phase 3
**Research**: Unlikely (domain logic, internal patterns)
**Plans**: TBD

Plans:
- [x] 04-01: Rolling window stats (3-week lookback)
- [x] 04-02: Opponent defensive strength metrics
- [x] 04-03: Feature pipeline orchestrator

### Phase 5: Model Development
**Goal**: Build and train ML models for stat prediction (passing/rushing/receiving)
**Depends on**: Phase 4
**Research**: Likely (ML architecture decisions)
**Research topics**: XGBoost vs Random Forest for stat prediction, hyperparameter tuning strategies, handling position-specific models
**Plans**: TBD

Plans:
- [x] 05-01: Training pipeline infrastructure
- [x] 05-02: QB passing stat models
- [x] 05-03: RB rushing stat models
- [x] 05-04: WR/TE receiving stat models

### Phase 6: Model Evaluation
**Goal**: Validate model accuracy, analyze feature importance, prevent overfitting
**Depends on**: Phase 5
**Research**: Unlikely (standard ML metrics)
**Plans**: TBD

Plans:
- [x] 06-01: Model evaluation infrastructure (metrics, holdout validation)
- [x] 06-02: Feature importance analysis
- [x] 06-03: Overfitting detection and correction

### Phase 7: Prediction API
**Goal**: Python API endpoints for inference with prediction caching
**Depends on**: Phase 6
**Research**: Unlikely (standard Python API patterns)
**Plans**: TBD

Plans:
- [x] 07-01: FastAPI setup and model loading
- [x] 07-02: Prediction endpoints by position
- [x] 07-03: Response caching layer

### Phase 8: Convex Backend
**Goal**: Convex schema for scoring configs, cached predictions, app state
**Depends on**: Phase 7
**Research**: Likely (Convex schema patterns)
**Research topics**: Convex schema design, mutation patterns, query optimization for prediction data
**Plans**: TBD

Plans:
- [x] 08-01: Convex schema and setup
- [x] 08-02: Scoring configuration CRUD
- [x] 08-03: Prediction storage and retrieval

### Phase 9: Matchup UI
**Goal**: Frontend for selecting players, opponents, and viewing projected stats
**Depends on**: Phase 8
**Research**: Unlikely (Next.js + Shadcn patterns)
**Plans**: TBD

Plans:
- [x] 09-01: Player selection component
- [x] 09-02: Opponent/matchup selection
- [x] 09-03: Stat projection display

### Phase 10: Integration & Polish
**Goal**: End-to-end flow working, error handling, UX polish
**Depends on**: Phase 9
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [x] 10-01: Homepage and navigation
- [x] 10-02: Error handling and edge cases
- [x] 10-03: UX refinements

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-01-14 |
| 2. Data Pipeline | 2/2 | Complete | 2026-01-14 |
| 3. Data Processing | 3/3 | Complete | 2026-01-15 |
| 4. Feature Engineering | 3/3 | Complete | 2026-01-15 |
| 5. Model Development | 4/4 | Complete | 2026-01-15 |
| 6. Model Evaluation | 3/3 | Complete | 2026-01-15 |
| 7. Prediction API | 3/3 | Complete | 2026-01-15 |
| 8. Convex Backend | 3/3 | Complete | 2026-01-15 |
| 9. Matchup UI | 3/3 | Complete | 2026-01-15 |
| 10. Integration & Polish | 3/3 | Complete | 2026-01-15 |
