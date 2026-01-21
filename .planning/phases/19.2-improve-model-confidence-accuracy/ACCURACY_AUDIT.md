# Accuracy Formula Audit

**Date:** 2026-01-20
**Phase:** 19.2-improve-model-confidence-accuracy
**Purpose:** Diagnose why accuracy_pct produces unintuitive results (49% for models with R² 0.545)

## Problem Analysis

### Current Formula

```python
accuracy_pct = max(0.0, 100.0 * (1.0 - mae / abs(mean_actual)))
```

**Source:** `packages/backend/src/lineupiq/models/accuracy.py` (lines 57-64)

**Decision Context (Phase 12):**
- Rationale: "Intuitive 0-100% scale for user trust"
- Goal: Provide a simple, user-friendly metric that non-ML users can understand
- Implementation: Measures how small MAE is relative to the mean of actual values

### Why It Fails

The formula assumes that MAE/mean provides an intuitive measure of model quality, but this creates several problems:

1. **Linear treatment of non-linear performance:** ML model performance is non-linear. R² explains variance and correlates with model quality, but accuracy_pct = 100*(1 - MAE/mean) treats error linearly.

2. **No variance accounting:** Stats with high variance (like touchdowns or big-play yards) naturally have higher MAE, even when the model is good. The formula penalizes models for stat variance, not model quality.

3. **Disconnect from R²:** R² and accuracy_pct should correlate (both measure model quality), but they don't. A model with R² 0.545 (explaining 54.5% of variance) shows only 47% accuracy_pct.

4. **Low-mean stats break down:** For rare events (fumbles_lost with mean 0.04), even small MAE (0.07) produces 0% accuracy despite reasonable R² (0.073).

### Specific Problem Cases

Using data from `ROLLING_WINDOW_BENCHMARK.md`:

#### Case 1: RB rushing_yards - GOOD model, BAD metric
- **MAE:** 17.69 yards
- **Mean:** 33.19 yards
- **R²:** 0.545 (explains 54.5% of variance)
- **Std:** 36.96 yards
- **accuracy_pct:** 100 * (1 - 17.69/33.19) = **46.7%**

**Problem:** R² of 0.545 is a GOOD model (explains more than half the variance), but users see "47% accurate" and lose trust.

**Python calculation:**
```python
mae, mean, r2 = 17.69, 33.19, 0.545
accuracy_pct = 100 * (1 - mae / mean)
# accuracy_pct = 46.7% ← LOW perception
# r2 = 54.5% ← GOOD reality
```

#### Case 2: WR receiving_yards - Poor model looks terrible
- **MAE:** 20.09 yards
- **Mean:** 30.72 yards
- **R²:** 0.407 (explains 40.7% of variance)
- **accuracy_pct:** 100 * (1 - 20.09/30.72) = **34.6%**

**Problem:** R² of 0.407 is acceptable for a high-variance stat, but 35% accuracy makes it look terrible.

#### Case 3: RB fumbles_lost - Formula breaks for rare events
- **MAE:** 0.07
- **Mean:** 0.04
- **R²:** 0.073
- **accuracy_pct:** 100 * (1 - 0.07/0.04) = **0%** (clamped to 0)

**Problem:** For rare events with mean < MAE, the formula produces negative values (clamped to 0%). Any model predicting rare events shows 0% accuracy.

#### Case 4: TE fumbles_lost - Even worse breakdown
- **MAE:** 0.02
- **Mean:** 0.01
- **R²:** 0.008
- **accuracy_pct:** 100 * (1 - 0.02/0.01) = **0%** (clamped to 0)

**Problem:** Despite MAE being only 0.02 (very small absolute error), the formula produces 0% accuracy because mean is so low.

#### Case 5: QB passing_yards - High-volume stat looks great
- **MAE:** 55.28 yards
- **Mean:** 186.62 yards
- **R²:** 0.524
- **accuracy_pct:** 100 * (1 - 55.28/186.62) = **70.4%**

