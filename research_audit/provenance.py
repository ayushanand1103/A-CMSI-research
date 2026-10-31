from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from packaging.requirements import Requirement


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(root, out):
    out.mkdir(parents=True, exist_ok=True)
    original=out/"original"
    if not original.exists():
        shutil.copytree(root/"outputs", original,
                        ignore=shutil.ignore_patterns("robustness","cache","models","__pycache__"))
        for name in ("acmsi","tests"):
            shutil.copytree(root/name, original/"source"/name,ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("METHODOLOGY.md","README.md","requirements.txt"):
            shutil.copy2(root/name,original/"source"/name)
    packages={}
    pending=["numpy","pandas","scipy","scikit-learn","statsmodels","arch","hmmlearn",
             "PyWavelets","matplotlib","requests","threadpoolctl","pypdf","PyMuPDF"]
    while pending:
        name=pending.pop()
        canonical=name.lower().replace("_","-")
        if canonical in packages:
            continue
        distribution=metadata.distribution(name)
        packages[canonical]=distribution.version
        for text in distribution.requires or []:
            requirement=Requirement(text)
            if requirement.marker is None or requirement.marker.evaluate({"extra":""}):
                pending.append(requirement.name)
    (out/"requirements.lock.txt").write_text("\n".join(f"{k}=={v}" for k,v in sorted(packages.items()))+"\n")
    hashes={str(p.relative_to(root)):sha256(p) for p in (root/"Data").rglob("*.csv")}
    sources={str(p.relative_to(root)):sha256(p) for folder in ("acmsi","research_audit","tests")
             for p in (root/folder).rglob("*.py")}
    git=subprocess.run(["git","rev-parse","HEAD"],cwd=root,capture_output=True,text=True)
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,
                  executable=sys.executable,packages=packages,dataset_sha256=hashes,source_sha256=sources,
                  git_revision=git.stdout.strip(),zenodo_doi="10.5281/zenodo.23682477",
                  previous_outputs="original/",reference_candidates={},
                  environment="Dedicated venv with recorded existing project dependencies; lock supports clean installation")
    (out/"provenance.json").write_text(json.dumps(manifest,indent=2))
    return manifest
