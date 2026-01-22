# Phase 20 Pre-Tuning Model Archive

**Date:** 2026-01-21
**Purpose:** Preserve pre-Phase 21 models for rollback capability

## Archived Models

This directory contains 21 models trained with the 28-feature set (before Phase 20's weather/injury/matchup additions).

**Training configuration:**
- Feature count: 28
- Training data: 2022-2025 (4 seasons)
- Rolling window: 5 games
- Optuna trials: 30 per model
- Model type: LightGBM

**Models archived:**
- QB: 6 models (passing_yards, passing_tds, interceptions, rushing_yards, rushing_tds, fumbles_lost)
- RB: 7 models (carries, rushing_yards, rushing_tds, targets, receptions, receiving_yards, fumbles_lost)
- WR: 4 models (targets, receptions, receiving_yards, receiving_tds)
- TE: 4 models (targets, receptions, receiving_yards, receiving_tds)

Total: 21 .joblib files

## Rollback

If Phase 21 retraining shows degraded performance with the expanded 42-feature set, restore these models with:

```bash
cp models_archive/phase20_pre_tuning/*.joblib models/
```

## Next Steps

Phase 21-01 will retrain all 32 models (adding K and DEF positions) with the expanded feature set and establish baseline performance metrics.
