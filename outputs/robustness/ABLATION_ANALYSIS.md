# HMM ablation and weighting audit

## Controlled definitions

- Adaptive: original P signal and regime multipliers.
- NoProbability: remove P, recompute V/T entropy weights, retain V/T regime multipliers.
- Entropy: retain P, remove regime multipliers (the no-multiplier ablation).
- NoHMM: remove both P and regime multipliers.
- Equal, PCA and entropy-only: retain the original baselines.
- EntropyDeficit: normalize 1-H instead of H, retaining the same floor rule.
- PCAFloor: explicitly apply the 0.05 floor to absolute PCA loadings; original PCA remains unchanged.
- ConditionalVT / VTP / VTStress / VTPStress: fixed multivariate ridge/logistic diagnostics of incremental information. These are not composite-weight variants or test-optimized coefficients.

All fixed calibration hyperparameters, horizon, refit schedule, training support and scoring dates are identical within the comparison family.

| variant | n | rmse | rmse_ci_low | rmse_ci_high | mae | auc | brier | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| Adaptive | 1810 | 0.1053 | 0.0557 | 0.1555 | 0.0569 | 0.6583 | 0.1869 | 0.2653 | 0.0835 | 0.127 |
| Adaptive4 | 1810 | 0.1053 | 0.0559 | 0.155 | 0.0576 | 0.6611 | 0.1844 | 0.275 | 0.0707 | 0.1124 |
| ConditionalVT | 1810 | 0.1052 | 0.06 | 0.1536 | 0.0594 | 0.5965 | 0.208 | 0.2645 | 0.1563 | 0.1965 |
| ConditionalVTP | 1810 | 0.1068 | 0.0601 | 0.1568 | 0.0598 | 0.5972 | 0.2085 | 0.263 | 0.152 | 0.1927 |
| ConditionalVTPStress | 1810 | 0.1068 | 0.0614 | 0.1558 | 0.0593 | 0.5843 | 0.2084 | 0.3186 | 0.2013 | 0.2467 |
| ConditionalVTStress | 1810 | 0.1061 | 0.0611 | 0.1549 | 0.0589 | 0.5866 | 0.2079 | 0.3 | 0.1927 | 0.2347 |
| Entropy | 1810 | 0.1048 | 0.0554 | 0.1546 | 0.0568 | 0.6656 | 0.1858 | 0.2312 | 0.0792 | 0.118 |
| EntropyDeficit | 1810 | 0.1072 | 0.058 | 0.1577 | 0.0593 | 0.6421 | 0.1941 | 0.3295 | 0.1242 | 0.1804 |
| Equal | 1810 | 0.1046 | 0.0554 | 0.1542 | 0.0568 | 0.6776 | 0.1842 | 0.4111 | 0.1585 | 0.2287 |
| NoEVT | 1810 | 0.1068 | 0.0583 | 0.156 | 0.0597 | 0.5919 | 0.1982 | 0.0672 | 0.0171 | 0.0273 |
| NoGARCH | 1810 | 0.1058 | 0.0559 | 0.1563 | 0.0572 | 0.6468 | 0.1906 | 0.1534 | 0.0535 | 0.0794 |
| NoHMM | 1810 | 0.1041 | 0.0547 | 0.154 | 0.0564 | 0.6573 | 0.1847 | 0.5322 | 0.1949 | 0.2853 |
| NoProbability | 1810 | 0.1052 | 0.0553 | 0.1552 | 0.0569 | 0.6527 | 0.1869 | 0.4903 | 0.1627 | 0.2444 |
| PCA | 1810 | 0.1053 | 0.0553 | 0.1555 | 0.057 | 0.6843 | 0.1799 | 0.5181 | 0.1842 | 0.2717 |
| PCAFloor | 1810 | 0.1049 | 0.0551 | 0.1551 | 0.0568 | 0.6836 | 0.18 | 0.5298 | 0.1906 | 0.2803 |
| RealizedVolBaseline | 1810 | 0.1227 | 0.0755 | 0.1664 | 0.0686 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |
| TrainMean | 1810 | 0.1118 | 0.0647 | 0.1606 | 0.0701 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |

| candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|
| Adaptive | NoProbability | -0.0001 | -0.0026 | 0.002 | 0.9092 | 1.0 | 1.0 |
| Adaptive | Entropy | -0.0005 | -0.0011 | 0.0002 | 0.2199 | 1.0 | 1.0 |
| Adaptive | NoHMM | -0.0012 | -0.0038 | 0.0012 | 0.341 | 1.0 | 1.0 |
| Adaptive | Equal | -0.0008 | -0.0015 | 0.0003 | 0.2169 | 1.0 | 1.0 |
| Adaptive | PCA | -0.0 | -0.0025 | 0.0021 | 0.9677 | 1.0 | 1.0 |
| Adaptive | NoEVT | 0.0015 | -0.0016 | 0.0057 | 0.3847 | 1.0 | 1.0 |
| Adaptive | NoGARCH | 0.0005 | -0.0002 | 0.0012 | 0.1795 | 1.0 | 1.0 |
| ConditionalVTP | ConditionalVT | -0.0017 | -0.0034 | 0.0002 | 0.2352 | 1.0 | 1.0 |
| ConditionalVTStress | ConditionalVT | -0.0009 | -0.0017 | 0.0002 | 0.1395 | 1.0 | 1.0 |
| ConditionalVTPStress | ConditionalVT | -0.0016 | -0.0026 | -0.0003 | 0.0816 | 0.8161 | 1.0 |

