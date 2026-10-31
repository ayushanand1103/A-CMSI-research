import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
import logging
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from acmsi.core import Config,load_data
from .provenance import prepare,sha256

LOG=logging.getLogger(__name__)


def read_series(path):
    return pd.read_csv(path,index_col=0,parse_dates=True).iloc[:,0]


def main():
    parser=argparse.ArgumentParser(description="A-CMSI robustness audit, resume-safe stage execution")
    parser.add_argument("--stage",choices=["all","hmm","evt","evaluate","report","audit"],default="all")
    parser.add_argument("--redo",action="store_true",help="Recompute selected generated HMM/EVT stages; preserve original snapshot")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]; out=root/"outputs/robustness"
    out.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler(out/f"{args.stage}.log",encoding="utf-8")])
    logging.getLogger("hmmlearn").setLevel(logging.ERROR)
    if not (out/"provenance.json").exists():
        prepare(root,out)
    cfg=Config(); prices,returns,vix=load_data(root)
    if args.redo:
        for directory in (["hmm","evt"] if args.stage=="all" else [args.stage] if args.stage in ("hmm","evt") else []):
            for marker in (out/directory).glob("*/complete.json"):
                marker.unlink()
    # Shared chronological volatility is independent of the number of HMM states.
    sigma=pd.read_csv(out/"original/data/conditional_volatility.csv",index_col=0,parse_dates=True)
    (out/"config.json").write_text(json.dumps(dict(base=asdict(cfg),states=[3,4,5,6],
        evt_windows=[252,378,504],evt_quantiles=[.9,.95,.975],bootstrap_blocks=[30,60],
        bootstrap_draws=1000,forecast_probability_cutoff=.5,primary_minimum_exceedances=20,
        claims="retrospective_robustness_no_test_period_tuning",zenodo_doi="10.5281/zenodo.23682477"),indent=2))
    with threadpool_limits(limits=1):
        if args.stage in ("all","hmm"):
            from .hmm import run_hmm
            for states in (3,4,5,6):
                run_hmm(returns,sigma,vix,cfg,out,states)
        if args.stage in ("all","evt"):
            from .evt import run_grid
            run_grid(returns,cfg,out)
        if args.stage in ("all","evaluate"):
            from .evaluate import evaluate
            evaluate(prices,returns,sigma,cfg,out)
        if args.stage in ("all","audit"):
            from .audit import run_audit
            run_audit(root,out,cfg)
        if args.stage in ("all","report"):
            if not (out/"test_results.json").exists():
                subprocess=__import__("subprocess")
                subprocess.run([sys.executable,"-m","research_audit.test_runner"],cwd=root,check=True)
            from .reports import generate
            generate(root,out,cfg)
    LOG.info("Stage %s finished",args.stage)
