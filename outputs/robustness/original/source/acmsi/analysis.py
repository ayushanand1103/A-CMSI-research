"""Descriptive diagnostics, wavelets, external benchmarks, and figures."""
import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pywt
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM, select_coint_rank
from statsmodels.nonparametric.smoothers_lowess import lowess
import statsmodels.api as sm
from .core import ASSETS

LOG = logging.getLogger(__name__)


def diagnostic_analysis(prices, returns, output):
    tables, figures = output / "tables", output / "figures"
    returns.describe().T.to_csv(tables / "return_descriptive_statistics.csv")
    rows = []
    for asset in ASSETS:
        for kind, x in (("price", prices[asset]), ("return", returns[asset]),
                        ("price_difference", prices[asset].diff().dropna())):
            adf = adfuller(x, autolag="BIC")
            kp = kpss(x, regression="c", nlags="auto")
            rows.append(dict(asset=asset, series=kind, adf_stat=adf[0], adf_p=adf[1],
                             kpss_stat=kp[0], kpss_p=kp[1], kpss_p_is_table_bound=kp[1] in (.01, .1)))
    pd.DataFrame(rows).to_csv(tables / "stationarity.csv", index=False)
    cointegration, adjustment = [], []
    for assets in (ASSETS, ("AAPL", "MSFT"), ("AAPL", "SPY"), ("MSFT", "SPY")):
        # Explicitly use log levels. ECM only if estimated rank is between 0 and n.
        x = np.log(prices[list(assets)])
        result = coint_johansen(x, det_order=0, k_ar_diff=1)
        rank = select_coint_rank(x, det_order=0, k_ar_diff=1, signif=.05).rank
        for i, (trace, critical) in enumerate(zip(result.lr1, result.cvt[:, 1])):
            cointegration.append(dict(assets="/".join(assets), null_rank=i, trace=trace,
                                       critical_5pct=critical, selected_rank=rank))
        if 0 < rank < len(assets):
            fit = VECM(x, k_ar_diff=1, coint_rank=rank, deterministic="ci").fit()
            for i, asset in enumerate(assets):
                for j in range(rank):
                    adjustment.append(dict(assets="/".join(assets), asset=asset, relation=j,
                                           alpha=fit.alpha[i,j], alpha_p=fit.pvalues_alpha[i,j],
                                           beta=fit.beta[i,j]))
    pd.DataFrame(cointegration).to_csv(tables / "johansen.csv", index=False)
    pd.DataFrame(adjustment, columns=["assets", "asset", "relation", "alpha", "alpha_p", "beta"]).to_csv(tables / "ecm.csv", index=False)
    # Offline segmented mean search: coarse-grid multiple-break regression on rolling variance.
    # It is labeled separately from the existing R strucchange Bai-Perron implementation.
    break_rows = []
    for asset in ASSETS:
        x = returns[asset].rolling(21).var().dropna()
        y = x.to_numpy()
        points = np.unique(np.r_[0, np.arange(252, len(y)-251, 21), len(y)])
        n = len(points)
        s1, s2 = np.r_[0, np.cumsum(y)], np.r_[0, np.cumsum(y*y)]
        def sse(a, b):
            return max(float(s2[b]-s2[a]-(s1[b]-s1[a])**2/(b-a)), 1e-30)
        dp = np.full((6, n), np.inf)
        previous = np.full((6, n), -1, dtype=int)
        dp[0, 0] = 0
        for segments in range(1, 6):
            for j in range(1, n):
                for k in range(j):
                    if points[j]-points[k] >= 252:
                        score = dp[segments-1,k] + sse(points[k], points[j])
                        if score < dp[segments,j]:
                            dp[segments,j], previous[segments,j] = score, k
        bics = [len(y)*np.log(dp[k,-1]/len(y))+(2*k-1)*np.log(len(y)) for k in range(1,6)]
        segments = int(np.argmin(bics))+1
        j, boundaries = n-1, []
        for k in range(segments, 0, -1):
            j = previous[k,j]
            if j > 0:
                boundaries.append(points[j])
        for b in sorted(boundaries):
            unrestricted = sse(0,b)+sse(b,len(y))
            f = (sse(0,len(y))-unrestricted)/(unrestricted/(len(y)-2))
            break_rows.append(dict(asset=asset, date=x.index[b], break_index=b,
                                   chow_f=f, chow_p_naive=stats.f.sf(f,1,len(y)-2),
                                   method="coarse_grid_segmented_mean_BIC_21day_grid",
                                   inference="post_selection_p_descriptive_only"))
        fig, axs = plt.subplots(3,1,figsize=(12,8), sharex=True)
        axs[0].plot(prices.index, prices[asset]); axs[0].set_title(asset+" adjusted close")
        axs[1].plot(returns.index, returns[asset], lw=.5); axs[1].set_title("Daily log returns")
        axs[2].plot(x.index, x); axs[2].set_title("21-day rolling variance; offline break estimates")
        for b in boundaries:
            axs[2].axvline(x.index[b], color="red", alpha=.5)
        fig.tight_layout(); fig.savefig(figures/f"eda_{asset}.png",dpi=150); plt.close(fig)
    pd.DataFrame(break_rows).to_csv(tables/"segmented_variance_breaks.csv",index=False)
    logprice = np.log(prices)
    detrended = pd.DataFrame(index=prices.index)
    for asset in ASSETS:
        trend = lowess(logprice[asset], np.arange(len(prices)), frac=.10, return_sorted=False)
        detrended[asset+"_trend"] = trend
        detrended[asset+"_residual"] = logprice[asset]-trend
    detrended.to_csv(output/"data/loess_descriptive_only.csv")
    correlations = pd.DataFrame({a+"_"+b: returns[a].rolling(63).corr(returns[b])
                                 for a,b in (("AAPL","MSFT"),("AAPL","SPY"),("MSFT","SPY"))})
    correlations.to_csv(output/"data/rolling_correlations_63.csv")
    ax = correlations.plot(figsize=(12,4), title="63-day rolling pairwise correlations")
    ax.figure.tight_layout(); ax.figure.savefig(figures/"correlations.png",dpi=150); plt.close(ax.figure)


