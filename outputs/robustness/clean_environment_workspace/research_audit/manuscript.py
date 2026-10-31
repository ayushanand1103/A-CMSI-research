"""Generate self-contained LaTeX publication candidate from verified tables."""
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd


def escape(value):
    text=str(value)
    for a,b in (("\\",r"\textbackslash{}"),("_",r"\_"),("%",r"\%"),("&",r"\&"),("#",r"\#")):
        text=text.replace(a,b)
    return text


def number(value):
    return "--" if pd.isna(value) or not np.isfinite(float(value)) else f"{float(value):.4f}"


def latex_table(df,columns,headers,caption,label):
    result=[r"\begin{table}[htbp]\centering\small",r"\caption{"+caption+"}\\label{"+label+"}",
            r"\resizebox{\textwidth}{!}{\begin{tabular}{"+"l"+"r"*(len(columns)-1)+"}",r"\toprule",
            " & ".join(headers)+r" \\",r"\midrule"]
    for _,row in df.iterrows():
        values=[]
        for col in columns:
            if col=="rmse_interval":
                values.append("["+number(row.rmse_ci_low)+", "+number(row.rmse_ci_high)+"]")
            elif col=="auc_interval":
                values.append("["+number(row.auc_ci_low)+", "+number(row.auc_ci_high)+"]")
            else:
                v=row[col]
                values.append(escape(v) if isinstance(v,str) else str(int(v)) if col in ("n","states","selected_hit_limit","selected_nonmonotone") else number(v))
        result.append(" & ".join(values)+r" \\")
    result += [r"\bottomrule\end{tabular}}\end{table}"]
    return "\n".join(result)


def write_manuscript(root,out,cfg,data):
    path=out/"manuscript"; path.mkdir(exist_ok=True)
    figures=path/"figures"; figures.mkdir(exist_ok=True)
    for p in (out/"figures").glob("*.png"):
        shutil.copy2(p,figures/p.name)
    shutil.copy2(Path(__file__).with_name("references.bib"),path/"references.bib")
    hm,ab,wt,et,diag,paired,tail=(data[k] for k in ("hmm","ablation","weighting","evt","diagnostic","paired","tail"))
    main=ab[ab.variant.eq("Adaptive")].iloc[0]
    best=ab[~ab.variant.str.startswith("Conditional")].sort_values("rmse").iloc[0]
    selected=["Adaptive","NoProbability","Entropy","NoHMM","Equal","PCA","NoEVT","NoGARCH","EntropyDeficit","PCAFloor"]
    original=pd.read_csv(out/"original/tables/main_ablation_metrics.csv")
    tables={
        "original_table.tex":latex_table(original,["variant","n","rmse","mae","crisis_auc"],["Model","Dates","RMSE","MAE","Future-crisis AUC"],"Original results reproduced from fresh estimation. Annualized volatility uses decimal-return units.","tab:original"),
        "hmm_table.tex":latex_table(hm[hm.variant.str.startswith("HMM")],["variant","n","rmse","rmse_interval","mae","auc","brier"],["States","Dates","RMSE","95\\% block CI","MAE","AUC","Brier"],"State-count robustness on identical chronological scoring dates. The model is the adaptive composite, not the HMM alone.","tab:hmm"),
        "ablation_table.tex":latex_table(ab[ab.variant.isin(selected)],["variant","n","rmse","rmse_interval","mae","auc"],["Model","Dates","RMSE","95\\% block CI","MAE","AUC"],"Controlled HMM ablations and weighting specifications. NoProbability removes P but retains regime multipliers; Entropy removes multipliers but retains P; NoHMM removes both.","tab:ablation"),
        "crisis_table.tex":latex_table(ab[ab.variant.isin(selected)],["variant","precision","recall","f1","auc","auc_interval","brier"],["Model","Precision","Recall","F1","AUC","95\\% AUC CI","Brier"],"Future 30-day crisis prediction, fixed probability cutoff 0.5. These are not same-day detection scores.","tab:crisis"),
        "evt_table.tex":latex_table(et,["variant","n","rmse","rmse_interval","mae","auc","brier"],["Tail specification","Dates","RMSE","95\\% block CI","MAE","AUC","Brier"],"Matched-date EVT-grid forecast evaluation. w denotes the POT window, q its threshold percentile; component normalization remains 252 days.","tab:evt"),
        "diagnostics_table.tex":latex_table(diag,["states","initial_bic","conditional_test_ll_per_day","mean_rare_state_fraction","median_refit_ari","median_expected_duration","selected_nonmonotone"],["K","Initial BIC","OOS log density/day","Rare-state fraction","Refit ARI","Duration","Nonmonotone fits"],"HMM density-generalization and stability diagnostics. A rare state has expected training occupancy below max(20,1 percent of training rows). Durations are 1/(1-A ss).", "tab:diagnostics"),
        "paired_table.tex":latex_table(paired[(paired.family.eq("ablation"))&(paired.candidate.eq("Adaptive"))],["reference","rmse_improvement","rmse_ci_low","rmse_ci_high","pvalue","p_holm_family","p_holm_global"],["Reference","RMSE gain","CI lower","CI upper","DM p","Family Holm","Global Holm"],"Adaptive versus controlled references. Positive gain favors Adaptive. Bootstrap intervals are marginal; adjusted p-values refer to squared-loss DM tests.","tab:paired"),
        "conditional_table.tex":latex_table(ab[ab.variant.str.startswith("Conditional")],["variant","n","rmse","rmse_interval","mae","auc","brier"],["Regressors","Dates","RMSE","95\\% block CI","MAE","AUC","Brier"],"Exploratory conditional-information regressions. V/T and P/stress are separate predictors; these rows are not weighted composite specifications.","tab:conditional")}
    for name,text in tables.items():
        (path/name).write_text(text,encoding="utf-8")
    fallback=tail.groupby("experiment").fallback_fraction.mean().reset_index()
    (path/"fallback_table.tex").write_text(latex_table(fallback,["experiment","fallback_fraction"],["Specification","Fallback fraction"],"Empirical ES99 fallback frequency averaged across assets. An all-fallback cell is not a successful GPD robustness check.","tab:fallback"))
    density=escape(data["density_text"])
    conclusion=escape(data["conclusion"])
    text=r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,booktabs,graphicx,natbib}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\setlength{\parskip}{0.4em}
