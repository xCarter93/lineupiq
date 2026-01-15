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
- `rolling_stats.py` - 3-week lookback window calculations
- `opponent_features.py` - Opponent defensive strength metrics
- `pipeline.py` - Feature pipeline orchestrator

### models/
ML training and inference:
- `training.py` - Base training pipeline infrastructure
- `qb.py` - QB passing stat models (yards, TDs)
- `rb.py` - RB rushing/receiving stat models
- `receiver.py` - WR/TE receiving stat models
- `persistence.py` - Model save/load with joblib
- `evaluation.py` - Performance metrics, holdout validation
- `importance.py` - SHAP-based feature importance
- `diagnostics.py` - Overfitting detection

Trained models are stored in `packages/backend/models/` as `.joblib` files.

## Key Technical Decisions

- **Predict individual stats, not fantasy points** - More accurate, allows custom scoring
- **nflreadpy for NFL data** - nfl_data_py is deprecated
- **XGBoost with Optuna** - Hyperparameter tuning for each position model
- **Minimal features first** - Avoid overfitting from previous attempts
- **Skill positions only (QB/RB/WR/TE)** - K/DEF deferred to later

## Project Planning

This project uses the GSD (Get Shit Done) workflow system. Planning docs are in `.planning/`:
- `PROJECT.md` - Project context, requirements, constraints
- `ROADMAP.md` - 10-phase development roadmap
- `STATE.md` - Current progress state
- `phases/` - Detailed plans for each phase

GSD commands are available as `/gsd:*` skills.
