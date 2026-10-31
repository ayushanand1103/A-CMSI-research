"""Reproduction checks, artifact integrity and a timestamp-by-timestamp audit."""
from pathlib import Path
from datetime import datetime,timezone
import json
import numpy as np
import pandas as pd
from .provenance import sha256


def compare_numeric(original,reproduction,name):
    a=pd.read_csv(original/name); b=pd.read_csv(reproduction/name)
    same_shape=a.shape==b.shape and list(a)==list(b)
    rows=[]
    if not same_shape:
        return [dict(artifact=name,check="shape_columns",passed=False,detail=f"{a.shape} vs {b.shape}")]
    for c in a:
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            aa,bb=a[c].to_numpy(dtype=float),b[c].to_numpy(dtype=float)
            mask=np.isfinite(aa)&np.isfinite(bb)
            error=float(np.max(np.abs(aa[mask]-bb[mask]))) if mask.any() else 0.
            passed=bool(np.array_equal(np.isnan(aa),np.isnan(bb)) and np.allclose(aa,bb,rtol=1e-8,atol=1e-10,equal_nan=True))
            rows.append(dict(artifact=name,check=c,passed=passed,max_absolute_error=error))
        else:
            rows.append(dict(artifact=name,check=c,passed=bool(a[c].fillna("").equals(b[c].fillna("")))))
    return rows


def run_audit(root,out,cfg):
    original,reproduction=out/"original",out/"reproduction"
    required=["tables/main_ablation_metrics.csv","tables/main_walk_forward_predictions.csv",
              "tables/hmm_state_comparison.csv","data/acmsi_portfolio.csv",
              "data/conditional_volatility.csv","data/panic_probability.csv","data/tail_ES99.csv"]
    results=[]
    for name in required:
        results+=compare_numeric(original,reproduction,name)
    pd.DataFrame(results).to_csv(out/"reproduction_comparison.csv",index=False)
    # Independent HMM loop must agree with the fresh five-state original implementation.
    hh=pd.read_csv(out/"hmm/states_5/panic.csv",index_col=0)
    pp=pd.read_csv(reproduction/"data/panic_probability.csv",index_col=0)
    hmm_error=float(np.nanmax(np.abs(hh.iloc[:,0].to_numpy()-pp.iloc[:,0].to_numpy())))
    checks=[dict(check="fresh reproduction",passed=all(r["passed"] for r in results)),
            dict(check="independent five-state HMM reproduction",passed=bool(np.allclose(hh.iloc[:,0],pp.iloc[:,0],atol=1e-8,rtol=1e-7,equal_nan=True)),max_absolute_error=hmm_error)]
    # New calibrator reproduces original predictions when given original inputs/mask.
    from .calibration import calibrate
    p=pd.read_csv(reproduction/"data/acmsi_portfolio.csv",index_col=0,parse_dates=True)
    target=pd.read_csv(reproduction/"data/validation_targets.csv",index_col=0,parse_dates=True)
    new,audit=calibrate(p,target,cfg)
    old=pd.read_csv(reproduction/"tables/main_walk_forward_predictions.csv",parse_dates=["Date"])
    aa=new[new.variant.isin(p)].set_index(["Date","variant"]).sort_index()
    bb=old[old.variant.isin(p)].set_index(["Date","variant"]).sort_index()
    error=float(np.nanmax(np.abs(aa.forecast_vol-bb.forecast_vol)))
    checks.append(dict(check="independent calibration reproduction",passed=bool(aa.index.equals(bb.index) and np.allclose(aa.forecast_vol,bb.forecast_vol,rtol=1e-9,atol=1e-10,equal_nan=True)),max_absolute_error=error))
    for path in (out/"evaluation").glob("*calibration_audit.csv"):
        audit=pd.read_csv(path)
        good=bool((pd.to_datetime(audit.latest_target_end)<pd.to_datetime(audit.test_start)).all())
        checks.append(dict(check=f"mature label boundary: {path.name}",passed=good))
    for k in (3,4,5,6):
        folder=out/"hmm"/f"states_{k}"
        models=pd.read_csv(folder/"models.csv")
        probability=pd.read_csv(folder/"posteriors.csv",index_col=0).dropna()
        checks.append(dict(check=f"HMM {k} training boundary and simplex",passed=bool(
            (pd.to_datetime(models.train_end)<pd.to_datetime(models.test_start)).all()
            and np.allclose(probability.sum(axis=1),1,atol=1e-12)
            and (probability>=0).all().all())))
    weight_records=[]
    for asset in ("AAPL","MSFT","SPY"):
        w=pd.read_csv(original/"data"/f"weights_{asset}.csv",header=[0,1],index_col=0)
        for kind in ("adaptive","entropy","pca","adaptive4"):
            complete=w[kind].dropna()
            weight_records.append(dict(asset=asset,kind=kind,minimum=float(complete.min().min()),
                nonnegative=bool((complete>=0).all().all()),max_sum_error=float((complete.sum(axis=1)-1).abs().max()),
                below_005_cells=int((complete<.05-1e-12).sum().sum()),
                constraint="base entropy and original PCA do not impose a floor; corrected variants are separate"))
    pd.DataFrame(weight_records).to_csv(out/"original_weight_audit.csv",index=False)
    pd.DataFrame(checks).to_csv(out/"integrity_checks.csv",index=False)
    provenance=json.loads((out/"provenance.json").read_text())
    unchanged=all(sha256(root/name)==digest for name,digest in provenance["dataset_sha256"].items())
    original_source_items=[(name,digest) for name,digest in provenance["source_sha256"].items() if Path(name).parts[0]=="acmsi"]
    unchanged_original_source=bool(original_source_items) and all(sha256(root/name)==digest for name,digest in original_source_items)
    (out/"audit_status.json").write_text(json.dumps(dict(executed_utc=datetime.now(timezone.utc).isoformat(),
        input_data_unchanged=unchanged,original_pipeline_unchanged=unchanged_original_source,
        checks_passed=all(c["passed"] for c in checks),hmm_probability_error=hmm_error),indent=2))
    if not unchanged or not unchanged_original_source or not all(c["passed"] for c in checks):
        raise RuntimeError("Audit checks failed; see integrity_checks.csv and reproduction_comparison.csv")
