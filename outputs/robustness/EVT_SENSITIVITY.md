# EVT sensitivity audit

All nine requested threshold/window combinations were executed chronologically with fixed minimum 20 exceedances. The GPD tail window changes; the component's trailing z-score normalization remains 252 days. Full-sample descriptive fits are in `evt/full_sample_descriptive.csv` and never enter forecast selection.

## Raw tail diagnostics

| experiment | asset | exceedance_median | fallback_fraction | xi_median | xi_p95 | beta_median | VaR99_median | ES99_median | ES99_max |
|---|---|---|---|---|---|---|---|---|---|
| w252_q90 | AAPL | 26.0 | 0.0 | 0.004373 | 0.311358 | 0.011587 | 0.04737 | 0.057235 | 0.177414 |
| w252_q90 | MSFT | 26.0 | 0.0 | -0.0607 | 0.338987 | 0.012328 | 0.042195 | 0.0514 | 0.1303 |
| w252_q90 | SPY | 26.0 | 0.000398 | -0.038001 | 0.323324 | 0.008255 | 0.028316 | 0.036111 | 0.112155 |
| w252_q95 | AAPL | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w252_q95 | MSFT | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w252_q95 | SPY | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w252_q97.5 | AAPL | 7.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w252_q97.5 | MSFT | 7.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w252_q97.5 | SPY | 7.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q90 | AAPL | 38.0 | 0.0 | -0.014175 | 0.261509 | 0.012837 | 0.049777 | 0.055778 | 0.122946 |
| w378_q90 | MSFT | 38.0 | 0.0 | -0.036356 | 0.286103 | 0.012492 | 0.042378 | 0.051647 | 0.106813 |
| w378_q90 | SPY | 38.0 | 0.0 | -0.014255 | 0.308057 | 0.008132 | 0.029431 | 0.036426 | 0.095841 |
| w378_q95 | AAPL | 19.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q95 | MSFT | 19.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q95 | SPY | 19.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q97.5 | AAPL | 10.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q97.5 | MSFT | 10.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w378_q97.5 | SPY | 10.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w504_q90 | AAPL | 51.0 | 0.0 | 0.063371 | 0.214962 | 0.012178 | 0.048251 | 0.058062 | 0.105019 |
| w504_q90 | MSFT | 51.0 | 0.0 | -0.002346 | 0.23787 | 0.012187 | 0.04294 | 0.052994 | 0.094807 |
| w504_q90 | SPY | 51.0 | 0.0 | 0.029555 | 0.271479 | 0.009064 | 0.030707 | 0.038674 | 0.083596 |
| w504_q95 | AAPL | 26.0 | 0.0 | 0.078698 | 0.414668 | 0.011092 | 0.047754 | 0.064699 | 0.122645 |
| w504_q95 | MSFT | 26.0 | 0.0 | 0.10869 | 0.430346 | 0.010539 | 0.042645 | 0.052979 | 0.155568 |
| w504_q95 | SPY | 26.0 | 0.0 | 0.018857 | 0.525648 | 0.009196 | 0.0301 | 0.038624 | 0.105447 |
| w504_q97.5 | AAPL | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w504_q97.5 | MSFT | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |
| w504_q97.5 | SPY | 13.0 | 1.0 | nan | nan | nan | nan | nan | nan |

High thresholds can make an experiment entirely empirical: approximately 13 exceedances at 95%/252 days, 19 at 95%/378 days, and 7–13 at 97.5% across these windows do not meet the original 20-exceedance rule. A 100% fallback rate is not a successful GPD validation. Identical fallback-based specifications are not independent evidence for threshold robustness. Undefined GPD ES at xi>=1 remains missing in the diagnostics; the operational hybrid score uses the disclosed empirical ES99 instead. No failed shape/scale estimate is replaced with a fabricated value. Daily estimates, fit exceptions, count failures and fallback flags are all retained.

## Matched future-risk evaluation

