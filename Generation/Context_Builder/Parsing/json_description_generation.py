from __future__ import annotations

import json
import re
from typing import Any

import yaml

from ...config import Config
from .profile_structure import ensure_requested_submodel_sections, prune_profile_sections
from .text_parsing import extract_outer_json_object, strip_code_fences as _strip_code_fences


def _strip_base_url_prefixes(node: Any, base_url: str) -> Any:
    if isinstance(node, dict):
        return {k: _strip_base_url_prefixes(v, base_url) for k, v in node.items()}
    if isinstance(node, list):
        return [_strip_base_url_prefixes(item, base_url) for item in node]
    if isinstance(node, str):
        prefix = base_url.rstrip("/")
        if prefix and node.startswith(prefix):
            suffix = node[len(prefix):]
            return suffix if suffix.startswith("/") else f"/{suffix}"
    return node


def strip_code_fences(text: str) -> str:
    # Compatibility wrapper; shared implementation lives in text_parsing.py.
    return _strip_code_fences(text)


def _assemble_profile_example_document(cfg: Config) -> dict[str, Any]:
    source_path = cfg.profile_example_path
    if source_path is not None:
        candidate = source_path
        if not candidate.is_absolute():
            candidate = (cfg.root_dir / candidate).resolve()
        if candidate.exists():
            source_text = candidate.read_text(encoding="utf-8")
            try:
                if candidate.suffix.lower() == ".json":
                    parsed = json.loads(source_text)
                else:
                    parsed = yaml.safe_load(source_text)
                if isinstance(parsed, dict):
                    pruned = prune_profile_sections(parsed, cfg)
                    system_name = next(iter(pruned.keys())) if pruned else ""
                    body = pruned.get(system_name)
                    if isinstance(body, dict):
                        ensure_requested_submodel_sections(body, cfg)
                    return _strip_base_url_prefixes(pruned, cfg.base_url)
            except Exception:
                pass

    system_name = f"{cfg.asset_name}AAS"
    root_id = f"/aas/{system_name}"
    global_asset_id = f"/assets/{cfg.asset_name}"

    profile: dict[str, Any] = {
        system_name: {
            "idShort": system_name,
            "id": root_id,
            "globalAssetId": global_asset_id,
            "assetType": "/Resource/[VERIFY: resource type]",
            "serialNumber": "[VERIFY: serial number]",
            "location": "[VERIFY: location]",
        }
    }

    body = profile[system_name]
    ensure_requested_submodel_sections(body, cfg)

    return profile


def _assemble_profile_semantic_guide_document(cfg: Config) -> dict[str, Any]:
    system_name = f"{cfg.asset_name}AAS"
    selected = {name.strip().lower() for name in cfg.submodels}

    guide: dict[str, Any] = {
        system_name: {
            "idShort": {
                "purpose": "Human-readable stable identifier for the AAS shell.",
                "constraints": ["AAS-safe token", "letters/digits/underscore only"],
                "source_priority": ["template/default", "config"],
                "example": system_name,
            },
            "id": {
                "purpose": "Globally unique AAS identifier URI.",
                "constraints": ["URI path or absolute URI"],
                "source_priority": ["config", "deterministic composition"],
                "example": f"/aas/{system_name}",
            },
            "globalAssetId": {
                "purpose": "Global identifier of the represented asset.",
                "constraints": ["URI path or absolute URI", "must be stable"],
                "source_priority": ["datasheet", "config"],
                "example": f"/assets/{cfg.asset_name}",
            },
            "assetType": {
                "purpose": "Asset type/classification URI for the resource.",
                "constraints": ["URI path or absolute URI"],
                "source_priority": ["datasheet", "domain model"],
            },
            "serialNumber": {
                "purpose": "Resource serial identifier.",
                "constraints": ["string, non-empty"],
                "source_priority": ["datasheet nameplate", "config"],
            },
            "location": {
                "purpose": "Physical/logical installation location.",
                "constraints": ["string"],
                "source_priority": ["plant docs", "config"],
            },
        }
    }

    body = guide[system_name]

    if "nameplate" in selected or "digitalnameplate" in selected:
        body["DigitalNameplate"] = {
            "ManufacturerName": {
                "purpose": "Manufacturer legal/common name.",
                "constraints": ["string", "use known vendor naming"],
                "source_priority": ["datasheet"],
            },
            "SerialNumber": {
                "purpose": "Serial number in nameplate payload.",
                "constraints": ["string", "must match shell serialNumber when available"],
                "source_priority": ["datasheet"],
            },
            "ManufacturerProductDesignation": {
                "purpose": "Manufacturer product designation/model.",
                "constraints": ["string"],
                "source_priority": ["datasheet title/model code"],
            },
            "DateOfManufacture": {
                "purpose": "Manufacturing date (optional).",
                "constraints": [
                    "xsd:date lexical form YYYY-MM-DD if known",
                    "OMIT this field entirely if the spec sheet does not state it — do NOT emit a [VERIFY: ...] placeholder",
                ],
                "source_priority": ["datasheet"],
                "optional": True,
            },
        }

    if "hierarchicalstructures" in selected:
        body["HierarchicalStructures"] = {
            "Name": {
                "purpose": "BoM hierarchy collection name.",
                "constraints": ["string"],
            },
            "Archetype": {
                "purpose": "Hierarchy archetype according to IDTA template.",
                "constraints": ["OneUp/other valid archetype token"],
            },
            "IsPartOf": {
                "purpose": "Parent relation for this resource in hierarchy.",
                "constraints": ["mapping of parent node -> globalAssetId"],
            },
        }

    if "aid" in selected or "assetinterfacesdescription" in selected:
        body["AssetInterfacesDescription"] = {
            "purpose": "Operational interface endpoints/actions/properties for the asset.",
            "constraints": ["InterfaceMQTT structure", "action/property schemas as URIs"],
            "source_priority": ["integration docs", "datasheet", "existing UNS specs"],
        }

    if "operationaldata" in selected or "variables" in selected:
        body["OperationalData"] = {
            "purpose": "Runtime variable mapping to interface properties.",
            "constraints": ["variable entries link to interface references"],
        }

    if "parameters" in selected:
        body["Parameters"] = {
            "purpose": "Configurable/static parameters relevant for operation.",
            "constraints": ["parameters should map to writable interface semantics where possible"],
        }

    if "capabilities" in selected:
        body["Capabilities"] = {
            "purpose": "Resource capabilities with semantic identifiers.",
            "constraints": ["capability should map to at least one skill via realizedBy"],
        }

    if "skills" in selected:
        body["Skills"] = {
            "purpose": "Executable skills and their interface bindings.",
            "constraints": ["skills should reference defined AID action/interface"],
        }

    return guide


