# Plan 19-03 Summary: Ensemble Benchmarking

**Plan:** 19-03 (Ensemble Strategy Benchmarking)
**Phase:** 19 (Ensemble Models & XGBoost Parity)
**Date:** 2026-01-20
**Status:** Complete ✓

## Overview

Benchmarked ensemble strategies against single models on 2024 holdout data to make evidence-based decision about ensemble adoption. Tested 5 strategies (lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking) across 21 skill position stats.

## Tasks Completed

### Task 1: Add benchmark_ensemble_strategies function
- ✓ Created comprehensive benchmark function in `ensemble.py`
- ✓ Evaluates 5 strategies: lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking
- ✓ Grid search (21 points, 0-1 in 0.05 steps) for optimal weighted averaging
- ✓ Computes MAE and R² for all strategies
- ✓ Returns correlation metric for model diversity assessment
- ✓ Identifies best strategy by lowest MAE

**Commit:** f13a9fb

### Task 2: Run pilot benchmark on QB passing_yards
- ✓ Validated benchmark methodology on single stat
- ✓ Confirmed all 5 strategies execute correctly
- ✓ Discovered LightGBM significantly outperforms XGBoost (MAE 4.73 vs 27.78)
- ✓ High correlation (0.950) indicates low model diversity
- ✓ Ensembles perform worse than best single model
- ✓ Fixed model loading to use correct naming convention

**Commit:** 408146e

### Task 3: Benchmark all skill position stats
- ✓ Ran benchmark on all 21 skill position stats (6 QB + 7 RB + 4 WR + 4 TE)
- ✓ Created comprehensive `BENCHMARK_RESULTS.md` with full analysis
- ✓ Generated summary table, full results, and data-driven recommendation
- ✓ Analyzed model diversity, ensemble vs single performance
- ✓ Provided clear recommendation based on empirical evidence

**Commit:** 4b06225

## Key Findings

### Model Performance
- **LightGBM dominates:** 17/21 stats (81.0%)
- **XGBoost wins:** 3/21 stats (14.3%)
- **Ensemble wins:** 1/21 stats (4.8% - only TE fumbles_lost with 6.2% improvement)

### Model Diversity
- **Average correlation:** 0.890 (low diversity)
- **High diversity (<0.7):** 3/21 stats (QB fumbles_lost, WR fumbles_lost, TE fumbles_lost)
- **Moderate diversity (0.7-0.9):** 3/21 stats
- **Low diversity (>=0.9):** 15/21 stats

### Ensemble Performance
- **Ensembles beat single models:** 1/21 stats (4.8%)
- **Single models win:** 20/21 stats (95.2%)
- **Worst ensemble degradations:**
  - QB passing_yards: 792.8% worse
  - RB receiving_yards: 154.5% worse
  - TE receiving_yards: 134.5% worse
  - QB fumbles_lost: 128.8% worse
  - WR receiving_yards: 90.1% worse

## Decision

**Recommendation: Keep single models**

Evidence-based rationale:
1. Ensembles only improve on 1 out of 21 stats (4.8%)
2. High correlation (0.890) indicates insufficient model diversity
3. Single models already performing well (R² mostly >0.6)
4. Ensemble overhead (training time, complexity, inference latency) not justified
5. LightGBM and XGBoost predictions too similar to benefit from averaging

### Path Forward
- Continue using single models (LightGBM as default per Phase 13)
- Do not integrate ensemble infrastructure into production API
- Consider revisiting ensembles if:
  - Add more diverse estimators (CatBoost, RandomForest, Neural Networks)
  - Improve base models to be more complementary
  - Find specific stats where diversity is higher

## Technical Implementation

### Files Modified
- `packages/backend/src/lineupiq/models/ensemble.py` - Added `benchmark_ensemble_strategies()` function
- `packages/backend/scripts/benchmark_pilot.py` - Created pilot benchmark script
- `packages/backend/scripts/benchmark_all.py` - Created comprehensive benchmark script
- `.planning/phases/19-ensemble-models/BENCHMARK_RESULTS.md` - Full benchmark results and analysis

### Benchmark Methodology
- **Training Data:** 2022-2023 seasons
- **Holdout Data:** 2024 season (strict holdout, never seen during training)
- **Positions:** QB, RB, WR, TE (21 total stats)
- **Strategies:**
  1. `lgbm_solo`: LightGBM model alone
  2. `xgb_solo`: XGBoost model alone
  3. `voting_simple`: Simple averaging (equal weights)
  4. `voting_weighted`: Weighted averaging (optimal weights via grid search)
  5. `stacking`: Ridge meta-learner with 5-fold CV
- **Metrics:** MAE (primary), R² (secondary)
- **Selection:** Best strategy chosen by lowest MAE on holdout

### Performance
- Total execution time: ~34 minutes for 21 stats
- Average per stat: ~1.6 minutes
- Grid search: 21 weight combinations per stat
- Stacking: 5-fold CV per stat

## Lessons Learned

1. **Ensembles are not always better** - This benchmark validates the research warning that ensembles require model diversity to be effective
2. **Correlation is predictive** - High correlation (>0.9) accurately predicted poor ensemble performance
3. **LightGBM vs XGBoost gap** - Significant performance gap suggests XGBoost hyperparameters may need re-tuning or different feature engineering
4. **Evidence-based decisions** - Running comprehensive benchmarks before integration prevents premature optimization
5. **Fumbles_lost anomaly** - Low R² for fumbles_lost (<0.8) suggests these rare events are harder to predict regardless of model choice

## Impact on Roadmap

- Phase 19 ensemble investigation complete - **do not proceed with Phase 19-04 (ensemble API integration)**
- Existing LightGBM models remain as production default (Phase 13 decision validated)
- XGBoost models serve as comparison baseline but not primary predictors
- Future work: Investigate why XGBoost underperforms, consider different architectures or feature sets

## Verification

All success criteria met:
- ✓ `benchmark_ensemble_strategies` function exists and works correctly
- ✓ Pilot run on QB passing_yards validated methodology
- ✓ BENCHMARK_RESULTS.md has results for all 21 skill position stats
- ✓ Clear, data-driven recommendation provided (keep single models)

## Next Steps

1. Mark Phase 19 complete (ensemble investigation done)
2. Continue with Phase 20+ per roadmap (likely UI/UX enhancements or other platform features)
3. Document ensemble decision in PROJECT.md decisions table
4. Consider XGBoost performance investigation as future optional work

---

**Phase 19 Status:** Investigation complete, recommendation implemented
**Ensemble Adoption:** Not recommended based on empirical evidence
**Production Strategy:** Continue with LightGBM single models (Phase 13 decision)