**Comparison with Case 1:** Both have similar R² (~0.52-0.54), but passing_yards shows 70% accuracy while rushing_yards shows 47%. The difference? Passing yards has a higher mean, making MAE/mean smaller.

### Root Cause

The formula `accuracy_pct = 100 * (1 - MAE / mean)` is fundamentally flawed because:

1. **Scale-dependent:** Stats with higher means (passing yards) always look better than stats with lower means (rushing yards), even with similar R².

2. **Variance-blind:** Doesn't account for stat volatility. A stat with std = 100 needs higher MAE tolerance than std = 10.

3. **No R² correlation:** R² measures explained variance (the gold standard for regression), but accuracy_pct doesn't correlate with R². Models with R² > 0.5 can show 47% accuracy.

4. **User impact:** Users see "49% accurate" for GOOD models and conclude the predictions are unreliable, even though R² 0.545 means the model explains 54.5% of variance.

### Mathematical Demonstration

For a model to show 80% accuracy_pct, we need:

```
100 * (1 - MAE / mean) ≥ 80
1 - MAE / mean ≥ 0.8
MAE / mean ≤ 0.2
MAE ≤ 0.2 * mean
```

For RB rushing_yards (mean = 33.19):
- Required MAE: ≤ 6.64 yards
- Actual MAE: 17.69 yards
- R²: 0.545

**The problem:** Achieving MAE ≤ 6.64 for a stat with std = 36.96 would require R² > 0.95 (near-perfect). The formula sets unrealistic expectations.

### User Impact

1. **Trust erosion:** Users see "49% accurate" and question all predictions, even for good models.

2. **Confidence tier confusion:** The confidence tier logic uses both R² and accuracy_pct:
   ```python
   if r2 > 0.5 and accuracy_pct > 80.0:
       return "High"
   ```
   Models with R² > 0.5 but accuracy_pct < 80 get downgraded to "Medium" despite being good.

3. **Rare event invisibility:** Low-mean stats (fumbles, some TDs) always show 0% accuracy, making users think we don't model them at all.

4. **Inconsistent expectations:** Passing yards models look great (70%), rushing yards models look poor (47%), but both have similar R² (~0.52).

## Summary

The current `accuracy_pct = 100 * (1 - MAE / mean)` formula fails because it:
- Treats MAE/mean linearly when ML performance is non-linear
- Ignores stat variance (penalizes models for volatile stats)
- Doesn't correlate with R² (the standard ML quality metric)
- Breaks down for low-mean stats (rare events)
- Creates unrealistic user expectations for model quality

**Result:** GOOD models (R² 0.545) show "49% accurate" and users lose trust.

---

## Alternative Metrics

Three options for replacing the problematic accuracy_pct formula:

### Option 1: R²-based accuracy (RECOMMENDED)

**Formula:**
```python
accuracy_pct = max(0, 100 * r2)
```

**Pros:**
- Standard ML metric - widely recognized and understood
- Directly measures variance explained (model quality)
- Always produces 0-100% scale (with clamping for negative R²)
- Correlates perfectly with model performance by definition
- Works for all stat types (high-mean, low-mean, high-variance, low-variance)

**Cons:**
- Can be negative for very bad models (requires clamping to 0)
- Less intuitive for non-ML users who don't know what "variance explained" means
- Doesn't provide absolute error magnitude information

**Example transformations:**
```python
# Case 1: RB rushing_yards (GOOD model)
r2 = 0.545
accuracy_pct = 100 * 0.545 = 54.5%  # ← Matches model quality

# Case 2: QB passing_yards (GOOD model)
r2 = 0.524
accuracy_pct = 100 * 0.524 = 52.4%  # ← Consistent with rushing_yards

# Case 3: RB fumbles_lost (POOR model, but not broken)
r2 = 0.073
accuracy_pct = 100 * 0.073 = 7.3%  # ← Honest assessment, not 0%
```

