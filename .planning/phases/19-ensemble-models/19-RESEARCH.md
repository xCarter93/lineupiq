# Phase 19: Ensemble Models - Research

**Researched:** 2026-01-20
**Domain:** Ensemble methods for gradient boosting regression (LightGBM + XGBoost)
**Confidence:** HIGH

<research_summary>
## Summary

Researched ensemble methods for combining LightGBM and XGBoost models in regression tasks. The standard approach is scikit-learn's `StackingRegressor` or `VotingRegressor`, with three main strategies: simple averaging (voting), weighted blending, and stacking with a meta-learner.

Key finding: Ensembles are NOT guaranteed to outperform single models. Success requires model diversity (different algorithms with complementary strengths), proper validation (cross-validation to prevent overfitting), and evidence-based selection (backtest to prove improvement on holdout data). Simple averaging often performs nearly as well as stacking at lower computational cost.

The project already has LightGBM and XGBoost models for each stat (Phase 13), providing natural diversity due to different tree-building strategies (leaf-wise vs level-wise growth). The standard approach is to benchmark all three strategies (averaging, weighted, stacking) on holdout data and choose based on MAE/R² metrics.

**Primary recommendation:** Start with simple averaging (VotingRegressor), benchmark against weighted averaging and stacking (StackingRegressor with Ridge meta-learner), use 2024 holdout season for validation, adopt ensemble only if it demonstrably beats best single model.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for ensemble regression:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.8.0 | VotingRegressor, StackingRegressor | Industry standard, proven ensemble infrastructure |
| xgboost | Latest | Base estimator (level-wise tree growth) | Already in project, provides diversity vs LightGBM |
| lightgbm | Latest | Base estimator (leaf-wise tree growth) | Already in project, 7x faster than XGBoost |
| MAPIE | 1.2.0 | Conformal prediction for ensembles | Already in project (Phase 12), model-agnostic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Ridge (sklearn) | 1.8.0 | Meta-learner for stacking | Default final estimator, handles correlated predictions |
| LinearRegression (sklearn) | 1.8.0 | Alternative meta-learner | Simpler, lower overfitting risk for small meta-data |
| numpy | Latest | Weighted averaging implementation | Custom blending when VotingRegressor weights insufficient |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| StackingRegressor | VotingRegressor | Voting simpler/faster, stacking may perform better |
| Ridge meta-learner | LinearRegression | Ridge better for correlated base predictions |
| scikit-learn | mlxtend StackingCVRegressor | scikit-learn more maintained, sufficient for use case |

**Installation:**
```bash
# Already installed in project
pip install scikit-learn xgboost lightgbm MAPIE
```

**Note:** All required libraries already present in `packages/backend/pyproject.toml`.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
packages/backend/src/lineupiq/models/
├── ensemble.py          # Ensemble training and inference
├── qb.py                # Existing QB models
├── rb.py                # Existing RB models
├── receiver.py          # Existing receiver models
├── kicker.py            # Existing kicker models
├── defense.py           # Existing defense models
└── persistence.py       # Model save/load (extend for ensembles)
```

### Pattern 1: Simple Averaging with VotingRegressor
**What:** Average predictions from LightGBM and XGBoost without weights
**When to use:** Starting point, baseline comparison, models have similar performance
**Example:**
```python
# Source: scikit-learn official docs
from sklearn.ensemble import VotingRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

# Load pre-trained models or train new ones
lgbm_model = LGBMRegressor(**lgbm_params)
xgb_model = XGBRegressor(**xgb_params)

# Create voting regressor
voting_reg = VotingRegressor(
    estimators=[
        ('lgbm', lgbm_model),
        ('xgb', xgb_model)
    ]
)

# Fit on training data
voting_reg.fit(X_train, y_train)

# Predict (returns average of both models)
y_pred = voting_reg.predict(X_test)
```

### Pattern 2: Weighted Averaging with VotingRegressor
**What:** Average predictions with custom weights based on validation performance
**When to use:** One model consistently outperforms the other
**Example:**
```python
# Source: scikit-learn VotingRegressor docs
# Determine weights from validation set performance
# e.g., if LightGBM MAE=3.5, XGBoost MAE=4.0
# weights inversely proportional: [1/3.5, 1/4.0] normalized

voting_reg = VotingRegressor(
    estimators=[
        ('lgbm', lgbm_model),
        ('xgb', xgb_model)
    ],
    weights=[0.53, 0.47]  # LightGBM gets 53%, XGBoost 47%
)