def wavelets(returns, output):
    periods = np.geomspace(4, 256, 72)
    wavelet = "cmor1.5-1.0"
    scales = periods * pywt.central_frequency(wavelet)
    coeffs = {}
    # Cone of influence: conservative sqrt(2)*scale distance from either edge.
    distance = np.minimum(np.arange(len(returns))+1, len(returns)-np.arange(len(returns)))
    edge = distance[None,:] < np.sqrt(2)*scales[:,None]
    summary = []
    for asset in ASSETS:
        x = returns[asset].to_numpy()
        x = (x-x.mean())/x.std()
        w,_ = pywt.cwt(x, scales, wavelet)
        coeffs[asset] = w
        power = np.abs(w)**2
        display = np.ma.array(power, mask=edge)
        fig,ax = plt.subplots(figsize=(12,4))
        im=ax.pcolormesh(returns.index,periods,display,shading="auto",cmap="magma")
        ax.set(yscale="log",ylabel="Period (trading days)",title=asset+": Morlet wavelet power; edges masked")
        fig.colorbar(im,ax=ax); fig.tight_layout()
        fig.savefig(output/"figures"/f"wavelet_{asset}.png",dpi=150); plt.close(fig)
        for period, values, mask in zip(periods, power, edge):
            summary.append(dict(asset=asset, period=period, mean_power=np.mean(values[~mask])))
    pd.DataFrame(summary).to_csv(output/"tables/wavelet_power.csv",index=False)
    for a,b in (("AAPL","MSFT"),("AAPL","SPY")):
        wa,wb = coeffs[a],coeffs[b]
        def smooth(x):
            # Time smoothing proportional to scale, plus local scale smoothing.
            from scipy.ndimage import gaussian_filter1d
            out = np.vstack([gaussian_filter1d(row, max(1.,scale), mode="nearest")
                             for row,scale in zip(x,scales)])
            return gaussian_filter1d(out,1.,axis=0,mode="nearest")
        cross = wa*np.conj(wb)/scales[:,None]
        sx = smooth(cross.real)+1j*smooth(cross.imag)
        denominator = smooth(np.abs(wa)**2/scales[:,None])*smooth(np.abs(wb)**2/scales[:,None])
        coherence = np.clip(np.abs(sx)**2/np.maximum(denominator,1e-12),0,1)
        fig,ax = plt.subplots(figsize=(12,4))
        im=ax.pcolormesh(returns.index,periods,np.ma.array(coherence,mask=edge),shading="auto",vmin=0,vmax=1,cmap="viridis")
        ax.set(yscale="log",ylabel="Period (trading days)",title=f"{a}–{b}: descriptive wavelet coherence (no significance contours)")
        fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(output/"figures"/f"coherence_{a}_{b}.png",dpi=150); plt.close(fig)


