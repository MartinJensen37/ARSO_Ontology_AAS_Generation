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
            "OrderCodeOfManufacturer": {
                "purpose": "Manufacturer's order code / article number for this exact product variant.",
                "constraints": [
                    "string",
                    "OMIT entirely if truly unknown — the builder inserts a [VERIFY: ...] placeholder, do NOT invent a value",
                ],
                "source_priority": ["datasheet order code / article number"],
                "optional": True,
            },
            "AddressInformation": {
                "purpose": "Manufacturer contact address (IDTA 02006 ContactInformation) — mandatory sub-object per the ontology, even though every individual field inside it is independently optional to you.",
                "constraints": [
                    "object with keys Street, ZipCode, CityTown, NationalCode",
                    "OMIT individual keys you don't know — the builder inserts a [VERIFY: ...] placeholder for each missing one, do NOT invent values",
                ],
                "source_priority": ["datasheet manufacturer address", "vendor website"],
                "example": {"Street": "Musterstrasse 1", "ZipCode": "70173", "CityTown": "Stuttgart", "NationalCode": "DE"},
                "optional": True,
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
                "example": "BillOfMaterials",
            },
            "Archetype": {
                "purpose": "Hierarchy archetype — which direction(s) of relations this resource declares.",
                "constraints": [
                    "MUST be exactly one of these three strings: \"OneUp\", \"OneDown\", \"Full\" — no other value is valid.",
                    "\"OneUp\" = this resource declares its parent only (use the IsPartOf field below).",
                    "\"OneDown\" = this resource declares its children only (use the HasPart field below).",
                    "\"Full\" = this resource declares both parent AND children (provide both IsPartOf and HasPart).",
                ],
                "example": "OneUp",
            },
            "IsPartOf": {
                "purpose": "Parent relation(s) — only meaningful when Archetype is \"OneUp\" or \"Full\".",
                "constraints": [
                    "An OBJECT keyed by a PascalCase name you choose for the parent, mapping to an object with the parent's globalAssetId — NEVER a JSON array/list.",
                    "OMIT this field entirely if Archetype is \"OneDown\" or if there is no known parent.",
                ],
                "example": {"ParentSystem": {"globalAssetId": "https://smartproductionlab.aau.dk/aas/ParentSystem"}},
            },
            "HasPart": {
                "purpose": "Child relation(s) — only meaningful when Archetype is \"OneDown\" or \"Full\".",
                "constraints": [
                    "Same shape as IsPartOf but for children: an OBJECT keyed by a PascalCase name per child, mapping to an object with that child's globalAssetId — NEVER a JSON array/list.",
                    "OMIT this field entirely if Archetype is \"OneUp\" or if there are no known children.",
                ],
                "example": {"SubComponent01": {"globalAssetId": "https://smartproductionlab.aau.dk/aas/SubComponent01"}},
                "optional": True,
            },
        }

    if "aid" in selected or "assetinterfacesdescription" in selected:
        body["AssetInterfacesDescription"] = {
            "purpose": "Operational interface endpoints/actions/properties/events for the asset (IDTA 02017 AID / W3C WoT Thing Description).",
            "constraints": [
                "Map of interface name -> interface object. One entry per communication interface the asset exposes (an asset MAY have more than one, e.g. an MQTT interface for commands plus a Modbus interface for register reads).",
                "Interface names are free-form (pick a descriptive PascalCase name, e.g. \"MqttInterface\" or \"ModbusRegisters\") — they are NOT required to be literally \"InterfaceMQTT\".",
                "Each interface object MUST have a 'protocol' field (exact key, lowercase) with one of these exact values: \"MQTT\", \"OPCUA\", \"HTTP\", \"MODBUS\" — this determines which EndpointMetadata fields apply and how downstream Skills/Variables/Parameters resolve their reference.",
                "InteractionMetadata.actions / .properties / .events are each an OBJECT keyed by name (e.g. {\"StartProcess\": {...}, \"StopProcess\": {...}}) — NEVER a JSON array/list of items. If you were about to write a list, convert it: each item's own name/key becomes the object's key instead. This is the single most common mistake — check it before returning your answer.",
                "actions: invokable operations (WoT ActionAffordance). properties: readable/observable data points (WoT PropertyAffordance). events: subscribable notifications (WoT EventAffordance). All three are optional — a read-only sensor interface may have properties only and no actions at all; that is valid, do not invent actions to fill the section.",
                "If this asset also has an OperationalData/Variables section (see that section's guide) and one of its variables needs to read a value published here, that value MUST be listed under 'properties', never 'events' — an OperationalData variable's InterfaceReference can only resolve to a property, even for a value that is semantically a one-shot notification (e.g. a cycle-completion reading). Only put something under 'events' if no OperationalData variable will reference it.",
                "Each action/property/event entry may have: 'key' (short code), 'title' (human label), 'forms' (protocol binding, see example — at minimum 'href': the topic/path/address on this interface). Actions may also have 'synchronous' (\"true\"/\"false\") and optionally 'input'/'output' (a URI to a JSON Schema document describing the payload — OMIT input/output entirely if you don't have a real schema URL, do not invent one).",
                "'forms' field names are protocol-specific: MQTT commonly uses 'href' (topic) + 'contentType'; HTTP adds 'htv_methodName' (GET/POST/PUT/DELETE/PATCH); Modbus adds 'modv_function' (e.g. readHoldingRegisters/writeSingleRegister) and 'modv_entity' (e.g. HoldingRegister/InputRegister). Only include the fields you actually know from the source material.",
                "If a command has SEPARATE topics for invoking it and for its asynchronous response/acknowledgement (a common MQTT request/response pattern: a CMD topic to publish to, a DATA topic to subscribe to for the result), put the invoke topic on 'forms.href' and nest the response topic under 'forms.response.href' — NOT as two separate actions and NOT as extra top-level keys. See the StartProcess example below.",
            ],
            "example": {
                "MqttInterface": {
                    "protocol": "MQTT",
                    "Title": "MQTT interface",
                    "EndpointMetadata": {"base": "mqtt://broker:1883", "contentType": "application/json"},
                    "InteractionMetadata": {
                        "actions": {
                            "StartProcess": {
                                "key": "start",
                                "title": "Start the process",
                                "synchronous": "true",
                                "forms": {
                                    "href": "CMD/StartProcess",
                                    "contentType": "application/json",
                                    "response": {"href": "DATA/StartProcess", "contentType": "application/json"},
                                },
                            }
                        },
                        "properties": {
                            "Temperature": {
                                "key": "temperature",
                                "title": "Current temperature reading",
                                "forms": {"href": "state/temperature", "contentType": "application/json"},
                            }
                        },
                        "events": {
                            "OverTemperature": {
                                "key": "overTemp",
                                "title": "Over-temperature alarm",
                                "forms": {"href": "alarms/overtemp", "contentType": "application/json"},
                            }
                        },
                    },
                },
                "ModbusRegisters": {
                    "protocol": "MODBUS",
                    "Title": "Modbus register interface",
                    "EndpointMetadata": {"base": "modbus+tcp://192.168.0.1:502", "contentType": "application/json"},
                    "InteractionMetadata": {
                        "properties": {
                            "HoldingReg0": {
                                "key": "holdingReg0",
                                "title": "Holding register 0",
                                "forms": {"href": "0", "modv_function": "readHoldingRegisters", "modv_entity": "HoldingRegister"},
                            }
                        }
                    },
                },
            },
            "source_priority": ["integration docs", "datasheet", "existing UNS specs"],
        }

    if "operationaldata" in selected or "variables" in selected:
        body["OperationalData"] = {
            "purpose": "Map of variable name to variable object. One entry per runtime operational variable.",
            "constraints": [
                "Each entry is a JSON OBJECT, never a plain string or dotted path.",
                "Each entry is keyed by a PascalCase variable name, e.g. \"State\": {...}",
                "'InterfaceReference' field (exact key, PascalCase) - the idShort of the matching AID property under InteractionMetadata.properties (or action under .actions) that this variable reads, e.g. \"State\" - REQUIRED",
                "'semanticId' field (exact key: semanticId, camelCase) - optional URI string, only if this variable needs its own distinct semantic identifier beyond the referenced interface property",
            ],
            "example": {"State": {"InterfaceReference": "State"}, "CycleTime": {"InterfaceReference": "CycleTime"}},
        }

    if "parameters" in selected:
        body["Parameters"] = {
            "purpose": "Map of parameter name to parameter object. One entry per configurable/static parameter.",
            "constraints": [
                "Each entry is a JSON OBJECT, never a plain string or dotted path.",
                "Each entry is keyed by a PascalCase parameter name, e.g. \"Setpoint\": {...}",
                "'InterfaceReference' field (exact key, PascalCase) - the idShort of the matching AID property/action this parameter writes to - REQUIRED",
                "'semanticId' field (exact key: semanticId, camelCase) - optional URI string, only if this parameter needs its own distinct semantic identifier",
            ],
            "example": {"Setpoint": {"InterfaceReference": "Setpoint"}},
        }

    if "capabilities" in selected:
        body["Capabilities"] = {
            "purpose": "Map of capability name to capability object. One entry per resource capability.",
            "constraints": [
                "Each entry is keyed by a PascalCase capability name, e.g. \"Dispense\": {...}",
                "Each entry MUST have a 'semantic_id' field (exact key: semantic_id, snake_case, NOT semanticId) - a URI string starting with https://smartproductionlab.aau.dk/",
                "Each entry MUST have a 'realizedBy' field - the name of the matching Skill entry that implements this capability",
                "Every Skill you define (see the Skills section below) needs at least one Capability whose 'realizedBy' names it - if you define 4 skills, provide 4 capabilities (or more, if a skill offers more than one distinct capability), not just one. A skill left without any matching capability is missing information, not a skill that doesn't need one.",
            ],
            "example": {
                "Dispense": {"semantic_id": "https://smartproductionlab.aau.dk/Capability/Dispense", "realizedBy": "Dispense"},
                "Stop": {"semantic_id": "https://smartproductionlab.aau.dk/Capability/Stop", "realizedBy": "Stop"},
            },
        }

    if "skills" in selected:
        body["Skills"] = {
            "purpose": "Map of skill name to skill object. One entry per executable skill.",
            "constraints": [
                "Each entry is keyed by a PascalCase skill name matching an AID action, e.g. \"Dispense\": {...}",
                "Each entry MUST have a 'semantic_id' field (exact key: semantic_id, snake_case, NOT semanticId) - a URI string starting with https://smartproductionlab.aau.dk/",
                "Each entry MUST have an 'interface' field (exact key, NOT 'action') - the idShort of the matching action under InteractionMetadata.actions on WHICHEVER AID interface defines it (the builder searches every configured interface for it), e.g. \"Dispense\" - this is the action's own name, not the containing interface's name",
            ],
            "example": {"Dispense": {"semantic_id": "https://smartproductionlab.aau.dk/skills/Dispense", "interface": "Dispense"}},
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


