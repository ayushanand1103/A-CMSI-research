"""Test exact copied sources without project .deps or global package fallback."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
out=root/"outputs/robustness"
workspace=out/"clean_environment_workspace"
workspace.mkdir(exist_ok=True)
for directory in ("acmsi","research_audit","tests"):
    shutil.copytree(root/directory,workspace/directory,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__"))
script=r'''
from pathlib import Path
import sys,unittest,io,json,importlib.metadata as m
workspace=Path(sys.argv[1]); root=Path(sys.argv[2])
sys.path.insert(0,str(workspace))
stream=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(workspace/'tests'))
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
print(stream.getvalue())
import numpy as np,pandas as pd,sklearn,scipy,hmmlearn,arch,statsmodels
packages={name:str(m.distribution(name).locate_file('')) for name in ('numpy','pandas','scipy','scikit-learn','statsmodels','arch','hmmlearn')}
isolated=all('.venv-reproduction' in p and '.deps' not in p for p in packages.values())
from acmsi.core import Config
from research_audit.calibration import calibrate
from threadpoolctl import threadpool_limits
with threadpool_limits(limits=1):
    output=root/'outputs/robustness/reproduction'
    x=pd.read_csv(output/'data/acmsi_portfolio.csv',index_col=0,parse_dates=True)
    y=pd.read_csv(output/'data/validation_targets.csv',index_col=0,parse_dates=True)
    predictions,audit=calibrate(x,y,Config())
    original=pd.read_csv(output/'tables/main_walk_forward_predictions.csv',parse_dates=['Date'])
    a=predictions[predictions.variant.isin(x)].set_index(['Date','variant']).sort_index()
    b=original[original.variant.isin(x)].set_index(['Date','variant']).sort_index()
    delta=float((a.forecast_vol-b.forecast_vol).abs().max())
    reproduction=bool(a.index.equals(b.index) and np.allclose(a.forecast_vol,b.forecast_vol,atol=1e-10,rtol=1e-9))
record=dict(tests_run=result.testsRun,passed=result.wasSuccessful(),packages_from_isolated_venv=isolated,
            package_locations=packages,calibration_reproduced=reproduction,max_forecast_difference=delta,
            no_project_deps_directory=not (workspace/'.deps').exists())
(root/'outputs/robustness/clean_environment_status.json').write_text(json.dumps(record,indent=2))
if not result.wasSuccessful() or not isolated or not reproduction:
    raise SystemExit(1)
print(json.dumps(record,indent=2))
'''
command=[str(root/".venv-reproduction/Scripts/python.exe"),"-I","-c",script,str(workspace),str(root)]
completed=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace")
(out/"clean_environment.log").write_text(completed.stdout+completed.stderr,encoding="utf-8")
print(completed.stdout)
if completed.stderr:
    print(completed.stderr,file=sys.stderr)
raise SystemExit(completed.returncode)