**Why this works:** R² = 0.545 means the model explains 54.5% of variance. Showing "54.5% accurate" is truthful and aligns user expectations with reality.

### Option 2: MAPE-based accuracy

**Formula:**
```python
mape = 100 * mean(abs((actuals - predictions) / actuals))
accuracy_pct = max(0, 100 * (1 - mape / 100))
```

**Pros:**
- Percentage-based like current formula (user familiarity)
- Handles different scales naturally (division by actual, not mean)
- Industry-standard metric for forecasting

**Cons:**
- Undefined for actuals = 0 (division by zero)
- Can explode for small actual values (fumbles issue persists)
- Asymmetric: over-predictions penalized more than under-predictions
- Still doesn't account for stat variance

**Example transformations:**
```python
# Hypothetical MAPE for RB rushing_yards
# If predictions average 30% error from actuals
mape = 30
accuracy_pct = 100 * (1 - 30/100) = 70%

# Problem: Low actual values blow up MAPE
# Actual = 0.04 fumbles, Predicted = 0.07
# Error = |0.04 - 0.07| / 0.04 = 0.75 = 75% error for tiny absolute miss
```

**Why this doesn't work well:** MAPE still suffers from scale issues. Low-mean stats (fumbles) will have huge percentage errors even for small absolute misses.

### Option 3: Skill Score (variance-normalized)

**Formula:**
```python
skill_score = 1 - (mae / std(actuals))
accuracy_pct = max(0, 100 * skill_score)
```

**Pros:**
- Accounts for stat variance (high-variance stats get more MAE tolerance)
- Better for boom/bust stats like touchdowns
- Provides 0-100% scale (with clamping)
- More fair to high-variance predictions than MAE/mean

**Cons:**
- More complex calculation than R² (requires std calculation)
- Less standard than R² in ML literature
- Can still be negative (requires clamping)
- Not as widely recognized outside ML

**Example transformations:**
```python
# Case 1: RB rushing_yards
mae, std = 17.69, 36.96
skill_score = 1 - (17.69 / 36.96) = 0.521
accuracy_pct = 100 * 0.521 = 52.1%  # ← Similar to R²

# Case 2: RB fumbles_lost (high variance helps)
mae, std = 0.07, 0.19
skill_score = 1 - (0.07 / 0.19) = 0.632
accuracy_pct = 100 * 0.632 = 63.2%  # ← Much better than 0%!

# Case 3: QB passing_yards
mae, std = 55.28, 102.28
skill_score = 1 - (55.28 / 102.28) = 0.460
accuracy_pct = 100 * 0.460 = 46.0%  # ← Lower than current, more realistic
```

**Why this helps:** Variance-normalization gives credit for predicting volatile stats. Fumbles with std = 0.19 can tolerate MAE = 0.07 without showing 0% accuracy.

## Recommendation

### Primary: Use R²-based accuracy (Option 1)

**Rationale:**
1. **Standard ML metric:** R² is the gold standard for regression model evaluation. Using it for accuracy_pct aligns our user-facing metric with industry standards.

2. **Perfect correlation:** By definition, accuracy_pct = 100 * R² means our accuracy metric matches model quality exactly. No more disconnect between "good R²" and "bad accuracy".

3. **Works everywhere:** R² handles all stat types equally. High-mean, low-mean, high-variance, low-variance - all treated fairly.

4. **User education:** We can add a tooltip: "Accuracy shows the % of variance the model explains. 50% = model explains half of why stats vary."

### Secondary: Keep skill score as "consistency" metric

For stats with extreme variance (TDs, fumbles), we could compute both:
- **Accuracy:** R²-based (primary metric)
- **Consistency:** Skill score (shows how well we handle volatility)

This gives users two dimensions:
- Accuracy = Overall model quality
- Consistency = Performance relative to stat volatility

### Update Confidence Tiers

Current logic (broken):
```python
if r2 > 0.5 and accuracy_pct > 80.0:
    return "High"
```

