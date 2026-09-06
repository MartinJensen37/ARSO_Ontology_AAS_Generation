"""Run every fixture in Testing/SHACL_Tests/Test_Cases/ through the SHACL
validator and report conformance + issue counts for each.

Usage:
    python Testing/SHACL_Tests/Test_Scripts/run_test_cases.py

All fixtures here are named invalid_*.aas.json by convention: each is a
deliberately broken AAS exercising one specific SHACL shape, so the expected
result for every one of them is conforms=False. This script's exit code is
nonzero if any fixture unexpectedly conforms (a regression that silently
weakened a shape) -- it does not track exact issue counts run-to-run, since
those can legitimately shift as shapes are added/changed.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Validation.Validator.validator import run_shacl

_CASES_DIR = Path(__file__).resolve().parent.parent / "Test_Cases"


def main() -> int:
    cases = sorted(_CASES_DIR.glob("*.aas.json"))
    if not cases:
        print(f"No test cases found in {_CASES_DIR}")
        return 1

    unexpected_pass = []
    for case in cases:
        json_text = case.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            conforms, all_issues, _metamodel, _ontology = run_shacl(json_text, Path(tmp))
        status = "CONFORMS" if conforms else "violations"
        print(f"{case.name}: {status} ({len(all_issues)} issue(s))")
        if conforms:
            unexpected_pass.append(case.name)

    print()
    if unexpected_pass:
        print(f"FAIL: {len(unexpected_pass)} fixture(s) unexpectedly conform: {', '.join(unexpected_pass)}")
        return 1
    print(f"OK: all {len(cases)} fixtures correctly fail validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
