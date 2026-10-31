# A-CMSI implementation decisions

The research plan is a methodological reference, not an instruction to force a winning result or publish work externally. The executable implementation makes the following choices explicit.

## Timeline and data

The canonical input is `Data/prices_clean.csv`. Dated merged adjusted closes retain the price history; undated raw per-asset exports are not used for alignment. Returns are recomputed as log price differences. VIX is an observed input taken from `Data/HMM data/HMM_Input_Features.csv`; it is available from January 2016 in that export. No later VIX values are backfilled into earlier days.

The initial training period is 756 trading observations. ARIMA and variance specifications are selected on this period by BIC. Selected specifications are re-estimated every 21 trading days, with parameters held fixed during the next block. The starting date, last scored date and input hashes are recorded in `outputs/run_manifest.json`.

Every daily signal uses data available through that day's close. All fitted scalers and model parameters used on a test block come from earlier observations. HMM likelihoods pass through a forward recursion:

`a_t(s) ∝ f_s(x_t) Σ_j a_(t-1)(j) A_(j,s)`.

Unlike `predict_proba` on a complete sample, this does not condition today's probability on later observations. A monthly refit re-filters the training history to initialize the next block, but previously exported out-of-sample component values are not revised. Training reconstructions before the first out-of-sample date are retained to initialize rolling statistics and are excluded from forecast calibration and evaluation.

## Components

**V** is a trailing 252-day z-score of conditional standard deviation, clipped to [-3,3]. ARIMA innovations feed GARCH, GJR-GARCH or EGARCH; normal and Student-t candidates are compared on initial-training BIC. The new implementation selects its models independently of the legacy full-sample notebook results.

**P** is the forward-filtered probability of the highest-risk HMM state. Training means rank states by VIX, realized volatility, conditional volatility and inverse return. That rule is recomputed for each refit to avoid treating numeric state IDs as persistent economic labels. A common market probability is used in each asset index; it is not three asset-specific HMM estimates. State count is five by default, following the latest saved project specification; alternatives 2–6 are compared on initial training data. Multiple deterministic random restarts select the highest training likelihood; state-count selection never uses future evaluation data.

**T** is trailing 252-day peaks-over-threshold expected shortfall. Losses are negative log returns; excesses above the window's 90th percentile fit a GPD with location fixed at zero. At least 20 excesses are needed. For tail probability `1-alpha`, exceedance rate `p_u`, shape `xi`, scale `beta` and threshold `u`:

`VaR_alpha = u + beta/xi * [(p_u/(1-alpha))^xi - 1]`

with logarithmic limit at `xi=0`, and

`ES_alpha = (VaR_alpha + beta - xi*u)/(1-xi)` for `xi<1`.

A quantile below the fitted threshold is left missing in the static sensitivity table. An unstable fit or infinite GPD ES uses a disclosed empirical ES99 fallback; no arbitrary shape clipping is used. Raw T is then normalized with the same trailing 252-day rule as V. Full-sample static fits, MEF plots and Q-Q plots are descriptive only.

**C**, evaluated separately, is the trailing 21-day mean of three pairwise return correlations, normalized using 252 days. Correlation measures co-movement rather than negative co-movement specifically; high C alone is not proof all assets are falling. No daily cointegration-breakdown claim is made.

## Weight engine

For component i and W=63 observations, define `p_i,k = |Z_i,k| / Σ_(k in window) |Z_i,k|`. The denominator is over **time within a component**, correcting the ambiguous component/time indices in the plan. Entropy is `H_i = -Σ_k p_i,k log(p_i,k)/log(W)`. A component concentrated in a few isolated spikes can have lower entropy than one with sustained activity; entropy does not directly measure predictive information or tail severity. This choice follows the plan's activity-weight interpretation and is tested against simpler baselines.

Base weights `e_i = H_i/Σ_j H_j` become equal only if a complete window has zero entropy everywhere. Warmup windows remain missing. Five-state economic multipliers interpolate linearly between documented bull and panic endpoints using the posterior expected risk rank. They are explicit assumptions, not estimated optimal coefficients. The intermediate three-state neutral vector is not exactly preserved by interpolation; this is a declared extension for the existing five-state model.

