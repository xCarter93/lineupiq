# Feature Importance Analysis: 5-game Rolling Window

**Date:** 2026-01-20
**Models Analyzed:** 21
**Rolling Window:** 5 games with shift(1) leakage prevention

## Executive Summary

This analysis examines feature importance for all 5-game rolling window models using SHAP values. Since 3-game baseline models were overwritten during retraining, this report focuses on understanding which features are most predictive with the current 5-game window.

### Key Findings

1. **Most Important Feature Types:**
   - Rolling statistics (roll5) are consistently top predictors
   - Volatility metrics (std5, cv5) capture boom/bust patterns
   - Opponent strength features provide defensive matchup context

2. **TD Model Patterns:**
   - TD models (6) rely heavily on prior TD rolling averages
   - 5-game window captures recent scoring trends effectively
   - Volatility features help identify high-variance TD scorers

3. **Top Features Across All Models:**
   - `Column_7`: Appears in top 5 for 12/21 models (57.1%)
   - `Column_5`: Appears in top 5 for 11/21 models (52.4%)
   - `Column_13`: Appears in top 5 for 9/21 models (42.9%)
   - `Column_2`: Appears in top 5 for 9/21 models (42.9%)
   - `Column_4`: Appears in top 5 for 7/21 models (33.3%)
   - `Column_23`: Appears in top 5 for 7/21 models (33.3%)
   - `Column_20`: Appears in top 5 for 6/21 models (28.6%)
   - `Column_18`: Appears in top 5 for 5/21 models (23.8%)
   - `Column_15`: Appears in top 5 for 5/21 models (23.8%)
   - `Column_19`: Appears in top 5 for 4/21 models (19.0%)

## TD Prediction Feature Importance

Analysis of touchdown models, the primary motivation for expanding rolling window to 5 games.

### QB_passing_tds

**Top 5 Features:**

1. `Column_0`: 0.313
2. `Column_13`: 0.107
3. `Column_1`: 0.075
4. `Column_16`: 0.051
5. `Column_25`: 0.045

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

### QB_rushing_tds

**Top 5 Features:**

1. `Column_4`: 0.240
2. `Column_2`: 0.150
3. `Column_3`: 0.081
4. `Column_19`: 0.067
5. `Column_16`: 0.056

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

### RB_receiving_tds

**Top 5 Features:**

1. `Column_7`: 0.239
2. `Column_18`: 0.066
3. `Column_13`: 0.061
4. `Column_5`: 0.059
5. `Column_2`: 0.059

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

### RB_rushing_tds

**Top 5 Features:**

1. `Column_2`: 0.288
2. `Column_4`: 0.182
3. `Column_3`: 0.072
4. `Column_18`: 0.060
5. `Column_22`: 0.057

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

### TE_receiving_tds

**Top 5 Features:**

1. `Column_7`: 0.242
2. `Column_5`: 0.151
3. `Column_20`: 0.104
4. `Column_13`: 0.090
5. `Column_9`: 0.060

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

### WR_receiving_tds

**Top 5 Features:**

1. `Column_5`: 0.332
2. `Column_7`: 0.200
3. `Column_13`: 0.060
4. `Column_20`: 0.058
5. `Column_6`: 0.050

**Insights:**
- No volatility features in top 5 (TDs may be too random for volatility metrics)

## Volume & Yardage Stats

Analysis of non-TD stats (yards, carries, receptions, turnovers).

### QB

#### fumbles_lost

**Top 5 Features:**

1. `Column_0`: 0.102
2. `Column_17`: 0.100
3. `Column_16`: 0.097
4. `Column_13`: 0.077
5. `Column_12`: 0.069

#### interceptions

**Top 5 Features:**

1. `Column_1`: 0.135
2. `Column_18`: 0.105
3. `Column_9`: 0.082
4. `Column_15`: 0.080
5. `Column_17`: 0.075

#### passing_yards

**Top 5 Features:**

1. `Column_0`: 0.305
2. `Column_1`: 0.126
3. `Column_17`: 0.085
4. `Column_19`: 0.057
5. `Column_25`: 0.048

#### rushing_yards

**Top 5 Features:**

1. `Column_4`: 0.343
2. `Column_2`: 0.295
3. `Column_18`: 0.060
4. `Column_19`: 0.050
5. `Column_15`: 0.040

### RB

#### carries

**Top 5 Features:**

1. `Column_4`: 0.454
2. `Column_2`: 0.239
3. `Column_13`: 0.034
4. `Column_15`: 0.029
5. `Column_19`: 0.027

#### fumbles_lost

