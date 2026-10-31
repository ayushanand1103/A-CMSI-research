import logging
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from .core import ASSETS, fit_tail

LOG = logging.getLogger(__name__)


def tail_analysis(returns, cfg, output):
    rows, static, mef = [], [], []
    tail = pd.DataFrame(np.nan, index=returns.index, columns=ASSETS)
    for asset in ASSETS:
        LOG.info("Rolling EVT: %s", asset)
        losses = -returns[asset]
        for q in (.90, .95, .99):
            static.append(dict(asset=asset, **fit_tail(losses, q, cfg.min_exceedances)))
        thresholds = np.quantile(losses, np.linspace(.80, .99, 60))
        fig, ax = plt.subplots(figsize=(8, 4))
        excess_mean = [float((losses[losses > u] - u).mean()) for u in thresholds]
        ax.plot(thresholds, excess_mean)
        ax.set(xlabel="Loss threshold", ylabel="Mean excess", title=f"{asset}: mean excess")
        fig.tight_layout()
        fig.savefig(output / "figures" / f"mef_{asset}.png", dpi=150)
        plt.close(fig)
        mef.extend(dict(asset=asset, threshold=u, mean_excess=m) for u, m in zip(thresholds, excess_mean))
        # At close t: use losses through t. No subsequent observation enters a fit.
        for i in range(cfg.window - 1, len(losses)):
            sample = losses.iloc[i-cfg.window+1:i+1]
            row = fit_tail(sample, cfg.threshold, cfg.min_exceedances)
            row.update(Date=returns.index[i], asset=asset)
            # Explicit empirical fallback keeps ES finite when a 252-day GPD is unstable.
            if row["status"] != "ok" or not np.isfinite(row.get("ES99", np.nan)):
                quantile = sample.quantile(.99)
                value = float(sample[sample >= quantile].mean())
                row["fallback"] = "empirical_ES99"
            else:
                value = row["ES99"]
                row["fallback"] = "none"
            tail.iloc[i, tail.columns.get_loc(asset)] = value
            row["tail_score_raw"] = value
            rows.append(row)
        # Full sample Q-Q is a descriptive diagnostic, never an OOS input.
        fitted = fit_tail(losses, cfg.threshold, cfg.min_exceedances)
        excess = np.sort(losses[losses > fitted["u"]] - fitted["u"])
        expected = stats.genpareto.ppf((np.arange(len(excess))+.5)/len(excess),
                                      fitted["xi"], scale=fitted["beta"])
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(expected, excess, s=8)
        limit = max(expected.max(), excess.max())
        ax.plot([0, limit], [0, limit], color="gray")
        ax.set(xlabel="Fitted GPD quantile", ylabel="Observed excess", title=f"{asset}: descriptive tail Q-Q")
        fig.tight_layout()
        fig.savefig(output / "figures" / f"gpd_qq_{asset}.png", dpi=150)
        plt.close(fig)
    pd.DataFrame(rows).to_csv(output / "tables/rolling_evt_diagnostics.csv", index=False)
    pd.DataFrame(static).to_csv(output / "tables/evt_threshold_sensitivity.csv", index=False)
    pd.DataFrame(mef).to_csv(output / "tables/mean_excess.csv", index=False)
    return tail
