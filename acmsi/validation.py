"""Chronological calibration, ablation, crisis detection and uncertainty."""
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (mean_squared_error, mean_absolute_error, precision_score,
                             recall_score, f1_score, roc_auc_score, brier_score_loss)
from .core import dm_test, moving_block_bootstrap

LOG = logging.getLogger(__name__)


def targets(returns, prices, posteriors, horizon):
    r = returns["SPY"]
    current = ((r < -.03) | (prices["SPY"].reindex(r.index).pct_change(20) < -.10)).astype(float)
    forward = pd.concat([r.shift(-k) for k in range(1, horizon+1)], axis=1)
    crises = pd.concat([current.shift(-k) for k in range(1, horizon+1)], axis=1)
    result = pd.DataFrame({"future_vol": forward.std(axis=1, ddof=1) * np.sqrt(252),
                           "future_crisis": crises.max(axis=1), "current_crisis": current,
                           "current_vol": r.rolling(horizon).std() * np.sqrt(252)})
    complete = posteriors.notna().all(axis=1)
    ranks = pd.Series(index=posteriors.index, dtype="object")
    ranks.loc[complete] = posteriors.loc[complete].idxmax(axis=1)
    result["future_transition"] = (ranks.shift(-horizon) != ranks).astype(float)
    result.loc[ranks.isna() | ranks.shift(-horizon).isna(), "future_transition"] = np.nan
    result.loc[forward.isna().any(axis=1), ["future_vol", "future_crisis", "future_transition"]] = np.nan
    return result


def safe_auc(y, p):
    return float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else np.nan


def walk_forward(portfolio, target, cfg, output, name="main"):
    """Monthly expanding calibration. Only fully matured labels enter training."""
    common = portfolio.notna().all(axis=1)
    predictions, audit = [], []
    for start in range(cfg.initial_train, len(portfolio), cfg.refit_every):
        end = min(start + cfg.refit_every, len(portfolio))
        # Models fit before first test date: max training label endpoint < start.
        train_end = start - cfg.horizon
        candidates = np.arange(cfg.initial_train, max(train_end, cfg.initial_train))
        train = candidates[common.iloc[candidates].to_numpy() & target.future_vol.iloc[candidates].notna().to_numpy()]
        test = np.arange(start, end)
        test = test[common.iloc[test].to_numpy()]
        if len(train) < 126 or not len(test):
            continue
        audit.append(dict(test_start=portfolio.index[start], test_end=portfolio.index[end-1],
                          n_train=len(train), latest_feature=portfolio.index[train[-1]],
                          latest_target_end=portfolio.index[train[-1]+cfg.horizon]))
        for variant in portfolio:
            x = portfolio[[variant]]
            regression = make_pipeline(StandardScaler(), Ridge(alpha=1.))
            regression.fit(x.iloc[train], np.log(target.future_vol.iloc[train].clip(lower=1e-8)))
            vol = np.exp(regression.predict(x.iloc[test]))
            probabilities = {}
            for label in ("future_crisis", "future_transition"):
                y = target[label].iloc[train]
                valid = y.notna().to_numpy()
                if y[valid].nunique() < 2:
                    probabilities[label] = np.full(len(test), float(y[valid].mean()))
                else:
                    classifier = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=300,
                                                                                      random_state=cfg.seed))
                    classifier.fit(x.iloc[train[valid]], y.iloc[np.flatnonzero(valid)])
                    probabilities[label] = classifier.predict_proba(x.iloc[test])[:, 1]
            for j, i in enumerate(test):
                predictions.append(dict(Date=portfolio.index[i], variant=variant,
                                        actual_vol=target.future_vol.iloc[i], forecast_vol=vol[j],
                                        current_vol=target.current_vol.iloc[i],
                                        actual_crisis=target.future_crisis.iloc[i],
                                        crisis_probability=probabilities["future_crisis"][j],
                                        actual_transition=target.future_transition.iloc[i],
                                        transition_probability=probabilities["future_transition"][j]))
        for i in test:
            predictions.append(dict(Date=portfolio.index[i], variant="RealizedVolBaseline",
                                    actual_vol=target.future_vol.iloc[i], forecast_vol=target.current_vol.iloc[i],
                                    current_vol=target.current_vol.iloc[i]))
    pred = pd.DataFrame(predictions)
    if pred.empty:
        raise RuntimeError("No mature walk-forward forecasts available")
    metrics = []
    for variant, g in pred.groupby("variant"):
        scored = g.dropna(subset=["actual_vol", "forecast_vol"])
        row = dict(variant=variant, n=len(scored), rmse=np.sqrt(mean_squared_error(scored.actual_vol, scored.forecast_vol)),
                   mae=mean_absolute_error(scored.actual_vol, scored.forecast_vol),
                   directional_accuracy=float(np.mean(np.sign(scored.forecast_vol-scored.current_vol)
                                                      == np.sign(scored.actual_vol-scored.current_vol))))
        for label, truth, probability in (("crisis", "actual_crisis", "crisis_probability"),
                                           ("transition", "actual_transition", "transition_probability")):
            gg = g.dropna(subset=[truth, probability])
            if len(gg):
                row[label+"_auc"] = safe_auc(gg[truth], gg[probability])
                row[label+"_brier"] = brier_score_loss(gg[truth], gg[probability])
                row[label+"_f1_at_0.5"] = f1_score(gg[truth], gg[probability] >= .5, zero_division=0)
        metrics.append(row)
    metric = pd.DataFrame(metrics).sort_values("rmse")
    pred.to_csv(output / "tables" / f"{name}_walk_forward_predictions.csv", index=False)
    metric.to_csv(output / "tables" / f"{name}_ablation_metrics.csv", index=False)
    pd.DataFrame(audit).to_csv(output / "tables" / f"{name}_calibration_audit.csv", index=False)
    comparisons = []
    a = pred[pred.variant.eq("Adaptive")].set_index("Date")
    for variant in ("Equal", "PCA", "Entropy", "NoEVT", "NoHMM", "NoGARCH", "Adaptive4"):
        b = pred[pred.variant.eq(variant)].set_index("Date")
        matched = a[["actual_vol", "forecast_vol"]].join(b[["forecast_vol"]].rename(columns={"forecast_vol":"forecast_vol_baseline"})).dropna()
        dm = dm_test(matched.actual_vol.to_numpy(), matched.forecast_vol.to_numpy(),
                     matched.forecast_vol_baseline.to_numpy(), cfg.horizon)
        # Bootstrap paired RMSE improvement, retaining serial dependence.
        ea = (matched.actual_vol - matched.forecast_vol).to_numpy() ** 2
        eb = (matched.actual_vol - matched.forecast_vol_baseline).to_numpy() ** 2
        rng = np.random.default_rng(cfg.seed)
        boot = []
        for _ in range(cfg.bootstrap):
            starts = rng.integers(0, len(ea), int(np.ceil(len(ea)/cfg.horizon)))
            idx = ((starts[:, None] + np.arange(cfg.horizon)) % len(ea)).ravel()[:len(ea)]
            boot.append(np.sqrt(eb[idx].mean()) - np.sqrt(ea[idx].mean()))
        ci = np.quantile(boot, [.025, .975])
        comparisons.append(dict(baseline=variant, **dm,
                                rmse_improvement=np.sqrt(eb.mean())-np.sqrt(ea.mean()),
                                ci_low=ci[0], ci_high=ci[1], bootstrap_repetitions=cfg.bootstrap))
    pd.DataFrame(comparisons).to_csv(output / "tables" / f"{name}_significance.csv", index=False)
    return pred, metric