def index_figures(portfolio, weights, components, returns, output):
    figures = output/"figures"
    events = {"COVID": "2020-03-16", "Inflation/rate hikes": "2022-01-03", "SVB": "2023-03-10", "AI rally": "2023-11-01"}
    ax=portfolio[["Adaptive","Equal","PCA","Entropy"]].plot(figsize=(14,5),lw=1)
    for label,date in events.items():
        ax.axvline(pd.Timestamp(date),color="gray",alpha=.5)
        ax.text(pd.Timestamp(date),ax.get_ylim()[1],label,rotation=90,va="top",fontsize=8)
    ax.set_title("A-CMSI and baselines; after-close signals, initial period is model warmup")
    ax.figure.tight_layout(); ax.figure.savefig(figures/"acmsi_comparison.png",dpi=160); plt.close(ax.figure)
    ax=weights["SPY"]["adaptive"].plot(figsize=(14,4),title="SPY adaptive component weights",ylim=(0,1))
    ax.figure.tight_layout(); ax.figure.savefig(figures/"adaptive_weights.png",dpi=150); plt.close(ax.figure)
    ax=components["SPY"].plot(subplots=True,figsize=(14,8),title="SPY normalized components")
    fig=ax[0].figure; fig.tight_layout(); fig.savefig(figures/"components_SPY.png",dpi=150); plt.close(fig)
    wealth = np.exp(returns["SPY"].cumsum())
    drawdown = wealth/wealth.cummax()-1
    for label,date in events.items():
        center=pd.Timestamp(date)
        lo,hi=center-pd.Timedelta(days=120),center+pd.Timedelta(days=150)
        fig,ax=plt.subplots(figsize=(11,4))
        ax.plot(portfolio.loc[lo:hi].index,portfolio.loc[lo:hi,"Adaptive"],label="Adaptive CMSI")
        ax.set_ylabel("Index z-score"); other=ax.twinx()
        other.plot(drawdown.loc[lo:hi].index,drawdown.loc[lo:hi],color="red",alpha=.5)
        other.set_ylabel("SPY drawdown from running high")
        ax.axvline(center,color="gray",ls="--"); ax.set_title(label+": descriptive event window")
        fig.tight_layout(); fig.savefig(figures/("event_"+date+".png"),dpi=150); plt.close(fig)


