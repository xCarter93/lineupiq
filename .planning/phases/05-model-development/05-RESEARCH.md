# Phase 5: Model Development - Research

**Researched:** 2026-01-15
**Domain:** ML models for fantasy football stat prediction (XGBoost/gradient boosting)
**Confidence:** HIGH

<research_summary>
## Summary

Researched machine learning approaches for predicting NFL player statistics. The standard approach uses gradient boosting (XGBoost or LightGBM) with position-specific models, Optuna for hyperparameter tuning, TimeSeriesSplit for temporal cross-validation, and SHAP for feature importance analysis.

Key finding: Don't hand-roll cross-validation for time series data. Standard k-fold will leak future data into training, causing inflated metrics that collapse in production. Use scikit-learn's TimeSeriesSplit or walk-forward validation.

**Primary recommendation:** Use XGBoost with position-specific models (QB, RB, WR, TE), Optuna for hyperparameter tuning with ~100 trials, TimeSeriesSplit for validation, and joblib for model persistence. Start with single-output models per stat before considering multi-output.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | 2.1+ | Gradient boosting regressor | Best balance of speed/accuracy for tabular data, native multi-output support |
| scikit-learn | 1.4+ | ML utilities, cross-validation, metrics | Industry standard, TimeSeriesSplit for temporal data |
| optuna | 3.6+ | Hyperparameter optimization | Bayesian optimization, pruning, XGBoost integration |
| shap | 0.45+ | Feature importance analysis | Consistent, accurate feature attribution vs built-in gain |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | 1.3+ | Model persistence | Efficient for large numpy arrays in sklearn pipelines |
| polars | 1.0+ | Data manipulation | Already used in feature pipeline, keep consistent |
| matplotlib | 3.8+ | Visualization | Training curves, feature importance plots |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| XGBoost | LightGBM | LightGBM faster but more prone to overfit on small data |
| XGBoost | CatBoost | CatBoost best for categorical features, but our data is mostly numeric |
| Optuna | GridSearch | GridSearch exhaustive but slow, Optuna more efficient |
| SHAP | Built-in gain | Built-in methods inconsistent, SHAP theoretically grounded |

**Installation:**
```bash
uv add xgboost optuna shap joblib matplotlib
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
packages/backend/src/lineupiq/models/
├── __init__.py           # Exports train_models, load_models, predict
├── training.py           # Training pipeline, hyperparameter tuning
├── persistence.py        # Model save/load with joblib
├── prediction.py         # Inference API
└── evaluation.py         # Metrics, cross-validation, SHAP analysis
```

### Pattern 1: Position-Specific Models
**What:** Train separate models per position (QB, RB, WR, TE)
**When to use:** Different positions have different stat distributions and feature importance
**Example:**
```python
# Source: Multiple NFL ML projects on GitHub
POSITION_TARGETS = {
    "QB": ["passing_yards", "passing_tds"],
    "RB": ["rushing_yards", "rushing_tds", "receiving_yards"],
    "WR": ["receiving_yards", "receiving_tds", "receptions"],
    "TE": ["receiving_yards", "receiving_tds", "receptions"],
}

def train_position_models(df: pl.DataFrame, position: str) -> dict[str, XGBRegressor]:
    """Train one model per target stat for a position."""
    targets = POSITION_TARGETS[position]
    models = {}
    for target in targets:
        model = XGBRegressor(...)
        model.fit(X, y[target])
        models[target] = model
    return models
```

### Pattern 2: TimeSeriesSplit Cross-Validation
**What:** Temporal cross-validation that respects time ordering
**When to use:** Always for sports/time-series data to avoid data leakage
**Example:**
```python
# Source: scikit-learn documentation
from sklearn.model_selection import TimeSeriesSplit

def temporal_cross_validate(model, X, y, n_splits=5):
    """Walk-forward validation respecting temporal order."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        model.fit(X_train, y_train)
        scores.append(model.score(X_val, y_val))
    return scores
```

