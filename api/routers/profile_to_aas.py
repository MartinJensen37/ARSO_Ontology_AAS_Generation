"""POST /api/profile-to-aas

Builds a full AAS JSON from a "profile" document (the same intermediate shape
Transformation/AAS_Builder/AAS_builder.py::profile_document_to_aas_json takes)
and validates the result in one round trip. This is the single canonical path
for turning a profile into AAS JSON -- used by the LLM generation pipeline
(via profile_document_to_aas_json directly, in-process) and now by the UI
canvas (via this endpoint), so both stay on exactly the same builder code.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Generation.config import Config, load_config  # noqa: E402
from api.models import ValidationIssue  # noqa: E402
from Validation.Validator.validator import issues_as_response_dicts, run_shacl  # noqa: E402
from Transformation.AAS_Builder.AAS_builder import profile_document_to_aas_json  # noqa: E402

router = APIRouter()


class ProfileToAasRequest(BaseModel):
    asset_name: str = "UnknownAsset"
    base_url: str = "https://smartproductionlab.aau.dk"
    selected_submodels: list[str] = []
    profile: dict[str, Any]


class ProfileToAasResponse(BaseModel):
    aas_json: str
    conforms: bool
    issues: list[ValidationIssue]
    report_ttl: str


def _throwaway_config(base_cfg: Config, req: ProfileToAasRequest) -> Config:
    """A Config carrying only what profile_document_to_aas_json/run_shacl need
    (paths, selected submodels, base_url) -- no LLM call happens on this path,
    so provider/api_key/models are unused placeholders."""
    return Config(
        provider=base_cfg.provider,
        api_key="",
        asset_name=req.asset_name,
        base_url=req.base_url,
        pdf_path=None,
        submodels=req.selected_submodels,
        generation_mode="json-description",
        profile_example_path=None,
        use_rag=False,
        use_example=False,
        force_full_aas_output=False,
        max_pdf_chars=None,
        max_attempts=1,
        models=[],
        provider_models=base_cfg.provider_models,
        provider_api_keys=base_cfg.provider_api_keys,
        gen_dir=base_cfg.gen_dir,
        root_dir=base_cfg.root_dir,
        context_dir=base_cfg.context_dir,
        rag_dir=base_cfg.rag_dir,
        output_json=base_cfg.output_json,
        output_issues=base_cfg.output_issues,
        shacl_shapes=base_cfg.shacl_shapes,
        ontology_paths=base_cfg.ontology_paths,
    )


@router.post("/profile-to-aas", response_model=ProfileToAasResponse)
async def profile_to_aas(req: ProfileToAasRequest) -> ProfileToAasResponse:
    base_cfg = load_config()
    cfg = _throwaway_config(base_cfg, req)

    try:
        aas_json = profile_document_to_aas_json(req.profile, cfg)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"profile-to-AAS build failed: {exc}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        try:
            conforms, all_issues, _meta, _onto = run_shacl(aas_json, tmp)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"validation error: {exc}")

        issues = [ValidationIssue(**d) for d in issues_as_response_dicts(all_issues)]

        report_path = tmp / "report.ttl"
        report_ttl_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    return ProfileToAasResponse(aas_json=aas_json, conforms=conforms, issues=issues, report_ttl=report_ttl_text)