def assemble_profile_example_json(cfg: Config) -> str:
    document = _assemble_profile_example_document(cfg)
    return json.dumps(document, indent=2, ensure_ascii=False)


def assemble_profile_semantic_guide_json(cfg: Config) -> str:
    document = _assemble_profile_semantic_guide_document(cfg)
    return json.dumps(document, indent=2, ensure_ascii=False)


def profile_json_text_to_document(text: str) -> dict[str, Any]:
    cleaned = extract_outer_json_object(text)
    document = json.loads(cleaned)
    if not isinstance(document, dict):
        raise ValueError("Profile output must be a JSON object.")
    return document


def validate_profile_document(document: dict[str, Any], cfg: Config) -> list[str]:
    issues: list[str] = []
    if not document:
        return ["Profile JSON is empty."]

    root = document
    if len(document) == 1 and isinstance(next(iter(document.values())), dict):
        root = next(iter(document.values()))

    if not isinstance(root, dict):
        return ["Profile root must be an object of key/value fields."]

    required_root = {"idShort", "id", "globalAssetId"}
    for key in sorted(required_root):
        if key not in root:
            issues.append(f"Missing required root field: {key}")

    def _is_verify(value: Any) -> bool:
        return isinstance(value, str) and "[VERIFY:" in value

    def _is_absolute_uri(value: str) -> bool:
        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value))

    def _is_relative_uri_path(value: str) -> bool:
        return value.startswith("/")

    def _is_aas_safe_idshort(value: str) -> bool:
        return bool(re.match(r"^[A-Za-z0-9_]+$", value))

    id_short = root.get("idShort")
    if id_short is not None:
        if not isinstance(id_short, str) or not id_short.strip():
            issues.append("Root field idShort must be a non-empty string")
        elif _is_verify(id_short):
            issues.append("Root field idShort contains a [VERIFY: ...] marker")
        elif not _is_aas_safe_idshort(id_short):
            issues.append("Root field idShort must use letters/digits/underscore only")

    for uri_field in ("id", "globalAssetId"):
        value = root.get(uri_field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            issues.append(f"Root field {uri_field} must be a non-empty string")
            continue
        if _is_verify(value):
            issues.append(f"Root field {uri_field} contains a [VERIFY: ...] marker")
            continue
        if not _is_absolute_uri(value) and not _is_relative_uri_path(value):
            issues.append(f"Root field {uri_field} must be an absolute URI or '/'-relative URI path")

    selected = {name.strip().lower() for name in cfg.submodels}
    if "nameplate" in selected or "digitalnameplate" in selected:
        if "DigitalNameplate" not in root:
            issues.append("Missing selected submodel section: DigitalNameplate")
        else:
            nameplate = root.get("DigitalNameplate")
            if isinstance(nameplate, dict):
                # DateOfManufacture is optional per IDTA 02006. If the LLM doesn't
                # have a value for it, the prompt instructs to OMIT the field
                # entirely rather than emit a [VERIFY: ...] placeholder. We only
                # validate the format when a non-VERIFY value is present.
                date_of_manufacture = nameplate.get("DateOfManufacture")
                if isinstance(date_of_manufacture, str) and not _is_verify(date_of_manufacture):
                    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_of_manufacture):
                        issues.append("DigitalNameplate.DateOfManufacture must match YYYY-MM-DD")
    if "hierarchicalstructures" in selected and "HierarchicalStructures" not in root:
        issues.append("Missing selected submodel section: HierarchicalStructures")

    return issues


