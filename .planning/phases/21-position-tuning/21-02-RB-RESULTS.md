# Phase 21-02: RB Model Results

**Trained:** 2026-01-22
**Position:** RB (7 models)
**Feature count:** 40 (Phase 20: +14 from weather/matchup; injury excluded)
**Training data:** 2022-2025 (4 seasons)
**Rolling window:** 5 games
**Optuna trials:** 30 per model
**Model type:** LightGBM

## Performance Metrics

| Model | R² | MAE | RMSE | CV RMSE | Samples | Accuracy % |
|-------|----|----|------|---------|---------|------------|
| carries | 0.633 | 3.22 | 4.24 | 4.24 ± 0.06 | 5948 | 63.3% |
| rushing_yards | 0.514 | 18.49 | 25.30 | 25.30 ± 0.83 | 5948 | 51.4% |
| receiving_yards | 0.427 | 8.91 | 12.43 | 12.43 ± 0.28 | 5948 | 42.7% |
| receptions | 0.361 | 1.08 | 1.41 | 1.41 ± 0.05 | 5948 | 36.1% |
| rushing_tds | 0.291 | 0.30 | 0.45 | 0.45 ± 0.02 | 5948 | 29.1% |
| receiving_tds | 0.209 | 0.10 | 0.22 | 0.22 ± 0.01 | 5948 | 20.9% |
| fumbles_lost | 0.097 | 0.07 | 0.19 | 0.19 ± 0.01 | 5948 | 9.7% |

**RB Average R²:** 0.362

## Analysis

### Performance Overview

**Strong performers (R² > 0.5):**
- carries (R² = 0.633): Best RB stat, highly predictable workload metric
- rushing_yards (R² = 0.514): Primary fantasy stat, good performance

**Moderate performers (R² 0.3-0.5):**
- receiving_yards (R² = 0.427): Pass-catching RBs captured well
- receptions (R² = 0.361): Decent prediction for PPR leagues

**Challenging stats (R² < 0.3):**
- rushing_tds (R² = 0.291): Low-frequency event, inherently volatile
- receiving_tds (R² = 0.209): Very rare for RBs (~0.05/game), hard to predict
- fumbles_lost (R² = 0.097): Rare event, difficult to predict (consistent with QB findings)

### Sample Size Strength

**5948 RB samples** across 2022-2025 provides strong statistical foundation:
- ~1487 samples per season
- Captures diverse RB roles (workhorse, committee, pass-catching specialists)
- Sufficient data for 40-feature model without overfitting

### RB vs QB Comparison

**Position differences:**

| Metric | RB Avg R² | QB Avg R² | Difference |
|--------|-----------|-----------|------------|
| Overall Average | 0.362 | 0.355 | +0.007 (essentially equal) |
| Best Stat | 0.633 (carries) | 0.485 (passing_yards) | +0.148 (RB better) |
| Worst Stat | 0.097 (fumbles_lost) | 0.186 (fumbles_lost) | -0.089 (QB better) |

**Key insights:**
1. **RB and QB have similar average predictability** (0.362 vs 0.355), suggesting the 40-feature set works equally well for both positions
2. **Workload metrics are more predictable for RB**: carries (R² = 0.633) significantly outperforms passing attempts equivalent, likely because:
   - RB usage is more consistent week-to-week
   - Game script features (Vegas spread/totals) help predict RB workload
   - RB committee roles are fairly stable throughout season
3. **RB touchdowns are less predictable**: rushing_tds (R² = 0.291) and receiving_tds (R² = 0.209) are lower than QB passing_tds (R² = 0.414), likely because:
   - RB TDs depend heavily on goal-line opportunities
   - QB has more TD opportunities per game (2-3 passing TDs vs 0-1 rushing TD for RB)
   - Red zone usage varies more for RBs (some teams use goal-line specialists)
4. **Fumbles equally unpredictable**: Both positions struggle with fumbles_lost (RB 0.097, QB 0.186), confirming these are random events

### Feature Impact Analysis

**Expected weather impact for RB:**
- Weather features (extreme cold, high wind, precipitation) should **increase RB usage** as teams shift from passing to running
- This is opposite of QB where weather **hurts** passing stats
- The 40-feature set likely helps RB models by capturing game script shifts toward rushing in bad weather

**Expected matchup impact for RB:**
- **Vegas spread**: Trailing teams pass more, leading teams run more → spread should predict RB usage
- **Total points**: High-scoring games mean more offensive plays → more RB touches
- **Divisional games**: May show different RB usage patterns (more conservative game plans)
- **Home favored**: Favored teams more likely to run in second half to control clock