\setlength{\parindent}{0pt}
\setlength{\emergencystretch}{2em}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prb}{\mathbb{P}}
\title{Does Adaptive Weighting Improve Equity Market Stress Measurement?\\
Chronological Robustness Evidence from a GARCH--HMM--EVT Composite Index}
\author{Ayush Anand\\\small Undergraduate Student, CHRIST (Deemed to be University),\\
\small Delhi NCR Campus, India\\\small\texttt{ayushanand.1103@gmail.com}}
\date{31 October 2026\\\small Revised preprint candidate; robustness revision of the research archived at\\
\small\href{https://doi.org/10.5281/zenodo.23682477}{doi:10.5281/zenodo.23682477}}
\begin{document}
\maketitle
\begin{abstract}
This paper investigates whether conditional volatility, filtered market-regime probabilities and extreme-loss
severity benefit from regime-conditioned entropy weighting in a composite equity-market stress indicator.
The Adaptive Composite Market Stress Index (A-CMSI) combines ARIMA--conditional-variance models,
forward-filtered Gaussian hidden Markov probabilities and rolling peaks-over-threshold expected shortfall
for AAPL, MSFT and SPY. Fresh estimation reproduces the previously reported five-state results on
2,765 adjusted-price observations from 2015--2025 and 1,810 scored 30-day forecasts: Adaptive RMSE is
0.10532, compared with 0.10457 for Equal and 0.10411 for NoHMM. This revision executes complete
three-, four-, five- and six-state paths, independently removes panic probability and regime multipliers,
evaluates direct and deficit entropy weights, and tests nine EVT window/threshold configurations.
@@ABSTRACT@@
The study separates after-close detection from future-event prediction, reports dependence-aware
uncertainty and multiplicity-adjusted loss comparisons, and retains unfavorable baselines.
The evidence supports a transparent research framework, rather than a universal predictive advantage
for adaptive weighting or a deployment-ready systemic-risk indicator.
\end{abstract}
\textbf{Keywords:} equity-market stress; composite indicator; GARCH; hidden Markov model;
extreme value theory; entropy weighting; chronological validation.\\
\textbf{JEL:} C58, G01, C53, G17.

\section{Introduction}
Financial stress is multidimensional. Conditional dispersion, persistent market regimes and the severity
of extreme losses need not convey identical information. A composite index can summarize these signals,
but a plausible economic narrative is not evidence of improved forecasting. More elaborate aggregation
can add estimation noise, obscure redundant components, or concentrate weight on signals unrelated to
the chosen loss. A stress index should therefore be evaluated against simple alternatives without a
presumption that adaptive construction must win.

Financial stress composites have substantial precedent. CISS combines market-specific indicators while
accounting for cross-market dependence \citep{ciss}. FIMSIS examines stress aggregation in a smaller
financial system \citep{fimsis}. A-CMSI has a narrower scope: two large technology stocks and a U.S.
equity ETF containing both stocks. It is an equity stress-measurement experiment, not a replacement for
multi-market financial-system indicators. The contribution investigated here is the explicit combination
of volatility, filtered panic probability and tail severity with trailing entropy and soft regime factors.

This revision asks three empirical questions. Does adding a sixth HMM state improve generalization
despite lower initial-training BIC? Does the panic probability contribute information beyond V/T, and
are any losses associated instead with the regime multipliers? Are index conclusions stable to feasible
POT thresholds and windows, and to direct versus deficit entropy? All requested specifications are
executed under a fixed protocol. Historical outputs are archived, not replaced with a winning selection.

The previous preprint already reported that NoHMM and Equal have lower point-estimate volatility RMSE
than Adaptive. The new experiments revisit the same historical period and are therefore retrospective
robustness analyses. Their chronological implementation prevents computational look-ahead, but does not
convert an already inspected period into an independent confirmatory holdout.

\section{Methodological context}
ARCH and GARCH model conditional variance \citep{engle,bollerslev}; EGARCH represents asymmetric
responses through log variance \citep{nelson}. Latent Markov regimes describe persistent distributional
changes \citep{hamilton}. POT tail inference is motivated by extreme-value approximations
\citep{pickands}, with financial conditional-tail applications in \citet{mcneil}. Hybrid HMM--EVT
risk modeling is also established \citep{salhi}; A-CMSI does not claim to invent these model families.

Shannon entropy quantifies concentration in a probability distribution \citep{shannon}; using it as a
component weight is a design choice rather than a theorem about predictive usefulness. The direct and
deficit constructions deliberately reward different temporal patterns. Cointegration \citep{johansen}
and wavelet analysis \citep{torrence} provide descriptive context but are not daily forecasting inputs
derived from full-sample smoothing. Forecast comparison follows the squared-loss framework of
\citet{dm}, with the small-sample horizon adjustment of \citet{hln} and additional block resampling.

\section{Data, chronology and reproducibility}
The canonical local input contains 2,765 complete adjusted-price rows from 2 January 2015 through
30 December 2025. For asset $a$, daily log return is
\begin{equation}r_{a,t}=\log P_{a,t}-\log P_{a,t-1}.\end{equation}
This yields 2,764 return dates. Prices are checked for missing and nonpositive values, sorted unique
dates and alignment. The saved VIX observations start on 4 January 2016; earlier missing VIX values
are not backfilled using future data. Legacy saved returns differ very slightly from recomputation,
so the operational pipeline always derives returns from the canonical dated price file.

The initial model window contains 756 return observations. Selected mean/variance specifications and
HMM parameters are re-estimated every 21 trading days. The next block receives fixed estimated
parameters; after-close observations update residuals and filtered states sequentially. The historical
initial reconstruction initializes rolling features and is excluded from forecast calibration/scoring.
All scalers use training rows only. Conditional-variance and filtering prefix tests verify that extending
a fixed-parameter sequence cannot revise its earlier operational values.

The original scored period covers 5 September 2018--14 November 2025. The last 30 signal dates still
receive forecasts but cannot be scored without future observations. Longer tail windows change warmup;
new comparisons are restricted to identical training support and scoring dates within each family, with
a second intersection shared across all families. Tables state their own sample sizes. They must not be
ranked across different eligible periods as though the observations were identical.

The audit stores full SHA-256 hashes of every input CSV, source hashes, exact package versions,
configuration, seeds, timestamps and logs. Fresh fits reproduce the original tables and predictions.
The original production implementation and observed data remain unchanged. A dedicated environment
uses the recorded project dependencies; a lock file supports clean installation elsewhere.

\section{Components and index construction}
\subsection{Conditional volatility}
Initial-training BIC selects ARIMA$(p,0,q)$ with $p,q\in\{0,1,2\}$. Innovations feed zero-mean
GARCH, GJR-GARCH and EGARCH candidates with normal and Student-$t$ errors. Selected specifications
are re-estimated monthly. Returns are scaled to percentage units during variance fitting and exported
in decimal-return units. Conditional standard deviation supplies raw volatility $\sigma_{a,t}$.

For a generic component $X$, let trailing normalization be
\begin{equation}
Z_t(X)=\operatorname{clip}_{[-3,3]}
\left[\frac{X_t-\bar X_{t,252}}{s_{t,252}(X)}\right],
\quad \bar X_{t,252}=\frac1{252}\sum_{k=0}^{251}X_{t-k}.
\end{equation}
Sample standard deviation is used; incomplete windows remain missing. Today's value is included
because signals are after close. Thus $V_{a,t}=Z_t(\sigma_a)$. No full-sample normalization is used.

\subsection{Forward-filtered regimes}
The multivariate Gaussian HMM observes SPY return, normalized conditional volatility, 21-day realized
volatility and skewness, drawdown, volatility of volatility, VIX and mean pairwise return correlation.
For transition matrix $A$, state density $f_s$, and filtered probability $\alpha_t(s)$,
\begin{equation}
\alpha_t(s)=\frac{f_s(x_t)\sum_j\alpha_{t-1}(j)A_{js}}
{\sum_\ell f_\ell(x_t)\sum_j\alpha_{t-1}(j)A_{j\ell}}.
\end{equation}
No backward smoothing conditions today's probability on later observations. At every refit, training
means rank states using VIX, realized volatility, conditional volatility and inverse return. The
highest-risk state defines raw panic probability; normalized $P_t=Z_t(\alpha_t(s_{\rm panic}))$
is common to all asset indices. Numeric state IDs themselves have no persistent economic meaning.

The original model uses five states. The audit executes three to six states at all 96 origins with
seeds 42, 43 and 44 and at most 200 EM iterations. Maximum training likelihood chooses the restart.
Iteration limits and negative final likelihood increments are reported rather than hidden behind a
library convergence flag. Occupancy is computed from filtered responsibilities; state-duration estimates
are $1/(1-A_{ss})$. State stability compares common 126-observation training anchors with permutation-
invariant ARI and Hungarian-aligned labels. Symmetric Gaussian KL diagnoses near-redundant emissions.

\subsection{Tail severity}
Let loss $L_{a,t}=-r_{a,t}$. For trailing window $N$ and threshold quantile $q$, the POT threshold
$u_t$ is estimated only from that window. Positive excesses $Y=L-u_t$ follow the fitted GPD
\begin{equation}
G(y)=1-\left(1+\xi_t y/\beta_t\right)^{-1/\xi_t},
\end{equation}
on its valid support, with fixed location zero and logarithmic/exponential limits at $\xi=0$.
If $p_{u,t}=n_{u,t}/N$ is the exceedance rate, then
\begin{align}
\operatorname{VaR}_{\alpha,t}
 &=u_t+\frac{\beta_t}{\xi_t}
 \left[\left(\frac{p_{u,t}}{1-\alpha}\right)^{\xi_t}-1\right],\\
\operatorname{ES}_{\alpha,t}
 &=\frac{\operatorname{VaR}_{\alpha,t}+\beta_t-\xi_tu_t}{1-\xi_t},\quad \xi_t<1.
\end{align}
The baseline uses $N=252$, $q=0.90$, at least 20 exceedances, and $\alpha=0.99$.
When insufficient excesses, numerical failure or infinite fitted ES makes the GPD unusable,
the operational raw tail score uses empirical ES99. The failure status and missing parametric
quantity are retained. Thus $T_{a,t}$ is a normalized \emph{hybrid} tail-severity estimator,
not an always-successful GPD estimate. Shape is never clipped to manufacture a finite mean.

The sensitivity grid is $N\in\{252,378,504\}$ and $q\in\{0.90,0.95,0.975\}$, with the original
20-exceedance constraint and 252-day normalization unchanged. Static full-sample fits are labeled
descriptive and never select the forecast specification.

\subsection{Entropy and adaptive weights}
For component $i\in\{V,P,T\}$ and trailing entropy window $W=63$, define probabilities across time:
\begin{equation}
p_{i,k,t}=\frac{|Z_{i,t-k}|}{\sum_{j=0}^{W-1}|Z_{i,t-j}|},\quad
H_{i,t}=-\frac{\sum_{k=0}^{W-1}p_{i,k,t}\log p_{i,k,t}}{\log W}.
\end{equation}
Direct entropy weights normalize $H_i$; deficit weights normalize $1-H_i$. A complete all-zero
denominator receives equal weights; incomplete windows remain missing. Direct entropy rewards
sustained temporal activity, while deficit weights emphasize concentrated activity. Neither definition
identifies economically useful information without empirical testing.

Let $\rho_s$ be evenly spaced risk ranks from zero to one, assigned from training means, and
$S_t=\sum_s\alpha_t(s)\rho_s$. Soft factors interpolate the documented bull/panic endpoints:
\begin{equation}
f_{V,t}=1.3-0.5S_t,\quad f_{P,t}=0.8+0.3S_t,\quad f_{T,t}=0.9+0.5S_t.
\end{equation}
This is the historical extension to ranked five-state probabilities, not a newly estimated multiplier
rule. It does not exactly preserve the neutral vector of the original conceptual three-regime table.
For entropy base $e_{i,t}$, raw weight $q_{i,t}=e_{i,t}f_{i,t}$ receives the exact floor map
\begin{equation}
w_{i,t}=m+(1-Km)\frac{q_{i,t}}{\sum_jq_{j,t}},\quad m=0.05,
\end{equation}
where $K$ is the number of included components, not the HMM state count. This guarantees nonnegative
weights, the minimum and a unit sum simultaneously. The final index is
\begin{equation}
\operatorname{ACMSI}_{a,t}=\sum_iw_{i,t}Z_{a,i,t},\qquad
\operatorname{ACMSI}_{\rm portfolio,t}=\frac13\sum_{a\in\{\mathrm{AAPL,MSFT,SPY}\}}
\operatorname{ACMSI}_{a,t}.
\end{equation}
An optional fourth component uses normalized mean rolling pairwise correlation with a neutral factor.
High correlation alone does not show all assets are falling and is not termed cointegration breakdown.

\section{Experimental design and inference}
\subsection{Controlled comparisons}
NoProbability removes P but retains V/T regime factors; Entropy removes factors but retains P;
NoHMM removes both. This distinction prevents the no-HMM ablation from merely duplicating entropy-only.
Equal, original absolute-loading PCA, NoEVT, NoGARCH and Adaptive4 remain visible. PCA uses earlier
observations only. The original PCA method does not impose the minimum floor; PCAFloor is a separately
reported constrained alternative. Original entropy exports are pre-floor weights, whereas the entropy
index applies the floor. The audit does not silently rewrite the original scores.

Conditional\-VT, Conditional\-VTP, Conditional\-VT\-Stress and Conditional\-VTP\-Stress use separate V/T/P/stress
regressors in otherwise fixed ridge/logistic calibration. They are exploratory incremental-information
diagnostics, not new composite weights. No hyperparameter is optimized on evaluation outcomes.

\subsection{Forecasting versus detection}
The future volatility target is the next 30 daily returns' sample standard deviation annualized by
$\sqrt{252}$. Standardized ridge calibration with penalty one predicts log volatility; exponentiation
produces forecasts. This preserves the original method, without a lognormal mean-bias correction.
A training label is admitted only if its entire 30-day future window ends before the next predicted
block. At least 126 mature operational observations are needed. Training means and current 30-day
realized volatility provide constant and persistence baselines.

A contemporaneous crisis label is one for SPY daily return below $-3\%$ or trailing 20-day cumulative
return below $-10\%$. Same-day index threshold scores are \emph{after-close detection}. Separate
logistic models with penalty one forecast any crisis label in the next 30 trading days. Precision,
recall and F1 use a predeclared probability cutoff of 0.5; ROC AUC is threshold-free. Expanding
training prevalence is supplied as a probability baseline. The future filtered-regime transition
target remains a model-derived proxy and does not substitute for observed crisis labels.

\subsection{Uncertainty and testing}
For forecasts A and B, squared-loss difference $d_t=(y_t-\hat y_{A,t})^2-(y_t-\hat y_{B,t})^2$
enters a DM statistic with Bartlett HAC long-run variance through lag 29. The HLN correction at
horizon $h=30$ multiplies the statistic by
\begin{equation}
\sqrt{\frac{n+1-2h+h(h-1)/n}{n}}.
\end{equation}
Paired circular moving-block bootstrap uses 30-day blocks and 1,000 replicates, resampling outcomes
and predictions together. The 60-day sensitivity changes block length and HAC bandwidth to 59.
Holm corrections are supplied within each stated squared-loss family and across the full comparison
set. Bootstrap intervals for other metrics are marginal descriptive intervals, not simultaneous bands.
AUC draws without both classes are omitted and counted. Nonsignificance is not evidence of equivalence.

\section{Results}
\subsection{Fresh reproduction}
\input{original_table.tex}
Fresh five-state estimation reproduces the original RMSE, MAE, directional accuracy and crisis
metrics, together with saved predictions, components and initial-training BIC comparisons.
Original and revised outputs are stored separately. The published negative result is retained:
Adaptive does not establish a forecasting advantage over Equal or NoHMM in that sample.

\subsection{State count and generalization}
\input{hmm_table.tex}
\input{diagnostics_table.tex}
@@HMM_CONCLUSION@@

@@DENSITY@@

The density result and index-forecast result address different targets. More complex Gaussian
emissions can improve training fit while assigning poor conditional density to later observations;
a nonlinear filtered-probability index need not exhibit the same ranking under volatility RMSE.
Raw state IDs cannot be compared across fits without alignment. Rare occupancy, refit instability
and close emission distributions are diagnostics rather than decisive individual tests of overfitting.
The historical default is retained for continuity, not selected anew from these inspected outcomes.

\begin{figure}[htbp]\centering\includegraphics[width=.85\textwidth]{figures/hmm_rmse.png}
\caption{Matched state-count RMSE intervals. Marginal interval overlap is not itself a test of a paired difference.}\end{figure}
\begin{figure}[htbp]\centering\includegraphics[width=.9\textwidth]{figures/hmm_stability.png}
\caption{Rare occupancy and adjacent-refit stability under the fixed diagnostic rules.}\end{figure}

\subsection{Incremental HMM contribution and weighting}
\input{ablation_table.tex}
\input{paired_table.tex}
\input{conditional_table.tex}
@@ABLATION@@
Removing P and removing regime factors are different interventions. Improvements must be read
with paired uncertainty, rather than assigned to an assumed mechanism based on a single ranking.
The conditional regressions ask whether P/stress has incremental information beyond V/T under the
same fixed calibration. They do not establish structural causality or prove absence of information
when an interval contains zero. PCAFloor explicitly tests a constraint correction while preserving
the original unconstrained PCA baseline.

\begin{figure}[htbp]\centering\includegraphics[width=.9\textwidth]{figures/ablation_effects.png}
\caption{Paired RMSE improvements for Adaptive relative to controlled references. Positive values favor Adaptive.}\end{figure}

\subsection{EVT feasibility and sensitivity}
\input{fallback_table.tex}
\input{evt_table.tex}
Five grid cells use empirical fallback for every asset/window estimate. At 95\%/252 days,
95\%/378 days and all three 97.5\% configurations, the available number of excesses cannot meet
the fixed minimum. These completed experiments reveal infeasible parametric specifications under
the original rule; they are not missing experiments or evidence of successful GPD estimation.
Identical all-fallback cells do not provide independent confirmations of threshold robustness.

Raw parameter and VaR/ES stability tables retain missing undefined estimates, fit failures and
extreme finite ES. A stable normalized index can coexist with unstable raw tail estimates because
rolling normalization and clipping compress differences. The score and forecast comparisons must
therefore be interpreted together with the raw-tail diagnostics. The full data include one empirical
fallback in the original 7,539 rolling fits; the new grid is assessed separately.

\begin{figure}[htbp]\centering\includegraphics[width=.75\textwidth]{figures/evt_fallback.png}
\caption{Fraction of operative tail estimates using empirical ES99 fallback.}\end{figure}

\subsection{Crisis prediction and descriptive context}
\input{crisis_table.tex}
The earlier after-close same-day detection F1 of 0.300 at an expanding 90th-percentile index
threshold remains a different task from Table~\ref{tab:crisis}. A contemporaneous signal observes
the day's return; it cannot demonstrate prevention or advance prediction of that loss. Positive
future-event labels span long runs, so many positive daily labels do not imply many independent
crisis episodes. The original five eligible early-warning events and conditional median crossing
lead of 7.5 trading days remain exploratory, not newly validated population lead-time estimates.

The original descriptive wavelet, stationarity, structural-break and cointegration analyses are
retained as context. Full-sample LOESS/wavelet transforms are not predictive inputs. The historical
external FSI comparison uses revised histories and assumed release lags; its lower augmented RMSE
is not treated as a vintage-correct benchmark advantage. None of these ancillary results resolves
the limited breadth of two overlapping technology stocks and their benchmark ETF.

\section{Discussion and limitations}
The results distinguish construction from usefulness. A-CMSI gives an explicit multidimensional
after-close stress summary, but a model assembled from economically plausible components need not
minimize forecasting loss. Direct entropy weights reward sustained activity; deficit entropy rewards
concentration. Regime factors impose analyst judgments about when tail severity matters more.
Changing these choices can redistribute the same correlated information rather than add new signal.

The sixth state is evaluated on training likelihood, future emission density, regime diagnostics and
index forecasts separately. A lower BIC is a penalized training criterion, not a guarantee of stable
or useful states. Conversely, an interpretable five-state taxonomy is not statistical evidence of
superiority. Any eventual production choice should be checked on a genuinely new period, not chosen
from the most favorable retrospective metric in the present tables.

Tail inference is especially sensitive to feasibility. A 252-day 90th-percentile fit contains only
roughly 25 excesses; moving to a higher quantile can exhaust the sample rather than improve tail
specificity. Longer windows add observations but assume greater temporal stability. The operational
fallback is useful for keeping a signal defined, yet changes the estimator's statistical meaning.
All-fallback robustness cells should be described as empirical-tail alternatives.

Several remaining limitations constrain the claims. Adjusted closes and published stress series
are revised observations rather than verified historical vintages. The assets have overlapping
economic exposures and cover neither credit nor funding markets. Crisis episodes are few. Forecast
targets overlap and may remain dependent beyond the tested 30/60-day block choices. Bootstrap/HAC
intervals are approximate under financial nonstationarity. HMM labels and transition targets are
estimated constructs. A small number of selected fits have negative final likelihood increments;
these are disclosed. The original log-volatility calibration is not an unbiased conditional-mean
forecast on the original scale. Weight multipliers, clipping, state ranks and exceedance rules
are design assumptions. Most importantly, the evaluation period has already been used in earlier
research and cannot support a claim of independent external validation.

Sixteen numerical and timing tests and artifact-level checks support implementation integrity,
not economic truth of the models. A prefix test cannot establish that revised source prices were
available historically. Better out-of-sample results on one loss cannot establish performance for
all crisis-detection tasks. Non-rejection of equal loss cannot establish model equivalence. These
distinctions are retained in the interpretation rather than hidden in supplementary material.

\section{Conclusion}
This revision reproduces the original A-CMSI experiment and executes the previously untested
state-count, controlled-ablation, weighting and EVT-grid alternatives. All comparisons preserve
chronological model fitting, mature-label calibration and fixed hyperparameters. The contribution
is a transparent and reproducible stress-measurement framework with an explicit robustness audit,
not proof of uniformly superior adaptive forecasting.
@@CONCLUSION@@
Further work should use a new evaluation period, broader non-overlapping exposures, verified
point-in-time observations and independently specified tail/state diagnostics before operational
or strong systemic-risk claims are made.

\section*{Version identity and availability}
This is a robustness revision of the same research archived under
\href{https://doi.org/10.5281/zenodo.23682477}{10.5281/zenodo.23682477}; it does not claim a new
Zenodo version DOI or arXiv identifier. The exact newer candidate PDF/source ZIP/readiness audit
named by the author were unavailable in the checked locations. The repository draft and a local
27 October 2026 Zenodo v2 PDF supplied reference context, including its 14 bibliographic entries.
All numerical additions in this revision derive from the executed audit tables, not from unverified
claims in those reference drafts. Code is available at
\url{https://github.com/ayushanand1103/A-CMSI-research}; audit commands, locks, data hashes,
configuration and reports are packaged separately from original outputs. Third-party input data
remain subject to their original terms. No upload or submission has been performed.

\section*{Declarations}
The reference preprint reports independent, sole-authored research without external funding and
without competing interests; these declarations are carried forward for author confirmation.
Affiliation is descriptive and does not imply institutional sponsorship. Generative-AI assistance
was used for code, research checking, experiment implementation, manuscript drafting and formatting.
The human author is responsible for verifying results, references, disclosures, licensing and final
submission decisions. No AI system is listed as an author.

\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
"""
    abstract=(f"The controlled Adaptive specification has RMSE {main.rmse:.5f} on {int(main.n)} matched dates; "
              f"the lowest point-estimate RMSE among the displayed composite/baseline variants is obtained by {escape(best.variant)}. "
              "Five EVT configurations cannot meet the fixed minimum-exceedance rule and become entirely empirical fallback estimates.")
    text=text.replace("@@ABSTRACT@@",abstract).replace("@@HMM_CONCLUSION@@",conclusion).replace("@@DENSITY@@",density)
    text=text.replace("@@ABLATION@@",escape(data["ablation_finding"])+f" The lowest composite point estimate is {escape(best.variant)}, {best.rmse:.5f}. Full paired effect sizes and adjusted loss-test p-values are reported rather than inferring significance from point rankings.")
    text=text.replace("@@CONCLUSION@@",conclusion)
    tests=json.loads((out/"test_results.json").read_text())
    text=text.replace("Sixteen numerical and timing tests",f"{tests['tests_run']} numerical and timing tests")
    (path/"main.tex").write_text(text,encoding="utf-8")
    (path/"README.md").write_text("# Revised preprint source\n\nCompile with `tectonic --keep-intermediates --keep-logs main.tex` or a standard LaTeX/BibTeX workflow. All graphics and input tables use relative paths. Original DOI: 10.5281/zenodo.23682477. This source is a revision candidate, not evidence of an actual arXiv submission. See BUILD_STATUS.json for executed compilation checks.\n",encoding="utf-8")