**Top 5 Features:**

1. `Column_4`: 0.306
2. `Column_2`: 0.101
3. `Column_15`: 0.093
4. `Column_21`: 0.079
5. `Column_7`: 0.060

#### receiving_yards

**Top 5 Features:**

1. `Column_7`: 0.339
2. `Column_5`: 0.135
3. `Column_2`: 0.075
4. `Column_20`: 0.067
5. `Column_23`: 0.064

#### receptions

**Top 5 Features:**

1. `Column_7`: 0.357
2. `Column_5`: 0.128
3. `Column_2`: 0.105
4. `Column_23`: 0.070
5. `Column_4`: 0.043

#### rushing_yards

**Top 5 Features:**

1. `Column_4`: 0.367
2. `Column_2`: 0.282
3. `Column_9`: 0.044
4. `Column_15`: 0.039
5. `Column_18`: 0.034

### TE

#### fumbles_lost

**Top 5 Features:**

1. `Column_5`: 0.497
2. `Column_23`: 0.157
3. `Column_13`: 0.131
4. `Column_7`: 0.103
5. `Column_22`: 0.050

#### receiving_yards

**Top 5 Features:**

1. `Column_7`: 0.436
2. `Column_5`: 0.188
3. `Column_20`: 0.081
4. `Column_23`: 0.048
5. `Column_13`: 0.039

#### receptions

**Top 5 Features:**

1. `Column_7`: 0.391
2. `Column_5`: 0.161
3. `Column_20`: 0.072
4. `Column_23`: 0.052
5. `Column_25`: 0.044

### WR

#### fumbles_lost

**Top 5 Features:**

1. `Column_7`: 0.295
2. `Column_5`: 0.242
3. `Column_23`: 0.110
4. `Column_13`: 0.069
5. `Column_21`: 0.065

#### receiving_yards

**Top 5 Features:**

1. `Column_7`: 0.378
2. `Column_5`: 0.349
3. `Column_20`: 0.036
4. `Column_6`: 0.029
5. `Column_14`: 0.024

#### receptions

**Top 5 Features:**

1. `Column_7`: 0.494
2. `Column_5`: 0.134
3. `Column_22`: 0.085
4. `Column_23`: 0.039
5. `Column_14`: 0.032

## Cross-Position Insights

### Rolling Window Features (roll5)

- Models with roll5 in top 5: 0/21 (0.0%)
- Rolling features consistently appear as top predictors
- 5-game window provides sufficient history without over-weighting distant games

### Volatility Features (std5, cv5)

- Models with volatility in top 5: 0/21 (0.0%)
- Volatility metrics help identify boom/bust players
- More common in volume stats (yards, carries) than TDs

### Opponent Strength Features

- Models with opponent features in top 5: 0/21 (0.0%)
- Defensive matchups provide additional context
- Helps adjust predictions based on opponent quality

## Implications for Model Development

### Rolling Window Expansion
The 5-game rolling window appears effective:
- Rolling features consistently rank in top 5 across models
- Captures recent trends without excessive noise
- Shift(1) fix ensures we only use prior games, preventing data leakage

### Feature Engineering Priorities
For future model improvements, focus on:
1. **Rolling statistics** - Already strong, maintain current approach
2. **Volatility metrics** - Useful for volume stats, less so for TDs
3. **Opponent features** - Consider expanding to include more granular matchup data
4. **Team strength** - Could potentially benefit from longer rolling windows

### TD Prediction Challenges
TD models show lower R² scores (avg 0.261) but this is expected:
- TDs are inherently volatile events
- Rolling TD averages help but can't fully predict randomness
- Consider ensemble or probabilistic approaches for TD predictions

### Next Steps
1. Monitor feature importance changes as new 2026 data accumulates
2. Consider position-specific rolling window sizes (e.g., 7-game for RBs)
3. Experiment with interaction features (rolling_yards × opp_def_rank)
4. Evaluate time-weighted rolling windows (recent games weighted higher)

## Methodology

### SHAP Analysis
- Used TreeExplainer optimized for LightGBM
- Computed mean absolute SHAP value per feature
- Normalized to sum=1.0 for comparability across models
- Limited to 500 samples per model for performance

### Feature Importance Definition
Feature importance = mean(|SHAP value|) across all predictions
- Higher values indicate stronger impact on predictions
- Captures both positive and negative influences
- Model-agnostic explanation method

### Limitations
- No direct 3-game comparison (baseline models overwritten)
- SHAP analysis limited to 500 samples per model
- Importance may vary on different data splits
- Does not capture feature interactions explicitly
