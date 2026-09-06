"""POST /api/validate

Accepts AAS JSON, runs unified pyshacl validation (AAS metamodel SHACL plus
auto-derived ARSO domain shapes), and returns structured issues.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api.models import ValidateRequest, ValidateResponse, ValidationIssue  # noqa: E402
from Validation.Validator.validator import issues_as_response_dicts, run_shacl  # noqa: E402

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_aas(req: ValidateRequest) -> ValidateResponse:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        try:
            conforms, all_issues, _meta, _onto = run_shacl(req.json_text, tmp)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"validation error: {exc}")

        issues = [ValidationIssue(**d) for d in issues_as_response_dicts(all_issues)]

        report_path = tmp / "report.ttl"
        report_ttl_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    return ValidateResponse(conforms=conforms, issues=issues, report_ttl=report_ttl_text)
