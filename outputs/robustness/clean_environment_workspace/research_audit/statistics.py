"""Matched-date metrics, dependence-aware uncertainty and multiplicity control."""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from statsmodels.stats.multitest import multipletests
from acmsi.core import dm_test


def block_indices(n, draws=1000, block=30, seed=42):
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n,(draws,int(np.ceil(n/block))))
    return ((starts[:,:,None]+np.arange(block))%n).reshape(draws,-1)[:,:n]


def values(frame):
    y=frame.actual_vol.to_numpy(); f=frame.forecast_vol.to_numpy()
    result=dict(rmse=float(np.sqrt(np.mean((y-f)**2))),mae=float(np.mean(np.abs(y-f))))
    if "crisis_probability" in frame and frame.crisis_probability.notna().all():
        truth=frame.actual_crisis.to_numpy(); probability=frame.crisis_probability.to_numpy()
        signal=probability>=.5
        positives=truth.astype(bool); n1=int(positives.sum()); n0=len(truth)-n1
        auc=(stats.rankdata(probability)[positives].sum()-n1*(n1+1)/2)/(n1*n0) if n1 and n0 else np.nan
        tp=int((signal&positives).sum()); fp=int((signal&~positives).sum()); fn=int((~signal&positives).sum())
        result.update(auc=float(auc),brier=float(np.mean((truth-probability)**2)),
                      precision=tp/(tp+fp) if tp+fp else 0.,recall=tp/(tp+fn) if tp+fn else 0.,
                      f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)
    return result


def summarize(predictions, draws=1000, block=30, seed=42):
    rows=[]
    for variant,g in predictions.groupby("variant",sort=True):
        g=g.dropna(subset=["actual_vol","forecast_vol"]).sort_values("Date")
        point=values(g)
        boot={name:[] for name in point}
        for ix in block_indices(len(g),draws,block,seed):
            for name,value in values(g.iloc[ix]).items():
                boot[name].append(value)
        row=dict(variant=variant,n=len(g),first_date=g.Date.min(),last_date=g.Date.max(),block=block,
                 crisis_positive=int(g.actual_crisis.sum()) if "actual_crisis" in g else np.nan,**point)
        for name,results in boot.items():
            a=np.asarray(results); a=a[np.isfinite(a)]
            row[name+"_ci_low"],row[name+"_ci_high"]=np.quantile(a,[.025,.975]) if len(a) else (np.nan,np.nan)
            row[name+"_bootstrap_valid"]=len(a)
        rows.append(row)
    return pd.DataFrame(rows)


def paired(predictions, pairs, family, draws=1000, block=30, seed=42, hac_lag=None):
    """Positive improvement always favors candidate; p-values are squared-loss DM."""
    rows=[]
    for candidate,reference in pairs:
        a=predictions[predictions.variant.eq(candidate)].set_index("Date").sort_index()
        b=predictions[predictions.variant.eq(reference)].set_index("Date").sort_index()
        dates=a.dropna(subset=["actual_vol","forecast_vol"]).index.intersection(b.dropna(subset=["actual_vol","forecast_vol"]).index)
        a,b=a.loc[dates],b.loc[dates]
        np.testing.assert_allclose(a.actual_vol,b.actual_vol,atol=1e-14)
        va,vb=values(a),values(b)
        dm=dm_test(a.actual_vol.to_numpy(),a.forecast_vol.to_numpy(),b.forecast_vol.to_numpy(),30)
        if hac_lag is not None:
            d=(a.actual_vol-a.forecast_vol)**2-(b.actual_vol-b.forecast_vol)**2
            centered=d.to_numpy()-d.mean(); n=len(d)
            lrv=np.dot(centered,centered)/n
            for lag in range(1,min(hac_lag,n-1)+1):
                lrv+=2*(1-lag/(hac_lag+1))*np.dot(centered[lag:],centered[:-lag])/n
            statistic=d.mean()/np.sqrt(lrv/n)*np.sqrt((n+1-60+30*29/n)/n) if lrv>0 else np.nan
            dm=dict(n=n,dm=statistic,pvalue=2*stats.t.sf(abs(statistic),n-1))
        row=dict(family=family,candidate=candidate,reference=reference,block=block,hac_lag=29 if hac_lag is None else hac_lag,**dm)
        improvements={name:[] for name in va.keys()&vb.keys()}
        for ix in block_indices(len(a),draws,block,seed):
            ba,bb=values(a.iloc[ix]),values(b.iloc[ix])
            for name in improvements:
                sign=-1 if name in ("rmse","mae","brier") else 1
                improvements[name].append(sign*(ba[name]-bb[name]))
        for name,results in improvements.items():
            sign=-1 if name in ("rmse","mae","brier") else 1
            row[name+"_improvement"]=sign*(va[name]-vb[name])
            x=np.asarray(results); x=x[np.isfinite(x)]
            low,high=np.quantile(x,[.025,.975]) if len(x) else (np.nan,np.nan)
            row[name+"_ci_low"],row[name+"_ci_high"]=low,high
            row[name+"_valid_draws"]=len(x)
        rows.append(row)
    result=pd.DataFrame(rows)
    if len(result):
        valid=result.pvalue.notna()
        result.loc[valid,"p_holm_family"]=multipletests(result.loc[valid,"pvalue"],method="holm")[1]
    return result


def global_adjustment(frames):
    combined=pd.concat(frames,ignore_index=True)
    valid=combined.pvalue.notna()
    combined.loc[valid,"p_holm_global"]=multipletests(combined.loc[valid,"pvalue"],method="holm")[1]
    return combined
