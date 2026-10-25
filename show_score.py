"""Display the latest saved portfolio A-CMSI score."""
import csv
from pathlib import Path


def main():
    path = Path(__file__).resolve().parent / "outputs/data/acmsi_portfolio.csv"
    if not path.exists():
        raise SystemExit("No index output found. Run python run_acmsi.py first.")
    latest = None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("Adaptive", "").strip():
                latest = row
    if latest is None:
        raise SystemExit("No calculated Adaptive score is available in the output.")
    score = float(latest["Adaptive"])
    print("\nA-CMSI | Latest saved portfolio score")
    print("=" * 42)
    print(f"Score:          {score:+.4f}")
    print(f"Data date:      {latest['Date']} (after close)")
    print("Specification:  Adaptive V/P/T portfolio")
    print("Scale:          Normalized index; not a percentage")
    print("Data mode:      Saved historical data; no live feed")
    print()


if __name__ == "__main__":
    main()
