"""Persist actual unit-test output and a machine-readable outcome."""
from pathlib import Path
import io
import json
import sys
import unittest
from datetime import datetime,timezone

root=Path(__file__).resolve().parents[1]
stream=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(root/"tests"))
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
out=root/"outputs/robustness"
(out/"tests.log").write_text(stream.getvalue(),encoding="utf-8")
(out/"test_results.json").write_text(json.dumps(dict(executed_utc=datetime.now(timezone.utc).isoformat(),
    tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
    passed=result.wasSuccessful()),indent=2))
print(stream.getvalue())
raise SystemExit(0 if result.wasSuccessful() else 1)