def external_comparison(portfolio, target, output, download=False):
    import io
    import requests
    directory=output/"external"; directory.mkdir(exist_ok=True)
    status=[]; series=[]
    for identifier in ("STLFSI4","KCFSI"):
        file=directory/(identifier+".csv")
        if download:
            response=requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",params={"id":identifier},timeout=60)
            response.raise_for_status()
            parsed=pd.read_csv(io.StringIO(response.text))
            if identifier not in parsed:
                raise ValueError(f"Unexpected FRED response for {identifier}")
            file.write_text(response.text,encoding="utf-8")
        if not file.exists():
            status.append(dict(series=identifier,status="not_downloaded")); continue
        df=pd.read_csv(file,na_values=".")
        df.index=pd.to_datetime(df.iloc[:,0])
        s=pd.to_numeric(df[identifier],errors="coerce").dropna()
        # Conservative publication lag; no vintage history is available in this export.
        lag=7 if identifier=="STLFSI4" else 45
        s.index=s.index+pd.Timedelta(days=lag)
        series.append(s.reindex(portfolio.index.union(s.index)).sort_index().ffill().reindex(portfolio.index).rename(identifier))
        status.append(dict(series=identifier,status="available_revised_data_descriptive_only",assumed_release_lag_days=lag))
    pd.DataFrame(status).to_csv(output/"tables/external_status.csv",index=False)
    if len(series)!=2:
        return
    external=pd.concat(series,axis=1)
    combined=external.join(portfolio.Adaptive).join(target.future_vol).dropna()
    rolling=pd.DataFrame({name:combined.Adaptive.rolling(63).corr(combined[name]) for name in external})
    rolling.to_csv(output/"data/external_rolling_correlations.csv")
    combined.corr().to_csv(output/"tables/external_correlations.csv")
    # Expanding residualization and held-out incremental volatility prediction.
    records=[]
    for start in range(504,len(combined),21):
        train=combined.iloc[:start-30]
        test=combined.iloc[start:start+21]
        projection=sm.OLS(train.Adaptive,sm.add_constant(train[list(external)])).fit()
        residual_train=train.Adaptive-projection.predict(sm.add_constant(train[list(external)],has_constant="add"))
        residual_test=test.Adaptive-projection.predict(sm.add_constant(test[list(external)],has_constant="add"))
        base_x=train[list(external)]
        augmented=base_x.assign(index_residual=residual_train)
        b=sm.OLS(train.future_vol,sm.add_constant(base_x)).fit()
        a=sm.OLS(train.future_vol,sm.add_constant(augmented)).fit()
        bp=b.predict(sm.add_constant(test[list(external)],has_constant="add"))
        ap=a.predict(sm.add_constant(test[list(external)].assign(index_residual=residual_test),has_constant="add"))
        records.extend(dict(Date=date,actual=row.future_vol,external_only=bp.loc[date],
                            external_plus_acmsi=ap.loc[date]) for date,row in test.iterrows())
    prediction=pd.DataFrame(records)
    prediction.to_csv(output/"tables/external_incremental_predictions.csv",index=False)
    if len(prediction):
        pd.DataFrame([dict(model=k,rmse=np.sqrt(np.mean((prediction.actual-prediction[k])**2)))
                      for k in ("external_only","external_plus_acmsi")]).to_csv(output/"tables/external_incremental_metrics.csv",index=False)