voting_reg.fit(X_train, y_train)
y_pred = voting_reg.predict(X_test)
```

### Pattern 3: Stacking with Ridge Meta-Learner
**What:** Train meta-model on cross-validated predictions from base models
**When to use:** Base models have complementary strengths, willing to pay computational cost
**Example:**
```python
# Source: scikit-learn StackingRegressor docs
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge

stacking_reg = StackingRegressor(
    estimators=[
        ('lgbm', lgbm_model),
        ('xgb', xgb_model)
    ],
    final_estimator=Ridge(alpha=1.0),
    cv=5,  # 5-fold CV for meta-learner training
    passthrough=False  # Use only base predictions, not original features
)

stacking_reg.fit(X_train, y_train)
y_pred = stacking_reg.predict(X_test)
```

### Pattern 4: Using Pre-Trained Models with cv="prefit"
**What:** Stack already-trained models without refitting
**When to use:** Models already optimized via Optuna (existing in project)
**Example:**
```python
# Source: scikit-learn StackingRegressor docs
# Load pre-trained models
lgbm_fitted = joblib.load('models/qb_passing_yards_lgbm.joblib')
xgb_fitted = joblib.load('models/qb_passing_yards_xgb.joblib')

stacking_reg = StackingRegressor(
    estimators=[
        ('lgbm', lgbm_fitted),
        ('xgb', xgb_fitted)
    ],
    final_estimator=Ridge(alpha=1.0),
    cv="prefit"  # Don't refit base models
)

# Fit only the meta-learner on full training set predictions
stacking_reg.fit(X_train, y_train)
```
**⚠️ Warning:** `cv="prefit"` risks overfitting if base models trained on same data. Use with caution.

### Pattern 5: MAPIE Compatibility for Prediction Intervals
**What:** Wrap ensemble in MAPIE for conformal prediction intervals
**When to use:** After selecting best ensemble, to provide uncertainty estimates
**Example:**
```python
# Source: MAPIE documentation + Phase 12 implementation
from mapie.regression import MapieRegressor

# Wrap ensemble (voting or stacking)
mapie_ensemble = MapieRegressor(
    estimator=voting_reg,  # or stacking_reg
    cv=5,
    method="plus"  # Split conformal (Phase 12 decision)
)

mapie_ensemble.fit(X_train, y_train)

