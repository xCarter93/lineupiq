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
