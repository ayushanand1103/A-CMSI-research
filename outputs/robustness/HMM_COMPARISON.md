# HMM state-count comparison

The historical table is reproduced: five-state BIC 5568.11, six-state BIC 5532.27. This table uses initial-training data only.

## Matched chronological forecasts

| variant | n | rmse | rmse_ci_low | rmse_ci_high | mae | auc | brier | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| HMM3 | 1810 | 0.1067 | 0.0577 | 0.1563 | 0.059 | 0.6164 | 0.1974 | 0.1978 | 0.0385 | 0.0645 |
| HMM4 | 1810 | 0.1069 | 0.0574 | 0.1574 | 0.0591 | 0.6395 | 0.1929 | 0.2761 | 0.0792 | 0.1231 |
| HMM5 | 1810 | 0.1053 | 0.0557 | 0.1555 | 0.0569 | 0.6583 | 0.1869 | 0.2653 | 0.0835 | 0.127 |
| HMM6 | 1810 | 0.105 | 0.0559 | 0.1544 | 0.057 | 0.6481 | 0.1866 | 0.5312 | 0.182 | 0.2711 |
| RealizedVolBaseline | 1810 | 0.1227 | 0.0755 | 0.1664 | 0.0686 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |
| TrainMean | 1810 | 0.1118 | 0.0647 | 0.1606 | 0.0701 | 0.3867 | 0.2083 | 0.0 | 0.0 | 0.0 |

| candidate | reference | rmse_improvement | rmse_ci_low | rmse_ci_high | pvalue | p_holm_family | p_holm_global |
|---|---|---|---|---|---|---|---|
| HMM3 | HMM4 | 0.0002 | -0.0021 | 0.0017 | 0.8156 | 1.0 | 1.0 |
| HMM3 | HMM5 | -0.0014 | -0.0046 | 0.0004 | 0.1644 | 0.501 | 1.0 |
| HMM3 | HMM6 | -0.0017 | -0.0043 | 0.0002 | 0.0835 | 0.501 | 1.0 |
| HMM4 | HMM5 | -0.0016 | -0.0037 | 0.0003 | 0.0955 | 0.501 | 1.0 |
| HMM4 | HMM6 | -0.0019 | -0.0042 | 0.0001 | 0.0922 | 0.501 | 1.0 |
| HMM5 | HMM6 | -0.0003 | -0.0021 | 0.0016 | 0.7344 | 1.0 | 1.0 |

HMM6 has the smaller point-estimate volatility RMSE. The five-versus-six comparison does not establish a family-adjusted volatility advantage; the RMSE difference remains uncertain. This is not proof of equivalence. Training BIC alone does not establish out-of-sample overfitting.

Six states increase average training log density by 0.354 per observation, but change held-out conditional log density by -2.090 per day relative to five (three-month-block 95% bootstrap interval [-7.601, 1.375]). This train/test divergence is evidence consistent with overfitting for emission-density estimation; it does not automatically establish a volatility-forecast disadvantage. The interval includes zero, so a density disadvantage is not statistically established. The density interval is exploratory and not a multiplicity-adjusted confirmatory test.

| candidate | reference | n_monthly_blocks | test_log_density_improvement_per_day | ci_low | ci_high | training_log_density_improvement_per_day | bootstrap_monthly_block_length | bootstrap_draws | interpretation |
|---|---|---|---|---|---|---|---|---|---|
| HMM6 | HMM5 | 96 | -2.0896 | -7.6008 | 1.3747 | 0.3543 | 3 | 1000 | exploratory_conditional_density_generalization_not_volatility_loss |

## Occupancy, duration, redundancy and stability

| states | initial_bic | conditional_test_ll_per_day | mean_rare_state_fraction | min_expected_occupancy | median_autocorrelation_ess | median_expected_duration | median_refit_ari | median_aligned_agreement | redundant_pair_fraction | minimum_pair_kl | selected_hit_limit | selected_nonmonotone | failed_restarts | restarts | n_folds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 6791.064 | -11.1151 | 0.0 | 23.6364 | 31.8378 | 43.087 | 0.9633 | 0.9921 | 0.0 | 10.9897 | 0 | 0 | 0 | 288 | 96 |
| 4 | 5917.5216 | -11.6698 | 0.0 | 21.0481 | 33.5258 | 32.1628 | 0.575 | 0.8095 | 0.0 | 6.7754 | 0 | 0 | 0 | 288 | 96 |
| 5 | 5568.1103 | -12.8373 | 0.0083 | 10.0 | 37.0134 | 26.4765 | 0.5551 | 0.7698 | 0.0 | 7.9941 | 0 | 1 | 0 | 288 | 96 |
| 6 | 5532.271 | -14.9269 | 0.0122 | 9.8175 | 41.7899 | 22.9985 | 0.434 | 0.7302 | 0.0 | 0.2388 | 0 | 1 | 0 | 288 | 96 |

Fractional occupancy is the sum of forward probabilities. Kish weight ESS describes concentration of state responsibilities and is not an independent-time sample size. Autocorrelation ESS uses positive autocorrelations through lag 60 of the state-probability series; it is an approximate dependence diagnostic. A state is flagged rare below max(20,1% of training observations). Expected state duration is 1/(1-A_ss). Redundancy flags symmetric Gaussian KL below 0.1 in standardized feature space; the threshold is a fixed descriptive heuristic, not a significance test. Detailed per-state, per-restart, per-fold and transition tables are retained in `hmm/states_*/`.

Refit stability re-filters the same last 126 shared training observations under adjacent fits, comparing adjusted Rand index, Hungarian-aligned agreement, and posterior differences. It does not assume raw state IDs persist across refits. Risk ranks may reorder and are model-derived labels.

The highest training likelihood selects one of seeds 42/43/44 at every origin. Fits hitting 200 iterations or finishing with a negative likelihood increment are disclosed, not silently called converged. Neither interpretability nor smaller training BIC is used to decide the winner. The production default remains the historical five-state specification for continuity, not a newly established optimal state count. A new independent sample is needed before selecting a state count on performance grounds.

Positive improvement means the candidate improves on the reference (reference minus candidate for RMSE/MAE/Brier; candidate minus reference for AUC/F1). Bootstrap intervals are paired circular moving-block intervals, 1,000 draws, block length 30 trading days; the separate 60-day analysis changes both block length and HAC bandwidth. Crisis probabilities use the fixed 0.5 cutoff. AUC is threshold-free. Precision/recall/F1 are for future 30-day events here, not same-day detection. Holm adjustment controls the stated comparison family; the global correction also includes the other experimental families. These intervals are marginal, not simultaneous confidence bands.