def crisis_detection(portfolio, target, cfg, output):
    rows, series = [], {}
    for variant in portfolio:
        s = portfolio[variant]
        for q in (.75, .90, .95):
            threshold = s.shift(1).expanding(min_periods=126).quantile(q)
            valid = s.notna() & threshold.notna() & (np.arange(len(s)) >= cfg.initial_train)
            y, signal = target.current_crisis.loc[valid], s.loc[valid] > threshold.loc[valid]
            rows.append(dict(variant=variant, quantile=q, n=int(valid.sum()),
                             precision=precision_score(y, signal, zero_division=0),
                             recall=recall_score(y, signal, zero_division=0),
                             f1=f1_score(y, signal, zero_division=0), auc=safe_auc(y, s.loc[valid]),
                             interpretation="same_day_detection_after_close"))
            series[f"{variant}_q{int(q*100)}"] = signal.reindex(s.index)
    pd.DataFrame(rows).to_csv(output / "tables/crisis_detection.csv", index=False)
    pd.DataFrame(series).to_csv(output / "data/crisis_signals.csv")


def early_warning(portfolio, returns, cfg, output):
    r = returns["SPY"]
    crash = np.expm1(r.rolling(20).sum()) < -.10
    # Collapse consecutive crisis days and require a 20-trading-day refractory period.
    candidates = np.flatnonzero(crash.to_numpy() & ~crash.shift(1, fill_value=False).to_numpy())
    events, last = [], -100
    for i in candidates:
        if i-last >= 20:
            events.append(i)
            last = i
    rows, correlations = [], []
    for variant in portfolio:
        s = portfolio[variant]
        threshold = s.shift(1).expanding(min_periods=126).quantile(.90)
        above = s > threshold
        crossings = above & ~above.shift(1, fill_value=False)
        for i in events:
            eligible = i >= cfg.initial_train and pd.notna(threshold.iloc[i])
            previous = np.flatnonzero(crossings.iloc[max(0, i-60):i].to_numpy())
            last_cross = max(0, i-60) + previous[-1] if len(previous) else None
            row = dict(variant=variant, event_date=s.index[i], evaluable=eligible,
                       last_crossing=s.index[last_cross] if eligible and last_cross is not None else None,
                       lead_trading_days=i-last_cross if eligible and last_cross is not None else np.nan)
            for lead in (5, 10, 20):
                row[f"warning_{lead}d"] = bool(above.iloc[max(0, i-lead):i].any()) if eligible else None
            rows.append(row)
        for lag in range(1, 31):
            # A future 21-day window beginning lag trading days after origin.
            future = pd.concat([r.shift(-(lag+k)) for k in range(21)], axis=1)
            rv = future.std(axis=1).where(future.notna().all(axis=1))
            correlations.append(dict(variant=variant, lag=lag,
                                     correlation=s.iloc[cfg.initial_train:].corr(rv.iloc[cfg.initial_train:])))
    pd.DataFrame(rows).to_csv(output / "tables/early_warning.csv", index=False)
    pd.DataFrame(correlations).to_csv(output / "tables/lead_correlations.csv", index=False)
