# Ensemble Benchmark Results (2025 Holdout)

**Date:** 2026-01-20
**Training Data:** 2020-2024 seasons (5 years)
**Holdout Season:** 2025
**Total Stats Benchmarked:** 21

## Executive Summary

This benchmark evaluates 5 strategies (lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking) across all skill position stats on 2025 holdout data with 5 years of training data (2020-2024).

**Comparison to 2024 Benchmark:** This uses 5 years of training data vs 2 years (2022-2023) in the original benchmark, and tests on the most recent 2025 season.

### Key Findings

1. **Model Diversity:** Average correlation between LightGBM and XGBoost predictions: 0.880
   - <0.7: Good diversity (ensemble likely helps)
   - 0.7-0.9: Moderate diversity
   - >0.9: Low diversity (ensemble unlikely to help)

2. **Ensemble Performance:** Ensembles beat best single model in 20/21 stats (95.2%)

3. **Winning Strategies:**
   - voting_weighted: 13/21 (61.9%)
   - stacking: 7/21 (33.3%)
   - xgb_solo: 1/21 (4.8%)

## Summary Table

| Position | Stat | Best Strategy | Best MAE | Best R² | Correlation | Optimal Weights |
|----------|------|---------------|----------|---------|-------------|-----------------|
| QB | passing_yards | voting_weighted | 37.94 | 0.766 | 0.958 | 0.35/0.65 |
| QB | passing_tds | stacking | 0.64 | 0.505 | 0.974 | 0.00/1.00 |
| QB | interceptions | voting_weighted | 0.62 | 0.056 | 0.674 | 0.00/1.00 |
| QB | rushing_yards | voting_weighted | 6.13 | 0.704 | 0.963 | 0.70/0.30 |
| QB | rushing_tds | stacking | 0.17 | 0.397 | 0.936 | 0.65/0.35 |
| QB | fumbles_lost | voting_weighted | 0.28 | 0.002 | 0.544 | 1.00/0.00 |
| RB | rushing_yards | stacking | 10.01 | 0.837 | 0.991 | 0.65/0.35 |
| RB | rushing_tds | voting_weighted | 0.21 | 0.474 | 0.986 | 1.00/0.00 |
| RB | carries | stacking | 1.98 | 0.839 | 0.997 | 0.35/0.65 |
| RB | receiving_yards | voting_weighted | 4.18 | 0.805 | 0.994 | 0.60/0.40 |
| RB | receptions | voting_weighted | 0.51 | 0.801 | 0.991 | 0.75/0.25 |
| RB | receiving_tds | voting_weighted | 0.07 | 0.457 | 0.972 | 0.70/0.30 |
| RB | fumbles_lost | voting_weighted | 0.07 | 0.020 | 0.850 | 1.00/0.00 |
| WR | receiving_yards | voting_weighted | 10.21 | 0.796 | 0.981 | 1.00/0.00 |
| WR | receiving_tds | voting_weighted | 0.18 | 0.473 | 0.965 | 0.10/0.90 |
| WR | receptions | stacking | 0.71 | 0.820 | 0.985 | 0.15/0.85 |
| WR | fumbles_lost | voting_weighted | 0.02 | 0.003 | 0.478 | 0.00/1.00 |
| TE | receiving_yards | voting_weighted | 7.51 | 0.811 | 0.970 | 0.60/0.40 |
| TE | receiving_tds | stacking | 0.18 | 0.432 | 0.921 | 0.00/1.00 |
| TE | receptions | stacking | 0.66 | 0.805 | 0.977 | 0.45/0.55 |
| TE | fumbles_lost | xgb_solo | 0.02 | -0.009 | 0.370 | 0.00/1.00 |

## Full Results

Detailed breakdown for each position/stat showing all 5 strategies.

### QB_passing_yards

- **Best Strategy:** voting_weighted
- **Correlation:** 0.958
- **Optimal Weights:** LightGBM=0.35, XGBoost=0.65

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 43.71 | 0.698 |
| xgb_solo | 37.96 | 0.769 |
| voting_simple | 38.04 | 0.763 |
| voting_weighted | 37.94 | 0.766 ← BEST |
| stacking | 38.20 | 0.767 |

### QB_passing_tds

- **Best Strategy:** stacking
- **Correlation:** 0.974
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.64 | 0.492 |
| xgb_solo | 0.64 | 0.504 |
| voting_simple | 0.65 | 0.499 |
| voting_weighted | 0.64 | 0.505 |
| stacking | 0.64 | 0.505 ← BEST |

### QB_interceptions

- **Best Strategy:** voting_weighted
- **Correlation:** 0.674
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.63 | -0.030 |
| xgb_solo | 0.62 | 0.048 |
| voting_simple | 0.62 | 0.019 |
| voting_weighted | 0.62 | 0.056 ← BEST |
| stacking | 0.63 | 0.058 |

