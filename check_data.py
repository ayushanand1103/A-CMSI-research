"""Audit local inputs and computed index coverage without modifying source data."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / ".deps"))
import json
import numpy as np
import pandas as pd
from acmsi.core import ASSETS, read_dated, load_data


def main():
    root = Path(__file__).resolve().parent
    prices, returns, vix = load_data(root)
    checks = []
    def check(name, passed, detail):
        checks.append(dict(check=name, passed=bool(passed), detail=detail))
    check("Unique ordered dates", not prices.index.has_duplicates and prices.index.is_monotonic_increasing,
          f"{prices.index.min().date()} through {prices.index.max().date()}")
    check("Complete positive finite prices", np.isfinite(prices).all().all() and (prices > 0).all().all(),
          f"{len(prices)} rows, {int(prices.isna().sum().sum())} missing price cells")
    check("Weekday observations", (prices.index.day_of_week < 5).all(), "Exchange-holiday completeness is not independently verified")
    gaps = prices.index.to_series().diff().dt.days
    long_gaps = gaps[gaps > 7]
    check("No gaps longer than seven calendar days", long_gaps.empty,
          f"Maximum gap: {int(gaps.max())} calendar days")
    all_prices = read_dated(root / "Data/all_prices.csv")[list(ASSETS)]
    check("Merged and clean prices agree", prices.equals(all_prices), "Compared dates, columns and price values")
    check("Return alignment", len(returns) == len(prices)-1 and returns.index.equals(prices.index[1:]),
          f"{len(returns)} return rows")
    legacy = read_dated(root / "Data/log_returns.csv")
    errors = {}
    for asset in ASSETS:
        errors[asset] = float((legacy[f"{asset.lower()}_ret"]-returns[asset]).abs().max())
    check("Legacy returns agree within 1e-7 decimal-return tolerance", max(errors.values()) < 1e-7,
          f"Maximum absolute differences: {errors}; values are not exactly identical; pipeline recomputes returns from prices")
    first_vix = vix.first_valid_index()
    check("VIX complete after first available date", vix.loc[first_vix:].notna().all(),
          f"Starts {first_vix.date()}; {int(vix.isna().sum())} earlier return rows have no saved VIX")
    summaries = []
    extremes = []
    for asset in ASSETS:
        r = returns[asset]
        summaries.append(dict(asset=asset, price_min=float(prices[asset].min()), price_max=float(prices[asset].max()),
                              return_mean=float(r.mean()), daily_return_std=float(r.std()),
                              min_log_return=float(r.min()), max_log_return=float(r.max()),
                              unchanged_price_days=int(prices[asset].diff().eq(0).sum())))
        for date in r.abs().nlargest(5).index:
            extremes.append(dict(asset=asset, Date=str(date.date()), log_return=float(r.loc[date]),
                                 simple_return=float(np.expm1(r.loc[date]))))
    out = root / "outputs"
    manifest = json.loads((out / "run_manifest.json").read_text())
    portfolio = pd.read_csv(out / "data/acmsi_portfolio.csv", index_col=0, parse_dates=True)
    operational = portfolio.loc[manifest["first_oos_model_date"]:]
    check("Output dates match returns", portfolio.index.equals(returns.index), "One output row per return date; warmup may be missing")
    check("Complete operational index coverage", np.isfinite(operational.to_numpy()).all(),
          f"{len(operational)} rows from {operational.index[0].date()} through {operational.index[-1].date()}")
    coverage = [dict(variant=name, first_valid=str(portfolio[name].first_valid_index().date()),
                     warmup_or_missing_rows=int(portfolio[name].isna().sum()),
                     missing_operational_rows=int(operational[name].isna().sum())) for name in portfolio]
    pd.DataFrame(checks).to_csv(out / "tables/data_quality_checks.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "tables/data_summary.csv", index=False)
    pd.DataFrame(extremes).to_csv(out / "tables/largest_daily_moves.csv", index=False)
    pd.DataFrame(coverage).to_csv(out / "tables/index_coverage.csv", index=False)
    lines = ["# Local data audit", "", f"Passed {sum(c['passed'] for c in checks)} of {len(checks)} checks.", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {c['check']} | {'PASS' if c['passed'] else 'FAIL'} | {c['detail']} |" for c in checks]
    lines += ["", "Large daily moves are retained as possible market events; they are listed in `tables/largest_daily_moves.csv` for inspection.",
              "Missing values before each component's first valid date reflect rolling-window/model warmup. The operational period is checked separately.",
              "", "These checks establish internal consistency of the saved files. They do not independently verify Yahoo observations, corporate-action adjustments, or all exchange holidays.",
              "The dataset ends in December 2025 and contains no 2026 market observations."]
    (out / "DATA_AUDIT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(f"{'PASS' if c['passed'] else 'FAIL'}: {c['check']} -- {c['detail']}" for c in checks))
    if not all(c["passed"] for c in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
