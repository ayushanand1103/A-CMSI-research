"""Prevent resume markers from silently reusing changed experiments."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import pandas as pd


def signature(cfg,frames,source):
    h=hashlib.sha256(json.dumps(asdict(cfg),sort_keys=True).encode())
    for frame in frames:
        h.update(pd.util.hash_pandas_object(frame,index=True).values.tobytes())
    for path in (Path(source),Path(__file__).resolve().parents[1]/"acmsi/core.py"):
        h.update(path.read_bytes())
    return h.hexdigest()
