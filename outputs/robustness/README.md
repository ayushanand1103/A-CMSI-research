# A-CMSI robustness revision

Original research DOI: **10.5281/zenodo.23682477**. No upload or new DOI registration is performed.

## Commands

From the repository root:

```powershell
python -m venv .venv-robustness-clean
.venv-robustness-clean/Scripts/python -m pip install -r outputs/robustness/requirements.lock.txt
.venv-robustness-clean/Scripts/python -m unittest discover -s tests -v
.venv-robustness-clean/Scripts/python run_acmsi.py --refresh --output outputs/robustness/reproduction
.venv-robustness-clean/Scripts/python run_robustness.py --stage all
```

The executed local `.venv-robustness` environment reuses recorded installed project dependencies and system fallback packages. It is not described as fully isolated. The lock records exact packages and required dependencies for clean installation. Entry points prefer `.deps` when present; omit that directory in a fresh clone to test clean environment resolution. Python 3.11 was used.

Individual stages:

A fully isolated `.venv-reproduction` was also installed from the lock. `python research_audit/clean_environment_check.py` tested copied sources without `.deps` or global packages: all 17 tests passed and calibrated forecasts matched exactly. See `clean_environment_status.json`. This is documented separately from the full fresh-fit reproduction in the project environment.

```powershell
.venv-robustness/Scripts/python run_robustness.py --stage hmm
.venv-robustness/Scripts/python run_robustness.py --stage evt
.venv-robustness/Scripts/python run_robustness.py --stage evaluate
.venv-robustness/Scripts/python run_robustness.py --stage audit
.venv-robustness/Scripts/python run_robustness.py --stage report
```

Completed HMM/EVT configurations have resume markers. The runner uses the fixed `outputs/robustness/` destination. For a wholly independent repeat, use a fresh workspace and preserve the original snapshot as `original/`. HMM experiments share the archived chronological volatility path, verified against fresh estimation; volatility is independent of HMM state count.

## Artifacts

Resume signatures check source, inputs and configuration. Add `--redo` to recompute a generated HMM/EVT stage after changes; the original snapshot stays intact. Persist test logs using `.venv-robustness/Scripts/python -m research_audit.test_runner`. The report stage creates them if absent.

- `original/`: archived original outputs/source, excluding disposable caches/models.
- `reproduction/`: fresh original-pipeline estimates and results.
- `hmm/states_*/`: all starts, state occupancy/ESS, transitions/durations, redundancy, refit stability, train/test likelihoods and forward probabilities.
- `evt/w*_q*/`: nine rolling tail specifications, raw parameters, missing/unstable estimates and fallback flags.
- `evaluation/`: scores, forecasts, family/universal matched-date metrics, confidence intervals, paired effects, Holm corrections, 60-day dependence sensitivity and calibration audits.
- `figures/`: report graphics.
- `manuscript/`: LaTeX, tables, bibliography, relative graphics and PDF.
- `provenance.json`, `config.json`, `requirements.lock.txt`: source/input hashes, dates, versions, seeds and settings.

The five requested audit reports explain findings and limits. Family comparisons use common calibration and scoring observations; universal comparisons additionally match across families. Different sample periods must not be ranked directly. Historical evaluation dates have already been inspected, so this is a retrospective robustness study, not an untouched confirmatory holdout.

## PDF and source package

After compilation, run `.venv-robustness/Scripts/python -m research_audit.package` from the repository root to validate the PDF and assemble the ZIP. Its `pypdf` dependency and the preview renderer are recorded in the lock.

Portable Tectonic 0.17.0 and its release SHA-256 are recorded in `toolchain/`. From `manuscript/`, compile with:

```powershell
../toolchain/tectonic.exe --keep-logs --keep-intermediates main.tex
```

The first build needs standard TeX resources. A normal LaTeX/BibTeX toolchain also supports the source. `manuscript/BUILD_STATUS.json` records the actual build checks. The submission ZIP contains source, bibliography, generated `.bbl`, tables and graphics. Author confirmation of affiliation, declarations, licensing and arXiv category/endorsement requirements remains necessary.