# Get predictions with intervals
y_pred, y_intervals = mapie_ensemble.predict(X_test, alpha=0.1)
```

### Anti-Patterns to Avoid
- **Using identical models in ensemble:** No diversity = no benefit over single model
- **Stacking without CV:** Training meta-learner on same data as base models causes severe overfitting
- **Assuming ensembles are always better:** Backtest first; sometimes single model wins
- **Over-weighting weak models:** If one model consistently underperforms, consider dropping it entirely
- **Passthrough=True without justification:** Doubles feature space, risks overfitting for high-dim data
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-validated stacking | Manual K-fold loop + meta-training | StackingRegressor with cv=5 | Handles train/predict split, prevents data leakage |
| Simple averaging | Custom np.mean() wrapper | VotingRegressor | Integrates with sklearn pipelines, supports fit/predict API |
| Weighted averaging optimization | Grid search over weights | VotingRegressor + validation holdout | Built-in sklearn interface, cleaner code |
| Prediction interval ensembles | Custom interval aggregation | MAPIE with ensemble estimator | Proven conformal prediction, model-agnostic |
| Ensemble persistence | Custom multi-model save/load | StackingRegressor + joblib | Single file, handles base + meta-learner |

**Key insight:** Ensemble infrastructure is subtle. Cross-validation splits, data leakage prevention, and proper meta-learner training have edge cases. scikit-learn's implementations are battle-tested across thousands of use cases. Don't reinvent unless you have specific requirements sklearn can't meet.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Assuming Ensembles Always Improve Performance
**What goes wrong:** Ensemble performs worse than best single model
**Why it happens:** Lack of model diversity - if models make similar errors, averaging doesn't help
**How to avoid:**
- Use different algorithms (LightGBM leaf-wise vs XGBoost level-wise) ✅ Already have this
- Verify diversity: check correlation between base model predictions on validation set
- Backtest rigorously: compare ensemble MAE/R² vs single model on holdout data
**Warning signs:** Ensemble R² < max(single model R²), high correlation (>0.95) between base predictions

### Pitfall 2: Overfitting the Meta-Learner
**What goes wrong:** Stacking performs great on training data, terrible on test data
**Why it happens:** Meta-learner trained on same data used to train base models, or cv="prefit" misuse
**How to avoid:**
- Use cv=5 (not cv="prefit") in StackingRegressor to generate out-of-fold predictions
- Keep meta-learner simple: Ridge or LinearRegression, not complex models
- Use regularization: Ridge alpha=1.0 prevents overfitting to correlated base predictions
**Warning signs:** Large gap between train and validation R², meta-learner coefficients unstable

### Pitfall 3: Ignoring Computational Cost
**What goes wrong:** Training time explodes, inference too slow for production
**Why it happens:** Stacking with cv=5 trains each base model 5 times, then fits meta-learner
**How to avoid:**
- Start with VotingRegressor (cheapest), benchmark stacking only if needed
- Use cv="prefit" only if you're reusing already-optimized models AND aware of overfitting risk
- For inference: pre-compute ensemble predictions, cache results in Convex
**Warning signs:** Training time >2x single model, prediction latency unacceptable for API

### Pitfall 4: Poor Quality Base Models
**What goes wrong:** Ensemble inherits weaknesses from bad base models
**Why it happens:** "Garbage in, garbage out" - ensemble can't fix fundamentally weak models
**How to avoid:**
- Ensure each base model has reasonable individual performance (R² > 0.5)
- Don't include models with error rate >50% (worse than random guessing)
- Phase 13 models already validated ✅ Can proceed confidently
**Warning signs:** All base models have poor R² individually

### Pitfall 5: Not Backtesting Properly
**What goes wrong:** Ensemble chosen based on flawed validation, performs poorly in production
**Why it happens:** Validation on same data used for hyperparameter tuning, or insufficient holdout data
**How to avoid:**
- Use Phase 13-08 methodology: 2024 as strict holdout season ✅ Already established
- Never touch holdout data during ensemble selection
- Compare ensemble vs single models on identical holdout set
**Warning signs:** Validation results differ drastically from holdout results

### Pitfall 6: Categorical Encoding Mismatch (LightGBM + XGBoost)
**What goes wrong:** StackingRegressor fails or performs poorly due to encoding differences
**Why it happens:** LightGBM uses label encoding, XGBoost needs one-hot encoding for categoricals
**How to avoid:**
- Use numerical features only (already the case in this project ✅)
- If adding categoricals: encode consistently before passing to ensemble
- Test with small dataset first to catch encoding issues early
**Warning signs:** LightGBM errors about categorical types, performance degrades with categoricals
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Example 1: Benchmark All Three Strategies
```python
# Source: Synthesized from scikit-learn docs + project Phase 13 patterns
from sklearn.ensemble import VotingRegressor, StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
import joblib

# Load pre-trained models (from Phase 13)
lgbm_model = joblib.load('models/qb_passing_yards_lgbm.joblib')
xgb_model = joblib.load('models/qb_passing_yards_xgb.joblib')

# Strategy 1: Simple Averaging
voting_simple = VotingRegressor(
    estimators=[('lgbm', lgbm_model), ('xgb', xgb_model)]
)
voting_simple.fit(X_train, y_train)
y_pred_simple = voting_simple.predict(X_holdout)

# Strategy 2: Weighted Averaging (weights from validation performance)
voting_weighted = VotingRegressor(
    estimators=[('lgbm', lgbm_model), ('xgb', xgb_model)],
    weights=[0.6, 0.4]  # Tune based on validation MAE
)
voting_weighted.fit(X_train, y_train)
y_pred_weighted = voting_weighted.predict(X_holdout)

# Strategy 3: Stacking with Ridge
stacking = StackingRegressor(
    estimators=[('lgbm', lgbm_model), ('xgb', xgb_model)],
    final_estimator=Ridge(alpha=1.0),
    cv=5
)
stacking.fit(X_train, y_train)
y_pred_stacking = stacking.predict(X_holdout)

# Compare on 2024 holdout season
results = {
    'lgbm_solo': {
        'mae': mean_absolute_error(y_holdout, lgbm_model.predict(X_holdout)),
        'r2': r2_score(y_holdout, lgbm_model.predict(X_holdout))
    },
    'xgb_solo': {
        'mae': mean_absolute_error(y_holdout, xgb_model.predict(X_holdout)),
        'r2': r2_score(y_holdout, xgb_model.predict(X_holdout))
    },
    'voting_simple': {
        'mae': mean_absolute_error(y_holdout, y_pred_simple),
        'r2': r2_score(y_holdout, y_pred_simple)
    },
    'voting_weighted': {
        'mae': mean_absolute_error(y_holdout, y_pred_weighted),
        'r2': r2_score(y_holdout, y_pred_weighted)
    },
    'stacking': {
        'mae': mean_absolute_error(y_holdout, y_pred_stacking),
        'r2': r2_score(y_holdout, y_pred_stacking)
    }
}

