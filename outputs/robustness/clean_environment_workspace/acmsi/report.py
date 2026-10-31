"""Generate evidence-linked research reports from actual output tables."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def table(df, digits=4):
    df=df.copy()
    for name in df.select_dtypes(include="number"):
        df[name]=df[name].round(digits)
    # Avoid requiring tabulate as an additional dependency.
    return "| "+" | ".join(map(str,df.columns))+" |\n|"+"|".join(["---"]*len(df.columns))+"|\n"+"\n".join(
        "| "+" | ".join(str(v) for v in row)+" |" for row in df.itertuples(index=False,name=None))


def write_reports(output, manifest, portfolio, metric):
    tables=output/"tables"
    detection=pd.read_csv(tables/"crisis_detection.csv")
    early=pd.read_csv(tables/"early_warning.csv")
    sensitivity=pd.read_csv(tables/"entropy_sensitivity.csv")
    significance=pd.read_csv(tables/"main_significance.csv")
    external_path=tables/"external_incremental_metrics.csv"
    external=pd.read_csv(external_path) if external_path.exists() else pd.DataFrame()
    external_text=table(external) if len(external) else "External benchmarks were not downloaded for this run."
    relative_sensitivity=(sensitivity.rmse.max()-sensitivity.rmse.min())/sensitivity.rmse.mean()
    adaptive=metric[metric.variant.eq("Adaptive")].iloc[0]
    winner=metric.sort_values("rmse").iloc[0]
    detect=detection[(detection.variant=="Adaptive")&(detection["quantile"]==.90)].iloc[0]
    evt=pd.read_csv(tables/"rolling_evt_diagnostics.csv")
    eligible=early[early.variant.eq("Adaptive") & early.evaluable.astype(bool)]
    lead=eligible.lead_trading_days.median()
    summary=f"""# A-CMSI completed research run

This report is generated from executed code and saved data. It does not assume the adaptive specification wins.

- Input: {manifest['n_prices']} adjusted-price rows, {manifest['price_start']}–{manifest['price_end']}.
- Chronological model outputs begin {manifest['first_oos_model_date']}; scored forecasts cover {manifest['first_scored_forecast']}–{manifest['last_scored_forecast']}.
- Lowest held-out volatility RMSE: **{winner.variant}**, {winner.rmse:.5f} annualized volatility units.
- Adaptive RMSE: {adaptive.rmse:.5f}; MAE: {adaptive.mae:.5f}; directional accuracy: {adaptive.directional_accuracy:.3f}.
- Adaptive same-day crisis F1 at the expanding 90th-percentile threshold: {detect.f1:.3f}. This is detection after close, not a forecast score.
- Adaptive future 30-day crisis ROC AUC: {adaptive.crisis_auc:.3f}.
- Evaluable adaptive early-warning events: {len(eligible)}; median last threshold-crossing lead within 60 prior trading days: {lead:.1f} trading days (conditional on a crossing existing).
- Rolling tail fits requiring empirical fallback: {(evt.fallback!='none').sum()} of {len(evt)}.

## Held-out comparison

{table(metric)}

## Paired significance and block-bootstrap uncertainty

Negative DM means lower squared forecast loss for Adaptive. Positive RMSE improvement favors Adaptive. P-values are exploratory, unadjusted for multiple comparisons.

{table(significance)}

## Entropy-window sensitivity

{table(sensitivity)}

The RMSE range across entropy windows is {relative_sensitivity:.2%} of mean RMSE. Small changes in this setting do not establish robustness to different assets, dates, thresholds or state counts.

## External benchmark comparison

{external_text}

These external-series metrics use their own matched sample. FRED observations are latest revised values with assumed publication lags, so this is an exploratory comparison rather than point-in-time forecasting evidence.

## Interpretation and limits

All operational signals are available after market close. Each monthly refit uses earlier observations only. The HMM uses a forward filter; numeric states are relabeled by training-sample risk ranks at every refit. Forecast calibration excludes targets that have not fully matured. Tables use the same eligible dates across ablations within each run.

The first training reconstruction is retained only to initialize rolling windows and model states. It is excluded from scored forecasts. Historical adjusted prices and downloaded FSI series are revised datasets, not point-in-time vintages. Early-warning results are exploratory; crises are few and overlapping forecast targets reduce effective sample size. The five-state specification and economic multipliers are design choices requiring wider-market replication. Tail fallback is disclosed rather than silently clipping a GPD shape with infinite expected shortfall. Wavelet results and offline structural-break p-values are descriptive. The transition target is a future filtered-regime proxy, not observed economic truth.

