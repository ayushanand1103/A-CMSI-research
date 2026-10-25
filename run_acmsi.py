"""Project-local entry point. Run python run_acmsi.py --help."""
from pathlib import Path
import sys

local_deps = Path(__file__).resolve().parent / ".deps"
if local_deps.exists():
    sys.path.insert(0, str(local_deps))

from acmsi.pipeline import main

if __name__ == "__main__":
    main()