### Pattern 3: Optuna Hyperparameter Tuning
**What:** Bayesian optimization with pruning for efficient tuning
**When to use:** Always - proper tuning matters more than model choice
**Example:**
```python
# Source: Optuna XGBoost integration docs
import optuna
from optuna.integration import XGBoostPruningCallback

def objective(trial):
    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 9),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
    }
    model = XGBRegressor(**params, callbacks=[XGBoostPruningCallback(trial, "validation_0-rmse")])
    # ... cross-validate and return score
    return score

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=100)
```

### Anti-Patterns to Avoid
- **K-Fold CV on time series:** Leaks future data, inflates metrics by 20%+
- **Global model for all positions:** Different positions have different feature importance
- **Grid search without pruning:** Wastes compute on bad hyperparameter regions
- **Using built-in feature importance:** Inconsistent results, prefer SHAP
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hyperparameter tuning | Manual grid loops | Optuna | Bayesian optimization is 10x more efficient |
| Time series CV | Custom train/test splits | TimeSeriesSplit | Easy to accidentally leak future data |
| Feature importance | Manual correlation analysis | SHAP | Theoretically grounded, handles interactions |
| Model persistence | Raw pickle | joblib + version pinning | Better for numpy arrays, need version control |
| Early stopping | Custom epoch tracking | XGBoost eval_set | Built-in is battle-tested |

**Key insight:** NFL player data has ~20 years of history with ~17 weeks/season = ~340 data points per player at most. With small datasets, proper validation methodology matters more than model complexity. Hand-rolled solutions tend to have subtle bugs that inflate apparent performance.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Temporal Data Leakage
**What goes wrong:** Model achieves 90%+ accuracy in development, fails in production
**Why it happens:** K-fold CV uses future games to predict past games
**How to avoid:** Use TimeSeriesSplit exclusively. Train on weeks 1-N, validate on week N+1
**Warning signs:** Suspiciously high R2 scores (>0.7), validation > test performance

### Pitfall 2: Overfitting on Small Samples
**What goes wrong:** Model memorizes player histories instead of learning patterns
**Why it happens:** NFL has limited games per player per season (~17)
**How to avoid:** Strong regularization (max_depth 3-6, min_child_weight 5-20), early stopping
**Warning signs:** Training R2 >> validation R2, performance drops on new season data

### Pitfall 3: Position Aggregation
**What goes wrong:** Model predicts QB stats for RBs or vice versa
**Why it happens:** Single model averages across positions with different stat distributions
**How to avoid:** Train separate models per position, filter data appropriately
**Warning signs:** Unrealistic predictions (QB with 200 rushing yards)

### Pitfall 4: Feature Importance Misinterpretation
**What goes wrong:** Removing "unimportant" features hurts model
**Why it happens:** Built-in XGBoost importance (gain/cover/weight) are inconsistent
**How to avoid:** Use SHAP values for feature analysis, don't blindly remove low-importance features
**Warning signs:** Conflicting importance rankings from different methods

### Pitfall 5: Ignoring Calibration
**What goes wrong:** Predictions are systematically biased (always too high/low)
**Why it happens:** Optimizing for RMSE doesn't guarantee unbiased predictions
**How to avoid:** Check residual plots, verify predictions center around actuals
**Warning signs:** Mean prediction != mean actual, residuals correlate with features
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### XGBoost with Early Stopping
```python
# Source: XGBoost documentation
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)  # shuffle=False for time series

model = XGBRegressor(
    n_estimators=1000,
    max_depth=6,
    learning_rate=0.1,
    early_stopping_rounds=50,
    eval_metric="rmse"
)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)
```

### SHAP Feature Importance
```python
# Source: SHAP documentation
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Summary plot
shap.summary_plot(shap_values, X_test, feature_names=feature_names)

# Single prediction explanation
shap.force_plot(explainer.expected_value, shap_values[0], X_test[0])
```

### Model Persistence with joblib
```python
# Source: scikit-learn documentation
import joblib
from pathlib import Path

def save_model(model, path: Path, metadata: dict):
    """Save model with metadata for version tracking."""
    artifact = {
        "model": model,
        "metadata": metadata,
        "features": list(model.feature_names_in_),
    }
    joblib.dump(artifact, path)

def load_model(path: Path):
    """Load model and verify compatibility."""
    artifact = joblib.load(path)
    return artifact["model"], artifact["metadata"]
```