## Weighting alternatives

Removing P alone gives RMSE 0.10519; removing multipliers alone gives 0.10478; removing both gives 0.10411, compared with 0.10532 for Adaptive. The paired RMSE intervals for these three Adaptive contrasts include zero. This pattern is consistent with redundant/noisy contributions under this fixed calibration, but it does not identify a unique mechanism or prove that HMM information is useless.

| variant | n | rmse | rmse_ci_low | rmse_ci_high | mae | auc | brier | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| Adaptive | 1810 | 0.1053 | 0.0557 | 0.1555 | 0.0569 | 0.6583 | 0.1869 | 0.2653 | 0.0835 | 0.127 |
| Entropy | 1810 | 0.1048 | 0.0554 | 0.1546 | 0.0568 | 0.6656 | 0.1858 | 0.2312 | 0.0792 | 0.118 |
| EntropyDeficit | 1810 | 0.1072 | 0.058 | 0.1577 | 0.0593 | 0.6421 | 0.1941 | 0.3295 | 0.1242 | 0.1804 |
| Equal | 1810 | 0.1046 | 0.0554 | 0.1542 | 0.0568 | 0.6776 | 0.1842 | 0.4111 | 0.1585 | 0.2287 |
| PCA | 1810 | 0.1053 | 0.0553 | 0.1555 | 0.057 | 0.6843 | 0.1799 | 0.5181 | 0.1842 | 0.2717 |
| PCAFloor | 1810 | 0.1049 | 0.0551 | 0.1551 | 0.0568 | 0.6836 | 0.18 | 0.5298 | 0.1906 | 0.2803 |
| RealizedVolBaseline | 1810 | 0.1227 | 0.0755 | 0.1664 | 0.0686 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |
| TrainMean | 1810 | 0.1118 | 0.0647 | 0.1606 | 0.0701 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |

| candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|
| Adaptive | Equal | -0.0008 | -0.0015 | 0.0003 | 0.2169 | 0.8678 | 1.0 |
| Adaptive | Entropy | -0.0005 | -0.0011 | 0.0002 | 0.2199 | 0.8678 | 1.0 |
| Adaptive | EntropyDeficit | 0.0019 | -0.0005 | 0.005 | 0.1188 | 0.5941 | 1.0 |
| Adaptive | PCA | -0.0 | -0.0025 | 0.0021 | 0.9677 | 1.0 | 1.0 |
| Adaptive | PCAFloor | -0.0004 | -0.0025 | 0.0015 | 0.7233 | 1.0 | 1.0 |

## Constraint verification

| asset | kind | minimum | nonnegative | max_sum_error | below_005_cells | constraint |
|---|---|---|---|---|---|---|
| AAPL | adaptive | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| AAPL | entropy | 0.0 | True | 0.0 | 200 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| AAPL | pca | 0.0464 | True | 0.0 | 42 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| AAPL | adaptive4 | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| MSFT | adaptive | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| MSFT | entropy | 0.0 | True | 0.0 | 200 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| MSFT | pca | 0.0094 | True | 0.0 | 105 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| MSFT | adaptive4 | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| SPY | adaptive | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| SPY | entropy | 0.0 | True | 0.0 | 200 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| SPY | pca | 0.0053 | True | 0.0 | 210 | base entropy and original PCA do not impose a floor; corrected variants are separate |
| SPY | adaptive4 | 0.05 | True | 0.0 | 0 | base entropy and original PCA do not impose a floor; corrected variants are separate |

Original PCA loadings have no imposed minimum-weight floor. They must not be described as satisfying that constraint when the saved weights fall below 0.05. The original entropy export is the base entropy vector, before final flooring; the actual entropy index applies the floor. Original results are preserved and PCAFloor is an additional disclosed specification. New-weight checks are in `evaluation/new_weight_constraints.csv`.

NoHMM's original lower point-estimate RMSE is not by itself a causal explanation of HMM failure. The controlled removals and conditional-information tests isolate observable changes under this calibration, but correlated components, sparse crises, state-label instability and fixed multipliers limit mechanistic inference. Nonsignificant differences do not establish that the HMM contains no information or that the models are equivalent.

Positive improvement means the candidate improves on the reference (reference minus candidate for RMSE/MAE/Brier; candidate minus reference for AUC/F1). Bootstrap intervals are paired circular moving-block intervals, 1,000 draws, block length 30 trading days; the separate 60-day analysis changes both block length and HAC bandwidth. Crisis probabilities use the fixed 0.5 cutoff. AUC is threshold-free. Precision/recall/F1 are for future 30-day events here, not same-day detection. Holm adjustment controls the stated comparison family; the global correction also includes the other experimental families. These intervals are marginal, not simultaneous confidence bands.