### QB_rushing_yards

- **Best Strategy:** voting_weighted
- **Correlation:** 0.963
- **Optimal Weights:** LightGBM=0.70, XGBoost=0.30

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 6.60 | 0.681 |
| xgb_solo | 6.33 | 0.689 |
| voting_simple | 6.15 | 0.703 |
| voting_weighted | 6.13 | 0.704 ← BEST |
| stacking | 6.17 | 0.698 |

### QB_rushing_tds

- **Best Strategy:** stacking
- **Correlation:** 0.936
- **Optimal Weights:** LightGBM=0.65, XGBoost=0.35

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.17 | 0.363 |
| xgb_solo | 0.17 | 0.381 |
| voting_simple | 0.17 | 0.393 |
| voting_weighted | 0.17 | 0.389 |
| stacking | 0.17 | 0.397 ← BEST |

### QB_fumbles_lost

- **Best Strategy:** voting_weighted
- **Correlation:** 0.544
- **Optimal Weights:** LightGBM=1.00, XGBoost=0.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.29 | -0.057 |
| xgb_solo | 0.29 | 0.008 |
| voting_simple | 0.28 | 0.016 |
| voting_weighted | 0.28 | 0.002 ← BEST |
| stacking | 0.29 | 0.012 |

### RB_rushing_yards

- **Best Strategy:** stacking
- **Correlation:** 0.991
- **Optimal Weights:** LightGBM=0.65, XGBoost=0.35

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 10.21 | 0.827 |
| xgb_solo | 10.42 | 0.821 |
| voting_simple | 10.06 | 0.836 |
| voting_weighted | 10.05 | 0.836 |
| stacking | 10.01 | 0.837 ← BEST |

### RB_rushing_tds

- **Best Strategy:** voting_weighted
- **Correlation:** 0.986
- **Optimal Weights:** LightGBM=1.00, XGBoost=0.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.21 | 0.466 |
| xgb_solo | 0.22 | 0.476 |
| voting_simple | 0.21 | 0.484 |
| voting_weighted | 0.21 | 0.474 ← BEST |
| stacking | 0.21 | 0.485 |

### RB_carries

- **Best Strategy:** stacking
- **Correlation:** 0.997
- **Optimal Weights:** LightGBM=0.35, XGBoost=0.65

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 2.03 | 0.836 |
| xgb_solo | 2.00 | 0.838 |
| voting_simple | 1.99 | 0.839 |
| voting_weighted | 1.99 | 0.839 |
| stacking | 1.98 | 0.839 ← BEST |

### RB_receiving_yards

- **Best Strategy:** voting_weighted
- **Correlation:** 0.994
- **Optimal Weights:** LightGBM=0.60, XGBoost=0.40

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 4.33 | 0.792 |
| xgb_solo | 4.34 | 0.791 |
| voting_simple | 4.18 | 0.805 |
| voting_weighted | 4.18 | 0.805 ← BEST |
| stacking | 4.20 | 0.807 |

### RB_receptions

- **Best Strategy:** voting_weighted
- **Correlation:** 0.991
- **Optimal Weights:** LightGBM=0.75, XGBoost=0.25

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.52 | 0.786 |
| xgb_solo | 0.53 | 0.785 |
| voting_simple | 0.51 | 0.801 |
| voting_weighted | 0.51 | 0.801 ← BEST |
| stacking | 0.52 | 0.801 |

### RB_receiving_tds

- **Best Strategy:** voting_weighted
- **Correlation:** 0.972
- **Optimal Weights:** LightGBM=0.70, XGBoost=0.30

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.07 | 0.451 |
| xgb_solo | 0.07 | 0.431 |
| voting_simple | 0.07 | 0.454 |
| voting_weighted | 0.07 | 0.457 ← BEST |
| stacking | 0.07 | 0.458 |

### RB_fumbles_lost

- **Best Strategy:** voting_weighted
- **Correlation:** 0.850
- **Optimal Weights:** LightGBM=1.00, XGBoost=0.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.07 | 0.018 |
| xgb_solo | 0.07 | 0.014 |
| voting_simple | 0.07 | 0.019 |
| voting_weighted | 0.07 | 0.020 ← BEST |
| stacking | 0.07 | 0.019 |

### WR_receiving_yards

- **Best Strategy:** voting_weighted
- **Correlation:** 0.981
- **Optimal Weights:** LightGBM=1.00, XGBoost=0.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 11.02 | 0.764 |
| xgb_solo | 10.65 | 0.787 |
| voting_simple | 10.31 | 0.796 |
| voting_weighted | 10.21 | 0.796 ← BEST |
| stacking | 10.33 | 0.796 |

