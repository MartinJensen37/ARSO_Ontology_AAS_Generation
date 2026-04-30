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
        body["AssetInterfacesDescription"] = {
            "InterfaceMQTT": {
                "Title": cfg.asset_name,
                "EndpointMetadata": {
                    "base": "[VERIFY: mqtt endpoint]",
                    "contentType": "application/json",
                },
                "InteractionMetadata": {
                    "actions": {},
                    "properties": {},
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