# Choose best performer
best_strategy = min(results, key=lambda k: results[k]['mae'])
print(f"Best strategy: {best_strategy}")
print(f"MAE: {results[best_strategy]['mae']:.2f}")
print(f"R²: {results[best_strategy]['r2']:.3f}")
```

### Example 2: Determine Optimal Weights for Weighted Averaging
```python
# Source: Community pattern, verified with sklearn VotingRegressor docs
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, RegressorMixin
import numpy as np

class WeightedVotingRegressor(BaseEstimator, RegressorMixin):
    """Custom wrapper to enable weight tuning via GridSearchCV"""
    def __init__(self, lgbm_model, xgb_model, lgbm_weight=0.5):
        self.lgbm_model = lgbm_model
        self.xgb_model = xgb_model
        self.lgbm_weight = lgbm_weight

    def fit(self, X, y):
        return self  # Models already fitted

    def predict(self, X):
        lgbm_pred = self.lgbm_model.predict(X)
        xgb_pred = self.xgb_model.predict(X)
        return self.lgbm_weight * lgbm_pred + (1 - self.lgbm_weight) * xgb_pred

# Grid search over weights
param_grid = {'lgbm_weight': np.linspace(0, 1, 21)}  # 0.0, 0.05, 0.10, ..., 1.0

grid = GridSearchCV(
    WeightedVotingRegressor(lgbm_model, xgb_model),
    param_grid,
    scoring='neg_mean_absolute_error',
    cv=5
)
grid.fit(X_val, y_val)

print(f"Optimal LightGBM weight: {grid.best_params_['lgbm_weight']:.2f}")
```

### Example 3: Ensemble Persistence Pattern
```python
# Source: scikit-learn joblib pattern
import joblib

# Save ensemble (single file includes base models + meta-learner)
joblib.dump(stacking_reg, 'models/qb_passing_yards_ensemble.joblib')

# Load and predict
ensemble = joblib.load('models/qb_passing_yards_ensemble.joblib')
predictions = ensemble.predict(X_new)
```

### Example 4: Check Base Model Diversity
```python
# Source: Best practice from ensemble learning literature
import numpy as np

# Get predictions from each base model on validation set
lgbm_preds = lgbm_model.predict(X_val)
xgb_preds = xgb_model.predict(X_val)

# Check correlation
correlation = np.corrcoef(lgbm_preds, xgb_preds)[0, 1]
print(f"Base model prediction correlation: {correlation:.3f}")

# Interpretation:
# correlation < 0.7: Good diversity, ensemble likely to help
# 0.7 <= correlation < 0.9: Moderate diversity, ensemble may help slightly
# correlation >= 0.9: Low diversity, ensemble unlikely to improve
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual ensemble code | scikit-learn StackingRegressor/VotingRegressor | 2020+ | Standardized API, less bug-prone |
| Blending (separate holdout) | Stacking (cross-validation) | 2015+ | Better use of training data, less overfitting risk |
| Complex meta-learners | Simple Ridge/LinearRegression | 2018+ | Reduced overfitting, faster training |
| Single model deployment | Ensemble as default | 2023+ | Many Kaggle winners use ensembles, but backtesting still critical |

**New tools/patterns to consider:**
- **MAPIE integration:** Conformal prediction works seamlessly with ensembles (model-agnostic)
- **cv="prefit":** Allows stacking pre-trained models, useful when base models already optimized via Optuna
- **VotingRegressor weights:** Can be tuned via validation set performance, simpler than stacking

**Deprecated/outdated:**
- **mlxtend StackingCVRegressor:** scikit-learn's StackingRegressor now has feature parity, better maintained
- **Manual blending with holdout set:** Stacking with CV uses data more efficiently
- **Heavy meta-learners (XGBoost/RF):** Simple Ridge prevents overfitting on small meta-training set

**Current best practices (2025-2026):**
- Start simple (averaging), add complexity (stacking) only if validated
- Use 5-fold CV for stacking to prevent overfitting
- Ridge with alpha=1.0 as default meta-learner
- Verify diversity (correlation < 0.9) before ensembling
- Backtest rigorously on true holdout data
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Optimal number of base models**
   - What we know: 2-3 models typical, diminishing returns beyond 5
   - What's unclear: Whether adding more diverse models (CatBoost, RandomForest) would improve accuracy
   - Recommendation: Start with LightGBM + XGBoost (already available), benchmark before adding more

