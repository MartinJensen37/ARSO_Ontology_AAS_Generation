from __future__ import annotations

from typing import Any

from ...config import Config

CORE_PROFILE_KEYS = {
    "idShort",
    "id",
    "globalAssetId",
    "derivedFrom",
    "assetType",
    "serialNumber",
    "location",
}


def selected_profile_section_keys(cfg: Config) -> set[str]:
    selected = {name.strip().lower() for name in cfg.submodels}
    allowed: set[str] = set(CORE_PROFILE_KEYS)

    if "nameplate" in selected or "digitalnameplate" in selected:
        allowed.add("DigitalNameplate")
    if "hierarchicalstructures" in selected:
        allowed.add("HierarchicalStructures")
    if "aid" in selected or "assetinterfacesdescription" in selected:
        allowed.update({"AssetInterfacesDescription", "AssetInterfaceDescription", "AID"})
    if "operationaldata" in selected or "variables" in selected:
        allowed.update({"OperationalData", "Variables"})
    if "parameters" in selected:
        allowed.add("Parameters")
    if "capabilities" in selected:
        allowed.add("Capabilities")
    if "skills" in selected:
        allowed.add("Skills")

    return allowed


def prune_profile_sections(profile: dict[str, Any], cfg: Config) -> dict[str, Any]:
    if not profile:
        return profile

    system_name = next(iter(profile.keys()))
    body = profile.get(system_name)
    if not isinstance(body, dict):
        return profile

    allowed = selected_profile_section_keys(cfg)
    pruned_body = {k: v for k, v in body.items() if k in allowed}
    return {system_name: pruned_body}


def ensure_requested_submodel_sections(body: dict[str, Any], cfg: Config) -> None:
    selected = {name.strip().lower() for name in cfg.submodels}

    if ("nameplate" in selected or "digitalnameplate" in selected) and "DigitalNameplate" not in body:
        # Only seed mandatory fields. Optional fields (DateOfManufacture,
        # YearOfConstruction, HardwareVersion, etc.) are intentionally absent —
        # the LLM should OMIT them when the spec sheet doesn't provide a value
        # rather than fill them with a [VERIFY: ...] placeholder.
        body["DigitalNameplate"] = {
            "ManufacturerName": "[VERIFY: manufacturer name]",
            "SerialNumber": str(body.get("serialNumber", "[VERIFY: serial number]")),
            "ManufacturerProductDesignation": cfg.asset_name,
        }

    if "hierarchicalstructures" in selected and "HierarchicalStructures" not in body:
        # Archetype MUST be exactly "OneUp", "OneDown", or "Full" (ontology
        # owl:oneOf in hierarchical-structures.ttl) -- this scaffold shows the
        # "OneUp" case (IsPartOf only). Swap in HasPart (same shape) for
        # "OneDown", or both fields for "Full".
        body["HierarchicalStructures"] = {
            "Name": "BillOfMaterials",
            "Archetype": "OneUp",
            "IsPartOf": {
                "ParentSystem": {
                    "globalAssetId": "[VERIFY: parent globalAssetId]"
                }
            },
        }

    if ("aid" in selected or "assetinterfacesdescription" in selected) and "AssetInterfacesDescription" not in body:
        # InteractionMetadata.actions / .properties / .events are each an
        # OBJECT keyed by name -- never a JSON array/list. This scaffold shows
        # one action and one property populated (not left empty) specifically
        # so that shape is unambiguous to whoever/whatever fills this in next.
        body["AssetInterfacesDescription"] = {
            "MqttInterface": {
                "protocol": "MQTT",
                "Title": cfg.asset_name,
                "EndpointMetadata": {
                    "base": "[VERIFY: mqtt endpoint]",
                    "contentType": "application/json",
                },
                "InteractionMetadata": {
                    "actions": {
                        "[VERIFY: action name]": {
                            "key": "[VERIFY: action key]",
                            "title": "[VERIFY: action title]",
                            "synchronous": "true",
                            "forms": {"href": "[VERIFY: mqtt topic]", "contentType": "application/json"},
                        }
                    },
                    "properties": {
                        "[VERIFY: property name]": {
                            "key": "[VERIFY: property key]",
                            "title": "[VERIFY: property title]",
                            "forms": {"href": "[VERIFY: mqtt topic]", "contentType": "application/json"},
                        }
                    },
                },
            }
        }

    if (
        "operationaldata" in selected or "variables" in selected
    ) and "OperationalData" not in body and "Variables" not in body:
        body["OperationalData"] = {}

    if "parameters" in selected and "Parameters" not in body:
        body["Parameters"] = {}

    if "capabilities" in selected and "Capabilities" not in body:
        body["Capabilities"] = {}

    if "skills" in selected and "Skills" not in body:
        body["Skills"] = {}


# Field-name aliases the LLM plausibly reaches for instead of the profile
# schema's actual key, per section. The rest of the AAS JSON convention uses
# camelCase ("semanticId" is the real AAS metamodel property name everywhere
# else in the spec), so an LLM slipping into "semanticId" for a Skill's
# semantic_id here is a predictable, harmless naming mismatch — not a sign
# the LLM failed to provide a real value. Normalizing it here means
# AAS_builder.py's _check_required_fields (deliberately strict about the
# *value* actually being present — see its docstring) isn't tripped by a
# key-naming variant alone.
_SKILL_CAPABILITY_FIELD_ALIASES: dict[str, str] = {
    "semanticId": "semantic_id",
    "realized_by": "realizedBy",
}


def _apply_field_aliases(entries: dict[str, Any]) -> None:
    for data in entries.values():
        if not isinstance(data, dict):
            continue
        for alias, canonical in _SKILL_CAPABILITY_FIELD_ALIASES.items():
            if alias in data and canonical not in data:
                data[canonical] = data.pop(alias)


def normalize_profile_for_builder(document: Any, cfg: Config) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("Description output must be a mapping/object at top-level.")

    if len(document) == 1 and isinstance(next(iter(document.values())), dict):
        system_name = next(iter(document.keys()))
        system_config = dict(next(iter(document.values())))
    else:
        system_name = f"{cfg.asset_name}AAS"
        system_config = dict(document)

    filtered = prune_profile_sections({system_name: system_config}, cfg)
    system_config = dict(filtered.get(system_name, {}))

    if "AssetInterfaceDescription" in system_config and "AssetInterfacesDescription" not in system_config:
        system_config["AssetInterfacesDescription"] = system_config["AssetInterfaceDescription"]

    if "AID" in system_config and "AssetInterfacesDescription" not in system_config:
        system_config["AssetInterfacesDescription"] = system_config["AID"]

    if "OperationalData" in system_config and "Variables" not in system_config:
        system_config["Variables"] = system_config["OperationalData"]

    if isinstance(system_config.get("Skills"), dict):
        _apply_field_aliases(system_config["Skills"])
    if isinstance(system_config.get("Capabilities"), dict):
        _apply_field_aliases(system_config["Capabilities"])

    if "DigitalNameplate" not in system_config:
        # Seed only mandatory fields; optional ones (DateOfManufacture,
        # YearOfConstruction, etc.) are absent by design — the builder skips
        # them when not present rather than emitting [VERIFY:] placeholders.
        system_config["DigitalNameplate"] = {
            "ManufacturerName": "[VERIFY: manufacturer name]",
            "SerialNumber": str(system_config.get("serialNumber", "[VERIFY: serial number]")),
            "ManufacturerProductDesignation": cfg.asset_name,
        }

    return {system_name: system_config}
