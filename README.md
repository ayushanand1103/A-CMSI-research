# A-CMSI research

Adaptive Composite Market Stress Index for AAPL, MSFT and SPY, using the repository's 2015–2025 adjusted-price data.

Display the single latest saved portfolio score with `python show_score.py`. This displays the Adaptive V/P/T index and its data date; it does not fetch live market prices. The main pipeline also prints this score when a run completes.

## Run

Use Python 3.11 or newer from this directory:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python run_acmsi.py
```

This workspace also supports `python run_acmsi.py` using the project-local `.deps` packages installed during implementation. `.deps` is ignored by Git. No global environment was modified by that installation.

The main run needs no network access. It rebuilds dated returns, refits ARIMA/variance/HMM models chronologically, fits rolling EVT tails, constructs the index and baselines, evaluates forecasts, creates wavelet and event figures, and writes a results report and manuscript draft. An exact source/data/config fingerprint caches expensive component estimation. `--refresh` forces re-estimation. A run takes several minutes on a typical CPU.

```powershell
python run_acmsi.py --download-external
python run_acmsi.py --external-only
python run_acmsi.py --report-only
python -m unittest discover -s tests -v
```

External downloads are optional; they retrieve STLFSI4 and KCFSI from FRED. The external comparison is explicitly based on revised data with assumed publication lags, rather than a point-in-time backtest. KCFSI is monthly; STLFSI4 is weekly.

For exact R Bai-Perron break estimates and rugarch Nyblom/sign-bias diagnostics, run this optional supplement after the main pipeline:

```powershell
Rscript Analysis/supplementary_diagnostics.R
```

It requires `strucchange`, `rugarch`, and `zoo`. Run from the repository root or set `ACMSI_ROOT`. Full-sample supplementary R fits are descriptive and do not feed the held-out forecasts.

## Outputs

| Location | Contents |
|---|---|
| `outputs/RESULTS.md` | Actual metrics and interpretation |
| `outputs/data/acmsi_portfolio.csv` | Eight index variants, daily |
| `outputs/data/acmsi_AAPL.csv` etc. | Asset-level indices |
| `outputs/data/components_*.csv` | Normalized V, P, T, C |
| `outputs/data/weights_*.csv` | Adaptive, entropy, PCA, four-component weights |
| `outputs/data/tail_ES99.csv` | Raw rolling tail expected shortfall |
| `outputs/data/filtered_posteriors.csv` | Forward-filtered risk-ranked state probabilities |
| `outputs/tables/` | Ablations, significance, warnings, sensitivity, model diagnostics and refit audit |
| `outputs/figures/` | Index, weights, EVT, wavelet, EDA and crisis figures |
| `outputs/models/` | Latest model objects and scalers; only unpickle your own trusted files |
| `outputs/run_manifest.json` | Parameters, dates, package versions and fingerprint |
| `outputs/manuscript.md` | Generated methods/results manuscript draft |

Signals are available **after close**. The first model-training reconstruction is warmup, not held-out evidence. Scored dates, target definitions and comparison limitations are recorded in the report and [methodology](METHODOLOGY.md).

## Repository layout

- `acmsi/`: canonical reproducible implementation, including the continuation beyond Phase 7.
- `Analysis/Phase 1`–`Phase 7`: original exploratory R scripts and notebooks, preserved. Many contain historical absolute paths and full-sample modeling; use the new runner for the reproducible analysis.
- `Data/`: original inputs and historical exports, preserved.
- `Reports/`: original phase documents, preserved.
- `tests/`: numerical and temporal-integrity tests.

The original five-state `P_component.csv` remains untouched. The new pipeline recomputes operational HMM probabilities instead of using smoothed historical notebook outputs. The core index has V/P/T; `Adaptive4` separately evaluates the proposed correlation addition. No preprint upload or journal submission is performed by this project.
