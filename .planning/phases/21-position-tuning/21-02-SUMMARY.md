# Phase 21-02: RB Model Training - Summary

**Phase:** 21-position-tuning
**Plan:** 02
**Completed:** 2026-01-22
**Position:** RB (Running Back)

## Objective

Train RB models with expanded 40-feature set from Phase 20, analyze results, and iterate until satisfied. Second highest-impact position after QB.

## What Was Done

### Task 1: Train RB Models
- Trained 7 RB models (carries, rushing_yards, rushing_tds, receptions, receiving_yards, receiving_tds, fumbles_lost)
- Used 40 features (28 baseline + 7 weather + 5 matchup)
- Training data: 2022-2025 (4 seasons, 5948 samples)
- Rolling window: 5 games
- Optuna trials: 30 per model
- Model type: LightGBM
- Training duration: ~45 minutes
- All models saved to `packages/backend/models/RB_*.joblib`

### Task 2: Analyze Results
- Computed R², MAE, and RMSE for all 7 RB models
- Created comprehensive analysis document: `21-02-RB-RESULTS.md`
- Compared RB performance to QB findings from Phase 21-01
- Analyzed position-specific insights and feature impact

## Key Results

**Performance Metrics:**
- Average R²: 0.362 (similar to QB's 0.355)
- Best stat: carries (R² = 0.633, MAE 3.22)
- Worst stat: fumbles_lost (R² = 0.097, MAE 0.07)
- Primary fantasy stats performing well:
  - rushing_yards: R² = 0.514, MAE 18.49
  - receiving_yards: R² = 0.427, MAE 8.91

**RB vs QB Comparison:**
- Overall predictability similar (RB 0.362 vs QB 0.355)
- RB workload metrics more predictable (carries 0.633 vs QB equivalent)
- RB TDs less predictable (rushing_tds 0.291 vs passing_tds 0.414)
- Fumbles equally challenging for both positions

## Important Decisions

| Decision | Rationale |
|----------|-----------|
| Proceed to WR/TE (21-03) | RB performance acceptable; primary fantasy stats performing well; consistent with position-by-position strategy |
| Accept TD model performance | rushing_tds (0.291) and receiving_tds (0.209) reasonable given low-frequency nature; significant improvement requires red zone features (future phase) |
| Document RB-specific insights | Workload predictability, game script impact, TD variance differences vs QB |

## Lessons Learned

1. **Workload is more predictable than production**: carries (R² = 0.633) significantly outperforms yards and TDs, suggesting game script features (Vegas lines) are working well

2. **RB receiving role matters**: receiving_yards (0.427) and receptions (0.361) show pass-catching RBs are moderately predictable, but variance is higher than rushing stats

3. **TDs remain challenging**: Both rushing_tds (0.291) and receiving_tds (0.209) confirm low-frequency events are hard to predict without red zone-specific features

4. **Feature set works across positions**: Similar average R² for QB (0.355) and RB (0.362) suggests 40-feature set is universally applicable

## Files Modified

- `packages/backend/models/RB_*.joblib` (7 models, gitignored)
- `packages/backend/compute_rb_metrics.py` (created)
- `packages/backend/rb_metrics.txt` (created)
- `.planning/phases/21-position-tuning/21-02-RB-RESULTS.md` (created)
- `.planning/phases/21-position-tuning/21-02-SUMMARY.md` (this file)

## Commits

1. `d1e7a69`: feat(21-02): train RB models with 40-feature set
2. `33dbb84`: docs(21-02): analyze RB model performance and document findings

## Next Steps

1. **Immediate:** Proceed to Plan 21-03 (train WR/TE models with 40-feature set)
2. **After all positions:** Holistic feature importance analysis across QB, RB, WR, TE, K, DEF
3. **Future optimization:** Position-specific feature selection, red zone features for TD prediction

## Blockers

None

## Notes

- Training completed without errors or convergence issues
- All 7 RB models have recent timestamps (2026-01-22)
- No API rate limit issues during training (Odds API caching worked well)
- Feature pipeline correctly builds 40 features for RB position
- Sample size (5948) provides strong statistical foundation for 40-feature models

---

**Plan 21-02 Complete** ✓
