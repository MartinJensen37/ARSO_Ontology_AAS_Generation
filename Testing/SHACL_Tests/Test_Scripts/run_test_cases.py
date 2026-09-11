"""Run every fixture in Testing/SHACL_Tests/Test_Cases/ through the SHACL validator.

Every invalid_*.aas.json fixture is deliberately broken against one shape, so all
are expected to fail. Exits nonzero if any unexpectedly conforms.

Usage:
    python Testing/SHACL_Tests/Test_Scripts/run_test_cases.py
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
