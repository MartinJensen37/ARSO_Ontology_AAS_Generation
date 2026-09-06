"""POST /api/aas-to-profile

Parses full AAS JSON back into a profile document -- the exact inverse of
POST /api/profile-to-aas. Response shape mirrors ProfileToAasRequest's
top-level fields so a client can feed this response straight into a
subsequent profile-to-aas call unchanged (symmetric round trip).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Transformation.AAS_Builder.AAS_to_Profile.aas_to_profile import aas_json_to_profile  # noqa: E402

router = APIRouter()


class AasToProfileRequest(BaseModel):
    aas_json_text: str


class AasToProfileResponse(BaseModel):
    asset_name: str
    base_url: str
    selected_submodels: list[str]
    profile: dict[str, Any]


@router.post("/aas-to-profile", response_model=AasToProfileResponse)
async def aas_to_profile(req: AasToProfileRequest) -> AasToProfileResponse:
    try:
        result = aas_json_to_profile(req.aas_json_text)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"AAS JSON parse failed: {exc}")
    return AasToProfileResponse(**result)
