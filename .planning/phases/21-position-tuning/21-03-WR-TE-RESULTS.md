# Phase 21-03: WR/TE Model Results

**Trained:** 2026-01-22
**Positions:** WR (4 models) + TE (4 models) = 8 total
**Feature count:** 40 (Phase 20: +14 from weather/matchup; injury excluded)
**Training data:** 2022-2025 (4 seasons)
**Rolling window:** 5 games
**Optuna trials:** 30 per model
**Model type:** LightGBM

## Performance Metrics

### WR Models

| Model | R² | MAE | RMSE | CV RMSE | Samples | Accuracy % |
|-------|----|-----|------|---------|---------|------------|
| receiving_yards | 0.416 | 20.76 | 27.76 | 29.52 ± 1.22 | 9453 | 41.6% |
| receiving_tds | 0.175 | 0.29 | 0.42 | 0.45 ± 0.02 | 9453 | 17.5% |
| receptions | 0.489 | 1.37 | 1.81 | 1.92 ± 0.10 | 9453 | 48.9% |
| fumbles_lost | 0.015 | 0.03 | 0.12 | 0.11 ± 0.02 | 9453 | 1.5% |

**WR Average R²:** 0.274

### TE Models

| Model | R² | MAE | RMSE | CV RMSE | Samples | Accuracy % |
|-------|----|-----|------|---------|---------|------------|
| receiving_yards | 0.482 | 13.84 | 18.58 | 21.59 ± 0.40 | 4766 | 48.2% |
| receiving_tds | 0.241 | 0.23 | 0.37 | 0.42 ± 0.02 | 4766 | 24.1% |
| receptions | 0.614 | 1.00 | 1.36 | 1.77 ± 0.07 | 4766 | 61.4% |
| fumbles_lost | 0.133 | 0.02 | 0.10 | 0.11 ± 0.01 | 4766 | 13.3% |

**TE Average R²:** 0.367

## Analysis

### Performance Overview

**Strong performers (R² > 0.4):**
- TE receptions (R² = 0.614): Best receiver stat overall, highly predictable TE target volume
- WR receptions (R² = 0.489): Second best, PPR leagues benefit from strong prediction
- TE receiving_yards (R² = 0.482): TE yardage more predictable than WR
- WR receiving_yards (R² = 0.416): Primary fantasy stat for WR, moderate performance

**Moderate performers (R² 0.2-0.4):**
- TE receiving_tds (R² = 0.241): Better than WR TDs, likely due to more consistent red zone usage
- WR receiving_tds (R² = 0.175): Low-frequency event, inherently volatile

**Challenging stats (R² < 0.2):**
- TE fumbles_lost (R² = 0.133): Rare event, but better than WR fumbles
- WR fumbles_lost (R² = 0.015): Extremely rare for WR, essentially unpredictable

### Sample Size Strength

**9453 WR samples** and **4766 TE samples** across 2022-2025 provide strong statistical foundation:
- WR: ~2363 samples per season, captures high-volume passing offenses
- TE: ~1192 samples per season, fewer TEs per game but sufficient data
- Both positions have sufficient data for 40-feature model without overfitting

## WR vs TE Comparison

**Position differences:**

| Metric | WR Avg R² | TE Avg R² | Difference |
|--------|-----------|-----------|------------|
| Overall Average | 0.274 | 0.367 | +0.093 (TE better) |
| Best Stat | 0.489 (receptions) | 0.614 (receptions) | +0.125 (TE better) |
| Worst Stat | 0.015 (fumbles_lost) | 0.133 (fumbles_lost) | +0.118 (TE better) |
| Yardage | 0.416 (receiving_yards) | 0.482 (receiving_yards) | +0.066 (TE better) |
| TDs | 0.175 (receiving_tds) | 0.241 (receiving_tds) | +0.066 (TE better) |

**Key insights:**

1. **TE is significantly more predictable than WR** (avg R² 0.367 vs 0.274):
   - TE usage is more consistent week-to-week
   - TEs have fewer "boom/bust" game scripts than WRs
   - TE target share is more stable (fewer TEs on field per play)
   - WR production varies more with defensive coverage schemes

