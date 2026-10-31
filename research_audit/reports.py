"""Reports and publication source built exclusively from completed experiments."""
from datetime import datetime,timezone
import json
import logging
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from acmsi.report import table
from .provenance import sha256

LOG=logging.getLogger(__name__)


def read(out,name):
    return pd.read_csv(out/"evaluation"/name)


def hmm_diagnostics(out):
    rows=[]
    for k in (3,4,5,6):
        path=out/"hmm"/f"states_{k}"
        occupancy=pd.read_csv(path/"occupancy.csv"); stability=pd.read_csv(path/"stability.csv")
        models=pd.read_csv(path/"models.csv"); restarts=pd.read_csv(path/"restarts.csv")
        redundancy=pd.read_csv(path/"redundancy.csv")
        selected=models[["fold","selected_seed"]].merge(restarts,left_on=["fold","selected_seed"],right_on=["fold","seed"])
        rows.append(dict(states=k,initial_bic=float(models.train_bic.iloc[0]),
                         conditional_test_ll_per_day=float(models.conditional_test_ll.sum()/models.n_test.sum()),
                         mean_rare_state_fraction=float(occupancy.rare.mean()),
                         min_expected_occupancy=float(occupancy.expected_occupancy.min()),
                         median_autocorrelation_ess=float(occupancy.autocorrelation_ess.median()),
                         median_expected_duration=float(occupancy.expected_duration.replace(np.inf,np.nan).median()),
                         median_refit_ari=float(stability.adjusted_rand.median()),
                         median_aligned_agreement=float(stability.hungarian_agreement.median()),
                         redundant_pair_fraction=float(redundancy.near_redundant.mean()),
                         minimum_pair_kl=float(redundancy.symmetric_kl.min()),
                         selected_hit_limit=int(selected.hit_iteration_limit.sum()),
                         selected_nonmonotone=int((~selected.monotone_final).sum()),
                         failed_restarts=int(restarts.status.ne("ok").sum()),
                         restarts=len(restarts),n_folds=len(models)))
    result=pd.DataFrame(rows)
    result.to_csv(out/"evaluation/hmm_diagnostic_summary.csv",index=False)
    # Conditional emission-density generalization is a different target from volatility RMSE.
    a=pd.read_csv(out/"hmm/states_6/models.csv")
    b=pd.read_csv(out/"hmm/states_5/models.csv")
    delta=a.conditional_test_ll.to_numpy()-b.conditional_test_ll.to_numpy()
    count=a.n_test.to_numpy()
    from .statistics import block_indices
    boot=[float(delta[ix].sum()/count[ix].sum()) for ix in block_indices(len(a),1000,3,42)]
    ci=np.quantile(boot,[.025,.975])
    pd.DataFrame([dict(candidate="HMM6",reference="HMM5",n_monthly_blocks=len(a),
        test_log_density_improvement_per_day=delta.sum()/count.sum(),ci_low=ci[0],ci_high=ci[1],
        training_log_density_improvement_per_day=float((a.train_ll/a.n_train-b.train_ll/b.n_train).mean()),
        bootstrap_monthly_block_length=3,bootstrap_draws=1000,
        interpretation="exploratory_conditional_density_generalization_not_volatility_loss")]).to_csv(
            out/"evaluation/hmm_likelihood_comparison.csv",index=False)
    return result