Let `q_i = e_i * multiplier_i`. Final weights use

`w_i = m + (1-Km) q_i/Σ_j q_j`, with `m=0.05`.

This guarantees the floor and unit sum simultaneously; simply clipping then renormalizing could violate the floor. The per-asset index is `Σ_i w_i Z_i`. Portfolio CMSI is the arithmetic average of three asset scores.

## Comparisons

The eight output specifications are Adaptive, Equal, PCA, Entropy, NoEVT, NoHMM, NoGARCH and Adaptive4. PCA uses absolute PC1 loadings, normalized to positive unit-sum weights, fitted to strictly earlier component observations every 21 days. Absolute loadings avoid arbitrary PCA sign flips; this is an explicit weighting convention rather than an unmodified principal-component score.

NoHMM removes both the P signal and regime multipliers; retaining P with unit multipliers would duplicate entropy-only. NoGARCH uses 21-day realized volatility. NoEVT removes T. Every available variant is compared on common eligible dates within an evaluation run.

## Prediction and detection

The index is a unitless stress signal, not a volatility forecast. Each variant therefore receives the same expanding standardized ridge calibration to log next-30-day annualized realized volatility. It also receives the same expanding logistic calibration to future crisis occurrence and filtered-regime change. Training labels must finish strictly before the first date of the predicted block. At least 126 mature out-of-sample signal/label observations are required. Ridge and logistic hyperparameters are fixed in advance; no test-period tuning is used.

Current 30-day realized volatility supplies a persistence baseline. RMSE/MAE are in annualized decimal-volatility units. Directional accuracy compares forecast and realized change relative to current volatility. Transition labels measure changes in future filtered risk ranks and are explicitly model-derived proxies.

Same-day crisis labels use SPY daily return below -3% or trailing 20-day cumulative return below -10%. Threshold signals use expanding historical quantiles computed strictly before today. Same-day precision/recall/F1 are detection after close; future-event AUC/Brier scores come from separately calibrated forecasts. The final 30 observations have no mature future target and are excluded from forecast scoring, while their after-close indices are still exported.

Early-warning events group repeated threshold breaches using a 20-day refractory period. Last crossings are searched only in the prior 60 trading days. Five-, ten- and twenty-day warning rates exclude the event day. Missing coverage is marked rather than counted as a successful warning. Lagged volatility correlations are descriptive and use complete future windows.

## Inference and sensitivity

The two-sided squared-error Diebold-Mariano test is implemented directly, rather than relying on the plan's nonexistent `arch.utility.dm_test` call. A Bartlett HAC estimate over 29 lags accounts for overlapping 30-day horizons, with an HLN small-sample correction. Circular moving-block bootstrap with 30-day blocks and 1,000 replicates resamples paired errors to estimate the interval for baseline RMSE minus adaptive RMSE. Positive improvements favor Adaptive. Multiple comparisons are not adjusted and are labeled exploratory.

Entropy windows 21, 63 and 126 receive complete recalculation and held-out evaluation. Wavelet power and coherence use complex Morlet coefficients, scale-dependent time smoothing, scale smoothing and masked boundary regions. They are descriptive, without Monte Carlo significance contours. Full-sample LOESS outputs do not enter forecasts. Johansen/ECM and exact supplementary R break/stability diagnostics are descriptive context.

## External data and publication

FRED STLFSI4 is weekly; KCFSI is monthly. External series are cached as returned by FRED and shifted by conservative 7- and 45-calendar-day assumed release lags. Rolling correlations and expanding incremental-volatility comparisons use these aligned series. Revised observations and assumed release lags mean this comparison is not a vintage-correct trading backtest. A true point-in-time benchmark would require ALFRED vintages and verified release calendars.

Results tables, a methods/results manuscript draft and figures are generated from actual execution. Bibliographic padding, predetermined winning numbers, preprint upload and journal submission are excluded from automation. The manuscript needs author review and a verified scholarly literature review before submission.