| variant | n | rmse | rmse_ci_low | rmse_ci_high | mae | auc | brier | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| RealizedVolBaseline | 1570 | 0.1297 | 0.075 | 0.1774 | 0.0722 | 0.4195 | 0.2062 | 0.0 | 0.0 | 0.0 |
| TrainMean | 1570 | 0.1179 | 0.0646 | 0.1724 | 0.0711 | 0.4195 | 0.2062 | 0.0 | 0.0 | 0.0 |
| w252_q90 | 1570 | 0.1125 | 0.0562 | 0.1682 | 0.0597 | 0.7015 | 0.1766 | 0.4978 | 0.2847 | 0.3622 |
| w252_q95 | 1570 | 0.114 | 0.0575 | 0.1699 | 0.0607 | 0.6855 | 0.1815 | 0.4266 | 0.151 | 0.223 |
| w252_q97.5 | 1570 | 0.114 | 0.0575 | 0.1699 | 0.0607 | 0.6855 | 0.1815 | 0.4266 | 0.151 | 0.223 |
| w378_q90 | 1570 | 0.1126 | 0.0601 | 0.1655 | 0.0629 | 0.6617 | 0.1812 | 0.4803 | 0.1807 | 0.2626 |
| w378_q95 | 1570 | 0.1128 | 0.0603 | 0.1658 | 0.0627 | 0.6609 | 0.1808 | 0.4895 | 0.1733 | 0.2559 |
| w378_q97.5 | 1570 | 0.1128 | 0.0603 | 0.1658 | 0.0627 | 0.6609 | 0.1808 | 0.4895 | 0.1733 | 0.2559 |
| w504_q90 | 1570 | 0.1147 | 0.0649 | 0.1665 | 0.0665 | 0.5227 | 0.2006 | 0.4383 | 0.1757 | 0.2509 |
| w504_q95 | 1570 | 0.1155 | 0.0659 | 0.1673 | 0.0675 | 0.514 | 0.2034 | 0.3987 | 0.1559 | 0.2242 |
| w504_q97.5 | 1570 | 0.1155 | 0.0653 | 0.1676 | 0.0667 | 0.5308 | 0.2019 | 0.4043 | 0.1411 | 0.2092 |

| candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|
| w252_q95 | w252_q90 | -0.0015 | -0.0026 | -0.0004 | 0.0853 | 0.6826 | 1.0 |
| w252_q97.5 | w252_q90 | -0.0015 | -0.0026 | -0.0004 | 0.0853 | 0.6826 | 1.0 |
| w378_q90 | w252_q90 | -0.0001 | -0.0051 | 0.0032 | 0.9585 | 1.0 | 1.0 |
| w378_q95 | w252_q90 | -0.0003 | -0.0054 | 0.0031 | 0.8823 | 1.0 | 1.0 |
| w378_q97.5 | w252_q90 | -0.0003 | -0.0054 | 0.0031 | 0.8823 | 1.0 | 1.0 |
| w504_q90 | w252_q90 | -0.0022 | -0.0121 | 0.0052 | 0.569 | 1.0 | 1.0 |
| w504_q95 | w252_q90 | -0.003 | -0.0128 | 0.0033 | 0.3794 | 1.0 | 1.0 |
| w504_q97.5 | w252_q90 | -0.003 | -0.0122 | 0.0033 | 0.3698 | 1.0 | 1.0 |

Each EVT family comparison uses identical signals/labels for calibration and scoring, and a second `*_universal_metrics.csv` analysis uses the same calibration support across every HMM/EVT/weighting family. Different warmup lengths reduce evaluation coverage, so these RMSEs must not be ranked against the original 1,810-date baseline without matching dates. Clipping normalized components can conceal instability in raw ES, so raw parameter tables must be interpreted jointly with score/forecast tables.

Positive improvement means the candidate improves on the reference (reference minus candidate for RMSE/MAE/Brier; candidate minus reference for AUC/F1). Bootstrap intervals are paired circular moving-block intervals, 1,000 draws, block length 30 trading days; the separate 60-day analysis changes both block length and HAC bandwidth. Crisis probabilities use the fixed 0.5 cutoff. AUC is threshold-free. Precision/recall/F1 are for future 30-day events here, not same-day detection. Holm adjustment controls the stated comparison family; the global correction also includes the other experimental families. These intervals are marginal, not simultaneous confidence bands.