Proposed logic (aligned):
```python
if r2 > 0.5:  # accuracy_pct will be > 50 by definition
    return "High"
elif r2 > 0.3:
    return "Medium"
else:
    return "Low"
```

Or keep both but make them consistent:
```python
if r2 > 0.5 and accuracy_pct > 50.0:  # Both mean same thing now
    return "High"
elif r2 > 0.3 or accuracy_pct > 30.0:
    return "Medium"
else:
    return "Low"
```

### Implementation Path

**Phase 19.2-02:** Update `calculate_model_accuracy()` in `accuracy.py`
1. Add new `r2_based_accuracy` field to return dict
2. Keep old `accuracy_pct` for backward compatibility (deprecated)
3. Update frontend to display `r2_based_accuracy` instead
4. Update confidence tier logic to use R² thresholds

**Phase 19.2-03:** Optional - add skill score as secondary metric
1. Add `consistency_score` field (variance-normalized)
2. Display in UI as separate metric for high-variance stats

---

## Validation

Using data from `ROLLING_WINDOW_BENCHMARK.md`, let's validate that R²-based accuracy fixes the problem:

### Comparison Table

| Position | Stat | R² | Current Accuracy | R²-based Accuracy | Skill Score | Confidence Change |
|----------|------|----|-----------------|--------------------|-------------|-------------------|
| QB | passing_yards | 0.524 | 70.4% | 52.4% | 46.0% | High → Medium |
| QB | passing_tds | 0.423 | 41.4% | 42.3% | 38.7% | Low → Medium |
| QB | rushing_yards | 0.380 | 28.4% | 38.0% | 40.7% | Low → Medium |
| QB | rushing_tds | 0.314 | 0.0% | 31.4% | 48.8% | Low → Medium |
| QB | interceptions | 0.223 | 0.0% | 22.3% | 26.6% | Low → Low |
| QB | fumbles_lost | 0.121 | 0.0% | 12.1% | 35.7% | Low → Low |
| RB | carries | 0.696 | 61.7% | 69.6% | 58.3% | Medium → Medium |
| RB | rushing_yards | 0.545 | 46.7% | 54.5% | 52.1% | Low → Medium |
| RB | rushing_tds | 0.253 | 0.0% | 25.3% | 41.8% | Low → Low |
| RB | receptions | 0.458 | 31.7% | 45.8% | 43.4% | Low → Medium |
| RB | receiving_yards | 0.374 | 15.4% | 37.4% | 44.6% | Low → Medium |
| RB | receiving_tds | 0.191 | 0.0% | 19.1% | 62.9% | Low → Low |
| RB | fumbles_lost | 0.073 | 0.0% | 7.3% | 63.2% | Low → Low |
| WR | receptions | 0.520 | 47.5% | 52.0% | 46.9% | Low → Medium |
| WR | receiving_yards | 0.407 | 34.6% | 40.7% | 41.9% | Low → Medium |
| WR | receiving_tds | 0.216 | 0.0% | 21.6% | 37.8% | Low → Low |
| WR | fumbles_lost | 0.021 | 0.0% | 2.1% | 80.0% | Low → Low |
| TE | receptions | 0.591 | 54.7% | 59.1% | 52.8% | Medium → Medium |
| TE | receiving_yards | 0.460 | 39.4% | 46.0% | 46.1% | Low → Medium |
| TE | receiving_tds | 0.170 | 0.0% | 17.0% | 40.9% | Low → Low |
| TE | fumbles_lost | 0.008 | 0.0% | 0.8% | 81.8% | Low → Low |

### Calculation Details

**Current Accuracy (MAE/mean formula):**
```python
current_accuracy = 100 * (1 - mae / mean)
# Clamped to 0% minimum
```

**R²-based Accuracy:**
```python
r2_based_accuracy = 100 * r2
# Matches R² directly
```

**Skill Score (variance-normalized):**
```python
skill_score = 100 * (1 - mae / std)
# Clamped to 0% minimum
```