### Optuna with TimeSeriesSplit
```python
# Source: Optuna + scikit-learn integration
import optuna
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from xgboost import XGBRegressor

def objective(trial):
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

    model = XGBRegressor(**params, random_state=42)
    tscv = TimeSeriesSplit(n_splits=5)

    scores = cross_val_score(model, X, y, cv=tscv, scoring="neg_root_mean_squared_error")
    return -scores.mean()

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=100, show_progress_bar=True)
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GridSearchCV | Optuna Bayesian | 2020+ | 10x faster tuning, better results |
| K-Fold CV | TimeSeriesSplit | Always for time series | Prevents 20%+ metric inflation from leakage |
| Single global model | Position-specific | Best practice | Better predictions, interpretable |
| Built-in importance | SHAP values | 2019+ | Consistent, theoretically grounded |
| Pickle persistence | joblib + metadata | Best practice | Better numpy handling, version tracking |

**New tools/patterns to consider:**
- **XGBoost 2.0+ multi-output:** Native support for predicting multiple targets simultaneously (experimental)
- **Optuna pruning callbacks:** Early termination of unpromising trials saves 50%+ compute
- **SHAP TreeExplainer:** Fast exact SHAP values for tree models

**Deprecated/outdated:**
- **Manual train/test splits for time series:** Use TimeSeriesSplit
- **GridSearchCV for large spaces:** Use Optuna for efficiency
- **Pickle without version pinning:** Models break across sklearn/xgboost versions
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Single vs Multi-Output Models**
   - What we know: XGBoost 2.0+ has experimental multi-output support
   - What's unclear: Whether shared learning across targets improves predictions for NFL stats
   - Recommendation: Start with single-output models per stat, benchmark against multi-output later

2. **Optimal Number of Training Seasons**
   - What we know: More data generally helps, but NFL rules/strategies change over time
   - What's unclear: Whether 10+ year old data helps or hurts modern predictions
   - Recommendation: Start with 5-7 recent seasons, experiment with expanding

3. **Player-Level Features vs Population Features**
   - What we know: Rolling stats capture individual player trends
   - What's unclear: Whether player-specific models (one per player) outperform position models
   - Recommendation: Use position models (more data per model), add player embeddings if needed later
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [XGBoost Documentation](https://xgboost.readthedocs.io/) - Multi-output, parameters, persistence
- [scikit-learn Model Persistence](https://scikit-learn.org/stable/model_persistence.html) - joblib best practices
- [Optuna Documentation](https://optuna.org/) - Hyperparameter optimization
- [SHAP Documentation](https://shap.readthedocs.io/) - Feature importance

### Secondary (MEDIUM confidence)
- [Neptune.ai XGBoost vs LightGBM](https://neptune.ai/blog/xgboost-vs-lightgbm) - Algorithm comparison, verified with docs
- [XGBoost Hyperparameter Tuning Guide](https://randomrealizations.com/posts/xgboost-parameter-tuning-with-optuna/) - Optuna integration patterns
- [Towards Data Science - Time Series Leakage](https://towardsdatascience.com/avoiding-data-leakage-in-timeseries-101-25ea13fcb15f/) - Temporal CV best practices
- [GitHub NFL ML Projects](https://github.com/zzhangusf/Predicting-Fantasy-Football-Points-Using-Machine-Learning) - Position-specific model patterns

### Tertiary (LOW confidence - needs validation)
- Sports betting research on calibration vs accuracy - interesting but our goal is stat prediction, not betting
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: XGBoost gradient boosting for regression
- Ecosystem: scikit-learn, Optuna, SHAP, joblib
- Patterns: Position-specific models, temporal CV, Bayesian tuning
- Pitfalls: Data leakage, overfitting, feature importance

**Confidence breakdown:**
- Standard stack: HIGH - verified with official documentation
- Architecture: HIGH - from official examples and established projects
- Pitfalls: HIGH - documented in academic papers and industry sources
- Code examples: HIGH - from official documentation

**Research date:** 2026-01-15
**Valid until:** 2026-02-15 (30 days - XGBoost/sklearn ecosystem stable)
</metadata>

---

*Phase: 05-model-development*
*Research completed: 2026-01-15*
*Ready for planning: yes*
