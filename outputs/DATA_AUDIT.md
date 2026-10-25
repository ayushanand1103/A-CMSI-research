# Local data audit

Passed 10 of 10 checks.

| Check | Result | Detail |
|---|---|---|
| Unique ordered dates | PASS | 2015-01-02 through 2025-12-30 |
| Complete positive finite prices | PASS | 2765 rows, 0 missing price cells |
| Weekday observations | PASS | Exchange-holiday completeness is not independently verified |
| No gaps longer than seven calendar days | PASS | Maximum gap: 4 calendar days |
| Merged and clean prices agree | PASS | Compared dates, columns and price values |
| Return alignment | PASS | 2764 return rows |
| Legacy returns agree within 1e-7 decimal-return tolerance | PASS | Maximum absolute differences: {'AAPL': 4.524737650211258e-08, 'MSFT': 3.8852182626397945e-08, 'SPY': 4.499528069367109e-08}; values are not exactly identical; pipeline recomputes returns from prices |
| VIX complete after first available date | PASS | Starts 2016-01-04; 251 earlier return rows have no saved VIX |
| Output dates match returns | PASS | One output row per return date; warmup may be missing |
| Complete operational index coverage | PASS | 2008 rows from 2018-01-04 through 2025-12-30 |

Large daily moves are retained as possible market events; they are listed in `tables/largest_daily_moves.csv` for inspection.
Missing values before each component's first valid date reflect rolling-window/model warmup. The operational period is checked separately.

These checks establish internal consistency of the saved files. They do not independently verify Yahoo observations, corporate-action adjustments, or all exchange holidays.
The dataset ends in December 2025 and contains no 2026 market observations.
