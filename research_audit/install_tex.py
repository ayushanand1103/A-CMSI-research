"""Fetch the pinned portable Tectonic release into this workspace only."""
from pathlib import Path
import hashlib
import json
import zipfile
import requests

root=Path(__file__).resolve().parents[1]
out=root/"outputs/robustness/toolchain"; out.mkdir(parents=True,exist_ok=True)
version="0.17.0"
url=f"https://api.github.com/repos/tectonic-typesetting/tectonic/releases/tags/tectonic@{version}"
response=requests.get(url,timeout=60); response.raise_for_status()
release=response.json()
asset=next(a for a in release["assets"] if "x86_64-pc-windows-msvc" in a["name"] and a["name"].endswith(".zip"))
response=requests.get(asset["browser_download_url"],timeout=120); response.raise_for_status()
archive=out/asset["name"]; archive.write_bytes(response.content)
digest=hashlib.sha256(response.content).hexdigest()
expected=asset.get("digest")
if expected and expected!="sha256:"+digest:
    raise ValueError("Release asset digest mismatch")
with zipfile.ZipFile(archive) as z:
    member=next(n for n in z.namelist() if n.endswith("tectonic.exe"))
    (out/"tectonic.exe").write_bytes(z.read(member))
(out/"tectonic_release.json").write_text(json.dumps(dict(version=version,url=asset["browser_download_url"],sha256=digest,github_digest=expected),indent=2))
print("Installed portable Tectonic",version,"SHA256",digest)
