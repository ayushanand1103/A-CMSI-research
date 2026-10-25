# Research-plan implementation status

The completed computational pipeline uses `run_acmsi.py`; original exploration remains in `Analysis/`.

| Plan phases | Implementation and artifacts |
|---|---|
| 1–2: preparation and exploration | Dated adjusted prices validated; returns rebuilt; descriptive statistics, stationarity, rolling correlations and EDA figures exported. Exact R Bai-Perron/Chow supplement executed. |
| 3: long-run relationships | Log-price Johansen tests on all assets and pairs; ECM only for admissible nonzero ranks. |
| 4: mean process | Initial-training ARIMA grid, BIC selection, monthly expanding refits, innovation diagnostics. |
| 5: conditional volatility | GARCH/GJR/EGARCH with normal and Student-t comparisons; monthly fits and forward conditional volatility; R sign-bias and Nyblom diagnostics executed separately. |
| 6: regimes | Initial-training 2–6-state comparison; monthly five-state HMM; filtered probabilities, automatic risk-ranked state identification, transition tables and regime-duration/probability plots. |
| 7: tail risk | MEF, GPD threshold sensitivity, Q-Q diagnostics, 95/99% VaR and ES, 252-day rolling ES99, disclosed fallback status. |
| 8: multi-scale analysis | Morlet CWT power and smoothed wavelet coherence, with masked edge regions and no significance claims. |
| 9: index construction | Trailing normalization, entropy weights, soft regime factors, exact weight floor, per-asset and portfolio indices, annotated figures. Optional C evaluated as Adaptive4. |
| 10: ablations | Equal, PCA, Entropy, NoEVT, NoHMM, NoGARCH, Adaptive, plus Adaptive4. |
| 11: early warning | Deduplicated crash events, 5/10/20-day warnings, crossing leads, lead correlations, event-specific shaded warning figures. |
| 12: crisis detection | Historical quantile signals, precision/recall/F1, detection ROC/AUC, separately calibrated future-crisis forecasts and ROC curves. |
| 13: validation and inference | Monthly expanding fits, mature-label embargo, future volatility/crisis/regime-proxy targets, RMSE/MAE/direction, HAC DM comparisons, 1,000-replicate paired block bootstrap. |
| 14: sensitivity | Complete 21/63/126-day entropy recalculations and validation exports. |
| 15: external comparison | STLFSI4 and KCFSI downloaded, assumed release lags, rolling correlations, expanding residualization and incremental future-volatility comparison. Revised-data limitation disclosed. |
| 16: writing | Generated abstract, introduction, methodological context, data, methods, actual results, discussion and conclusion in `outputs/manuscript.md`. This is an author-review draft, not a verified journal-ready paper. |
| Additional plan notes | Descriptive LOESS trends exported; four-component extension kept separate from the core index. |

The nine numerical/timing unit tests and `verify_outputs.py` check formulas, prefix invariance, label maturity, output completeness and weight/probability normalization.

Remaining publication work: verify and complete the scholarly bibliography, author review and journal formatting, final manuscript approval, SSRN upload and journal submission. No external publication has been performed. The research-plan word count and 50-reference target are not represented as completed deliverables.

No performance claim is predetermined. The executed held-out comparison favors NoHMM on volatility RMSE, and does not establish adaptive superiority over equal weighting.
