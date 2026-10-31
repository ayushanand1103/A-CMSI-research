"""Matched-date evaluations; all specifications fixed by the execution protocol."""
import itertools
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from acmsi.core import build_indices,ASSETS
from acmsi.validation import targets,crisis_detection
from .calibration import calibrate
from .indices import controlled
from .statistics import summarize,paired,global_adjustment
from .evt import experiment_name

LOG=logging.getLogger(__name__)


def series(path):
    return pd.read_csv(path,index_col=0,parse_dates=True).iloc[:,0]


def evaluate(prices,returns,sigma,cfg,out):
    directory=out/"evaluation"; directory.mkdir(exist_ok=True)
    base=out/"original/data"
    tail=pd.read_csv(base/"tail_ES99.csv",index_col=0,parse_dates=True)
    families={}; conditionals={}; pairsets={}
    state_ports={}
    for k in (3,4,5,6):
        path=out/"hmm"/f"states_{k}"
        panic,stress=series(path/"panic.csv"),series(path/"stress.csv")
        _,port,_,_=build_indices(returns,sigma,panic,stress,tail,cfg)
        state_ports[f"HMM{k}"]=port.Adaptive
    families["hmm"]=pd.DataFrame(state_ports)
    pairsets["hmm"]=list(itertools.combinations(state_ports,2))
    path=out/"hmm/states_5"
    panic,stress=series(path/"panic.csv"),series(path/"stress.csv")
    post=pd.read_csv(path/"posteriors.csv",index_col=0,parse_dates=True)
    target=targets(returns,prices,post,cfg.horizon)
    control,weights,conditional=controlled(returns,sigma,panic,stress,tail,cfg)
    weights.to_csv(directory/"new_weight_constraints.csv",index=False)
    families["ablation"]=control
    conditionals["ablation"]=conditional
    pairsets["ablation"]=[("Adaptive",name) for name in ("NoProbability","Entropy","NoHMM","Equal","PCA","NoEVT","NoGARCH")]
    pairsets["ablation"] += [("ConditionalVTP","ConditionalVT"),("ConditionalVTStress","ConditionalVT"),
                              ("ConditionalVTPStress","ConditionalVT")]
    weighting_names=["Equal","Entropy","EntropyDeficit","PCA","PCAFloor","Adaptive"]
    # This family is a view of identical calibrated forecasts, rather than a new fit.
    families["weighting"]=control[weighting_names]
    pairsets["weighting"]=[("Adaptive",name) for name in weighting_names if name!="Adaptive"]
    evt_ports={}
    for window in (252,378,504):
        for q in (.9,.95,.975):
            name=experiment_name(window,q)
            tt=pd.read_csv(out/"evt"/name/"tail.csv",index_col=0,parse_dates=True)
            _,port,_,_=build_indices(returns,sigma,panic,stress,tt,cfg)
            evt_ports[name]=port.Adaptive
    families["evt"]=pd.DataFrame(evt_ports)
    pairsets["evt"]=[(name,"w252_q90") for name in evt_ports if name!="w252_q90"]
    universal_mask=pd.concat([x.notna().all(axis=1).rename(k) for k,x in families.items()],axis=1).all(axis=1)
    pd.DataFrame({"common_signal_available":universal_mask}).to_csv(directory/"universal_date_mask.csv",index_label="Date")
    comparisons=[]; sensitivity=[]; all_predictions={}
    for family,portfolio in families.items():
        LOG.info("Evaluate %s: %d variants",family,len(portfolio.columns))
        portfolio.to_csv(directory/f"{family}_indices.csv",index_label="Date")
        pred,audit=calibrate(portfolio,target,cfg,conditional=conditionals.get(family))
        pred.to_csv(directory/f"{family}_predictions.csv",index=False)
        audit.to_csv(directory/f"{family}_calibration_audit.csv",index=False)
        summary=summarize(pred,cfg.bootstrap,30,cfg.seed)
        summary.to_csv(directory/f"{family}_metrics.csv",index=False)
        compare=paired(pred,pairsets[family],family,cfg.bootstrap,30,cfg.seed)
        compare.to_csv(directory/f"{family}_paired.csv",index=False)
        comparisons.append(compare)
        compare60=paired(pred,pairsets[family],family,cfg.bootstrap,60,cfg.seed,hac_lag=59)
        compare60.to_csv(directory/f"{family}_paired_60.csv",index=False)
        sensitivity.append(compare60)
        all_predictions[family]=pred
        # Ensure common observations within a family, including constant baselines.
        scored=pred.dropna(subset=["actual_vol","forecast_vol"])
        dates=[set(g.Date) for _,g in scored.groupby("variant")]
        if not all(d==dates[0] for d in dates):
            raise AssertionError(f"Unequal evaluation dates in {family}")
        # Uniform cross-family calibration dates, including same historical training dates.
        universal,ua=calibrate(portfolio,target,cfg,mask=universal_mask,conditional=conditionals.get(family))
        universal.to_csv(directory/f"{family}_universal_predictions.csv",index=False)
        ua.to_csv(directory/f"{family}_universal_calibration_audit.csv",index=False)
        # Summaries without CIs here; matched-date CIs are provided in the primary families.
        from .statistics import values
        rows=[]
        for variant,g in universal.groupby("variant"):
            g=g.dropna(subset=["actual_vol","forecast_vol"])
            rows.append(dict(variant=variant,n=len(g),first_date=g.Date.min(),last_date=g.Date.max(),**values(g)))
        pd.DataFrame(rows).to_csv(directory/f"{family}_universal_metrics.csv",index=False)
    global_adjustment(comparisons).to_csv(directory/"all_paired_global_holm.csv",index=False)
    global_adjustment(sensitivity).to_csv(directory/"all_paired_global_holm_60.csv",index=False)
    # Same-day detections are deliberately separated from forecast probabilities.
    detectdir=directory/"detection"; (detectdir/"tables").mkdir(parents=True,exist_ok=True); (detectdir/"data").mkdir(exist_ok=True)
    crisis_detection(control,target,cfg,detectdir)
    main=all_predictions["ablation"]
    scored=main.dropna(subset=["actual_vol","forecast_vol"])
    point=scored[scored.variant.eq("Adaptive")]
    effective=dict(n_forecasts=len(point),overlapping_target_horizon=30,
                   rough_nonoverlapping_windows=len(point)/30,
                   crisis_positive_days=int(point.actual_crisis.sum()),
                   crisis_positive_episodes=int(((point.actual_crisis==1)&(point.actual_crisis.shift(1)!=1)).sum()),
                   caution="These are dependence diagnostics, not an exact inferential sample size")
    (directory/"effective_sample.json").write_text(json.dumps(effective,indent=2))
    # Score and forecast sensitivity relative to the 252/.90 operative hybrid baseline.
    baseline=families["evt"]["w252_q90"]
    rows=[]
    for name,s in families["evt"].items():
        both=pd.concat([baseline.rename("base"),s.rename("score")],axis=1).dropna()
        both=both.loc[returns.index[cfg.initial_train]:]
        rows.append(dict(experiment=name,n=len(both),score_correlation=both.base.corr(both.score),
                         mean_absolute_score_change=float((both.base-both.score).abs().mean()),
                         max_absolute_score_change=float((both.base-both.score).abs().max())))
    pd.DataFrame(rows).to_csv(directory/"evt_score_sensitivity.csv",index=False)
    LOG.info("All matched-date evaluations finished")
