"""Full nine-cell chronological EVT grid; no unreported threshold changes."""
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from acmsi.core import ASSETS,fit_tail
from .signatures import signature

LOG=logging.getLogger(__name__)


def experiment_name(window,quantile):
    return f"w{window}_q{quantile*100:g}"


def run_grid(returns,cfg,out):
    directory=out/"evt"; directory.mkdir(parents=True,exist_ok=True)
    descriptive=[]
    for asset in ASSETS:
        for q in (.9,.95,.975):
            descriptive.append(dict(asset=asset,**fit_tail(-returns[asset],q,cfg.min_exceedances)))
    pd.DataFrame(descriptive).to_csv(directory/"full_sample_descriptive.csv",index=False)
    summary=[]
    key=signature(cfg,[returns],__file__)
    for window in (252,378,504):
        for q in (.9,.95,.975):
            name=experiment_name(window,q); path=directory/name; path.mkdir(exist_ok=True)
            marker=path/"complete.json"
            if marker.exists() and json.loads(marker.read_text()).get("signature")!=key:
                raise RuntimeError(f"Stale experiment marker {marker}; rerun with --redo")
            if not (path/"complete.json").exists():
                LOG.info("EVT rolling grid %s",name)
                tail=pd.DataFrame(np.nan,index=returns.index,columns=ASSETS); records=[]
                for asset in ASSETS:
                    losses=-returns[asset]
                    for i in range(window-1,len(losses)):
                        sample=losses.iloc[i-window+1:i+1].to_numpy()
                        try:
                            row=fit_tail(sample,q,cfg.min_exceedances)
                        except Exception as error:
                            # An experiment failure is retained as a diagnosed per-fit fallback.
                            u=float(np.quantile(sample,q))
                            row=dict(status="fit_exception",error=repr(error),n=len(sample),
                                     threshold_quantile=q,u=u,n_exceed=int((sample>u).sum()))
                        if row["status"]!="ok" or not np.isfinite(row.get("ES99",np.nan)):
                            cutoff=np.quantile(sample,.99)
                            value=float(sample[sample>=cutoff].mean()); fallback="empirical_ES99"
                        else:
                            value=row["ES99"]; fallback="none"
                        row.update(Date=returns.index[i],asset=asset,window=window,q=q,
                                   fallback=fallback,tail_score_raw=value)
                        records.append(row); tail.iloc[i,tail.columns.get_loc(asset)]=value
                pd.DataFrame(records).to_csv(path/"diagnostics.csv",index=False)
                tail.to_csv(path/"tail.csv",index_label="Date")
                (path/"complete.json").write_text(json.dumps(dict(window=window,q=q,min_exceedances=cfg.min_exceedances,signature=key)))
            records=pd.read_csv(path/"diagnostics.csv")
            for asset,g in records.groupby("asset"):
                row=dict(experiment=name,window=window,q=q,asset=asset,n=len(g),
                         fallback_count=int(g.fallback.ne("none").sum()),fallback_fraction=float(g.fallback.ne("none").mean()),
                         exceedance_min=int(g.n_exceed.min()),exceedance_median=float(g.n_exceed.median()),
                         fit_exception_count=int(g.status.eq("fit_exception").sum()),
                         infinite_es_count=int(g.status.eq("infinite_expected_shortfall").sum()))
                for column in ("xi","beta","VaR99","ES99","tail_score_raw"):
                    x=g[column].replace([np.inf,-np.inf],np.nan).dropna() if column in g else pd.Series(dtype=float)
                    row[column+"_valid"]=len(x)
                    for label,qv in (("p05",.05),("median",.5),("p95",.95),("p99",.99)):
                        row[column+"_"+label]=float(x.quantile(qv)) if len(x) else np.nan
                    row[column+"_max"]=float(x.max()) if len(x) else np.nan
                    row[column+"_median_abs_daily_change"]=float(g[column].diff().abs().median()) if column in g else np.nan
                summary.append(row)
            LOG.info("EVT %s complete; fallback %d/%d",name,records.fallback.ne("none").sum(),len(records))
    pd.DataFrame(summary).to_csv(directory/"parameter_stability.csv",index=False)
