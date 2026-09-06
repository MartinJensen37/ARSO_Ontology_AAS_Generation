"""Validate an AAS JSON file against the combined ARSO SHACL shapes.

Usage:
    python Testing/SHACL_Tests/Test_Scripts/validate_aas.py <path-to-aas.json>

Thin CLI wrapper around Validation.Validator.validator.run_shacl -- the same
function the API's /api/validate endpoint and the generation pipeline's
retry loop use, so this always checks against the current shapes/ontology,
never a separately-maintained copy.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Validation.Validator.validator import run_shacl


def validate(aas_json_path: Path) -> bool:
    json_text = aas_json_path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        conforms, all_issues, _metamodel_issues, _ontology_issues = run_shacl(json_text, Path(tmp))

    print(f"\nConforms: {conforms}")
    if not conforms:
        print(f"{len(all_issues)} issue(s):\n")
        for issue in all_issues:
            print(f"  [{issue.get('severity', '?')}] {issue.get('message', '')}")
    return conforms


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Testing/SHACL_Tests/Test_Scripts/validate_aas.py <path-to-aas.json>")
        sys.exit(1)
    ok = validate(Path(sys.argv[1]))
    sys.exit(0 if ok else 1)
