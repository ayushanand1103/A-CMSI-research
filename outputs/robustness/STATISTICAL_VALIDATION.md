# Statistical validation

Positive improvement means the candidate improves on the reference (reference minus candidate for RMSE/MAE/Brier; candidate minus reference for AUC/F1). Bootstrap intervals are paired circular moving-block intervals, 1,000 draws, block length 30 trading days; the separate 60-day analysis changes both block length and HAC bandwidth. Crisis probabilities use the fixed 0.5 cutoff. AUC is threshold-free. Precision/recall/F1 are for future 30-day events here, not same-day detection. Holm adjustment controls the stated comparison family; the global correction also includes the other experimental families. These intervals are marginal, not simultaneous confidence bands.

## Original result reproduction

Fresh five-state estimation reproduced the original saved model-comparison metrics. Detailed tolerance checks are in `reproduction_comparison.csv`; integrity status is `True`. The original pipeline and observed CSV data were preserved. Independent HMM and calibration loops were checked against the fresh original implementation.

The separate clean-environment verification is recorded in `clean_environment_status.json`: {'tests_run': 17, 'passed': True, 'packages_from_isolated_venv': True, 'package_locations': {'numpy': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'pandas': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'scipy': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'scikit-learn': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'statsmodels': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'arch': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages', 'hmmlearn': 'C:\\A-CMSI research\\.venv-reproduction\\Lib\\site-packages'}, 'calibration_reproduced': True, 'max_forecast_difference': 0.0, 'no_project_deps_directory': True}. The full fresh-fit reproduction used the project environment; the clean environment independently passed the copied-source tests and reproduced calibrated forecasts, without project `.deps` or global package fallback.

## Dependence and multiplicity

Of 29 primary squared-loss comparisons, 0 pass the global Holm correction. This is a statement about these tests and their power, not evidence that all specifications are equivalent. Bootstrap RMSE intervals and HAC/DM p-values can disagree because their finite-sample approximations differ; the audit reports both rather than selecting the favorable procedure.

There are 1810 primary ablation forecast dates, but overlapping 30-day targets are not 1810 independent observations. The crude number of disjoint horizon-sized blocks is 60.3; this is not an exact inferential ESS. There are 467 positive future-event dates and 10 contiguous positive-label episodes. A crisis spanning many dates must not be represented as many independent crises.

The original squared-error DM test uses a Bartlett HAC estimate through lag 29 and an HLN horizon-30 correction. It is an approximate inference procedure, not a finite-sample guarantee. Primary 30-day block bootstrap and 60-day block/HAC sensitivity results are retained. Labels and forecast errors can have dependence beyond the overlap horizon. The 60-day analysis tests one longer scale, not all possible nonstationarity.

Holm family and global adjustments are supplied for squared-loss DM p-values. Bootstrap intervals for AUC, Brier, precision, recall and F1 are descriptive paired uncertainty intervals; no independent-day binomial or DeLong claim is made. Bootstrap draws without both classes are counted and omitted from AUC intervals, not assigned artificial AUC values.

## Complete paired comparisons

| family | candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|---|
| hmm | HMM3 | HMM4 | 0.0002 | -0.0021 | 0.0017 | 0.8156 | 1.0 | 1.0 |
| hmm | HMM3 | HMM5 | -0.0014 | -0.0046 | 0.0004 | 0.1644 | 0.501 | 1.0 |
| hmm | HMM3 | HMM6 | -0.0017 | -0.0043 | 0.0002 | 0.0835 | 0.501 | 1.0 |
| hmm | HMM4 | HMM5 | -0.0016 | -0.0037 | 0.0003 | 0.0955 | 0.501 | 1.0 |
| hmm | HMM4 | HMM6 | -0.0019 | -0.0042 | 0.0001 | 0.0922 | 0.501 | 1.0 |
| hmm | HMM5 | HMM6 | -0.0003 | -0.0021 | 0.0016 | 0.7344 | 1.0 | 1.0 |
| ablation | Adaptive | NoProbability | -0.0001 | -0.0026 | 0.002 | 0.9092 | 1.0 | 1.0 |
| ablation | Adaptive | Entropy | -0.0005 | -0.0011 | 0.0002 | 0.2199 | 1.0 | 1.0 |
| ablation | Adaptive | NoHMM | -0.0012 | -0.0038 | 0.0012 | 0.341 | 1.0 | 1.0 |
| ablation | Adaptive | Equal | -0.0008 | -0.0015 | 0.0003 | 0.2169 | 1.0 | 1.0 |
| ablation | Adaptive | PCA | -0.0 | -0.0025 | 0.0021 | 0.9677 | 1.0 | 1.0 |
| ablation | Adaptive | NoEVT | 0.0015 | -0.0016 | 0.0057 | 0.3847 | 1.0 | 1.0 |
| ablation | Adaptive | NoGARCH | 0.0005 | -0.0002 | 0.0012 | 0.1795 | 1.0 | 1.0 |
| ablation | ConditionalVTP | ConditionalVT | -0.0017 | -0.0034 | 0.0002 | 0.2352 | 1.0 | 1.0 |
| ablation | ConditionalVTStress | ConditionalVT | -0.0009 | -0.0017 | 0.0002 | 0.1395 | 1.0 | 1.0 |
| ablation | ConditionalVTPStress | ConditionalVT | -0.0016 | -0.0026 | -0.0003 | 0.0816 | 0.8161 | 1.0 |
| weighting | Adaptive | Equal | -0.0008 | -0.0015 | 0.0003 | 0.2169 | 0.8678 | 1.0 |
| weighting | Adaptive | Entropy | -0.0005 | -0.0011 | 0.0002 | 0.2199 | 0.8678 | 1.0 |
| weighting | Adaptive | EntropyDeficit | 0.0019 | -0.0005 | 0.005 | 0.1188 | 0.5941 | 1.0 |
| weighting | Adaptive | PCA | -0.0 | -0.0025 | 0.0021 | 0.9677 | 1.0 | 1.0 |
| weighting | Adaptive | PCAFloor | -0.0004 | -0.0025 | 0.0015 | 0.7233 | 1.0 | 1.0 |
| evt | w252_q95 | w252_q90 | -0.0015 | -0.0026 | -0.0004 | 0.0853 | 0.6826 | 1.0 |
| evt | w252_q97.5 | w252_q90 | -0.0015 | -0.0026 | -0.0004 | 0.0853 | 0.6826 | 1.0 |
| evt | w378_q90 | w252_q90 | -0.0001 | -0.0051 | 0.0032 | 0.9585 | 1.0 | 1.0 |
| evt | w378_q95 | w252_q90 | -0.0003 | -0.0054 | 0.0031 | 0.8823 | 1.0 | 1.0 |
| evt | w378_q97.5 | w252_q90 | -0.0003 | -0.0054 | 0.0031 | 0.8823 | 1.0 | 1.0 |
| evt | w504_q90 | w252_q90 | -0.0022 | -0.0121 | 0.0052 | 0.569 | 1.0 | 1.0 |
| evt | w504_q95 | w252_q90 | -0.003 | -0.0128 | 0.0033 | 0.3794 | 1.0 | 1.0 |
| evt | w504_q97.5 | w252_q90 | -0.003 | -0.0122 | 0.0033 | 0.3698 | 1.0 | 1.0 |

## Longer-dependence sensitivity

| family | candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|---|
| hmm | HMM3 | HMM4 | 0.0002 | -0.0024 | 0.002 | 0.8429 | 1.0 | 1.0 |
| hmm | HMM3 | HMM5 | -0.0014 | -0.0046 | 0.0006 | 0.2224 | 0.6854 | 1.0 |
| hmm | HMM3 | HMM6 | -0.0017 | -0.0048 | 0.0003 | 0.1348 | 0.6854 | 1.0 |
| hmm | HMM4 | HMM5 | -0.0016 | -0.0038 | 0.0003 | 0.1221 | 0.6854 | 1.0 |
| hmm | HMM4 | HMM6 | -0.0019 | -0.0044 | 0.0002 | 0.1142 | 0.6854 | 1.0 |
| hmm | HMM5 | HMM6 | -0.0003 | -0.0024 | 0.0017 | 0.729 | 1.0 | 1.0 |
| ablation | Adaptive | NoProbability | -0.0001 | -0.0027 | 0.0023 | 0.9068 | 1.0 | 1.0 |
| ablation | Adaptive | Entropy | -0.0005 | -0.0012 | 0.0004 | 0.2655 | 1.0 | 1.0 |
| ablation | Adaptive | NoHMM | -0.0012 | -0.0035 | 0.0012 | 0.3063 | 1.0 | 1.0 |
| ablation | Adaptive | Equal | -0.0008 | -0.0016 | 0.0006 | 0.2695 | 1.0 | 1.0 |
| ablation | Adaptive | PCA | -0.0 | -0.0022 | 0.002 | 0.9633 | 1.0 | 1.0 |
| ablation | Adaptive | NoEVT | 0.0015 | -0.0017 | 0.0065 | 0.4069 | 1.0 | 1.0 |
| ablation | Adaptive | NoGARCH | 0.0005 | -0.0001 | 0.0012 | 0.1515 | 1.0 | 1.0 |
| ablation | ConditionalVTP | ConditionalVT | -0.0017 | -0.0037 | 0.0003 | 0.2809 | 1.0 | 1.0 |
| ablation | ConditionalVTStress | ConditionalVT | -0.0009 | -0.0018 | 0.0004 | 0.1776 | 1.0 | 1.0 |
| ablation | ConditionalVTPStress | ConditionalVT | -0.0016 | -0.0027 | -0.0002 | 0.1091 | 1.0 | 1.0 |
| weighting | Adaptive | Equal | -0.0008 | -0.0016 | 0.0006 | 0.2695 | 1.0 | 1.0 |
| weighting | Adaptive | Entropy | -0.0005 | -0.0012 | 0.0004 | 0.2655 | 1.0 | 1.0 |
| weighting | Adaptive | EntropyDeficit | 0.0019 | -0.0005 | 0.0056 | 0.138 | 0.6899 | 1.0 |
| weighting | Adaptive | PCA | -0.0 | -0.0022 | 0.002 | 0.9633 | 1.0 | 1.0 |
| weighting | Adaptive | PCAFloor | -0.0004 | -0.0023 | 0.0015 | 0.6831 | 1.0 | 1.0 |
| evt | w252_q95 | w252_q90 | -0.0015 | -0.0026 | -0.0001 | 0.149 | 1.0 | 1.0 |
| evt | w252_q97.5 | w252_q90 | -0.0015 | -0.0026 | -0.0001 | 0.149 | 1.0 | 1.0 |
| evt | w378_q90 | w252_q90 | -0.0001 | -0.0061 | 0.0037 | 0.9649 | 1.0 | 1.0 |
| evt | w378_q95 | w252_q90 | -0.0003 | -0.0063 | 0.0036 | 0.8989 | 1.0 | 1.0 |
| evt | w378_q97.5 | w252_q90 | -0.0003 | -0.0063 | 0.0036 | 0.8989 | 1.0 | 1.0 |
| evt | w504_q90 | w252_q90 | -0.0022 | -0.0143 | 0.0057 | 0.6211 | 1.0 | 1.0 |
| evt | w504_q95 | w252_q90 | -0.003 | -0.0147 | 0.0043 | 0.4516 | 1.0 | 1.0 |
| evt | w504_q97.5 | w252_q90 | -0.003 | -0.0143 | 0.004 | 0.4401 | 1.0 | 1.0 |

## Timing audit and remaining bias

The code fits model parameters/scalers using dates before the next block. GaussianHMM forward recursion conditions only on observations through the signal date. Conditional volatility recursions with fixed training parameters pass a future-prefix mutation test. Trailing component normalization and entropy include today's after-close signal but no later data. PCA loadings use earlier component rows. Calibration excludes every training label whose 30-day window has not matured before block start. After-close same-day detection is reported separately from future crisis prediction.

Initial reconstructed training probabilities are used only for warmup and feature history, not scored forecasts. Adjusted-close histories are revised observations rather than a point-in-time corporate-action database. The historical evaluation period has already been inspected and reported; new robustness comparisons on it are retrospective, not independent confirmation. No hyperparameters or production state counts were chosen by the new test rankings.

The volatility calibration fits log volatility and exponentiates predictions without a lognormal mean-bias correction, preserving the original method across variants. It therefore does not directly optimize the original-scale squared-error estimand. This is a disclosed modeling limitation, not a silently revised estimator. Model-defined regime-transition labels are not observable economic ground truth and are not used to support crisis-prediction claims.