def generate(root,out,cfg):
    status=json.loads((out/"audit_status.json").read_text())
    tests=json.loads((out/"test_results.json").read_text())
    clean_path=out/"clean_environment_status.json"
    clean=json.loads(clean_path.read_text()) if clean_path.exists() else None
    diagnostic=hmm_diagnostics(out)
    hmm=read(out,"hmm_metrics.csv"); ablation=read(out,"ablation_metrics.csv")
    weighting=read(out,"weighting_metrics.csv"); evt=read(out,"evt_metrics.csv")
    paired=read(out,"all_paired_global_holm.csv"); paired60=read(out,"all_paired_global_holm_60.csv")
    tail=pd.read_csv(out/"evt/parameter_stability.csv")
    original_weights=pd.read_csv(out/"original_weight_audit.csv")
    effective=json.loads((out/"evaluation/effective_sample.json").read_text())
    comparison=paired[(paired.family=="hmm")&(paired.candidate=="HMM5")&(paired.reference=="HMM6")].iloc[0]
    hmm56=hmm[hmm.variant.isin(["HMM5","HMM6"])].sort_values("rmse")
    better=hmm56.iloc[0].variant
    supported=bool(comparison.p_holm_family<.05 and (comparison.rmse_ci_low>0 or comparison.rmse_ci_high<0))
    conclusion=(f"{better} has the smaller point-estimate volatility RMSE. The five-versus-six comparison "
                +("shows a family-adjusted squared-loss difference, with the paired RMSE interval excluding zero."
                  if supported else "does not establish a family-adjusted volatility advantage; the RMSE difference remains uncertain.")
                +" This is not proof of equivalence. Training BIC alone does not establish out-of-sample overfitting.")
    density=read(out,"hmm_likelihood_comparison.csv")
    dd=density.iloc[0]
    density_text=(f"Six states increase average training log density by {dd.training_log_density_improvement_per_day:.3f} "
                  f"per observation, but change held-out conditional log density by {dd.test_log_density_improvement_per_day:.3f} "
                  f"per day relative to five (three-month-block 95% bootstrap interval "
                  f"[{dd.ci_low:.3f}, {dd.ci_high:.3f}]). This train/test divergence is "
                  +("evidence consistent with overfitting for emission-density estimation; it does not automatically establish a volatility-forecast disadvantage."
                    if dd.test_log_density_improvement_per_day<0 else "not evidence of deterioration in held-out emission density.")
                  +(" The interval includes zero, so a density disadvantage is not statistically established." if dd.ci_low<=0<=dd.ci_high else "")
                  +" The density interval is exploratory and not a multiplicity-adjusted confirmatory test.")
    cols=["variant","n","rmse","rmse_ci_low","rmse_ci_high","mae","auc","brier","precision","recall","f1"]
    metric_lookup=ablation.set_index("variant")
    ablation_finding=(f"Removing P alone gives RMSE {metric_lookup.loc['NoProbability','rmse']:.5f}; removing multipliers alone gives "
        f"{metric_lookup.loc['Entropy','rmse']:.5f}; removing both gives {metric_lookup.loc['NoHMM','rmse']:.5f}, "
        f"compared with {metric_lookup.loc['Adaptive','rmse']:.5f} for Adaptive. The paired RMSE intervals for these "
        "three Adaptive contrasts include zero. This pattern is consistent with redundant/noisy contributions under this fixed "
        "calibration, but it does not identify a unique mechanism or prove that HMM information is useless.")
    paircols=["candidate","reference","rmse_improvement","rmse_ci_low","rmse_ci_high","pvalue","p_holm_family","p_holm_global"]
    definitions="""Positive improvement means the candidate improves on the reference (reference minus candidate for RMSE/MAE/Brier; candidate minus reference for AUC/F1). Bootstrap intervals are paired circular moving-block intervals, 1,000 draws, block length 30 trading days; the separate 60-day analysis changes both block length and HAC bandwidth. Crisis probabilities use the fixed 0.5 cutoff. AUC is threshold-free. Precision/recall/F1 are for future 30-day events here, not same-day detection. Holm adjustment controls the stated comparison family; the global correction also includes the other experimental families. These intervals are marginal, not simultaneous confidence bands."""
    htext=f"""# HMM state-count comparison

The historical table is reproduced: five-state BIC {diagnostic.loc[diagnostic.states==5,'initial_bic'].iloc[0]:.2f}, six-state BIC {diagnostic.loc[diagnostic.states==6,'initial_bic'].iloc[0]:.2f}. This table uses initial-training data only.

## Matched chronological forecasts

{table(hmm[cols])}

{table(paired[paired.family.eq('hmm')][paircols])}

{conclusion}

{density_text}

{table(density)}

## Occupancy, duration, redundancy and stability

{table(diagnostic)}

Fractional occupancy is the sum of forward probabilities. Kish weight ESS describes concentration of state responsibilities and is not an independent-time sample size. Autocorrelation ESS uses positive autocorrelations through lag 60 of the state-probability series; it is an approximate dependence diagnostic. A state is flagged rare below max(20,1% of training observations). Expected state duration is 1/(1-A_ss). Redundancy flags symmetric Gaussian KL below 0.1 in standardized feature space; the threshold is a fixed descriptive heuristic, not a significance test. Detailed per-state, per-restart, per-fold and transition tables are retained in `hmm/states_*/`.

Refit stability re-filters the same last 126 shared training observations under adjacent fits, comparing adjusted Rand index, Hungarian-aligned agreement, and posterior differences. It does not assume raw state IDs persist across refits. Risk ranks may reorder and are model-derived labels.

The highest training likelihood selects one of seeds 42/43/44 at every origin. Fits hitting 200 iterations or finishing with a negative likelihood increment are disclosed, not silently called converged. Neither interpretability nor smaller training BIC is used to decide the winner. The production default remains the historical five-state specification for continuity, not a newly established optimal state count. A new independent sample is needed before selecting a state count on performance grounds.

{definitions}
"""
    (out/"HMM_COMPARISON.md").write_text(htext,encoding="utf-8")
    tcols=["experiment","asset","exceedance_median","fallback_fraction","xi_median","xi_p95","beta_median","VaR99_median","ES99_median","ES99_max"]
    etext=f"""# EVT sensitivity audit

All nine requested threshold/window combinations were executed chronologically with fixed minimum 20 exceedances. The GPD tail window changes; the component's trailing z-score normalization remains 252 days. Full-sample descriptive fits are in `evt/full_sample_descriptive.csv` and never enter forecast selection.

## Raw tail diagnostics

{table(tail[tcols],6)}

High thresholds can make an experiment entirely empirical: approximately 13 exceedances at 95%/252 days, 19 at 95%/378 days, and 7–13 at 97.5% across these windows do not meet the original 20-exceedance rule. A 100% fallback rate is not a successful GPD validation. Identical fallback-based specifications are not independent evidence for threshold robustness. Undefined GPD ES at xi>=1 remains missing in the diagnostics; the operational hybrid score uses the disclosed empirical ES99 instead. No failed shape/scale estimate is replaced with a fabricated value. Daily estimates, fit exceptions, count failures and fallback flags are all retained.

## Matched future-risk evaluation

{table(evt[cols])}

{table(paired[paired.family.eq('evt')][paircols])}

Each EVT family comparison uses identical signals/labels for calibration and scoring, and a second `*_universal_metrics.csv` analysis uses the same calibration support across every HMM/EVT/weighting family. Different warmup lengths reduce evaluation coverage, so these RMSEs must not be ranked against the original 1,810-date baseline without matching dates. Clipping normalized components can conceal instability in raw ES, so raw parameter tables must be interpreted jointly with score/forecast tables.

{definitions}
"""
    (out/"EVT_SENSITIVITY.md").write_text(etext,encoding="utf-8")
    atext=f"""# HMM ablation and weighting audit

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

{table(ablation[cols])}

{table(paired[paired.family.eq('ablation')][paircols])}

## Weighting alternatives

{ablation_finding}

{table(weighting[cols])}

{table(paired[paired.family.eq('weighting')][paircols])}

## Constraint verification

{table(original_weights)}

Original PCA loadings have no imposed minimum-weight floor. They must not be described as satisfying that constraint when the saved weights fall below 0.05. The original entropy export is the base entropy vector, before final flooring; the actual entropy index applies the floor. Original results are preserved and PCAFloor is an additional disclosed specification. New-weight checks are in `evaluation/new_weight_constraints.csv`.

NoHMM's original lower point-estimate RMSE is not by itself a causal explanation of HMM failure. The controlled removals and conditional-information tests isolate observable changes under this calibration, but correlated components, sparse crises, state-label instability and fixed multipliers limit mechanistic inference. Nonsignificant differences do not establish that the HMM contains no information or that the models are equivalent.

{definitions}
"""
    (out/"ABLATION_ANALYSIS.md").write_text(atext,encoding="utf-8")
    stext=f"""# Statistical validation

{definitions}

## Original result reproduction

Fresh five-state estimation reproduced the original saved model-comparison metrics. Detailed tolerance checks are in `reproduction_comparison.csv`; integrity status is `{status['checks_passed']}`. The original pipeline and observed CSV data were preserved. Independent HMM and calibration loops were checked against the fresh original implementation.

The separate clean-environment verification is recorded in `clean_environment_status.json`: {clean}. The full fresh-fit reproduction used the project environment; the clean environment independently passed the copied-source tests and reproduced calibrated forecasts, without project `.deps` or global package fallback.

## Dependence and multiplicity

Of {len(paired)} primary squared-loss comparisons, {int((paired.p_holm_global<.05).sum())} pass the global Holm correction. This is a statement about these tests and their power, not evidence that all specifications are equivalent. Bootstrap RMSE intervals and HAC/DM p-values can disagree because their finite-sample approximations differ; the audit reports both rather than selecting the favorable procedure.

There are {effective['n_forecasts']} primary ablation forecast dates, but overlapping 30-day targets are not {effective['n_forecasts']} independent observations. The crude number of disjoint horizon-sized blocks is {effective['rough_nonoverlapping_windows']:.1f}; this is not an exact inferential ESS. There are {effective['crisis_positive_days']} positive future-event dates and {effective['crisis_positive_episodes']} contiguous positive-label episodes. A crisis spanning many dates must not be represented as many independent crises.

The original squared-error DM test uses a Bartlett HAC estimate through lag 29 and an HLN horizon-30 correction. It is an approximate inference procedure, not a finite-sample guarantee. Primary 30-day block bootstrap and 60-day block/HAC sensitivity results are retained. Labels and forecast errors can have dependence beyond the overlap horizon. The 60-day analysis tests one longer scale, not all possible nonstationarity.

Holm family and global adjustments are supplied for squared-loss DM p-values. Bootstrap intervals for AUC, Brier, precision, recall and F1 are descriptive paired uncertainty intervals; no independent-day binomial or DeLong claim is made. Bootstrap draws without both classes are counted and omitted from AUC intervals, not assigned artificial AUC values.

## Complete paired comparisons

{table(paired[['family']+paircols])}

## Longer-dependence sensitivity

{table(paired60[['family']+paircols])}

## Timing audit and remaining bias

The code fits model parameters/scalers using dates before the next block. GaussianHMM forward recursion conditions only on observations through the signal date. Conditional volatility recursions with fixed training parameters pass a future-prefix mutation test. Trailing component normalization and entropy include today's after-close signal but no later data. PCA loadings use earlier component rows. Calibration excludes every training label whose 30-day window has not matured before block start. After-close same-day detection is reported separately from future crisis prediction.

Initial reconstructed training probabilities are used only for warmup and feature history, not scored forecasts. Adjusted-close histories are revised observations rather than a point-in-time corporate-action database. The historical evaluation period has already been inspected and reported; new robustness comparisons on it are retrospective, not independent confirmation. No hyperparameters or production state counts were chosen by the new test rankings.

The volatility calibration fits log volatility and exponentiates predictions without a lognormal mean-bias correction, preserving the original method across variants. It therefore does not directly optimize the original-scale squared-error estimand. This is a disclosed modeling limitation, not a silently revised estimator. Model-defined regime-transition labels are not observable economic ground truth and are not used to support crisis-prediction claims.
"""
    (out/"STATISTICAL_VALIDATION.md").write_text(stext,encoding="utf-8")
    fallback_only=tail.groupby('experiment').fallback_fraction.min().eq(1).sum()
    final=f"""# Final scientific research audit

Research identity: Ayush Anand, A-CMSI, original Zenodo DOI **10.5281/zenodo.23682477**. This is a robustness revision of the same work, not a claim that a new Zenodo version has already been registered.

## Findings supported by execution

1. Original five-state results were reproduced from fresh fits; numeric comparisons and data/source integrity checks passed.
2. All four state-count paths and all nine rolling EVT specifications completed. Each state count used 96 refits and three starts. All requested baselines remain visible.
3. {conclusion}
   {density_text}
4. {ablation_finding} No universal adaptive advantage is established.
5. {fallback_only} of nine EVT configurations use empirical fallback for every operative estimate in every asset under the original minimum-exceedance constraint. Those cells do not validate a fitted GPD.
6. The historical PCA weighting lacks an explicit floor. The audit preserves it and adds PCAFloor, rather than rewriting original scores.
7. {tests['tests_run']} formula, timing and numerical tests passed. Full artifact checks are supplied separately.
8. A fully isolated, exact-lock environment also passed all {tests['tests_run']} tests and reproduced calibrated forecasts without `.deps` or global fallback. The initial premature check before installation completed is retained in `clean_environment_first_attempt.log`; it was rerun successfully after dependencies were installed.

## Reference material and manuscript

The exact files `ACMSI_arXiv_Preprint_Candidate.pdf`, `ACMSI_arXiv_Source_Candidate.zip`, and `ACMSI_Submission_Readiness_Audit.md` were unavailable in the repository, Downloads/Documents and Codex attachments locations checked. A distinct local `ACMSI_Zenodo_Preprint_v2.pdf` dated 27 October 2026 was found in Downloads and used as additional reference, alongside the repository manuscript. Its original mathematical definitions, research question and 14 bibliographic entries are retained in the revised LaTeX source. It was treated as a reference draft, not validated evidence. The original DOI is author supplied; the remote Zenodo record could not be independently retrieved in this session.

## arXiv readiness assessment

The computational audit supports a reproducible research preprint with limited, explicitly retrospective claims. It does not establish a superior forecasting model, broad systemic-risk coverage, equivalence of state counts, or reliable early crisis prediction. Compilation and source-package validation are recorded in `manuscript/BUILD_STATUS.json`. Author review is still required for claims, affiliation, disclosures, licensing, bibliography and choice of arXiv category. No submission, endorsement request, upload or new DOI registration has been performed.

Unresolved scientific limitations: revised daily inputs; three overlapping U.S. equity exposures; only a few crisis episodes; approximate dependence treatment; nonstationary financial data; sparse POT tail samples; selected HMM iteration-limit/nonmonotonic cases; economic multipliers chosen by design; after-close timing; and test-period reuse. These belong in the paper, not just a supplementary log.

## Commands

See `README.md` in this folder. Data hashes, exact dependency lock, seeds, configurations, execution logs and original/revised outputs are included. Main data and original production code were not modified to improve performance.
"""
    (out/"FINAL_RESEARCH_AUDIT.md").write_text(final,encoding="utf-8")
    figures(out,hmm,diagnostic,tail,ablation,paired)
    from .manuscript import write_manuscript
    write_manuscript(root,out,cfg,dict(hmm=hmm,ablation=ablation,weighting=weighting,evt=evt,
        diagnostic=diagnostic,paired=paired,tail=tail,conclusion=conclusion,density_text=density_text,
        ablation_finding=ablation_finding,effective=effective))
    provenance=json.loads((out/"provenance.json").read_text())
    provenance["completed_utc"]=datetime.now(timezone.utc).isoformat()
    provenance["final_source_sha256"]={str(p.relative_to(root)):sha256(p) for folder in ("acmsi","research_audit","tests") for p in (root/folder).glob("*.py")}
    provenance["reference_candidates"]={name:"unavailable_in_checked_locations" for name in
        ("ACMSI_arXiv_Preprint_Candidate.pdf","ACMSI_arXiv_Source_Candidate.zip","ACMSI_Submission_Readiness_Audit.md")}
    provenance["reference_found"]="references/ACMSI_Zenodo_Preprint_v2.pdf"
    provenance["clean_environment_verification"]=clean
    (out/"provenance.json").write_text(json.dumps(provenance,indent=2),encoding="utf-8")
    LOG.info("All audit reports and manuscript source generated")


