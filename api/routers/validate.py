"""POST /api/validate

Accepts AAS JSON, runs unified pyshacl validation (AAS metamodel SHACL plus
auto-derived ARSO domain shapes), and returns structured issues.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api.models import ValidateRequest, ValidateResponse, ValidationIssue  # noqa: E402
from Validation.Validator.validator import run_shacl  # noqa: E402

router = APIRouter()


_MESSAGE_TO_FIELD: list[tuple[re.Pattern, str]] = [
    (re.compile(r"DigitalNameplate submodel is mandatory", re.I), "DigitalNameplate"),
    (re.compile(r"HierarchicalStructures.*submodel is mandatory", re.I), "HierarchicalStructures"),
    (re.compile(r"AID submodel must be present", re.I), "AID"),
    (re.compile(r"SoftwareInterface must be present", re.I), "AID"),
    (re.compile(r"ResourceInterface must be mapped", re.I), "AID.InterfaceMQTT"),
    (re.compile(r"SkillInterface.*must use.*ResourceInterface", re.I), "Skills"),
    (re.compile(r"exactly one SkillInterface", re.I), "Skills"),
    (re.compile(r"Skills submodel.*Capabilities submodel", re.I), "Capabilities"),
    (re.compile(r"Capabilities submodel.*Skills submodel", re.I), "Skills"),
    (re.compile(r"provides Skills.*must provide.*Capabilit", re.I), "Capabilities"),
    (re.compile(r"provides Capabilit.*must provide.*Skill", re.I), "Skills"),
    (re.compile(r"Capabilit.*isRealizedBySkill", re.I), "Capabilities"),
    (re.compile(r"serialNumber.*manufacturerName", re.I), "DigitalNameplate"),
    (re.compile(r"HierarchicalStructures.*Name is required", re.I), "HierarchicalStructures.Name"),
    (re.compile(r"BoM entity.*globalAssetId", re.I), "HierarchicalStructures"),
    (re.compile(r"Archetype.*no entity entries", re.I), "HierarchicalStructures"),
    (re.compile(r"sourceSemanticId.*capabilit", re.I), "Capabilities"),
    (re.compile(r"sourceSemanticId.*skill", re.I), "Skills"),
    (re.compile(r"yearOfConstruction", re.I), "DigitalNameplate.YearOfConstruction"),
    (re.compile(r"dateOfManufacture", re.I), "DigitalNameplate.DateOfManufacture"),
    (re.compile(r"serialNumber", re.I), "DigitalNameplate.SerialNumber"),
    (re.compile(r"manufacturerName", re.I), "DigitalNameplate.ManufacturerName"),
    (re.compile(r"ManufacturerName", re.I), "DigitalNameplate.ManufacturerName"),
    (re.compile(r"ContactInformation", re.I), "DigitalNameplate"),
    (re.compile(r"OrderCodeOfManufacturer", re.I), "DigitalNameplate"),
]


def _map_message_to_field(message: str) -> str:
    for pattern, field in _MESSAGE_TO_FIELD:
        if pattern.search(message):
            return field
    return ""


@router.post("/validate", response_model=ValidateResponse)
async def validate_aas(req: ValidateRequest) -> ValidateResponse:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        try:
            conforms, all_issues, _meta, _onto = run_shacl(req.json_text, tmp)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"validation error: {exc}")

        issues: list[ValidationIssue] = []
        seen: set[str] = set()
        for issue in all_issues:
            message = issue.get("message", "No message")
            if message in seen:
                continue
            seen.add(message)
            issues.append(ValidationIssue(
                severity=issue.get("severity", "Violation"),
                message=message,
                field=_map_message_to_field(message),
                focus_node=issue.get("focus_node") or None,
                result_path=None,
            ))

        report_path = tmp / "report.ttl"
        report_ttl_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    return ValidateResponse(conforms=conforms, issues=issues, report_ttl=report_ttl_text)