2. **Ensemble for K/DEF positions**
   - What we know: Ensembles require base models with reasonable performance (R² > 0.5)
   - What's unclear: Phase 13-08 noted K/DEF have lower accuracy due to high variance - may not benefit from ensembling
   - Recommendation: Focus ensemble effort on QB/RB/WR/TE first, evaluate K/DEF ensemble value after

3. **Production inference strategy**
   - What we know: Stacking adds latency (2 models + meta-learner), averaging adds latency (2 models)
   - What's unclear: Acceptable latency for API responses, whether pre-caching in Convex is sufficient
   - Recommendation: Measure inference time during implementation, cache ensemble predictions in Convex

4. **Weighted vs stacking in practice**
   - What we know: Literature suggests stacking can improve 10-20% over single models, weighted averaging simpler
   - What's unclear: For this specific dataset (NFL player stats), which approach wins on holdout data
   - Recommendation: Benchmark all three (simple, weighted, stacking) on 2024 holdout, choose empirically
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [scikit-learn StackingRegressor API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html) - Official API reference, feature documentation
- [scikit-learn Ensemble Guide](https://scikit-learn.org/stable/modules/ensemble.html) - Official guide covering voting, stacking, boosting
- [MAPIE Documentation](https://mapie.readthedocs.io/) - Model-agnostic conformal prediction, ensemble compatibility
- [MAPIE GitHub](https://github.com/scikit-learn-contrib/MAPIE) - Official repository, scikit-learn-contrib project

### Secondary (MEDIUM confidence)
- [Ensemble Learning: Stacking, Blending & Voting - Towards Data Science](https://towardsdatascience.com/ensemble-learning-stacking-blending-voting-b37737c4f483/) - Comprehensive comparison, verified against sklearn docs
- [XGBoost vs LightGBM - Neptune.ai](https://neptune.ai/blog/xgboost-vs-lightgbm) - Model diversity analysis, hyperparameter differences
- [Stacking Ensembles: XGBoost, LightGBM - Medium](https://medium.com/@stevechesa/stacking-ensembles-combining-xgboost-lightgbm-and-catboost-to-improve-model-performance-d4247d092c2e) - Implementation patterns, verified code examples
- [When You Shouldn't Use Ensemble Learning - Deepchecks](https://www.deepchecks.com/when-you-shouldnt-use-ensemble-learning/) - Pitfalls and failure modes

### Tertiary (LOW confidence - needs validation during implementation)
- [Regression with Stacking, LightGBM, XGBoost - Kaggle](https://www.kaggle.com/code/davidrivasphd/regression-with-stacking-light-gbm-xgboost) - Community notebook, practical patterns
- [Optimal ensemble size - BigML](https://support.bigml.com/hc/en-us/articles/207310145-How-many-models-should-I-choose-to-build-a-robust-ensemble-) - General guidance on model count
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: scikit-learn ensemble methods (VotingRegressor, StackingRegressor)
- Ecosystem: LightGBM, XGBoost, Ridge, MAPIE integration
- Patterns: Simple averaging, weighted averaging, stacking with meta-learner
- Pitfalls: Lack of diversity, overfitting, computational cost, poor base models

**Confidence breakdown:**
- Standard stack: HIGH - scikit-learn is industry standard, well-documented
- Architecture: HIGH - Patterns from official docs and verified examples
- Pitfalls: HIGH - Well-documented in literature, consistent across sources
- Code examples: HIGH - Synthesized from official sklearn docs and verified community patterns
- MAPIE compatibility: MEDIUM - Documented as model-agnostic, but limited examples with ensembles specifically

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - scikit-learn ecosystem stable, LightGBM/XGBoost mature)

**Alignment with Phase 19 Context:**
- ✅ Evidence-based approach: Research emphasizes backtesting to prove ensemble value
- ✅ Benchmark all strategies: Documented simple averaging, weighted, stacking
- ✅ Prove improvement on holdout: Research highlights proper validation methodology
- ✅ Use 2024 holdout season: Aligned with Phase 13-08 backtesting approach
- ✅ Data-driven selection: Let metrics decide, not assumptions

**Integration with existing project:**
- LightGBM and XGBoost models already trained (Phase 13) ✅
- MAPIE already integrated (Phase 12) ✅
- Backtesting methodology established (Phase 13-08) ✅
- joblib persistence pattern in place ✅
- Prediction API exists (Phase 7), can extend for ensembles ✅
</metadata>

---

*Phase: 19-ensemble-models*
*Research completed: 2026-01-20*
*Ready for planning: yes*