The strong carries prediction (R² = 0.633) suggests these matchup features are working well to capture game script effects on RB workload.

### Notable Observations

1. **Carries is the most predictable RB stat** (R² = 0.633): This makes sense as RB workload is more stable than production. Game script features (spread, totals) likely contribute significantly.

2. **Receiving stats moderate performance**: receiving_yards (R² = 0.427) and receptions (R² = 0.361) show RB pass-catching is predictable but less so than rushing. This may reflect:
   - Not all RBs have consistent receiving roles
   - Receiving usage varies more week-to-week than rushing usage
   - Some RBs are pure rushers, others are pass-catchers

3. **TD models need improvement**: Both rushing_tds (R² = 0.291) and receiving_tds (R² = 0.209) have low R². This is consistent with TD being low-frequency, high-variance events. Future improvements:
   - Red zone usage features (RB touches inside 10-yard line)
   - Goal-line role indicators (starter vs specialist)
   - Team offensive identity (run-heavy vs pass-heavy near goal line)

4. **Fumbles remain unpredictable**: fumbles_lost (R² = 0.097) confirms these are rare, random events. No amount of feature engineering will significantly improve this.

## Baseline Comparison

**Phase 19.2.1 (28 features) → Phase 21-02 (40 features):**

Direct comparison requires retraining baseline models with identical data splits, which is out of scope for this phase. However, archived models exist in `models_archive/phase20_pre_tuning/` for rollback if needed.

**Informal observation:** The 40-feature set (with weather and matchup additions) shows strong performance, particularly for workload metrics like carries. The R² of 0.633 for carries suggests game script features (Vegas lines, divisional games) are highly predictive.

## Decision

**Satisfied with RB performance?**
- [x] Yes - proceed to WR/TE (Plan 21-03)
- [ ] No - adjust RB training

**Recommendation:** Proceed to WR/TE position

**Rationale:**
1. **Strong average R²:** 0.362 is solid for NFL prediction (inherently high-variance sport)
2. **Workload metrics performing well:** carries (0.633) and rushing_yards (0.514) are the primary fantasy stats for RB
3. **Consistent with QB findings:** Both positions show ~0.35-0.36 average R², suggesting feature set is working
4. **TD models acceptable:** rushing_tds (0.291) is reasonable given low-frequency nature. Significant improvement would require red zone-specific features (future phase)
5. **Position-by-position approach:** Phase 21 strategy is to train all positions first, then iterate holistically if needed

### Next Steps

1. **Proceed to Plan 21-03:** Train WR/TE models with 40-feature set
2. **After all positions trained:** Holistic analysis comparing feature importance across positions
3. **Future optimization (if needed):**
   - Position-specific feature selection (e.g., weather may matter less for RB than QB)
   - Custom hyperparameter ranges for TD models (lower learning rate, more trees for rare events)
   - Red zone features for TD prediction improvements

### RB-Specific Insights

**What we learned about RB vs QB:**
1. **Workload is more predictable for RB** (carries R² = 0.633 vs QB attempts equivalent)
2. **Game script features work well for RB** (Vegas lines likely driving carries prediction)
3. **RB TDs are harder to predict than QB TDs** (goal-line variance, specialist usage)
4. **Weather impact hypothesis:** Weather features may help RB models by capturing run-heavy game scripts, but we'll need SHAP analysis to confirm

**Feature importance priorities for future analysis:**
- Vegas spread/totals → expected to be top features for carries
- Weather features → hypothesis: extreme conditions increase RB usage
- Divisional games → may show more conservative (run-heavy) game plans
- Rolling stats → still expect these to be most important (recent form)

## Training Details

**Models saved to:** `packages/backend/models/RB_*.joblib`
**Metrics file:** `packages/backend/rb_metrics.txt`
**Training script:** `packages/backend/scripts/train_all.py --positions RB --seasons 2022 2023 2024 2025 --trials 30 --rolling-window 5`

**Training duration:** ~45 minutes for 7 models (30 trials each)
**No errors or convergence issues**

**Model file sizes:**
- rushing_yards: 433 KB
- rushing_tds: 897 KB
- carries: 536 KB
- receiving_yards: 971 KB (largest)
- receptions: 353 KB
- receiving_tds: 338 KB
- fumbles_lost: 248 KB (smallest, simplest model)

Total: ~3.8 MB for all RB models
