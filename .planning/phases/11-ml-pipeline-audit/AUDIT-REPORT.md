# ML Pipeline Audit Report

**Phase:** 11-ml-pipeline-audit
**Audited:** 2026-01-15
**Purpose:** Establish baseline understanding of current pipeline, identify gaps, and create actionable recommendations for Phase 12.

---

## Data Pipeline Audit

### Current Approach

The current data pipeline (`packages/backend/src/lineupiq/data/`) handles null values with a **fill with 0** strategy for stat columns.

**Key files:**
- `cleaning.py` (lines 17-29): Defines `NUMERIC_STAT_COLUMNS` and fills nulls with 0
- `processing.py` (lines 166-189): Additional null handling for weather features (fill with neutral values)
- `rolling_stats.py` (line 83): Uses `min_samples=1` to handle early-season data

**How it works:**

1. **cleaning.py** - `clean_numeric_stats()` function:
   ```python
   NUMERIC_STAT_COLUMNS = [
       "passing_yards", "passing_tds", "interceptions",
       "rushing_yards", "rushing_tds", "carries",
       "receptions", "receiving_yards", "receiving_tds", "targets"
   ]

   for col in existing_stat_columns:
       df = df.with_columns(pl.col(col).fill_null(0))
   ```

2. **rolling_stats.py** - Uses `min_samples=1`:
   - Allows rolling averages to compute with fewer than `window` games
   - Enables predictions for rookies/early season
   - Doesn't handle null input values (relies on upstream cleaning)

3. **processing.py** - Weather context:
   - `temp_normalized`: Fills null temp with 65 (neutral)
   - `wind_normalized`: Fills null wind with 0 (calm)

