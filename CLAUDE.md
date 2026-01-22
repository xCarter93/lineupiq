# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LineupIQ is a fantasy football prediction web app that trains ML models on historical NFL data to predict individual player statistics (passing yards, rushing yards, TDs, etc.) which feed into configurable fantasy point calculations.

## Monorepo Structure

This is a pnpm monorepo with two packages:
- `packages/frontend` - Next.js 16 TypeScript app with Shadcn UI (Radix, Tailwind CSS 4)
- `packages/backend` - Python ML backend using uv for package management

## Commands

### Root Level (pnpm)
```bash
pnpm dev          # Run frontend dev server
pnpm build        # Build frontend
pnpm lint         # Lint frontend
pnpm dev:all      # Run all packages in dev mode
```

### Frontend (packages/frontend)
```bash
pnpm dev          # Start Next.js dev server at localhost:3000
pnpm build        # Production build
pnpm lint         # ESLint
```

### Backend (packages/backend)
```bash
uv sync           # Install dependencies
uv sync --dev     # Install with dev dependencies
uv run pytest     # Run all tests
uv run pytest tests/test_qb_models.py  # Run single test file
uv run pytest tests/test_qb_models.py::test_function_name -v  # Run single test
uv run mypy src/  # Type checking
uv run ruff check src/  # Linting
```

### Model Training

**Automated (Production):**
- GitHub Actions runs bi-weekly training automatically during NFL season
- See `.github/workflows/README.md` for schedule and configuration

**Manual (Development):**
```bash
# Train all models (default: 2022-2025 data, 30 trials, all positions)
cd packages/backend
uv run python scripts/train_all.py

# Quick training for testing (10 trials)
uv run python scripts/train_all.py --quick

# Train specific positions
uv run python scripts/train_all.py --positions QB RB WR TE

# Custom seasons and trials
uv run python scripts/train_all.py --seasons 2020 2021 2022 2023 2024 2025 --trials 50
```

**See also:** `packages/backend/TRAINING.md`, `packages/backend/SEASON_STRATEGY.md`, `packages/backend/FEATURE_SCHEMA_SYNC.md`

## Backend Architecture

The Python ML backend (`packages/backend/src/lineupiq/`) has three main modules:

### data/
Data pipeline from nflreadpy to processed training data:
- `fetchers.py` - nflreadpy API wrappers for fetching NFL data
- `storage.py` - Raw data caching and storage
- `cleaning.py` - Data validation and cleaning
- `normalization.py` - Player/team ID normalization
- `processing.py` - Weekly stat aggregations

### features/
Feature engineering for ML models:
- `rolling_stats.py` - 5-game rolling window calculations (mean, std, CV)
- `opponent_features.py` - Opponent defensive strength metrics
- `pipeline.py` - Feature pipeline orchestrator

### models/
ML training and inference:
- `training.py` - Base training pipeline infrastructure
- `qb.py` - QB passing/rushing stat models (6 targets)
- `rb.py` - RB rushing/receiving stat models (7 targets)
- `receiver.py` - WR/TE receiving stat models (4 targets each)
- `kicker.py` - K field goal models (5 targets)
- `defense.py` - DEF team defense models (5 targets)
- `persistence.py` - Model save/load with joblib
- `evaluation.py` - Performance metrics, holdout validation
- `importance.py` - SHAP-based feature importance
- `diagnostics.py` - Overfitting detection

Trained models are stored in `packages/backend/models/` as `.joblib` files (32 total models).

## Key Technical Decisions

- **Predict individual stats, not fantasy points** - More accurate, allows custom scoring
- **nflreadpy for NFL data** - nfl_data_py is deprecated
- **LightGBM with Optuna** - Fast training (7x faster than XGBoost), good performance
- **Single models (not ensembles)** - Simpler architecture, ensembles showed minimal improvement
- **5-game rolling window** - Captures recent trends without over-weighting distant games
- **2022-2025 training data** - 4 recent years, excludes COVID-era noise (2020-2021)
- **All fantasy positions** - QB, RB, WR, TE, K, DEF (32 models total)
- **⚠️ Feature schema synchronization** - When adding/removing features, update 4 files (backend prediction schema, backend explainability schema, backend roster endpoint, frontend TypeScript). See `packages/backend/FEATURE_SCHEMA_SYNC.md` for details.

## Project Planning

This project uses the GSD (Get Shit Done) workflow system. Planning docs are in `.planning/`:
- `PROJECT.md` - Project context, requirements, constraints
- `ROADMAP.md` - 10-phase development roadmap
- `STATE.md` - Current progress state
- `phases/` - Detailed plans for each phase

GSD commands are available as `/gsd:*` skills.
