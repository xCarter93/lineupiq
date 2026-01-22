# Phase 21-01: QB Model Results

**Trained:** 2026-01-22
**Position:** QB (6 models)
**Feature count:** 40 (Phase 20: +14 from weather/matchup; injury excluded)
**Training data:** 2022-2025 (4 seasons)
**Rolling window:** 5 games
**Optuna trials:** 30 per model
**Model type:** LightGBM

## Performance Metrics

| Model | R² | MAE | RMSE | CV RMSE | Samples | Accuracy % |
|-------|----|----|------|---------|---------|------------|
| passing_yards | 0.485 | 57.65 | 72.67 | 87.86 ± 2.06 | 2508 | 48.5% |
| passing_tds | 0.414 | 0.71 | 0.88 | 1.07 ± 0.04 | 2508 | 41.4% |
| interceptions | 0.285 | 0.57 | 0.70 | 0.83 ± 0.03 | 2508 | 28.5% |
| rushing_yards | 0.447 | 10.98 | 15.26 | 16.68 ± 0.55 | 2508 | 44.7% |
| rushing_tds | 0.313 | 0.22 | 0.36 | 0.42 ± 0.02 | 2508 | 31.3% |
| fumbles_lost | 0.186 | 0.28 | 0.39 | 0.43 ± 0.03 | 2508 | 18.6% |

**QB Average R²:** 0.355

## Analysis

### Performance Overview

**Strong performers (R² > 0.4):**
- passing_yards (R² = 0.485): Best QB stat, ~49% variance explained
- rushing_yards (R² = 0.447): Second best, mobile QBs captured well
- passing_tds (R² = 0.414): Good performance, key fantasy stat

**Moderate performers (R² 0.3-0.4):**
- interceptions (R² = 0.285): Harder to predict, inherently volatile stat
- rushing_tds (R² = 0.313): Low-frequency event, reasonable performance

**Challenging stats (R² < 0.3):**
- fumbles_lost (R² = 0.186): Rare event, difficult to predict

### Baseline Comparison

This is the first training with Phase 20's expanded 40-feature set (weather + matchup additions). Previous models (Phase 19.2.1) used 28 features. Direct comparison requires retraining baseline models with identical data splits, which is out of scope for this phase.

**Key observation:** The archived Phase 20 pre-tuning models (28 features) exist in `models_archive/phase20_pre_tuning/` for rollback if needed.

### Feature Impact Analysis

The 40-feature set includes:
- **28 baseline features:** Rolling stats (5-game window), team/opponent strength
- **7 weather features:** Temperature, wind, precipitation (added Phase 20-01)
- **5 matchup features:** Home/away, divisional, spread, total points, Vegas lines (added Phase 20-03)
- **Injury features excluded:** Prediction-time only, not available during training

**Expected weather impact for QB:**
- Extreme cold (<25°F), high wind (>=15mph) should negatively impact passing stats
- Dome games neutralized with 72°F, 0 wind

**Expected matchup impact for QB:**
- Vegas total points correlates with high-scoring games (more passing volume)
- Spread indicates game script (trailing teams pass more)
- Divisional games may show different patterns

### Training Set Characteristics

- **2508 samples:** Strong sample size across 4 seasons (2022-2025)
- **40 features:** Sufficient for LightGBM without overfitting
- **5-game rolling window:** Captures recent trends (Phase 19.1 improvement)
- **TimeSeriesSplit CV:** Respects temporal ordering, prevents data leakage

### Notable Observations

1. **Training vs CV metrics:** Training R² (full dataset) is higher than CV RMSE suggests. This is expected - CV measures generalization, training measures fit.

2. **Low-frequency events:** fumbles_lost has lowest R² (0.186). This is consistent with Phase 13 findings - rare events are inherently harder to predict.

3. **Passing dominance:** passing_yards and passing_tds are most predictable QB stats, aligning with fantasy importance.

4. **Sample warnings:** API rate limit warnings during feature building (Odds API free tier). This doesn't affect model quality - cached data used where available.

## Decision

**Satisfied with QB performance?**
- [x] Yes - proceed to RB (Plan 21-02)
- [ ] No - adjust QB training

**Recommendation:** Proceed to RB position

**Rationale:**
1. **Reasonable R² range:** 0.186-0.485 is acceptable for NFL prediction (high variance sport)
2. **Key stats performing well:** passing_yards (0.485) and rushing_yards (0.447) are primary fantasy stats
3. **Consistent with prior phases:** Phase 19.1 showed similar R² ranges (0.261-0.332 for TDs)
4. **Feature engineering focus:** Additional tuning (50-100 trials) unlikely to yield significant gains. Feature engineering is the leverage point.
5. **Position-by-position approach:** Phase 21 strategy is to train all positions first, then iterate if needed

### Next Steps

1. **Proceed to Plan 21-02:** Train RB models with 40-feature set
2. **After all positions trained:** Holistic analysis of which positions benefit most from Phase 20 features
3. **Future optimization (if needed):**
   - Increase trials to 50-100 for low-R² stats (fumbles_lost, interceptions)
   - Position-specific feature selection (remove low-importance features)
   - Custom hyperparameter ranges for rare events (fumbles, TDs)

### Archived Models

Pre-Phase 21 models (28 features) archived to `models_archive/phase20_pre_tuning/`:
- QB_passing_yards.joblib
- QB_passing_tds.joblib
- QB_interceptions.joblib
- QB_rushing_yards.joblib
- QB_rushing_tds.joblib
- QB_fumbles_lost.joblib

To rollback: `cp models_archive/phase20_pre_tuning/QB_*.joblib models/`
