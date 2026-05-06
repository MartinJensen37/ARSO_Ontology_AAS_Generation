from __future__ import annotations

from pydantic import BaseModel


class ValidateRequest(BaseModel):
    json_text: str


class ValidationIssue(BaseModel):
    severity: str
    message: str
    field: str = ""
    focus_node: str | None = None
    result_path: str | None = None


class ValidateResponse(BaseModel):
    conforms: bool
    issues: list[ValidationIssue]
    report_ttl: str