def validation_figures(portfolio, posteriors, panic, returns, target, prediction, cfg, output):
    from sklearn.metrics import roc_curve, roc_auc_score
    figures=output/"figures"
    fig,ax=plt.subplots(figsize=(7,6))
    for variant,g in prediction.groupby("variant"):
        g=g.dropna(subset=["actual_crisis","crisis_probability"])
        if not len(g) or g.actual_crisis.nunique()<2:
            continue
        fpr,tpr,_=roc_curve(g.actual_crisis,g.crisis_probability)
        ax.plot(fpr,tpr,label=f"{variant} ({roc_auc_score(g.actual_crisis,g.crisis_probability):.3f})")
    ax.plot([0,1],[0,1],color="gray",ls="--")
    ax.set(xlabel="False positive rate",ylabel="True positive rate",title="Held-out next-30-day crisis ROC curves")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figures/"crisis_roc_forecast.png",dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6))
    for variant in portfolio:
        s=portfolio[variant].iloc[cfg.initial_train:]
        keep=s.notna()
        y=target.current_crisis.reindex(s.index)[keep]
        fpr,tpr,_=roc_curve(y,s[keep])
        ax.plot(fpr,tpr,label=f"{variant} ({roc_auc_score(y,s[keep]):.3f})")
    ax.plot([0,1],[0,1],color="gray",ls="--")
    ax.set(xlabel="False positive rate",ylabel="True positive rate",title="Same-day after-close detection ROC curves")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figures/"crisis_roc_detection.png",dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(14,4))
    g=prediction[prediction.variant.eq("Adaptive")].set_index("Date")
    ax.plot(g.index,g.actual_vol,label="Next-30-day realized volatility",color="black",lw=1)
    ax.plot(g.index,g.forecast_vol,label="Adaptive forecast",alpha=.8,lw=1)
    ax.set(ylabel="Annualized volatility",title="Chronological forecasts (last 30 outcomes not yet available)")
    ax.legend(); fig.tight_layout(); fig.savefig(figures/"volatility_forecasts.png",dpi=150); plt.close(fig)
    fig,axs=plt.subplots(2,1,figsize=(14,6),sharex=True)
    axs[0].stackplot(posteriors.index,posteriors.fillna(0).to_numpy().T,
                     labels=[f"Risk rank {i}" for i in range(posteriors.shape[1])],alpha=.8)
    axs[0].legend(loc="upper right",ncol=3,fontsize=8)
    axs[0].set_title("Forward-filtered regime probabilities; initial region is training reconstruction")
    axs[1].plot(panic.index,panic,color="red",lw=1)
    axs[1].set(ylabel="Panic probability",ylim=(0,1))
    fig.tight_layout(); fig.savefig(figures/"filtered_regime_probabilities.png",dpi=150); plt.close(fig)
    valid=posteriors.dropna()
    ranks=np.argmax(valid.to_numpy(),axis=1)
    durations=[]; start=0
    for i in range(1,len(ranks)+1):
        if i==len(ranks) or ranks[i]!=ranks[start]:
            durations.append(dict(risk_rank=int(ranks[start]),start=valid.index[start],
                                  end=valid.index[i-1],duration=i-start))
            start=i
    pd.DataFrame(durations).to_csv(output/"tables/regime_durations.csv",index=False)
    fig,ax=plt.subplots(figsize=(7,4))
    for rank in range(posteriors.shape[1]):
        values=[d["duration"] for d in durations if d["risk_rank"]==rank]
        ax.hist(values,bins=np.arange(0,125,5),alpha=.4,label=f"Risk {rank}")
    ax.set(xlabel="Consecutive trading days",ylabel="Episodes",title="Filtered-regime durations (display truncated at 120 days)")
    ax.legend(); fig.tight_layout(); fig.savefig(figures/"regime_durations.png",dpi=150); plt.close(fig)
    events=pd.read_csv(output/"tables/early_warning.csv")
    events=events[events.variant.eq("Adaptive") & events.evaluable.astype(bool)]
    s=portfolio.Adaptive
    threshold=s.shift(1).expanding(min_periods=126).quantile(.90)
    dd=np.expm1(returns.SPY.rolling(20).sum())
    for _,row in events.iterrows():
        event=pd.Timestamp(row.event_date)
        lo,hi=event-pd.Timedelta(days=100),event+pd.Timedelta(days=60)
        fig,ax=plt.subplots(figsize=(11,4))
        ax.plot(s.loc[lo:hi].index,s.loc[lo:hi],label="Adaptive")
        ax.plot(threshold.loc[lo:hi].index,threshold.loc[lo:hi],ls="--",label="Prior-history 90th percentile")
        if pd.notna(row.last_crossing):
            ax.axvspan(pd.Timestamp(row.last_crossing),event,alpha=.15,color="orange",label="Last crossing to event")
        other=ax.twinx(); other.plot(dd.loc[lo:hi].index,dd.loc[lo:hi],color="red",alpha=.5)
        other.set_ylabel("Trailing 20-day cumulative return"); other.axhline(-.1,color="red",ls=":")
        ax.axvline(event,color="gray"); ax.set_title(f"Early-warning event {event.date()}")
        ax.legend(loc="upper left",fontsize=8); fig.tight_layout()
        fig.savefig(figures/f"early_warning_{event.date()}.png",dpi=150); plt.close(fig)
