# Adaptive Composite Market Stress Index: volatility, regimes and tail severity

Research manuscript draft — generated from an executed experiment. Editorial review and a verified literature review remain necessary before submission.

## Abstract

Financial market stress combines conditional volatility, changing market regimes and extreme-loss severity. We construct an adaptive composite market stress index for AAPL, MSFT and SPY using ARIMA innovations, conditional variance models, a forward-filtered Gaussian hidden Markov model, generalized Pareto tail estimates and trailing information-entropy weights. Monthly expanding-window evaluation yields an adaptive volatility-forecast RMSE of 0.10532, a same-day crisis-detection F1 of 0.300 at a historical 90th-percentile threshold, and a future-crisis ROC AUC of 0.658; the lowest volatility RMSE belongs to NoHMM. The experiment provides a reproducible comparison of adaptive and simpler stress composites while separating descriptive crisis alignment from forecasts formed without future observations.

## 1. Introduction

A market stress index is useful only when its construction and evaluation match its intended use. An index reconstructed after a crisis can describe that crisis accurately while offering little information before it. This distinction matters especially for latent-state models, whose smoothed historical probabilities condition on subsequent returns. A-CMSI therefore treats crisis description, contemporaneous detection and future-risk prediction as separate tasks.

The proposed index combines three dimensions of stress: conditional volatility V, market panic probability P and expected tail-loss severity T. Volatility describes dispersion under an estimated conditional distribution. A regime probability describes the likelihood of an adverse latent market state. Expected shortfall describes severity conditional on entering an extreme-loss tail. A fourth specification adds rolling cross-asset correlation C as a measure of market synchronization. Correlation is not called cointegration breakdown: long-run equilibrium tests and short-run co-movement measure different phenomena.

The contribution tested here is an adaptive weighting mechanism. Trailing entropy supplies component activity weights, and filtered regime probabilities supply continuous economic multipliers. Neither mechanism guarantees improvement. Equal weights, PCA weights, entropy-only weights and component ablations are assessed on the same held-out dates. The experiment permits a simpler model to win.

## 2. Methodological context and literature

Conditional heteroskedasticity, latent Markov regimes, peaks-over-threshold extreme-value methods, entropy weighting and financial stress composites are established methodological families. This draft does not claim their invention. The research question concerns their combination and incremental value under chronological validation. A complete submission needs a verified discussion of original ARCH/GARCH and EGARCH papers, Hamilton-style regime switching, peaks-over-threshold asymptotics, financial stress aggregation and forecast-comparison inference. No bibliography has been fabricated to meet a citation count.

