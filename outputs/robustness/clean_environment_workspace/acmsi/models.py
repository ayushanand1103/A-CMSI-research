"""Mean/variance models and monthly forward-only market regime estimation."""
import logging
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera

from .core import ASSETS, features, filtered_probabilities, state_mapping

LOG = logging.getLogger(__name__)


def fit_hmm(x, cfg, states=None):
    scaler = StandardScaler().fit(x)
    scaled = scaler.transform(x)
    best, score = None, -np.inf
    for restart in range(cfg.restarts):
        candidate = GaussianHMM(n_components=states or cfg.hmm_states,
                                covariance_type="full", n_iter=cfg.hmm_iter,
                                tol=.01, min_covar=1e-4,
                                random_state=cfg.seed + restart)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                candidate.fit(scaled)
            ll = candidate.score(scaled)
            if np.isfinite(ll) and ll > score:
                best, score = candidate, ll
        except (ValueError, np.linalg.LinAlgError):
            continue
    if best is None:
        raise RuntimeError("All HMM restarts failed")
    ranks, means = state_mapping(best, scaler, list(x.columns))
    return best, scaler, ranks, means


def variance_model(resid, spec):
    kind, distribution = spec
    return arch_model(np.asarray(resid) * 100, mean="Zero", vol=kind,
                      p=1, o=int(kind != "GARCH"), q=1,
                      dist=distribution, rescale=False)


