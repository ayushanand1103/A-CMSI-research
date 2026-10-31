"""Pure numerical routines shared by historical and chronological analyses."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp

ASSETS = ("AAPL", "MSFT", "SPY")
COMPONENTS = ("V", "P", "T")


@dataclass(frozen=True)
class Config:
    seed: int = 42
    window: int = 252
    entropy_window: int = 63
    threshold: float = .90
    min_exceedances: int = 20
    initial_train: int = 756
    refit_every: int = 21
    horizon: int = 30
    hmm_states: int = 5
    restarts: int = 3
    hmm_iter: int = 200
    min_weight: float = .05
    bootstrap: int = 1000


def read_dated(path):
    df = pd.read_csv(path)
    text = df.pop("Date").astype(str)
    dates = pd.to_datetime(text, format="mixed", dayfirst=True, errors="raise")
    df.index = pd.DatetimeIndex(dates, name="Date")
    if df.index.has_duplicates or not df.index.is_monotonic_increasing:
        raise ValueError(f"Dates must be unique and sorted: {path}")
    return df


def load_data(root):
    prices = read_dated(Path(root) / "Data/prices_clean.csv")[list(ASSETS)]
    if prices.isna().any().any() or (prices <= 0).any().any():
        raise ValueError("Adjusted prices must be complete and positive")
    returns = np.log(prices).diff().dropna()
    # The saved VIX feature is observed data; all other HMM features are rebuilt.
    saved = read_dated(Path(root) / "Data/HMM data/HMM_Input_Features.csv")
    vix = saved["VIX"].reindex(returns.index)
    return prices, returns, vix


def zscore(x, window=252):
    """Trailing z-score, including today's observation, available after close."""
    mean, sd = x.rolling(window).mean(), x.rolling(window).std(ddof=1)
    return ((x - mean) / sd.replace(0, np.nan)).clip(-3, 3)


def entropy_weights(z, window=63):
    """Normalize absolute signals over TIME separately for each component."""
    def entropy(x):
        a = np.abs(x)
        if a.sum() < 1e-12:
            return 0.
        p = a[a > 0] / a.sum()
        return float(-np.sum(p * np.log(p)) / np.log(len(x)))
    h = z.rolling(window).apply(entropy, raw=True)
    weights = h.div(h.sum(axis=1).replace(0, np.nan), axis=0)
    # A complete zero window has no discriminatory information.
    complete = h.notna().all(axis=1) & h.sum(axis=1).eq(0)
    weights.loc[complete, :] = 1 / z.shape[1]
    return weights


def floor_weights(raw, minimum=.05):
    """Affine simplex map: each weight >= minimum and rows sum exactly to one."""
    n = raw.shape[1]
    if not 0 <= minimum < 1 / n:
        raise ValueError("Invalid minimum weight")
    normalized = raw.div(raw.sum(axis=1).replace(0, np.nan), axis=0)
    return minimum + (1 - n * minimum) * normalized


