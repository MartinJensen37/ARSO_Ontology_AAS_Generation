"""Thin wrapper mirroring generation/AAS_builder.py — points at v2 AASGenerator."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from Generation.config import Config
from Generation.Context_Builder.Parsing.profile_structure import normalize_profile_for_builder
from Generation.Context_Builder.Parsing.text_parsing import extract_outer_json_object


def _check_required_fields(normalized: dict[str, Any]) -> list[str]:
    """Return errors for fields that the builder would otherwise silently patch.

    The builder's _apply_ontology_guidance mutates the profile in-place to
    insert default semantic_id / realizedBy values. This hides missing fields
    from the LLM retry loop and can make non-conforming outputs appear to pass
    SHACL. We surface them here as explicit validation errors instead.
    """
    errors: list[str] = []
    root = next(iter(normalized.values()), {}) if normalized else {}

    for name, data in (root.get("Skills") or {}).items():
        if isinstance(data, dict) and "semantic_id" not in data:
            errors.append(f"Skills.{name}: missing required 'semantic_id'")
        if isinstance(data, dict) and "interface" not in data:
            errors.append(f"Skills.{name}: missing required 'interface' (AID affordance name this skill invokes)")

    for name, data in (root.get("Capabilities") or {}).items():
        if isinstance(data, dict) and "semantic_id" not in data:
            errors.append(f"Capabilities.{name}: missing required 'semantic_id'")
        if isinstance(data, dict) and "realizedBy" not in data:
            errors.append(f"Capabilities.{name}: missing required 'realizedBy'")

    return errors


def profile_document_to_aas_json(document: dict[str, Any], cfg: Config) -> str:
    normalized = normalize_profile_for_builder(document, cfg)

    missing = _check_required_fields(normalized)
    if missing:
        raise ValueError(
            "Profile is missing required fields that the builder would silently patch:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    try:
        from .AAS_generation.core.generate_aas import AASGenerator
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Unable to import v2 AAS generation builder: {exc}") from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "profile.json"
        config_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
        generator = AASGenerator(str(config_path), base_url_override=cfg.base_url)
        aas_dict = generator.generate_system(system_id="unused", config=normalized)

    return json.dumps(aas_dict, indent=2, ensure_ascii=False)


def profile_json_text_to_aas_json(profile_text: str, cfg: Config) -> tuple[str, str]:
    cleaned = extract_outer_json_object(profile_text)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Profile JSON must be an object at top-level.")
    return profile_document_to_aas_json(parsed, cfg), cleaned
