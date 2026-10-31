import argparse
from dataclasses import asdict, replace
import importlib.metadata
import json
import logging
from pathlib import Path
import pickle
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .core import Config, ASSETS, load_data, build_indices, fingerprint, features
from .models import chronological_models
from .evt import tail_analysis
from .analysis import diagnostic_analysis, wavelets, index_figures, external_comparison, validation_figures
from .validation import targets, walk_forward, crisis_detection, early_warning

LOG=logging.getLogger(__name__)


def save_frame(frame, path):
    frame.to_csv(path, index_label="Date")


def execute(root, output, cfg, refresh=False, download_external=False):
    for directory in ("tables","figures","data","cache","models"):
        (output/directory).mkdir(parents=True,exist_ok=True)
    prices,returns,vix=load_data(root)
    LOG.info("Loaded %d prices and %d returns (%s to %s)",len(prices),len(returns),returns.index[0],returns.index[-1])
    key=fingerprint(root,cfg)
    component_key=fingerprint(root,cfg,components_only=True)
    cache=output/"cache"/(component_key+".pkl")
    if cache.exists() and not refresh:
        LOG.info("Loading matching component-source/data/config cache %s",component_key)
        with cache.open("rb") as handle:
            sigma,residuals,panic,stress,posteriors,tail=pickle.load(handle)
    else:
        sigma,residuals,panic,stress,posteriors=chronological_models(returns,vix,cfg,output)
        tail=tail_analysis(returns,cfg,output)
        with cache.open("wb") as handle:
            pickle.dump((sigma,residuals,panic,stress,posteriors,tail),handle)
    for name,frame in (("conditional_volatility",sigma),("mean_residuals",residuals),
                       ("panic_probability",panic),("regime_stress",stress),
                       ("filtered_posteriors",posteriors),("tail_ES99",tail)):
        save_frame(frame,output/"data"/(name+".csv"))
    asset_indices,portfolio,weights,components=build_indices(returns,sigma,panic,stress,tail,cfg)
    save_frame(portfolio,output/"data/acmsi_portfolio.csv")
    for asset in ASSETS:
        save_frame(asset_indices[asset],output/"data"/f"acmsi_{asset}.csv")
        save_frame(weights[asset],output/"data"/f"weights_{asset}.csv")
        save_frame(components[asset],output/"data"/f"components_{asset}.csv")
    target=targets(returns,prices,posteriors,cfg.horizon)
    save_frame(target,output/"data/validation_targets.csv")
    LOG.info("Calibrating walk-forward forecasts and comparing ablations")
    prediction,metric=walk_forward(portfolio,target,cfg,output)
    crisis_detection(portfolio,target,cfg,output)
    early_warning(portfolio,returns,cfg,output)
    sensitivity=[]
    for window in (21,63,126):
        _,p,_,_=build_indices(returns,sigma,panic,stress,tail,cfg,window)
        _,m=walk_forward(p,target,cfg,output,name=f"entropy_{window}")
        row=m[m.variant.eq("Adaptive")].iloc[0].to_dict()
        row["entropy_window"]=window
        sensitivity.append(row)
    pd.DataFrame(sensitivity).to_csv(output/"tables/entropy_sensitivity.csv",index=False)
    LOG.info("Producing diagnostics, wavelets and figures")
    diagnostic_analysis(prices,returns,output)
    wavelets(returns,output)
    index_figures(portfolio,weights,components,returns,output)
    validation_figures(portfolio,posteriors,panic,returns,target,prediction,cfg,output)
    external_comparison(portfolio,target,output,download=download_external)
    manifest=dict(config=asdict(cfg),fingerprint=key,component_fingerprint=component_key,python=sys.version,
                  packages={name:importlib.metadata.version(name) for name in
                            ("numpy","pandas","scipy","scikit-learn","statsmodels","arch","hmmlearn","PyWavelets")},
                  price_start=str(prices.index[0].date()),price_end=str(prices.index[-1].date()),
                  n_prices=len(prices),n_returns=len(returns),
                  first_oos_model_date=str(returns.index[cfg.initial_train].date()),
                  first_scored_forecast=str(prediction.Date.min().date()),
                  last_scored_forecast=str(prediction.loc[prediction.actual_vol.notna(),"Date"].max().date()),
                  latest_forecast=str(prediction.Date.max().date()),
                  as_of="after_market_close",validation="monthly_expanding_refits_forward_filtered_HMM",
                  warmup="Rows before first_oos_model_date are training reconstructions; never scored",
                  data_sources=["Existing Yahoo adjusted-close CSVs", "Existing saved VIX observations"],
                  optional_correlation_component="Adaptive4; core remains V/P/T",
                  publication="No external publishing or submission performed")
    (output/"run_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    from .report import write_reports
    write_reports(output,manifest,portfolio,metric)
    latest = portfolio["Adaptive"].dropna()
    LOG.info("LATEST A-CMSI PORTFOLIO SCORE: %+.4f | data date: %s after close | saved historical data, no live feed",
             latest.iloc[-1], latest.index[-1].date())
    LOG.info("Finished. Best held-out volatility RMSE: %s",metric.iloc[0].to_dict())


def main():
    parser=argparse.ArgumentParser(description="Rebuild and validate A-CMSI from the repository data")
    parser.add_argument("--output",type=Path,default=Path("outputs"))
    parser.add_argument("--refresh",action="store_true",help="Ignore exact-match component cache")
    parser.add_argument("--download-external",action="store_true",help="Fetch optional FRED STLFSI4 and KCFSI")
    parser.add_argument("--external-only",action="store_true",help="Download/compare external series using completed output")
    parser.add_argument("--report-only",action="store_true")
    parser.add_argument("--restarts",type=int,default=3)
    parser.add_argument("--hmm-states",type=int,choices=[2,3,4,5,6],default=5)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler(output/"run.log",encoding="utf-8")])
    logging.getLogger("hmmlearn").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore",category=FutureWarning)
    if args.external_only:
        portfolio=pd.read_csv(output/"data/acmsi_portfolio.csv",index_col=0,parse_dates=True)
        target=pd.read_csv(output/"data/validation_targets.csv",index_col=0,parse_dates=True)
        external_comparison(portfolio,target,output,download=True)
        return
    if args.report_only:
        from .report import write_reports
        manifest=json.loads((output/"run_manifest.json").read_text())
        write_reports(output,manifest,pd.read_csv(output/"data/acmsi_portfolio.csv",index_col=0,parse_dates=True),
                      pd.read_csv(output/"tables/main_ablation_metrics.csv"))
        return
    cfg=Config(restarts=args.restarts,hmm_states=args.hmm_states)
    if cfg.restarts<1:
        parser.error("--restarts must be positive")
    with threadpool_limits(limits=1):
        execute(root,output,cfg,args.refresh,args.download_external)
