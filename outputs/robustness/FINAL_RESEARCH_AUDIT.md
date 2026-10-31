# Final scientific research audit

Research identity: Ayush Anand, A-CMSI, original Zenodo DOI **10.5281/zenodo.23682477**. This is a robustness revision of the same work, not a claim that a new Zenodo version has already been registered.

## Findings supported by execution

1. Original five-state results were reproduced from fresh fits; numeric comparisons and data/source integrity checks passed.
2. All four state-count paths and all nine rolling EVT specifications completed. Each state count used 96 refits and three starts. All requested baselines remain visible.
3. HMM6 has the smaller point-estimate volatility RMSE. The five-versus-six comparison does not establish a family-adjusted volatility advantage; the RMSE difference remains uncertain. This is not proof of equivalence. Training BIC alone does not establish out-of-sample overfitting.
   Six states increase average training log density by 0.354 per observation, but change held-out conditional log density by -2.090 per day relative to five (three-month-block 95% bootstrap interval [-7.601, 1.375]). This train/test divergence is evidence consistent with overfitting for emission-density estimation; it does not automatically establish a volatility-forecast disadvantage. The interval includes zero, so a density disadvantage is not statistically established. The density interval is exploratory and not a multiplicity-adjusted confirmatory test.
4. Removing P alone gives RMSE 0.10519; removing multipliers alone gives 0.10478; removing both gives 0.10411, compared with 0.10532 for Adaptive. The paired RMSE intervals for these three Adaptive contrasts include zero. This pattern is consistent with redundant/noisy contributions under this fixed calibration, but it does not identify a unique mechanism or prove that HMM information is useless. No universal adaptive advantage is established.
5. 5 of nine EVT configurations use empirical fallback for every operative estimate in every asset under the original minimum-exceedance constraint. Those cells do not validate a fitted GPD.
6. The historical PCA weighting lacks an explicit floor. The audit preserves it and adds PCAFloor, rather than rewriting original scores.
7. 17 formula, timing and numerical tests passed. Full artifact checks are supplied separately.
8. A fully isolated, exact-lock environment also passed all 17 tests and reproduced calibrated forecasts without `.deps` or global fallback. The initial premature check before installation completed is retained in `clean_environment_first_attempt.log`; it was rerun successfully after dependencies were installed.

## Reference material and manuscript

The exact files `ACMSI_arXiv_Preprint_Candidate.pdf`, `ACMSI_arXiv_Source_Candidate.zip`, and `ACMSI_Submission_Readiness_Audit.md` were unavailable in the repository, Downloads/Documents and Codex attachments locations checked. A distinct local `ACMSI_Zenodo_Preprint_v2.pdf` dated 27 October 2026 was found in Downloads and used as additional reference, alongside the repository manuscript. Its original mathematical definitions, research question and 14 bibliographic entries are retained in the revised LaTeX source. It was treated as a reference draft, not validated evidence. The original DOI is author supplied; the remote Zenodo record could not be independently retrieved in this session.

## arXiv readiness assessment

The computational audit supports a reproducible research preprint with limited, explicitly retrospective claims. It does not establish a superior forecasting model, broad systemic-risk coverage, equivalence of state counts, or reliable early crisis prediction. Compilation and source-package validation are recorded in `manuscript/BUILD_STATUS.json`. Author review is still required for claims, affiliation, disclosures, licensing, bibliography and choice of arXiv category. No submission, endorsement request, upload or new DOI registration has been performed.

Unresolved scientific limitations: revised daily inputs; three overlapping U.S. equity exposures; only a few crisis episodes; approximate dependence treatment; nonstationary financial data; sparse POT tail samples; selected HMM iteration-limit/nonmonotonic cases; economic multipliers chosen by design; after-close timing; and test-period reuse. These belong in the paper, not just a supplementary log.

## Commands

See `README.md` in this folder. Data hashes, exact dependency lock, seeds, configurations, execution logs and original/revised outputs are included. Main data and original production code were not modified to improve performance.
