"""Execute the reproducibility and robustness protocol. See --help."""
from pathlib import Path
import sys
deps=Path(__file__).resolve().parent/".deps"
if deps.exists():
    sys.path.insert(0,str(deps))
from research_audit.runner import main
if __name__=="__main__":
    main()
