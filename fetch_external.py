"""Download the two optional public FRED benchmarks without rerunning models."""
from pathlib import Path
import requests

directory=Path(__file__).resolve().parent/"outputs/external"
directory.mkdir(parents=True,exist_ok=True)
for identifier in ("STLFSI4","KCFSI"):
    response=requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                          params={"id":identifier},timeout=60)
    response.raise_for_status()
    if identifier not in response.text.splitlines()[0]:
        raise ValueError(f"Unexpected response for {identifier}")
    (directory/(identifier+".csv")).write_text(response.text,encoding="utf-8")
    print("Downloaded",identifier)