Implementation references are the official [arch documentation](https://arch.readthedocs.io/en/latest/univariate/forecasting.html), [hmmlearn API](https://hmmlearn.readthedocs.io/en/stable/api.html), [SciPy generalized Pareto API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genpareto.html), [statsmodels VECM](https://www.statsmodels.org/stable/vector_ar.html), [PyWavelets CWT](https://pywavelets.readthedocs.io/en/latest/ref/cwt.html) and [FRED financial stress series](https://fred.stlouisfed.org/series/STLFSI4). These document computation; they do not replace a scholarly literature review.

## 3. Data and exploratory analysis

The experiment uses 2765 observations of adjusted closes from 2015-01-02 through 2025-12-30. Daily log differences produce 2764 return observations. Prices come from the repository's original Yahoo Finance exports. VIX observations are recovered from the saved HMM input dataset and are not replaced with volatility estimates. All dates are parsed explicitly; duplicates and nonpositive prices cause failure. Raw per-asset legacy CSVs lack dates, so the merged dated adjusted-price file is the canonical input.

Descriptive statistics, price and return plots, 21-day variance plots, 63-day correlations, ADF/KPSS tests, log-price Johansen tests and conditional ECM estimates are exported. ECMs are fitted only where estimated rank lies strictly between zero and the number of assets. A separate coarse-grid segmented-variance analysis estimates multiple mean shifts under BIC. Its search grid and post-selection interpretation are explicit; it is not passed off as the exact R Bai-Perron implementation. Offline LOESS trends are exported for exploration and are excluded from the predictive pipeline.

## 4. Methodology

### 4.1 Conditional volatility

ARIMA orders with p and q from zero to two and d fixed at zero are selected by BIC on the initial training sample. Innovations feed zero-mean GARCH, GJR-GARCH and EGARCH candidates with normal and Student-t innovations. BIC chooses a specification on that same initial sample. Every 21 trading days the selected specification is re-estimated using only earlier returns; conditional means and variances are propagated through the next block with fixed estimated parameters. Inputs are scaled to percentage returns for numerical conditioning and exported in decimal-return units.

### 4.2 Forward-filtered market regimes

The HMM uses SPY returns, normalized conditional volatility, rolling realized volatility, skewness, drawdown, volatility of volatility, VIX and mean pairwise correlation. Feature scaling is fitted only on the current training window. Three deterministic-seed restarts select the largest training likelihood. Two- through six-state alternatives are compared on the initial training data; the five-state model remains an explicit primary design choice. Numeric state identifiers receive economic risk ranks based on training means of VIX, realized volatility, conditional volatility and inverse returns. P is the highest-risk state's forward-filtered probability. Regime stress is the posterior expectation of evenly spaced risk ranks. The forward recursion conditions on observations through the current day and never applies a backward smoothing pass.

### 4.3 Extreme losses

Loss is the negative daily log return. The main POT specification fits a GPD to excesses above each trailing 252-day window's 90th-percentile threshold. At least 20 excesses are required. Full-sample 90th, 95th and 99th percentile fits support a descriptive threshold-sensitivity table; a VaR level below its fitted threshold is deliberately left missing. The tail exceedance rate enters the unconditional VaR extrapolation. Expected shortfall is finite only when shape xi is below one. Fits violating that condition, or otherwise failing validity checks, use an explicitly logged empirical 99% expected-shortfall fallback. Raw rolling expected shortfall becomes T after trailing normalization.

### 4.4 Normalization and adaptive weights

Each raw component is transformed using its trailing 252-observation mean and sample standard deviation and clipped to [-3,3]. Volatility is normalized once; the new pipeline does not renormalize an already normalized legacy V export. Each component's absolute normalized values are converted to probabilities over the previous W observations, including today. Normalized Shannon entropy is minus the sum of p log p divided by log W. Component entropy divided by total entropy supplies base weights. A complete all-zero entropy window receives equal weights; missing warmup windows remain missing.

Risk-ranked regime factors interpolate between bull endpoints (1.3,0.8,0.9) and panic endpoints (0.8,1.1,1.4) for V, P and T. This implements a documented extension of the original three-regime table to five ranked states. Factors multiply entropy weights before normalization. The affine floor map w_i = m + (1-Km) raw_i / sum(raw) guarantees each weight is at least m=0.05 and their sum is exactly one. Multipliers are prior design assumptions rather than estimated economic truths.

### 4.5 Composite variants

Each asset index is the weighted sum of its V and T components and the common market P component. The portfolio is the arithmetic mean of three asset indices. Equal weighting fixes all component weights to one third. PCA uses normalized absolute first-component loadings fitted only to earlier available component observations at monthly boundaries. Entropy-only removes the regime adjustment. No-EVT removes T and redistributes weight. No-HMM removes both P and regime adjustment; this prevents duplication of entropy-only. No-GARCH replaces conditional volatility with rolling realized volatility. Adaptive4 adds normalized mean pairwise correlation with a neutral multiplier. The adaptive and baseline indices are not presumed to have identical interpretations after removing a component, so comparison uses calibrated forecasts rather than raw index-to-volatility errors.

### 4.6 Evaluation

The initial model window contains 756 trading days. Subsequent models refit every 21 trading days. Signals are formed after close. For future volatility, the target is the sample standard deviation of the next 30 daily returns annualized by sqrt(252). A standardized ridge regression maps each scalar index to log future volatility. Forecasts use an expanding calibration sample containing only fully matured target windows. Current 30-day realized volatility supplies a persistence baseline. Classification uses expanding logistic calibration for a crisis within the next 30 days and for a change in filtered risk-rank regime at horizon 30. Regime transition is a model-derived proxy, not an observed crisis label.

Same-day crisis detection is assessed separately. A day is labeled stressed when SPY return is below -3% or its trailing 20-day cumulative price return is below -10%. Signals exceed historical expanding 75th, 90th or 95th-percentile index thresholds formed using strictly earlier observations. Early-warning events are first crossings of the -10% trailing-return criterion, separated by a 20-day refractory period. Warning rates use the preceding 5, 10 and 20 trading days. Last threshold-crossing leads are searched over the preceding 60 trading days, with non-evaluable events retained and marked.

Squared-loss Diebold-Mariano comparisons use a Bartlett HAC estimator over 29 lags and the Harvey-Leybourne-Newbold small-sample correction. Paired circular moving-block bootstrap resamples 30-day blocks 1,000 times to estimate uncertainty in RMSE improvement. These intervals account for local dependence but do not eliminate model-selection or multiple-testing uncertainty. Entropy windows 21, 63 and 126 are recomputed and evaluated. Optional external comparisons use STLFSI4 and KCFSI with conservative release lags and an explicit warning that latest revised observations are not point-in-time vintages.

## 5. Results

### 5.1 Forecast and ablation comparison

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

The lowest volatility RMSE is obtained by NoHMM; the adaptive model has RMSE 0.10532. This outcome is reported directly rather than adjusting the index until the adaptive model wins. Forecast directional accuracy measures whether the forecast and realized future volatility move in the same direction relative to current realized volatility. Crisis ROC AUC uses future-event probabilities; same-day threshold F1 is a different task.

### 5.2 Crisis detection

| variant | quantile | n | precision | recall | f1 | auc | interpretation |
|---|---|---|---|---|---|---|---|
| Adaptive | 0.75 | 2008 | 0.0932 | 0.8596 | 0.1681 | 0.9107 | same_day_detection_after_close |
| Adaptive | 0.9 | 2008 | 0.1967 | 0.6316 | 0.3 | 0.9107 | same_day_detection_after_close |
| Adaptive | 0.95 | 2008 | 0.3158 | 0.5263 | 0.3947 | 0.9107 | same_day_detection_after_close |

The primary 90th-percentile same-day threshold yields F1 0.300. Because the current return enters both the signal and the contemporaneous label, this score measures after-close detection. It must not be cited as evidence that an investor could have forecast the day's loss.

### 5.3 Early-warning events

| variant | event_date | evaluable | last_crossing | lead_trading_days | warning_5d | warning_10d | warning_20d |
|---|---|---|---|---|---|---|---|
| Adaptive | 2018-12-24 | True | 2018-12-17 | 5.0 | True | True | True |
| Adaptive | 2020-03-06 | True | 2020-02-25 | 8.0 | True | True | True |
| Adaptive | 2022-05-09 | True | nan | nan | False | False | False |
| Adaptive | 2022-09-23 | True | 2022-09-14 | 7.0 | True | True | True |
| Adaptive | 2025-04-04 | True | 2025-03-11 | 18.0 | False | True | True |

Lead times are conditional on a preceding threshold crossing being found within the declared search interval. Missing leads do not become successful warnings. Crisis sample size is small, and persistent stress can generate both early signals and false alarms. The event table supports exploratory interpretation rather than a reliable estimate of crisis-prediction performance in new markets.

### 5.4 Significance and sensitivity

| baseline | n | dm | pvalue | rmse_improvement | ci_low | ci_high | bootstrap_repetitions |
|---|---|---|---|---|---|---|---|
| Equal | 1810 | 1.2351 | 0.2169 | -0.0008 | -0.0015 | 0.0003 | 1000 |
| PCA | 1810 | 0.0405 | 0.9677 | -0.0 | -0.0025 | 0.0021 | 1000 |
| Entropy | 1810 | 1.2272 | 0.2199 | -0.0005 | -0.0011 | 0.0002 | 1000 |
| NoEVT | 1810 | -0.8694 | 0.3847 | 0.0015 | -0.0016 | 0.0057 | 1000 |
| NoHMM | 1810 | 0.9525 | 0.341 | -0.0012 | -0.0038 | 0.0012 | 1000 |
| NoGARCH | 1810 | -1.3427 | 0.1795 | 0.0005 | -0.0002 | 0.0012 | 1000 |
| Adaptive4 | 1810 | 0.0937 | 0.9253 | -0.0001 | -0.001 | 0.0016 | 1000 |

| variant | n | rmse | mae | directional_accuracy | crisis_auc | crisis_brier | crisis_f1_at_0.5 | transition_auc | transition_brier | transition_f1_at_0.5 | entropy_window |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Adaptive | 1810 | 0.1055 | 0.057 | 0.6613 | 0.6569 | 0.1875 | 0.1216 | 0.4303 | 0.2297 | 0.8065 | 21 |
| Adaptive | 1810 | 0.1053 | 0.0569 | 0.6646 | 0.6583 | 0.1869 | 0.127 | 0.4293 | 0.2297 | 0.8065 | 63 |
| Adaptive | 1810 | 0.1053 | 0.0569 | 0.6657 | 0.6588 | 0.1868 | 0.1244 | 0.4293 | 0.2297 | 0.8065 | 126 |

Statistical significance is interpreted jointly with effect size and confidence intervals. A bootstrap interval containing zero gives no clear evidence of an RMSE improvement under the chosen resampling design. Tests are exploratory and their p-values are not corrected for the multiple comparisons in this experiment.

### 5.5 Component and descriptive diagnostics

Across 7539 trailing tail fits, 1 require empirical fallback. Parameter estimates, tail diagnostics, stationarity results, HMM means and transition persistence are available in the accompanying tables. Figures include annotated index comparisons, adaptive weight dynamics, event windows, Morlet scalograms and smoothed wavelet coherence with boundary regions masked. Coherence plots include no unearned significance claims.

### 5.6 External stress indices

External benchmarks were not downloaded for this run.

The external-only and residual-augmented models are compared on the same external-data sample. This is a separate sample from the main ablation table, so its RMSEs must not be ranked directly against the main results. Latest revised FRED histories and assumed publication lags make this evidence exploratory. An incremental reduction in this table is not sufficient to claim an independently validated new systemic-risk signal.

### 5.7 Stability under entropy-window changes

The range of adaptive RMSE across the three entropy windows is 0.23% of their mean. This describes local sensitivity to a single window parameter. It does not validate the chosen HMM state count, threshold family, clipping bounds or economic multipliers. Those choices remain limitations and potential subjects for a pre-registered replication.

## 6. Discussion

The index combines complementary definitions of stress, but complementarity in economic language does not imply independent statistical information. Conditional volatility, tail severity and HMM probabilities can rise together, making adaptive weighting unnecessary in some periods. Comparing component ablations with a realized-volatility persistence forecast is therefore essential. The resulting tables should guide whether the adaptive construction is retained, simplified or treated as a descriptive index.

Using a common market panic probability for all three assets makes the regime signal systemic within this small universe. It does not create three independent panic estimates. AAPL and MSFT are large constituents of SPY, so both the portfolio average and pairwise correlation component reflect overlapping economic exposures. Evidence from this universe cannot establish broad financial-system stress coverage.

The 252-day rolling POT window offers adaptation at the expense of few exceedances. A 90th-percentile threshold yields roughly 25 observations, and extrapolation to 99% expected shortfall is correspondingly uncertain. The explicit empirical fallback prevents undefined conditional expectations from silently contaminating the composite. It also makes the operative tail measure a hybrid estimator whose contribution requires direct ablation analysis.

A chronological forward filter fixes one common source of future information in HMM evaluations. Remaining limitations include revised adjusted-close histories, finite initial samples, manually specified multipliers, model-derived regime labels, overlapping forecast horizons and exploratory threshold choices. External FSI comparisons have an additional vintage limitation. None of these should be concealed by reporting a single high F1 score or visually attractive COVID plot.

## 7. Conclusion

A-CMSI is implemented as a reproducible after-close stress signal with separate contemporaneous and future-risk evaluations. It combines normalized conditional volatility, filtered panic probability and rolling extreme-loss severity, with a separate correlation-augmented specification. In the executed sample, NoHMM has the lowest held-out volatility RMSE; the adaptive model's RMSE is 0.10532. The evidence supports comparison and refinement of stress composites without assuming adaptive weighting is universally beneficial. Broader assets, unrevised point-in-time data, pre-registered thresholds and independent evaluation periods are needed before deployment or strong predictive claims.

## Reproducibility and submission status

Run `python run_acmsi.py` from the repository root. The run manifest records configuration, package versions and input/source fingerprint. All tables in this manuscript are generated from saved output. The current manuscript is a substantive methods-and-results draft, not a verified 7,000-word submission with 50 scholarly references. SSRN upload and journal submission have not been performed; those are separate external actions requiring a finished author-reviewed manuscript and explicit instructions.