### Identified Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| **Fill with 0 destroys correlations** | MEDIUM | Feature relationships (e.g., targets vs receptions) are distorted when nulls become 0 |
| **Biases predictions low** | MEDIUM | Zero-filled values pull rolling averages down artificially |
| **No distinction between true 0 and missing** | LOW | A player with 0 receptions (didn't catch passes) is treated the same as missing data |
| **No imputation for correlated features** | LOW | Each feature imputed independently; KNN would preserve cross-feature relationships |

### Research Findings (from 11-RESEARCH.md)

The research phase identified several improvements:

1. **KNN Imputation** (`sklearn.KNNImputer`):
   - Preserves correlations between related features
   - Uses k-nearest neighbors to estimate missing values
   - Better for features with strong relationships (targets/receptions, carries/rushing_yards)

2. **Iterative Imputation** (`sklearn.IterativeImputer`):
   - Models each feature as a function of others
   - Good for multivariate data with complex relationships
   - Higher computational cost

3. **Sports-specific consideration**:
   - In NFL data, 0 often represents true absence (player didn't play/record stats)
   - Imputation should only apply to genuinely missing data, not semantic zeros
   - Need to distinguish: "player had 0 receptions" vs "receptions data not recorded"

### Recommendation

**Priority: MEDIUM** (current approach works but suboptimal)

**Recommended action for Phase 12:**

1. **Audit data to distinguish true zeros from missing:**
   - If player appears in game but stat is null = missing (impute)
   - If player didn't play or stat is recorded as 0 = true zero (keep as 0)

2. **Evaluate KNN imputation for non-zero historical values:**
   - Add `imputation.py` module with KNN option
   - Wrap in sklearn Pipeline to prevent data leakage
   - Test impact on model accuracy

3. **Defer IterativeImputer:**
   - Higher complexity, marginal benefit over KNN
   - Consider only if KNN shows significant improvement

**Implementation complexity:** LOW-MEDIUM (~100 LOC, 1 new file)

**Risk:** LOW - can A/B test against current approach

---

## Model Architecture

### Current Configuration

The model architecture (`packages/backend/src/lineupiq/models/`) uses **XGBoost with Optuna hyperparameter tuning** and **TimeSeriesSplit validation**.

**Key files:**
- `training.py`: Core training infrastructure with Optuna + XGBoost
- `qb.py`, `rb.py`, `receiver.py`: Position-specific model training

**XGBoost Search Space (training.py lines 72-81):**

```python
params = {
    "max_depth": trial.suggest_int("max_depth", 3, 9),
    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
    "n_estimators": trial.suggest_int("n_estimators", 100, 500),
    "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
    "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
    "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
}
```

**Validation approach:**
- `TimeSeriesSplit` with `n_splits=5` (default)
- Cross-validation scoring with `neg_root_mean_squared_error`
- Final model fit on full training data

### Current Strengths

| Strength | Details |
|----------|---------|
| **Proper temporal validation** | TimeSeriesSplit prevents data leakage |
| **Solid search space** | Good regularization range (reg_alpha, reg_lambda) |
| **Reproducibility** | Uses `random_state=42` |
| **Optuna pruning** | Efficient hyperparameter search |

### Identified Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| **No LightGBM option** | LOW | Missing 7x speedup potential and better categorical handling |
| **No ensemble support** | LOW | Research shows 10-20% accuracy gains from stacking |
| **No native categorical handling** | LOW | Team/opponent IDs encoded manually instead of native support |
| **Single objective** | LOW | Only RMSE, no multi-objective optimization |

### Research Recommendations

1. **LightGBM integration:**
   - Add LightGBM as alternative to XGBoost
   - 7x faster training enables more Optuna trials
   - Native categorical handling for team IDs

2. **Stacking ensemble (deferred):**
   - Combine XGBoost + LightGBM + CatBoost with meta-learner
   - Research shows 10-20% accuracy gains in sports prediction
   - Higher complexity - defer until single models optimized

---

## Feature Engineering

### Current Features (17 total)

The feature pipeline (`packages/backend/src/lineupiq/features/`) produces 17 features across 4 categories:

**Rolling Features (8)** - `rolling_stats.py`:
- `passing_yards_roll3`, `passing_tds_roll3`
- `rushing_yards_roll3`, `rushing_tds_roll3`, `carries_roll3`
- `receiving_yards_roll3`, `receiving_tds_roll3`, `receptions_roll3`

**Opponent Features (5)** - `opponent_features.py`:
- `opp_pass_defense_strength`, `opp_rush_defense_strength`
- `opp_pass_yards_allowed_rank`, `opp_rush_yards_allowed_rank`
- `opp_total_yards_allowed_rank`

**Weather Features (2)** - `processing.py`:
- `temp_normalized`, `wind_normalized`

**Context Features (2)** - `processing.py`:
- `is_home`, `is_dome`

### Identified Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| **Static 3-game window** | MEDIUM | Doesn't adapt to player tenure (rookies vs veterans) |
| **No team offensive strength** | MEDIUM | Player performance depends on team context |
| **No player consistency metrics** | MEDIUM | High-variance vs consistent players need different handling |
| **No exponential moving average** | LOW | EMA weights recent games more heavily |
| **No rest days feature** | LOW | Short weeks affect performance |

### Recommended New Features

1. **Team offensive strength:**
   - Offense points per game (rolling)
   - Offensive line ranking
   - Pace of play (plays per game)

2. **Player consistency metrics:**
   - Standard deviation of rolling stats
   - Coefficient of variation (CV = std/mean)
   - Streak indicators (consecutive good/bad games)

3. **Dynamic windows (deferred):**
   - Adaptive window based on games played
   - EMA instead of simple moving average
   - Higher complexity - measure baseline first

---

## Evaluation Gaps

### Current Evaluation Capabilities

The evaluation module (`packages/backend/src/lineupiq/models/`) provides solid baseline metrics:

**evaluation.py:**
- MAE, RMSE, R2, MAPE calculation
- Holdout split by season
- All-model evaluation

**diagnostics.py:**
- Train/test RMSE ratio
- Overfitting detection
- Recommendations based on fit status

### Critical Gap: No Prediction Intervals

**Current state:** Models output point predictions only.

**Why this matters:**
- Users can't assess prediction confidence
- High-variance players (boom/bust WRs) look the same as consistent players
- No way to communicate uncertainty to end users
- Fantasy football decisions need confidence context

### Research Findings (from 11-RESEARCH.md)

1. **MAPIE library for conformal prediction:**
   - Provides prediction intervals with statistical guarantees
   - Conformalized Quantile Regression (CQR) adapts to heteroscedasticity
   - High-variance players get wider intervals automatically

2. **Implementation pattern:**
   ```python
   from mapie.regression import MapieQuantileRegressor

   mapie_qr = MapieQuantileRegressor(
       estimator=xgb_model,
       method="quantile",
       alpha=0.1,  # 90% confidence intervals
   )
   mapie_qr.fit(X_train, y_train)
   y_pred, y_intervals = mapie_qr.predict(X_test)
   ```

3. **Calibration validation:**
   - Need `regression_coverage_score` to verify intervals achieve nominal coverage
   - Track mean interval width for different player types

### Recommendation

**Priority: HIGH** - This is the biggest gap in the current pipeline.

**Phase 12 action:**
1. Add `uncertainty.py` module with MAPIE integration
2. Add `calibration.py` for interval validation
3. Update API to return prediction intervals
4. Update UI to display confidence bounds

**Implementation complexity:** LOW (~100 LOC, 1-2 new files)

**Risk:** LOW - MAPIE is battle-tested, minimal code changes

---
