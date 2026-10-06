"""Run the SHACL regression suite through the validator.

The valid example has to conform: with closed shapes a mistake in the shapes
makes everything fail, and a suite of invalid fixtures alone cannot tell.

Every invalid_*.aas.json fixture in Testing/SHACL_Tests/Test_Cases/ is
deliberately broken against one shape, so all are expected to fail, and to fail
for that reason: the text recorded for it in _EXPECTED has to occur in the
source shape, the path or the message of one of its issues.

Exits nonzero if a valid file does not conform, a fixture unexpectedly conforms
or a fixture fails without its recorded reason.

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

_VALID = [
    _REPO_ROOT / "Generation" / "Context_Builder" / "context" / "valid-example.json",
]

# Fixture -> the shape or class its break is reported against.
_EXPECTED: dict[str, str] = {
    "invalid_address_missing_city": "AddressCityTownMLP",
    "invalid_aid_empty_interface": "InterfaceSMC",
    "invalid_aimc_unknown_aid_property": "AIMCSourceRefTargetShape",
    "invalid_capabilities_missing_capability_element": "CapabilityElement",
    "invalid_capability_realizedby_unknown_skill": "RealizedByRefTargetShape",
    "invalid_entry_node_empty_statements": "HierarchicalStructuresEntryNodeNonEmptyShape",
    "invalid_missing_hierarchical_structures": "hasHierarchicalStructuresSubmodel",
    "invalid_missing_nameplate": "hasDigitalNameplateSubmodel",
    "invalid_nameplate_missing_address": "AddressInformationSMC",
    "invalid_nameplate_missing_mandatory_elements": "ManufacturerNameMLP",
    "invalid_operational_data_unknown_aid_property": "OperationalDataInterfaceRefTargetShape",
    "invalid_parameter_unknown_aid_property": "ParameterInterfaceRefTargetShape",
    "invalid_skills_without_aid": "SkillsImplyAidShape",
}


def _validate(path: Path) -> tuple[bool, list[dict]]:
    json_text = path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        conforms, all_issues, _metamodel, _ontology = run_shacl(json_text, Path(tmp))
    return conforms, all_issues


def _names(issue: dict, text: str) -> bool:
    return any(text in issue.get(key, "") for key in ("source_shape", "result_path", "message"))


def main() -> int:
    cases = sorted(_CASES_DIR.glob("*.aas.json"))
    if not cases:
        print(f"No test cases found in {_CASES_DIR}")
        return 1

    unexpected_fail = []
    for valid in _VALID:
        conforms, all_issues = _validate(valid)
        status = "conforms" if conforms else "VIOLATIONS"
        print(f"{valid.name}: {status} ({len(all_issues)} issue(s))")
        if not conforms:
            unexpected_fail.append(valid.name)
            for issue in all_issues[:10]:
                print(f"    {issue.get('message', '')}")

    unexpected_pass = []
    wrong_reason = []
    for case in cases:
        conforms, all_issues = _validate(case)
        status = "CONFORMS" if conforms else "violations"
        print(f"{case.name}: {status} ({len(all_issues)} issue(s))")
        if conforms:
            unexpected_pass.append(case.name)
            continue
        expected = _EXPECTED.get(case.name.removesuffix(".aas.json"))
        if expected and not any(_names(issue, expected) for issue in all_issues):
            wrong_reason.append(f"{case.name} (no issue names {expected})")

    print()
    if unexpected_fail:
        print(f"FAIL: {len(unexpected_fail)} valid file(s) do not conform: {', '.join(unexpected_fail)}")
    if unexpected_pass:
        print(f"FAIL: {len(unexpected_pass)} fixture(s) unexpectedly conform: {', '.join(unexpected_pass)}")
    if wrong_reason:
        print(f"FAIL: {len(wrong_reason)} fixture(s) fail for another reason: {', '.join(wrong_reason)}")
    if unexpected_fail or unexpected_pass or wrong_reason:
        return 1
    print(f"OK: {len(_VALID)} valid file(s) conform and all {len(cases)} fixtures fail validation as intended.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