2. **Receptions are most predictable for both positions**:
   - TE receptions (R² = 0.614): Elite predictability, consistent target volume
   - WR receptions (R² = 0.489): Strong but lower than TE
   - Both benefit from stable play-calling patterns and route trees

3. **TE yardage more predictable than WR yardage**:
   - TE receiving_yards (R² = 0.482) > WR receiving_yards (R² = 0.416)
   - TEs typically run shorter, more predictable routes (underneath, seam)
   - WRs face more variable coverage (man, zone, double teams) affecting YAC

4. **TE TDs more predictable than WR TDs**:
   - TE receiving_tds (R² = 0.241) > WR receiving_tds (R² = 0.175)
   - TEs are more consistently used in red zone (safety valve, size advantage)
   - WR TD opportunities vary more with game script and defensive adjustments

5. **Fumbles unpredictable for both, but TE slightly better**:
   - Both have low R² (WR 0.015, TE 0.133), confirming rare events
   - TE fumbles slightly more predictable, possibly due to contact after catch patterns

## Receivers vs QB/RB Comparison

**Cross-position insights:**

| Position | Avg R² | Best Stat R² | Sample Size |
|----------|--------|--------------|-------------|
| QB | 0.355 | 0.485 (passing_yards) | 2508 |
| RB | 0.362 | 0.633 (carries) | 5948 |
| WR | 0.274 | 0.489 (receptions) | 9453 |
| TE | 0.367 | 0.614 (receptions) | 4766 |

**Key findings:**

1. **TE predictability matches RB and QB** (avg R² 0.367 vs RB 0.362, QB 0.355):
   - TE usage consistency rivals RB workload predictability
   - Validates TE as a "stable" fantasy position despite lower volume

2. **WR is least predictable position** (avg R² 0.274):
   - WR production has highest variance due to:
     - Coverage schemes (man, zone, double teams)
     - Game script variations (trailing teams pass more to specific WRs)
     - Competitive depth charts (WR2/WR3 usage varies)
     - Big-play dependency (one long TD can dominate stat line)
   - This aligns with fantasy football wisdom: "WRs are volatile, TEs are stable"

3. **Volume metrics more predictable than production**:
   - RB carries (R² = 0.633) > all receiver stats
   - TE receptions (R² = 0.614) > WR receptions (R² = 0.489)
   - Yardage harder to predict than touches/targets
   - TDs even harder due to low-frequency nature

4. **Weather features likely help receivers less than RB/QB**:
   - WR avg R² (0.274) is lowest despite 40-feature set
   - Weather may affect passing volume (QB/RB game script) more than WR-specific production
   - WR performance depends more on coverage matchups than weather conditions
   - Future SHAP analysis needed to confirm weather feature importance by position

5. **Vegas totals predict pass volume, but WR-specific production remains volatile**:
   - High-scoring games (total points) increase passing volume
   - But predicting which WR benefits is harder (WR1 vs WR2 vs WR3)
   - TE benefits more from increased volume due to consistent safety valve role

## Feature Impact (Inferred from Training)

**Expected weather impact for receivers:**
- Weather features (extreme cold, high wind, precipitation) should **reduce passing volume**
- This would hurt all receiving stats (yards, TDs, receptions)
- However, WR avg R² (0.274) is lowest, suggesting weather alone doesn't explain WR variance
- TE avg R² (0.367) is higher, possibly because TEs are used more in bad weather (short routes)

**Expected matchup impact for receivers:**
- **Vegas total points**: High-scoring games → more passing volume → more receiver production
- **Spread**: Trailing teams pass more, but WR-specific production still volatile
- **Divisional games**: May show different patterns (more conservative, fewer deep shots)
- **Home favored**: Favored teams may shift to run-heavy in second half, reducing WR targets

**Hypothesis for future SHAP analysis:**
- Weather features likely less important for receivers than RB/QB
- Vegas totals likely important for predicting passing volume (affects all receivers)
- Coverage-specific features (future phase) would help WR predictions more than weather/matchup

## Baseline Comparison

**Phase 19.2.1 (28 features) → Phase 21-03 (40 features):**