Legacy R scripts and notebooks are retained as the original exploratory work. The Python pipeline is the reproducible continuation and uses its own exported component series, not the old full-sample HMM probabilities.

See [methodology](../METHODOLOGY.md), [manifest](run_manifest.json), [manuscript draft](manuscript.md), [tables](tables/) and [figures](figures/).
"""
    (output/"RESULTS.md").write_text(summary,encoding="utf-8")
    manuscript=f"""# Adaptive Composite Market Stress Index: volatility, regimes and tail severity

Research manuscript draft — generated from an executed experiment. Editorial review and a verified literature review remain necessary before submission.

## Abstract

Financial market stress combines conditional volatility, changing market regimes and extreme-loss severity. We construct an adaptive composite market stress index for AAPL, MSFT and SPY using ARIMA innovations, conditional variance models, a forward-filtered Gaussian hidden Markov model, generalized Pareto tail estimates and trailing information-entropy weights. Monthly expanding-window evaluation yields an adaptive volatility-forecast RMSE of {adaptive.rmse:.5f}, a same-day crisis-detection F1 of {detect.f1:.3f} at a historical 90th-percentile threshold, and a future-crisis ROC AUC of {adaptive.crisis_auc:.3f}; the lowest volatility RMSE belongs to {winner.variant}. The experiment provides a reproducible comparison of adaptive and simpler stress composites while separating descriptive crisis alignment from forecasts formed without future observations.

## 1. Introduction

A market stress index is useful only when its construction and evaluation match its intended use. An index reconstructed after a crisis can describe that crisis accurately while offering little information before it. This distinction matters especially for latent-state models, whose smoothed historical probabilities condition on subsequent returns. A-CMSI therefore treats crisis description, contemporaneous detection and future-risk prediction as separate tasks.

The proposed index combines three dimensions of stress: conditional volatility V, market panic probability P and expected tail-loss severity T. Volatility describes dispersion under an estimated conditional distribution. A regime probability describes the likelihood of an adverse latent market state. Expected shortfall describes severity conditional on entering an extreme-loss tail. A fourth specification adds rolling cross-asset correlation C as a measure of market synchronization. Correlation is not called cointegration breakdown: long-run equilibrium tests and short-run co-movement measure different phenomena.

The contribution tested here is an adaptive weighting mechanism. Trailing entropy supplies component activity weights, and filtered regime probabilities supply continuous economic multipliers. Neither mechanism guarantees improvement. Equal weights, PCA weights, entropy-only weights and component ablations are assessed on the same held-out dates. The experiment permits a simpler model to win.

## 2. Methodological context and literature

Conditional heteroskedasticity, latent Markov regimes, peaks-over-threshold extreme-value methods, entropy weighting and financial stress composites are established methodological families. This draft does not claim their invention. The research question concerns their combination and incremental value under chronological validation. A complete submission needs a verified discussion of original ARCH/GARCH and EGARCH papers, Hamilton-style regime switching, peaks-over-threshold asymptotics, financial stress aggregation and forecast-comparison inference. No bibliography has been fabricated to meet a citation count.

