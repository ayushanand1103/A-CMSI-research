"""Integration assertions for the completed research artifacts."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/".deps"))
import json
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parent
out=root/"outputs"
manifest=json.loads((out/"run_manifest.json").read_text())
portfolio=pd.read_csv(out/"data/acmsi_portfolio.csv",index_col=0,parse_dates=True)
assert len(portfolio)==manifest["n_returns"]
assert str(portfolio.index[-1].date())==manifest["price_end"]
assert np.isfinite(portfolio.iloc[-1]).all()
for asset in ("AAPL","MSFT","SPY"):
    weights=pd.read_csv(out/"data"/f"weights_{asset}.csv",header=[0,1],index_col=0)
    for kind in ("adaptive","adaptive4"):
        w=weights[kind].dropna()
        np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-12)
        assert (w>=.05-1e-12).all().all()
    components=pd.read_csv(out/"data"/f"components_{asset}.csv",index_col=0)
    assert (components.abs().dropna()<=3+1e-12).all().all()
posterior=pd.read_csv(out/"data/filtered_posteriors.csv",index_col=0).dropna()
np.testing.assert_allclose(posterior.sum(axis=1),1,atol=1e-12)
audit=pd.read_csv(out/"tables/refit_audit.csv")
assert (pd.to_datetime(audit.train_end)<pd.to_datetime(audit.test_start)).all()
calibration=pd.read_csv(out/"tables/main_calibration_audit.csv")
assert (pd.to_datetime(calibration.latest_target_end)<pd.to_datetime(calibration.test_start)).all()
prediction=pd.read_csv(out/"tables/main_walk_forward_predictions.csv",parse_dates=["Date"])
dates=[set(g.Date) for _,g in prediction.groupby("variant")]
assert all(d==dates[0] for d in dates)
assert prediction.Date.max()==portfolio.index[-1]
latest=prediction[prediction.Date.eq(prediction.Date.max())]
assert latest.actual_vol.isna().all()
assert np.isfinite(latest.forecast_vol).all()
for required in ("R_Bai_Perron_Chow.csv","external_incremental_metrics.csv",
                 "main_significance.csv","entropy_sensitivity.csv","rolling_evt_diagnostics.csv"):
    assert (out/"tables"/required).stat().st_size>0
for required in ("crisis_roc_forecast.png","early_warning_2020-02-27.png",
                 "wavelet_SPY.png","coherence_AAPL_SPY.png","filtered_regime_probabilities.png"):
    if required.startswith("early_warning"):
        assert list((out/"figures").glob("early_warning_*.png"))
    else:
        assert (out/"figures"/required).stat().st_size>0
print(f"PASS: {len(portfolio)} daily rows, {len(audit)} refits, matching forecast dates, causal label boundaries, finite final signals, normalized weights/posteriors, and required artifacts.")