def figures(out,hmm,diagnostic,tail,ablation,paired):
    path=out/"figures"; path.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(8,4))
    g=hmm[hmm.variant.str.startswith("HMM")].sort_values("variant")
    ax.errorbar(g.variant,g.rmse,yerr=[g.rmse-g.rmse_ci_low,g.rmse_ci_high-g.rmse],fmt="o",capsize=5)
    ax.set(ylabel="Annualized-volatility RMSE",title="HMM state count: matched-date forecast uncertainty")
    fig.tight_layout(); fig.savefig(path/"hmm_rmse.png",dpi=180); plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    axs[0].plot(diagnostic.states,diagnostic.mean_rare_state_fraction,marker="o")
    axs[0].set(xlabel="States",ylabel="Rare-state fraction")
    axs[1].plot(diagnostic.states,diagnostic.median_refit_ari,marker="o")
    axs[1].set(xlabel="States",ylabel="Median adjacent-refit ARI")
    fig.tight_layout(); fig.savefig(path/"hmm_stability.png",dpi=180); plt.close(fig)
    pivot=tail.groupby(["window","q"]).fallback_fraction.mean().unstack()
    fig,ax=plt.subplots(figsize=(6,4)); im=ax.imshow(pivot.to_numpy(),vmin=0,vmax=1,cmap="magma")
    ax.set_xticks(range(len(pivot.columns)),[f"{100*q:g}%" for q in pivot.columns]); ax.set_yticks(range(len(pivot.index)),pivot.index)
    for i in range(len(pivot)):
        for j in range(len(pivot.columns)):
            ax.text(j,i,f"{pivot.iloc[i,j]:.1%}",ha="center",va="center",color="white" if pivot.iloc[i,j]<.5 else "black")
    ax.set(xlabel="POT threshold",ylabel="Rolling window",title="Empirical ES fallback frequency (mean across assets)")
    fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(path/"evt_fallback.png",dpi=180); plt.close(fig)
    selected=paired[paired.family.eq("ablation")&paired.candidate.eq("Adaptive")]
    fig,ax=plt.subplots(figsize=(8,5)); y=np.arange(len(selected))
    ax.errorbar(selected.rmse_improvement,y,xerr=[selected.rmse_improvement-selected.rmse_ci_low,
                selected.rmse_ci_high-selected.rmse_improvement],fmt="o",capsize=4)
    ax.axvline(0,color="gray",ls="--"); ax.set_yticks(y,selected.reference)
    ax.set(xlabel="Reference RMSE minus Adaptive RMSE",title="Paired ablation effects; 95% block-bootstrap intervals")
    fig.tight_layout(); fig.savefig(path/"ablation_effects.png",dpi=180); plt.close(fig)
