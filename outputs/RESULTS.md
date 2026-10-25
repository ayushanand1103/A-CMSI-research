# A-CMSI completed research run

This report is generated from executed code and saved data. It does not assume the adaptive specification wins.

- Input: 2765 adjusted-price rows, 2015-01-02–2025-12-30.
- Chronological model outputs begin 2018-01-04; scored forecasts cover 2018-09-05–2025-11-14.
- Lowest held-out volatility RMSE: **NoHMM**, 0.10411 annualized volatility units.
- Adaptive RMSE: 0.10532; MAE: 0.05692; directional accuracy: 0.665.
- Adaptive same-day crisis F1 at the expanding 90th-percentile threshold: 0.300. This is detection after close, not a forecast score.
- Adaptive future 30-day crisis ROC AUC: 0.658.
- Evaluable adaptive early-warning events: 5; median last threshold-crossing lead within 60 prior trading days: 7.5 trading days (conditional on a crossing existing).
- Rolling tail fits requiring empirical fallback: 1 of 7539.

## Held-out comparison

| variant | n | rmse | mae | directional_accuracy | crisis_auc | crisis_brier | crisis_f1_at_0.5 | transition_auc | transition_brier | transition_f1_at_0.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| NoHMM | 1810 | 0.1041 | 0.0564 | 0.6785 | 0.6573 | 0.1847 | 0.2853 | 0.4189 | 0.23 | 0.8065 |
| Equal | 1810 | 0.1046 | 0.0568 | 0.6646 | 0.6776 | 0.1842 | 0.2287 | 0.4327 | 0.23 | 0.8065 |
| Entropy | 1810 | 0.1048 | 0.0568 | 0.6696 | 0.6656 | 0.1858 | 0.118 | 0.4319 | 0.2296 | 0.8065 |
| Adaptive4 | 1810 | 0.1053 | 0.0576 | 0.6663 | 0.6611 | 0.1844 | 0.1124 | 0.4406 | 0.2296 | 0.8065 |
| PCA | 1810 | 0.1053 | 0.057 | 0.6729 | 0.6843 | 0.1799 | 0.2717 | 0.4195 | 0.2303 | 0.8065 |
| Adaptive | 1810 | 0.1053 | 0.0569 | 0.6646 | 0.6583 | 0.1869 | 0.127 | 0.4293 | 0.2297 | 0.8065 |
| NoGARCH | 1810 | 0.1058 | 0.0572 | 0.6519 | 0.6468 | 0.1906 | 0.0794 | 0.4344 | 0.2298 | 0.8065 |
| NoEVT | 1810 | 0.1068 | 0.0597 | 0.6696 | 0.5919 | 0.1982 | 0.0273 | 0.4703 | 0.2289 | 0.8053 |
| RealizedVolBaseline | 1810 | 0.1227 | 0.0686 | 0.0 | nan | nan | nan | nan | nan | nan |

## Paired significance and block-bootstrap uncertainty

Negative DM means lower squared forecast loss for Adaptive. Positive RMSE improvement favors Adaptive. P-values are exploratory, unadjusted for multiple comparisons.

| baseline | n | dm | pvalue | rmse_improvement | ci_low | ci_high | bootstrap_repetitions |
|---|---|---|---|---|---|---|---|
| Equal | 1810 | 1.2351 | 0.2169 | -0.0008 | -0.0015 | 0.0003 | 1000 |
| PCA | 1810 | 0.0405 | 0.9677 | -0.0 | -0.0025 | 0.0021 | 1000 |
| Entropy | 1810 | 1.2272 | 0.2199 | -0.0005 | -0.0011 | 0.0002 | 1000 |
| NoEVT | 1810 | -0.8694 | 0.3847 | 0.0015 | -0.0016 | 0.0057 | 1000 |
| NoHMM | 1810 | 0.9525 | 0.341 | -0.0012 | -0.0038 | 0.0012 | 1000 |
| NoGARCH | 1810 | -1.3427 | 0.1795 | 0.0005 | -0.0002 | 0.0012 | 1000 |
| Adaptive4 | 1810 | 0.0937 | 0.9253 | -0.0001 | -0.001 | 0.0016 | 1000 |

## Entropy-window sensitivity

| variant | n | rmse | mae | directional_accuracy | crisis_auc | crisis_brier | crisis_f1_at_0.5 | transition_auc | transition_brier | transition_f1_at_0.5 | entropy_window |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Adaptive | 1810 | 0.1055 | 0.057 | 0.6613 | 0.6569 | 0.1875 | 0.1216 | 0.4303 | 0.2297 | 0.8065 | 21 |
| Adaptive | 1810 | 0.1053 | 0.0569 | 0.6646 | 0.6583 | 0.1869 | 0.127 | 0.4293 | 0.2297 | 0.8065 | 63 |
| Adaptive | 1810 | 0.1053 | 0.0569 | 0.6657 | 0.6588 | 0.1868 | 0.1244 | 0.4293 | 0.2297 | 0.8065 | 126 |

The RMSE range across entropy windows is 0.23% of mean RMSE. Small changes in this setting do not establish robustness to different assets, dates, thresholds or state counts.

## External benchmark comparison

| model | rmse |
|---|---|
| external_only | 0.1156 |
| external_plus_acmsi | 0.1106 |

These external-series metrics use their own matched sample. FRED observations are latest revised values with assumed publication lags, so this is an exploratory comparison rather than point-in-time forecasting evidence.

## Interpretation and limits

All operational signals are available after market close. Each monthly refit uses earlier observations only. The HMM uses a forward filter; numeric states are relabeled by training-sample risk ranks at every refit. Forecast calibration excludes targets that have not fully matured. Tables use the same eligible dates across ablations within each run.

The first training reconstruction is retained only to initialize rolling windows and model states. It is excluded from scored forecasts. Historical adjusted prices and downloaded FSI series are revised datasets, not point-in-time vintages. Early-warning results are exploratory; crises are few and overlapping forecast targets reduce effective sample size. The five-state specification and economic multipliers are design choices requiring wider-market replication. Tail fallback is disclosed rather than silently clipping a GPD shape with infinite expected shortfall. Wavelet results and offline structural-break p-values are descriptive. The transition target is a future filtered-regime proxy, not observed economic truth.

Legacy R scripts and notebooks are retained as the original exploratory work. The Python pipeline is the reproducible continuation and uses its own exported component series, not the old full-sample HMM probabilities.

See [methodology](../METHODOLOGY.md), [manifest](run_manifest.json), [manuscript draft](manuscript.md), [tables](tables/) and [figures](figures/).