Implementation references are the official [arch documentation](https://arch.readthedocs.io/en/latest/univariate/forecasting.html), [hmmlearn API](https://hmmlearn.readthedocs.io/en/stable/api.html), [SciPy generalized Pareto API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genpareto.html), [statsmodels VECM](https://www.statsmodels.org/stable/vector_ar.html), [PyWavelets CWT](https://pywavelets.readthedocs.io/en/latest/ref/cwt.html) and [FRED financial stress series](https://fred.stlouisfed.org/series/STLFSI4). These document computation; they do not replace a scholarly literature review.

## 3. Data and exploratory analysis

The experiment uses {manifest['n_prices']} observations of adjusted closes from {manifest['price_start']} through {manifest['price_end']}. Daily log differences produce {manifest['n_returns']} return observations. Prices come from the repository's original Yahoo Finance exports. VIX observations are recovered from the saved HMM input dataset and are not replaced with volatility estimates. All dates are parsed explicitly; duplicates and nonpositive prices cause failure. Raw per-asset legacy CSVs lack dates, so the merged dated adjusted-price file is the canonical input.

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

{table(metric)}

The lowest volatility RMSE is obtained by {winner.variant}; the adaptive model has RMSE {adaptive.rmse:.5f}. This outcome is reported directly rather than adjusting the index until the adaptive model wins. Forecast directional accuracy measures whether the forecast and realized future volatility move in the same direction relative to current realized volatility. Crisis ROC AUC uses future-event probabilities; same-day threshold F1 is a different task.

### 5.2 Crisis detection

{table(detection[detection.variant.eq('Adaptive')])}

The primary 90th-percentile same-day threshold yields F1 {detect.f1:.3f}. Because the current return enters both the signal and the contemporaneous label, this score measures after-close detection. It must not be cited as evidence that an investor could have forecast the day's loss.

### 5.3 Early-warning events

{table(eligible)}

Lead times are conditional on a preceding threshold crossing being found within the declared search interval. Missing leads do not become successful warnings. Crisis sample size is small, and persistent stress can generate both early signals and false alarms. The event table supports exploratory interpretation rather than a reliable estimate of crisis-prediction performance in new markets.

### 5.4 Significance and sensitivity

{table(significance)}

{table(sensitivity)}

Statistical significance is interpreted jointly with effect size and confidence intervals. A bootstrap interval containing zero gives no clear evidence of an RMSE improvement under the chosen resampling design. Tests are exploratory and their p-values are not corrected for the multiple comparisons in this experiment.

### 5.5 Component and descriptive diagnostics

Across {len(evt)} trailing tail fits, {(evt.fallback!='none').sum()} require empirical fallback. Parameter estimates, tail diagnostics, stationarity results, HMM means and transition persistence are available in the accompanying tables. Figures include annotated index comparisons, adaptive weight dynamics, event windows, Morlet scalograms and smoothed wavelet coherence with boundary regions masked. Coherence plots include no unearned significance claims.

### 5.6 External stress indices

{external_text}

The external-only and residual-augmented models are compared on the same external-data sample. This is a separate sample from the main ablation table, so its RMSEs must not be ranked directly against the main results. Latest revised FRED histories and assumed publication lags make this evidence exploratory. An incremental reduction in this table is not sufficient to claim an independently validated new systemic-risk signal.

### 5.7 Stability under entropy-window changes

The range of adaptive RMSE across the three entropy windows is {relative_sensitivity:.2%} of their mean. This describes local sensitivity to a single window parameter. It does not validate the chosen HMM state count, threshold family, clipping bounds or economic multipliers. Those choices remain limitations and potential subjects for a pre-registered replication.

## 6. Discussion

The index combines complementary definitions of stress, but complementarity in economic language does not imply independent statistical information. Conditional volatility, tail severity and HMM probabilities can rise together, making adaptive weighting unnecessary in some periods. Comparing component ablations with a realized-volatility persistence forecast is therefore essential. The resulting tables should guide whether the adaptive construction is retained, simplified or treated as a descriptive index.

Using a common market panic probability for all three assets makes the regime signal systemic within this small universe. It does not create three independent panic estimates. AAPL and MSFT are large constituents of SPY, so both the portfolio average and pairwise correlation component reflect overlapping economic exposures. Evidence from this universe cannot establish broad financial-system stress coverage.

The 252-day rolling POT window offers adaptation at the expense of few exceedances. A 90th-percentile threshold yields roughly 25 observations, and extrapolation to 99% expected shortfall is correspondingly uncertain. The explicit empirical fallback prevents undefined conditional expectations from silently contaminating the composite. It also makes the operative tail measure a hybrid estimator whose contribution requires direct ablation analysis.

A chronological forward filter fixes one common source of future information in HMM evaluations. Remaining limitations include revised adjusted-close histories, finite initial samples, manually specified multipliers, model-derived regime labels, overlapping forecast horizons and exploratory threshold choices. External FSI comparisons have an additional vintage limitation. None of these should be concealed by reporting a single high F1 score or visually attractive COVID plot.

## 7. Conclusion

A-CMSI is implemented as a reproducible after-close stress signal with separate contemporaneous and future-risk evaluations. It combines normalized conditional volatility, filtered panic probability and rolling extreme-loss severity, with a separate correlation-augmented specification. In the executed sample, {winner.variant} has the lowest held-out volatility RMSE; the adaptive model's RMSE is {adaptive.rmse:.5f}. The evidence supports comparison and refinement of stress composites without assuming adaptive weighting is universally beneficial. Broader assets, unrevised point-in-time data, pre-registered thresholds and independent evaluation periods are needed before deployment or strong predictive claims.

## Reproducibility and submission status

Run `python run_acmsi.py` from the repository root. The run manifest records configuration, package versions and input/source fingerprint. All tables in this manuscript are generated from saved output. The current manuscript is a substantive methods-and-results draft, not a verified 7,000-word submission with 50 scholarly references. SSRN upload and journal submission have not been performed; those are separate external actions requiring a finished author-reviewed manuscript and explicit instructions.
"""
    (output/"manuscript.md").write_text(manuscript,encoding="utf-8")
