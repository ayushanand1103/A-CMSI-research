# Final manuscript review — 31 October 2026

**Finding retained: adaptive weighting has no demonstrated predictive advantage over simpler weighting baselines in this sample.** This is stated explicitly in both the abstract and conclusion. It is not converted into a claim of equivalence or a proof that every possible adaptive method is ineffective.

## Tables and results

All nine tables were independently parsed and compared against their corresponding generated CSV outputs: **442 displayed fields**, including labels, values and interval endpoints, agree within four-decimal rounding. The row-by-row evidence is in `table_cell_checks.csv` and `table_summary.csv`. **336 point-metric fields** were independently recomputed from saved forecasts using NumPy and scikit-learn, including RMSE, MAE, AUC, Brier, precision, recall, F1 and sample size; all agree to numerical tolerance. Bootstrap endpoints and adjusted p-values were checked against their generated outputs rather than recalculating or selectively changing the experiments.

| Manuscript table | Verified output |
|---|---|
| Original comparison | `original/tables/main_ablation_metrics.csv` |
| HMM state counts | `evaluation/hmm_metrics.csv` |
| Controlled ablations | `evaluation/ablation_metrics.csv` |
| Future crisis prediction | `evaluation/ablation_metrics.csv` |
| EVT forecast grid | `evaluation/evt_metrics.csv` |
| HMM diagnostics | `evaluation/hmm_diagnostic_summary.csv`, checked against per-state/refit outputs during the audit |
| Paired Adaptive comparisons | `evaluation/all_paired_global_holm.csv` |
| Conditional-information regressions | `evaluation/ablation_metrics.csv` |
| Empirical fallback rates | `evt/parameter_stability.csv`, grouped by experiment |

No data or model outputs were changed. Original price/return counts, scoring dates, 0.10532 Adaptive / 0.10457 Equal / 0.10411 NoHMM RMSEs, five-state/six-state BICs, the uncertain state-count comparison, five all-fallback EVT configurations, the original detection F1 of 0.300 and the conditional 7.5-day warning lead remain consistent with their saved evidence. The 7.5-day lead is conditional on four observed crossings among five eligible events, not a successful warning for every crisis.

## Mathematical corrections and clarifications

These align the written methods with existing code; they do not modify the estimators or results:

1. Price is denoted by Pi, distinct from panic probability P.
2. Component-vector definitions make clear that V/P/T are normalized once, not twice.
3. Entropy and final weights carry the asset subscript because each asset's V/T signals yield different weights. Panic probabilities and regime factors remain common market signals.
4. M denotes the component count in the affine weight-floor equation; K remains the HMM state count. The condition `0 <= m < 1/M` is explicit.
5. Component magnitude-zero, entropy/deficit-total-zero, `0 log 0`, missing-window and zero-standard-deviation cases are described consistently with the implementation.
6. HMM start-probability initialization is distinguished from subsequent transition recursion.
7. Tail confidence tau is distinct from HMM filtered probabilities alpha. The GPD extrapolation condition, xi=0 limit and xi<1 finite-ES condition are stated.
8. The empirical fallback is described as the average of observed losses at or above the empirical 99th percentile, without fractional boundary weighting.
9. The crisis label explicitly distinguishes a daily **log-return** cutoff of -0.03 from a trailing 20-day **simple price-return** cutoff of -0.10.
10. Ridge alpha=1 is distinguished from logistic inverse regularization C=1. Volatility-baseline rows' crisis probabilities are identified as training prevalence.
11. HMM diagnostic captions identify medians and the state/refit denominator for rare-state fractions. Emission-density diagnostics use all 2,008 operational dates, whereas calibrated volatility scores use 1,810 dates.
12. The supplementary three-month density bootstrap is explicitly described as exploratory and added after inspecting the density pattern.

The POT VaR/ES, HMM forward recursion, entropy normalization, affine minimum-weight mapping and HLN correction agree with the implemented formulas. Log-volatility retransformation without a mean-bias correction, revised input histories, sparse tail fits, few crisis episodes and dependence uncertainty remain disclosed limitations.

## Citations and authorship

See `CITATION_REVIEW.md` for all 16 entries and the scope of external checks. All 14 original references are retained; Holm and Künsch support the newly used robustness methods. Pickands' author suffix and DOI were clarified. Every in-text citation is defined, and all listed entries are cited. Some publisher full-text access was restricted; the review does not claim unrestricted independent full-text verification.

Author name, correspondence and affiliation match the local reference preprint. Present affiliation, email deliverability, funding/conflict declarations and submission licensing still require author confirmation. The DOI is preserved without inventing a new version identifier. No submission was performed.

## Conclusion review

- Adaptive superiority is **not** claimed.
- NoHMM's lower RMSE is reported as a point estimate with uncertainty, not proof that HMM information is useless.
- Six states' lower point-estimate RMSE is retained, without asserting a statistically established advantage or conclusive overfitting.
- Non-significance is not interpreted as equivalence.
- Entirely empirical fallback cells are not described as successful GPD validation.
- Same-day after-close detection is not described as advance crisis prediction.
- Retrospective re-use of the historical evaluation period is disclosed.

## Build and verification

Reproducible check: `.venv-reproduction/Scripts/python -m research_audit.final_review` from the repository root. Machine-readable status is in `review_checks.json`. The updated compiled PDF and source ZIP are validated separately in `../manuscript/BUILD_STATUS.json`; the pre-review versions are retained in `before_review/`. Author sign-off remains a separate step from these scientific and technical checks.


## Author-confirmed submission update — 31 October 2026

The author requested removal of the CHRIST affiliation; the submission copy now identifies Ayush Anand as an independent researcher. The author explicitly confirmed sole authorship, no external funding, no competing interests and the AI disclosure, and chose CC BY 4.0. The internal candidate-file/drafting note was removed from the paper and retained only in the audit history. The PDF and source ZIP were rebuilt and verified. Models and results were not optimized or refitted. No arXiv upload occurred because no authenticated submission connection was available. See arxiv_submission/author_confirmation.json and arxiv_submission/SUBMIT_TO_ARXIV.md.