Direct comparison requires retraining baseline models with identical data splits, which is out of scope for this phase. However, archived models exist in `models_archive/phase20_pre_tuning/` for rollback if needed.

**Informal observation:** The 40-feature set shows reasonable performance for TE (avg R² 0.367 similar to QB/RB), but WR remains challenging (avg R² 0.274). This suggests WR predictions require more than weather/matchup features—likely need coverage-specific or target share features.

## Decision

**Satisfied with WR/TE performance?**
- [x] Yes - proceed to K/DEF (Plan 21-04)
- [ ] No - adjust WR/TE training

**Recommendation:** Proceed to K/DEF position

**Rationale:**

1. **TE performance is strong** (avg R² 0.367, matches QB/RB):
   - TE receptions (R² = 0.614) is elite predictability
   - TE receiving_yards (R² = 0.482) is solid
   - TE is a stable fantasy position, models reflect this

2. **WR performance is reasonable given inherent volatility** (avg R² 0.274):
   - WR production is known to be volatile in fantasy football
   - Models capture what's predictable (receptions R² = 0.489)
   - Further improvement would require coverage-specific features (future phase)
   - Receptions (PPR leagues) are well-predicted, which is valuable

3. **Volume metrics performing well**:
   - Both WR and TE receptions are strong (0.489 and 0.614)
   - PPR leagues benefit from these predictions
   - Standard leagues may see less value from WR models due to TD volatility (R² = 0.175)

4. **Phase 21 strategy is position-by-position baseline**:
   - Train all positions first, then iterate holistically
   - After K/DEF, we can assess which positions need most improvement
   - WR may benefit from position-specific features in future phase

5. **Feature engineering is the leverage point**:
   - Additional tuning (50-100 trials) unlikely to yield significant gains
   - WR needs coverage-specific features (slot rate, aDOT, target share, CB matchup)
   - This is a future phase, not Phase 21 scope

### Next Steps

1. **Proceed to Plan 21-04:** Train K/DEF models with 40-feature set
2. **After all positions trained:** Holistic analysis of feature importance across positions
3. **Future optimization for WR (if needed):**
   - Add coverage-specific features (slot rate, aDOT, target share, CB matchup)
   - Position-specific feature selection (remove low-importance weather features for WR)
   - Custom hyperparameter ranges for TD models (lower learning rate, more trees)
   - Consider ensemble models specifically for volatile WR TDs

### Position-Specific Insights

**What we learned about WR vs TE:**

1. **TE is significantly more predictable than WR** (0.367 vs 0.274 avg R²)
2. **Receptions are most predictable stat for both** (TE 0.614, WR 0.489)
3. **TE yardage and TDs more predictable** due to consistent usage patterns
4. **WR volatility is real** and matches fantasy football conventional wisdom
5. **Fumbles unpredictable for both** (rare events, R² < 0.15)

**What we learned about receivers vs other positions:**

1. **WR is least predictable position** (0.274 avg R² vs QB 0.355, RB 0.362, TE 0.367)
2. **TE predictability matches RB/QB** despite lower volume
3. **Volume metrics trump production** (receptions > yards > TDs)
4. **Weather/matchup features likely less impactful for WR** than RB/QB
5. **WR needs position-specific features** (coverage, target share) more than other positions

## Training Details

**Models saved to:** `packages/backend/models/{WR,TE}_*.joblib`
**Training script:** `packages/backend/scripts/train_all.py --positions WR TE --seasons 2022 2023 2024 2025 --trials 30 --rolling-window 5`

**Training duration:** ~1 hour 24 minutes for 8 models (30 trials each):
- WR: 46 minutes for 4 models (~11.5 min per model)
- TE: 38 minutes for 4 models (~9.5 min per model)

**No errors or convergence issues**

**Model file sizes:**
- WR_receiving_yards: 343 KB
- WR_receiving_tds: 492 KB
- WR_receptions: 436 KB
- WR_fumbles_lost: 289 KB
- TE_receiving_yards: 429 KB
- TE_receiving_tds: 313 KB
- TE_receptions: 2.1 MB (largest, likely due to more complex tree structure)
- TE_fumbles_lost: 340 KB

Total: ~5.4 MB for all WR/TE models
