# Ensemble Benchmark Discrepancy Analysis

**Date:** 2026-01-20
**Analyst:** Phase 19.1 Investigation
**Purpose:** Understand why two benchmark runs reached contradictory conclusions about ensemble model adoption

## Executive Summary

Two comprehensive benchmarks on the same 21 skill position stats reached **opposite conclusions**:

- **2024 Holdout (BENCHMARK_RESULTS.md):** Single models win 20/21 stats (95.2%) → Keep single models
- **2025 Holdout (BENCHMARK_RESULTS_2025.md):** Ensembles win 20/21 stats (95.2%) → Adopt ensembles

**Root Cause:** The models being compared are **completely different**. The benchmarks both use `benchmark_ensemble_strategies()` which trains fresh models on-the-fly for each stat, but with different training data windows. This creates fundamentally different base models, making the comparison invalid.

**Critical Finding:** The benchmarks are NOT comparing "same models, different holdout years" - they're comparing "completely different models with different training windows."

## Detailed Comparison

### Training Data Volume

| Benchmark | Training Seasons | Years of Data | Holdout Season |
|-----------|------------------|---------------|----------------|
| 2024 Holdout | 2022-2023 | 2 years | 2024 |
| 2025 Holdout | 2020-2024 | 5 years | 2025 |

**Impact:** 2.5x more training data in the 2025 benchmark (5 vs 2 years).

### Performance Results Comparison

| Benchmark | Single Model Wins | Ensemble Wins | Avg Correlation |
|-----------|------------------|---------------|-----------------|
| 2024 Holdout | 20/21 (95.2%) | 1/21 (4.8%) | 0.890 |
| 2025 Holdout | 1/21 (4.8%) | 20/21 (95.2%) | 0.880 |

**Observation:** Near-perfect reversal of outcomes despite similar correlation metrics.

### Winning Strategy Breakdown

**2024 Holdout:**
- lgbm_solo: 17/21 (81.0%)
- xgb_solo: 3/21 (14.3%)
- voting_weighted: 1/21 (4.8%)
- voting_simple: 0/21
- stacking: 0/21

**2025 Holdout:**
- voting_weighted: 13/21 (61.9%)
- stacking: 7/21 (33.3%)
- xgb_solo: 1/21 (4.8%)
- lgbm_solo: 0/21
- voting_simple: 0/21

**Critical Observation:** LightGBM went from dominating (81%) to never winning (0%). This is statistically implausible if comparing the same models.

## Root Cause Analysis

### 1. Different Models, Not Different Holdout Sets

The fundamental issue: `benchmark_ensemble_strategies()` **trains new models** for each benchmark run. Looking at the code:

```python
# From ensemble.py benchmark_ensemble_strategies()
lgbm_model = train_model(X_train, y_train, model_type="lightgbm", ...)
xgb_model = train_model(X_train, y_train, model_type="xgboost", ...)
```

This means:
- 2024 benchmark trained models on 2022-2023 data
- 2025 benchmark trained models on 2020-2024 data
- These are **fundamentally different models** with different learned patterns

### 2. Training Data Volume Effect

**Hypothesis:** More training data (5 years vs 2 years) changes the model landscape:

1. **Single models with limited data (2 years):**
   - May learn clearer, more distinct patterns
   - Less overfitting risk with smaller dataset
   - LightGBM's regularization advantages shine

2. **Single models with abundant data (5 years):**
   - Models may learn more nuanced, overlapping patterns
   - Both LightGBM and XGBoost converge toward similar solutions
   - Ensembles benefit from averaging out year-specific quirks

### 3. Holdout Season Characteristics

**2024 Season:**
- First post-COVID "normal" season with full 17-game schedule established
- May have been more predictable/stable

**2025 Season:**
- Most recent season, still in progress during benchmark
- Potential for incomplete data or different meta-game dynamics

### 4. Methodology Issues

Both benchmarks use identical code (`benchmark_ensemble_strategies()`), so no methodology differences exist. The issue is **conceptual** - comparing different model vintages rather than holdout performance.

## Statistical Significance Assessment

### Model Diversity (Correlation)

- 2024 Holdout: 0.890 avg correlation (low diversity)
- 2025 Holdout: 0.880 avg correlation (low diversity)