### WR_receiving_tds

- **Best Strategy:** voting_weighted
- **Correlation:** 0.965
- **Optimal Weights:** LightGBM=0.10, XGBoost=0.90

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.20 | 0.444 |
| xgb_solo | 0.18 | 0.468 |
| voting_simple | 0.19 | 0.471 |
| voting_weighted | 0.18 | 0.473 ← BEST |
| stacking | 0.18 | 0.474 |

### WR_receptions

- **Best Strategy:** stacking
- **Correlation:** 0.985
- **Optimal Weights:** LightGBM=0.15, XGBoost=0.85

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.78 | 0.784 |
| xgb_solo | 0.72 | 0.817 |
| voting_simple | 0.72 | 0.818 |
| voting_weighted | 0.71 | 0.820 |
| stacking | 0.71 | 0.820 ← BEST |

### WR_fumbles_lost

- **Best Strategy:** voting_weighted
- **Correlation:** 0.478
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.03 | -0.089 |
| xgb_solo | 0.02 | 0.002 |
| voting_simple | 0.02 | -0.003 |
| voting_weighted | 0.02 | 0.003 ← BEST |
| stacking | 0.02 | 0.002 |

### TE_receiving_yards

- **Best Strategy:** voting_weighted
- **Correlation:** 0.970
- **Optimal Weights:** LightGBM=0.60, XGBoost=0.40

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 8.41 | 0.759 |
| xgb_solo | 7.71 | 0.807 |
| voting_simple | 7.51 | 0.812 |
| voting_weighted | 7.51 | 0.811 ← BEST |
| stacking | 7.52 | 0.810 |

### TE_receiving_tds

- **Best Strategy:** stacking
- **Correlation:** 0.921
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.20 | 0.351 |
| xgb_solo | 0.18 | 0.422 |
| voting_simple | 0.19 | 0.423 |
| voting_weighted | 0.18 | 0.423 |
| stacking | 0.18 | 0.432 ← BEST |

### TE_receptions

- **Best Strategy:** stacking
- **Correlation:** 0.977
- **Optimal Weights:** LightGBM=0.45, XGBoost=0.55

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.73 | 0.764 |
| xgb_solo | 0.68 | 0.803 |
| voting_simple | 0.66 | 0.805 |
| voting_weighted | 0.66 | 0.805 |
| stacking | 0.66 | 0.805 ← BEST |

### TE_fumbles_lost

- **Best Strategy:** xgb_solo
- **Correlation:** 0.370
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.03 | -0.087 |
| xgb_solo | 0.02 | -0.009 ← BEST |
| voting_simple | 0.03 | -0.035 |
| voting_weighted | 0.03 | -0.010 |
| stacking | 0.03 | -0.004 |

## Analysis

### Model Diversity

- High diversity (correlation < 0.7): 4/21 stats
- Moderate diversity (0.7-0.9): 1/21 stats
- Low diversity (>= 0.9): 16/21 stats

### Ensemble vs Single Model Performance

**Stats where ensemble wins:** 20/21

Top ensemble improvements:
- WR_receiving_yards: 4.1% improvement
- QB_fumbles_lost: 4.1% improvement
- RB_receiving_yards: 3.4% improvement
- QB_rushing_yards: 3.1% improvement
- QB_rushing_tds: 2.9% improvement

**Stats where single model wins:** 1/21

Worst ensemble degradations:
- TE_fumbles_lost: 1.9% worse

## Recommendation

**Adopt ensemble models** - Ensembles beat single models on 20/21 (95.2%) stats.

Recommended approach:
- Use voting_weighted as default ensemble strategy (wins most frequently)
- Deploy ensemble models for production predictions
- Keep single models as fallback for comparison

## Methodology

- **Training Data:** 2020-2024 seasons (5 years)
- **Holdout Data:** 2025 season (strict holdout, never seen during training)
- **Strategies Tested:**
  1. `lgbm_solo`: LightGBM model alone
  2. `xgb_solo`: XGBoost model alone
  3. `voting_simple`: Simple averaging (equal weights)
  4. `voting_weighted`: Weighted averaging (optimal weights via grid search)
  5. `stacking`: Ridge meta-learner with 5-fold CV
- **Metrics:** MAE (lower is better), R² (higher is better)
- **Best Strategy:** Selected by lowest MAE on holdout data

## Comparison to 2024 Benchmark

The original benchmark (BENCHMARK_RESULTS.md) trained on 2022-2023 and tested on 2024 holdout. This benchmark:
- Uses 5 years vs 2 years of training data (2020-2024 vs 2022-2023)
- Tests on most recent 2025 season vs 2024
- Validates whether ensemble findings hold with more training data and recent season