### Key Insights

#### 1. R²-based accuracy fixes the "good model, bad metric" problem

**Before (Current Formula):**
- RB rushing_yards: R² 0.545 → 47% accuracy (looks BAD)
- QB passing_yards: R² 0.524 → 70% accuracy (looks GOOD)
- **Problem:** Similar R² models show wildly different accuracy

**After (R²-based):**
- RB rushing_yards: R² 0.545 → 55% accuracy (consistent)
- QB passing_yards: R² 0.524 → 52% accuracy (consistent)
- **Fixed:** Accuracy now correlates with R²

#### 2. Rare events no longer show 0% accuracy

**Stats with 0% current accuracy (9 total):**
- QB rushing_tds: 0% → 31.4% (R²-based)
- QB interceptions: 0% → 22.3% (R²-based)
- QB fumbles_lost: 0% → 12.1% (R²-based)
- RB rushing_tds: 0% → 25.3% (R²-based)
- RB receiving_tds: 0% → 19.1% (R²-based)
- RB fumbles_lost: 0% → 7.3% (R²-based)
- WR receiving_tds: 0% → 21.6% (R²-based)
- WR fumbles_lost: 0% → 2.1% (R²-based)
- TE receiving_tds: 0% → 17.0% (R²-based)
- TE fumbles_lost: 0% → 0.8% (R²-based)

**Result:** Users can now see that we do model rare events, even if performance is modest.

#### 3. Skill score shows variance-normalization benefits

For high-variance, low-mean stats like fumbles:
- RB fumbles_lost: R²-based 7.3% vs Skill Score 63.2%
- WR fumbles_lost: R²-based 2.1% vs Skill Score 80.0%
- TE fumbles_lost: R²-based 0.8% vs Skill Score 81.8%

**Insight:** Skill score could be useful as a secondary "consistency" metric for volatile stats, but R²-based should be the primary accuracy metric.

#### 4. Confidence tier changes

Using the proposed logic: High (R² > 0.5), Medium (R² > 0.3), Low (R² < 0.3)

**Upgrades (Low → Medium):** 9 models
- QB passing_tds (0.423)
- QB rushing_yards (0.380)
- QB rushing_tds (0.314)
- RB rushing_yards (0.545)
- RB receptions (0.458)
- RB receiving_yards (0.374)
- WR receptions (0.520)
- WR receiving_yards (0.407)
- TE receiving_yards (0.460)

**Downgrades (High → Medium):** 1 model
- QB passing_yards (0.524) - was "High" due to 70.4% accuracy, now "Medium" (consistent with R² < 0.5)

**Net effect:** 9 upgrades, 1 downgrade = more fair representation of model quality

### Summary Statistics

**Current Formula:**
- Models showing 0% accuracy: 10/21 (47.6%)
- Average accuracy: 23.8%
- Accuracy range: 0-70.4%

**R²-based Accuracy:**
- Models showing 0% accuracy: 0/21 (0%)
- Average accuracy: 33.2% (matches average R²)
- Accuracy range: 0.8-69.6%

**Key Improvement:** R²-based accuracy is more consistent, fair, and aligned with actual model performance. No more "0% accurate" models that actually have modest predictive power.

## Final Recommendation

**Adopt R²-based accuracy immediately** (Phase 19.2-02):
1. Replace `accuracy_pct = 100 * (1 - MAE / mean)` with `accuracy_pct = 100 * r2`
2. Update confidence tier thresholds: High (R² > 0.5), Medium (R² 0.3-0.5), Low (R² < 0.3)
3. Add tooltip: "Accuracy measures % of variance the model explains"
4. Keep MAE in UI for absolute error context

**Consider skill score as secondary metric** (Phase 19.2-03):
1. Add `consistency_score = 100 * (1 - MAE / std)` for high-variance stats
2. Display in UI for TDs, fumbles, and other volatile stats
3. Label as "Consistency" to distinguish from "Accuracy"