**Interpretation:** Correlation is nearly identical (-1.1% difference), yet ensemble effectiveness completely reversed. This suggests correlation alone is insufficient to predict ensemble utility.

### MAE Improvements/Degradations

**Stats that flipped from single→ensemble winners (examples):**

| Stat | 2024 Best | 2024 MAE | 2025 Best | 2025 MAE | Change |
|------|-----------|----------|-----------|----------|--------|
| QB_passing_yards | lgbm_solo | 4.73 | voting_weighted | 37.94 | 8x higher error |
| RB_rushing_yards | lgbm_solo | 6.16 | stacking | 10.01 | 62% higher error |
| WR_receiving_yards | lgbm_solo | 5.90 | voting_weighted | 10.21 | 73% higher error |

**Critical Finding:** Not only did ensemble strategies win in 2025, but **absolute performance degraded significantly** across the board. This indicates the 2020-2024 trained models are worse at predicting 2025 than the 2022-2023 models were at predicting 2024.

### Possible Explanations

1. **Concept drift:** NFL meta-game changed between training periods
2. **Data quality:** 2025 season data may be incomplete or lower quality
3. **Overfitting to old patterns:** 5 years of data includes outdated strategies (2020-2021 COVID seasons)
4. **Rolling window need:** Models need recent data (2022-2024) more than volume (2020-2024)

## Conclusion and Recommendation

### Key Findings

1. **The benchmarks compared different models, not different holdout sets** - This invalidates direct comparison
2. **More training data ≠ better models** - 5-year models performed worse (higher MAE) than 2-year models
3. **Ensemble benefit appears when base models are weak** - 2025 ensembles "won" by being less bad
4. **Recency likely matters more than volume** - 2022-2023 data may be more relevant than 2020-2021 data

### Recommended Decision: **Keep Single Models (trust 2024 benchmark)**

**Rationale:**

1. **Production models use 2022-2023 training window** - The 2024 benchmark matches our actual model training approach
2. **Lower absolute errors** - 2024 benchmark showed better performance (MAE 4.73-6.16 for major stats vs 10.01-37.94 in 2025)
3. **Simpler is better when equally effective** - Our production LightGBM models already perform well
4. **Ensemble "wins" in 2025 are Pyrrhic victories** - Winning by having less-bad errors isn't a compelling reason to add complexity

### Why Not 2025 Benchmark?

1. **Worse absolute performance** - Even winning strategies have higher MAE
2. **Training window includes COVID seasons** - 2020-2021 data may introduce noise
3. **Potential data quality issues** - 2025 season was in-progress during benchmarking
4. **Doesn't match production setup** - Our models don't use 2020-2024 training data

### Path Forward

**Immediate (Phase 19.1):**
- Keep single models (LightGBM default)
- Reject ensemble adoption
- Document decision in STATE.md

**Future Investigation (Phase 20+):**
- Implement rolling training windows (use most recent N years, not fixed years)
- Re-benchmark with controlled training windows (e.g., both use 2022-2024)
- Validate on multiple holdout years simultaneously (2024 AND 2025)
- Consider whether recency bias helps (weight recent seasons more heavily)

## Appendix: Stats-by-Stats Flip Analysis

### Stats Where Single Models Won in 2024 BUT Ensembles Won in 2025

All 21 stats flipped except TE_fumbles_lost:
- 2024: voting_weighted won (6.2% improvement)
- 2025: xgb_solo won (1.9% degradation)

**Complete reversal** confirms these are fundamentally different model comparisons.

### Model Diversity by Correlation Range

**2024 Holdout:**
- High diversity (<0.7): 3/21 stats
- Moderate diversity (0.7-0.9): 3/21 stats
- Low diversity (≥0.9): 15/21 stats

**2025 Holdout:**
- High diversity (<0.7): 4/21 stats
- Moderate diversity (0.7-0.9): 1/21 stats
- Low diversity (≥0.9): 16/21 stats

**Minimal difference** - diversity metrics are nearly identical, yet outcomes completely reversed.

---

**Final Decision:** Keep single models. Trust the 2024 benchmark as it matches our production training approach and demonstrates superior absolute performance. The 2025 benchmark revealed the need for rolling training windows, not ensemble adoption.