def fit_tail(losses, threshold=.90, min_exceedances=20):
    """POT GPD fit with fixed location zero. ES exists only for xi < 1."""
    x = np.asarray(losses, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 30:
        return dict(status="insufficient_sample", n=len(x))
    u = float(np.quantile(x, threshold))
    excess = x[x > u] - u
    row = dict(n=len(x), threshold_quantile=threshold, u=u, n_exceed=len(excess))
    if len(excess) < min_exceedances:
        return dict(row, status="insufficient_exceedances")
    xi, _, beta = stats.genpareto.fit(excess, floc=0)
    row.update(xi=float(xi), beta=float(beta))
    if not np.isfinite([xi, beta]).all() or beta <= 0:
        return dict(row, status="invalid_fit")
    row["status"] = "ok" if xi < 1 else "infinite_expected_shortfall"
    rate = len(excess) / len(x)
    for alpha in (.95, .99):
        suffix = str(int(alpha * 100))
        if 1 - alpha > rate + 1e-12:
            # This level lies below the POT threshold and cannot be extrapolated.
            row["VaR" + suffix] = row["ES" + suffix] = np.nan
            continue
        q = (1 - alpha) / rate
        var = u - beta * np.log(q) if abs(xi) < 1e-7 else u + beta / xi * (q ** (-xi) - 1)
        row["VaR" + suffix] = float(var)
        row["ES" + suffix] = float((var + beta - xi * u) / (1 - xi)) if xi < 1 else np.nan
    return row


def filtered_probabilities(model, x, initial=None):
    """Forward filter P(S_t | X_1:t), never backward/smoothed probabilities."""
    emission = model._compute_log_likelihood(np.asarray(x))
    trans = np.log(np.maximum(model.transmat_, 1e-300))
    prior = np.log(np.maximum(model.startprob_ if initial is None else initial, 1e-300))
    result = []
    for i, likelihood in enumerate(emission):
        if i or initial is not None:
            prior = logsumexp(prior[:, None] + trans, axis=0)
        posterior = prior + likelihood
        prior = posterior - logsumexp(posterior)
        result.append(np.exp(prior))
    return np.asarray(result)


def state_mapping(model, scaler, names):
    means = pd.DataFrame(scaler.inverse_transform(model.means_), columns=names)
    # Economic labels are recomputed at every refit, independent of numeric IDs.
    risk = (means["VIX"].rank() + means["RollingVol21"].rank()
            + means["SPY_V"].rank() - means["SPY_Return"].rank())
    order = np.argsort(risk.to_numpy(), kind="stable")
    stress = np.empty(len(order))
    stress[order] = np.linspace(0, 1, len(order))
    means["stress_rank"] = stress
    return stress, means


def features(returns, sigma, vix):
    r = returns["SPY"]
    wealth = np.exp(r.cumsum())
    corr = pd.concat([returns[a].rolling(21).corr(returns[b])
                      for a, b in (("AAPL", "MSFT"), ("AAPL", "SPY"), ("MSFT", "SPY"))], axis=1).mean(axis=1)
    vol = r.rolling(21).std()
    return pd.DataFrame({"SPY_Return": r, "SPY_V": zscore(sigma["SPY"]),
                         "RollingVol21": vol, "RollingSkew21": r.rolling(21).skew(),
                         "Drawdown": wealth / wealth.cummax() - 1,
                         "VolOfVol": vol.rolling(21).std(), "VIX": vix, "C_t": corr})


def build_indices(returns, sigma, panic, stress, tail, cfg, entropy_window=None):
    """Build asset and portfolio variants; panic is common market-level signal."""
    window = entropy_window or cfg.entropy_window
    v = zscore(sigma, cfg.window)
    t = zscore(tail, cfg.window)
    p = zscore(panic, cfg.window)
    realized = zscore(returns.rolling(21).std(), cfg.window)
    corr = features(returns, sigma, pd.Series(index=returns.index, dtype=float))["C_t"]
    c = zscore(corr, cfg.window)
    out, weights, components = {}, {}, {}
    for asset in ASSETS:
        z = pd.DataFrame({"V": v[asset], "P": p, "T": t[asset]})
        e = entropy_weights(z, window)
        # Risk-ranked five-state factors interpolate the documented bull/panic endpoints.
        factors = pd.DataFrame({"V": 1.3 - .5 * stress, "P": .8 + .3 * stress,
                                "T": .9 + .5 * stress})
        w = floor_weights(e * factors, cfg.min_weight)
        variants = {"Adaptive": (w * z).sum(axis=1, min_count=3),
                    "Equal": z.mean(axis=1, skipna=False),
                    "Entropy": (floor_weights(e, cfg.min_weight) * z).sum(axis=1, min_count=3)}
        noevt = floor_weights((e * factors)[["V", "P"]], cfg.min_weight)
        variants["NoEVT"] = (noevt * z[["V", "P"]]).sum(axis=1, min_count=2)
        # Remove both the panic signal AND its regime-driven weighting.
        no_hmm_z = z[["V", "T"]]
        variants["NoHMM"] = (floor_weights(entropy_weights(no_hmm_z, window), cfg.min_weight)
                              * no_hmm_z).sum(axis=1, min_count=2)
        nongarch = z.assign(V=realized[asset])
        variants["NoGARCH"] = (floor_weights(entropy_weights(nongarch, window) * factors,
                                             cfg.min_weight) * nongarch).sum(axis=1, min_count=3)
        # PCA loadings fit only to observations strictly before each monthly block.
        pca = pd.Series(np.nan, index=z.index)
        loadings = pd.DataFrame(np.nan, index=z.index, columns=COMPONENTS)
        for start in range(0, len(z), cfg.refit_every):
            history = z.iloc[:start].dropna()
            if len(history) < 126:
                continue
            _, _, vh = np.linalg.svd(history - history.mean(), full_matrices=False)
            loading = np.abs(vh[0])
            loading = loading / loading.sum()
            end = min(start + cfg.refit_every, len(z))
            pca.iloc[start:end] = z.iloc[start:end].mul(loading).sum(axis=1, min_count=3)
            loadings.iloc[start:end] = loading
        variants["PCA"] = pca
        four_z = z.assign(C=c)
        four_f = factors.assign(C=1.)
        four_w = floor_weights(entropy_weights(four_z, window) * four_f, cfg.min_weight)
        variants["Adaptive4"] = (four_w * four_z).sum(axis=1, min_count=4)
        out[asset] = pd.DataFrame(variants)
        weights[asset] = pd.concat({"adaptive": w, "entropy": e, "pca": loadings,
                                    "adaptive4": four_w}, axis=1)
        components[asset] = four_z
    portfolio = sum(out.values()) / len(ASSETS)
    return out, portfolio, weights, components


def moving_block_bootstrap(values, repetitions=1000, block=30, seed=42):
    x = np.asarray(values)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.array([np.nan, np.nan])
    rng = np.random.default_rng(seed)
    result = []
    for _ in range(repetitions):
        starts = rng.integers(0, len(x), size=int(np.ceil(len(x) / block)))
        indices = (starts[:, None] + np.arange(block)) % len(x)
        result.append(np.mean(x[indices.ravel()[:len(x)]]))
    return np.quantile(result, [.025, .975])


def dm_test(actual, forecast_a, forecast_b, horizon=30):
    """Two-sided squared-loss DM test with Bartlett HAC and HLN correction."""
    d = (np.asarray(actual) - forecast_a) ** 2 - (np.asarray(actual) - forecast_b) ** 2
    d = np.asarray(d)[np.isfinite(d)]
    n = len(d)
    if n <= horizon + 2:
        return dict(n=n, dm=np.nan, pvalue=np.nan)
    centered = d - d.mean()
    lrv = np.dot(centered, centered) / n
    for lag in range(1, horizon):
        lrv += 2 * (1 - lag / horizon) * np.dot(centered[lag:], centered[:-lag]) / n
    if lrv <= 0:
        return dict(n=n, dm=np.nan, pvalue=np.nan)
    correction = np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n)
    statistic = d.mean() / np.sqrt(lrv / n) * correction
    return dict(n=n, dm=float(statistic), pvalue=float(2 * stats.t.sf(abs(statistic), n - 1)))


def fingerprint(root, cfg, components_only=False):
    digest = hashlib.sha256(json.dumps(asdict(cfg), sort_keys=True).encode())
    for p in sorted((Path(root) / "acmsi").glob("*.py")):
        if components_only and p.name not in ("core.py", "models.py", "evt.py"):
            continue
        digest.update(p.read_bytes())
    for name in ("Data/prices_clean.csv", "Data/HMM data/HMM_Input_Features.csv"):
        digest.update((Path(root) / name).read_bytes())
    return digest.hexdigest()[:16]