def select_models(returns, cfg, tables):
    orders, specs, selection, diagnostics = {}, {}, [], []
    for asset in ASSETS:
        y = returns[asset].iloc[:cfg.initial_train].to_numpy() * 100
        candidates = []
        for p in range(3):
            for q in range(3):
                try:
                    fit = ARIMA(y, order=(p, 0, q), trend="c").fit()
                    if fit.mle_retvals.get("converged", False):
                        candidates.append((fit.bic, (p, 0, q), fit))
                except (ValueError, np.linalg.LinAlgError):
                    pass
        if not candidates:
            raise RuntimeError(f"ARIMA grid failed for {asset}")
        _, order, meanfit = min(candidates, key=lambda v: v[0])
        orders[asset] = order
        for _, candidate_order, fit in candidates:
            selection.append(dict(asset=asset, layer="ARIMA", spec=str(candidate_order),
                                  aic=fit.aic, bic=fit.bic, selected=candidate_order == order))
        residual = meanfit.resid / 100
        best = None
        variance_candidates = []
        for kind in ("GARCH", "EGARCH", "GJR"):
            for dist in ("normal", "t"):
                spec = ("GARCH" if kind == "GJR" else kind, dist)
                # GJR is GARCH with o=1; keep its identity in saved selection.
                model = arch_model(residual * 100, mean="Zero", vol=spec[0],
                                   p=1, o=int(kind in ("GJR", "EGARCH")), q=1,
                                   dist=dist, rescale=False)
                vf = model.fit(disp="off", show_warning=False)
                variance_candidates.append((vf.bic, (kind, dist), vf))
                if vf.convergence_flag == 0 and (best is None or vf.bic < best[0]):
                    best = (vf.bic, (kind, dist), vf)
        if best is None:
            raise RuntimeError(f"Variance model selection failed for {asset}")
        specs[asset] = best[1]
        for _, spec, vf in variance_candidates:
            selection.append(dict(asset=asset, layer="variance", spec=str(spec),
                                  aic=vf.aic, bic=vf.bic, selected=spec == best[1],
                                  convergence=vf.convergence_flag))
        jb, jbp, skew, kurtosis = jarque_bera(residual)
        lm, lmp, _, _ = het_arch(residual, nlags=12)
        stdresid = np.asarray(best[2].std_resid)
        diagnostics.append(dict(asset=asset, arima=str(order), variance=str(best[1]),
                                residual_lb_p=acorr_ljungbox(residual, lags=[20],
                                                           model_df=order[0]+order[2]).lb_pvalue.iloc[0],
                                arch_lm_p=lmp, jb_p=jbp, skew=skew, kurtosis=kurtosis,
                                standardized_lb_p=acorr_ljungbox(stdresid, lags=[20]).lb_pvalue.iloc[0],
                                standardized_squared_lb_p=acorr_ljungbox(stdresid**2, lags=[20]).lb_pvalue.iloc[0]))
        LOG.info("Selected %s ARIMA%s %s on initial training sample", asset, order, best[1])
    pd.DataFrame(selection).to_csv(tables / "model_selection.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(tables / "initial_model_diagnostics.csv", index=False)
    return orders, specs


def make_variance(resid, spec):
    kind, dist = spec
    return arch_model(np.asarray(resid) * 100, mean="Zero", vol="GARCH" if kind == "GJR" else kind,
                      p=1, o=int(kind in ("GJR", "EGARCH")), q=1, dist=dist, rescale=False)


def chronological_models(returns, vix, cfg, output):
    tables = output / "tables"
    orders, specs = select_models(returns, cfg, tables)
    sigma = pd.DataFrame(np.nan, index=returns.index, columns=ASSETS)
    residuals = sigma.copy()
    panic = pd.Series(np.nan, index=returns.index, name="P")
    stress = pd.Series(np.nan, index=returns.index, name="stress")
    posteriors = pd.DataFrame(np.nan, index=returns.index,
                              columns=[f"Prob_RiskRank{i}" for i in range(cfg.hmm_states)])
    records, comparisons, parameter_rows, means_rows = [], [], [], []
    model_dir = output / "models"
    model_dir.mkdir(exist_ok=True)
    for fold, start in enumerate(range(cfg.initial_train, len(returns), cfg.refit_every)):
        end = min(start + cfg.refit_every, len(returns))
        LOG.info("Monthly refit %d: train through %s; score %s to %s", fold + 1,
                 returns.index[start-1].date(), returns.index[start].date(), returns.index[end-1].date())
        for asset in ASSETS:
            y = returns[asset].iloc[:end].to_numpy() * 100
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                meanfit = ARIMA(y[:start], order=orders[asset], trend="c").fit()
            # append conditions on each new observed return without refitting parameters.
            extended = meanfit.append(y[start:end], refit=False)
            resid = np.asarray(extended.resid) / 100
            vf = make_variance(resid[:start], specs[asset]).fit(disp="off", show_warning=False)
            if vf.convergence_flag:
                raise RuntimeError(f"Variance fit did not converge: {asset} fold {fold}")
            fixed = make_variance(resid, specs[asset]).fix(vf.params)
            target = slice(0 if fold == 0 else start, end)
            residuals.iloc[target, residuals.columns.get_loc(asset)] = resid[target]
            sigma.iloc[target, sigma.columns.get_loc(asset)] = np.asarray(fixed.conditional_volatility)[target] / 100
            parameter_rows.extend(dict(fold=fold, train_end=str(returns.index[start-1].date()),
                                       asset=asset, parameter=k, value=v)
                                  for k, v in vf.params.items())
            with (model_dir / f"latest_{asset}.pkl").open("wb") as handle:
                pickle.dump(dict(mean=meanfit, variance=vf, train_end=returns.index[start-1]), handle)
        feature_frame = features(returns.iloc[:end], sigma.iloc[:end], vix.iloc[:end])
        train = feature_frame.iloc[:start].dropna()
        test = feature_frame.iloc[start:end]
        if len(train) < 150 or test.isna().any().any():
            raise ValueError("Insufficient HMM features or missing VIX observations")
        if fold == 0:
            # Exploratory state count comparison, NOT future-data model selection.
            for states in (2, 3, 4, 5, 6):
                model, scaler, ranks, means = fit_hmm(train, cfg, states)
                xs = scaler.transform(train)
                comparisons.append(dict(states=states, log_likelihood=model.score(xs),
                                        aic=model.aic(xs), bic=model.bic(xs),
                                        converged=model.monitor_.converged))
            pd.DataFrame(comparisons).to_csv(tables / "hmm_state_comparison.csv", index=False)
        model, scaler, ranks, means = fit_hmm(train, cfg)
        train_prob = filtered_probabilities(model, scaler.transform(train))
        test_prob = filtered_probabilities(model, scaler.transform(test), train_prob[-1])
        rank_order = np.argsort(ranks)
        panic_state = int(np.argmax(ranks))
        if fold == 0:
            panic.loc[train.index] = train_prob[:, panic_state]
            stress.loc[train.index] = train_prob @ ranks
            posteriors.loc[train.index] = train_prob[:, rank_order]
        panic.loc[test.index] = test_prob[:, panic_state]
        stress.loc[test.index] = test_prob @ ranks
        posteriors.loc[test.index] = test_prob[:, rank_order]
        means["fold"] = fold
        means["state"] = means.index
        means_rows.append(means)
        transition = pd.DataFrame(model.transmat_[np.ix_(rank_order, rank_order)],
                                  index=posteriors.columns, columns=posteriors.columns)
        transition.to_csv(tables / "latest_transition_matrix.csv")
        with (model_dir / "latest_hmm.pkl").open("wb") as handle:
            pickle.dump(dict(model=model, scaler=scaler, risk_ranks=ranks,
                             features=list(train.columns), train_end=returns.index[start-1]), handle)
        records.append(dict(fold=fold, train_end=returns.index[start-1], test_start=test.index[0],
                            test_end=test.index[-1], n_train=len(train),
                            hmm_score=model.score(scaler.transform(train)), panic_state=panic_state,
                            panic_persistence=model.transmat_[panic_state, panic_state]))
    pd.DataFrame(records).to_csv(tables / "refit_audit.csv", index=False)
    pd.DataFrame(parameter_rows).to_csv(tables / "variance_parameters_by_fold.csv", index=False)
    pd.concat(means_rows).to_csv(tables / "hmm_state_means_by_fold.csv", index=False)
    return sigma, residuals, panic, stress, posteriors
