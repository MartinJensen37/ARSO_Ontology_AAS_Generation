"""Full AAS JSON -> profile document; inverse of profile_document_to_aas_json.

Each parse_* function mirrors the matching builder in
Transformation/AAS_Builder/AAS_generation/submodels/*.py and must stay in lockstep
with it. Canonical converter for both the UI (via api/routers/aas_to_profile.py)
and in-process callers.
"""
from __future__ import annotations

from ..submodel_registry import SPEC_BY_ID_SHORT, SUBMODEL_IDSHORT_TO_KEY

import json
import re
from typing import Any

AnyDict = dict[str, Any]

_AID_INTERFACE_SEMANTIC_ID = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
_OPCUA_ENDPOINT_FIELDS = (
    "protocol", "encoding", "base", "port",
    "security_mode", "security_policy", "namespace_uri", "namespace_index",
)
# WoT binding supplementalSemanticId -> protocol. Mirrors
# semantic_ids.py's _MQTT_PROTOCOL/_OPCUA_PROTOCOL/_HTTP_PROTOCOL/_MODBUS_PROTOCOL.
_PROTOCOL_BY_BINDING_URI = {
    "https://www.w3.org/2019/wot/td/v1/binding/mqtt": "MQTT",
    "https://www.w3.org/2019/wot/td/v1/binding/opcua": "OPCUA",
    "https://www.w3.org/2019/wot/td/v1/binding/http": "HTTP",
    "https://www.w3.org/2019/wot/td/v1/binding/modbus": "MODBUS",
}
# Legacy fixed idShorts, for interfaces built before free-form naming.
_LEGACY_IDSHORT_PROTOCOL = {
    "InterfaceMQTT": "MQTT",
    "InterfaceOPCUA": "OPCUA",
    "InterfaceHTTP": "HTTP",
    "InterfaceMODBUS": "MODBUS",
}

# AAS submodel idShort -> profile section key, derived from the registry so it
# cannot drift from what the builders emit.
_SUBMODEL_IDSHORT_TO_KEY: dict[str, str] = dict(SUBMODEL_IDSHORT_TO_KEY)


# ── small element-tree helpers ──────────────────────────────────────────────

def _elements(sm: AnyDict) -> list[AnyDict]:
    return sm.get("submodelElements") or []


def _smc_value(el: AnyDict) -> list[AnyDict]:
    return el.get("value") or []


def _prop_val(elements: list[AnyDict], id_short: str) -> Any | None:
    for e in elements:
        if e.get("idShort") == id_short and e.get("modelType") == "Property":
            return e.get("value")
    return None


def _mlp_text(el: AnyDict) -> str | None:
    values = el.get("value")
    if not values:
        return None
    for v in values:
        if v.get("language") == "en":
            return v.get("text")
    return values[0].get("text")


def _mlp_val(elements: list[AnyDict], id_short: str) -> str | None:
    for e in elements:
        if e.get("idShort") == id_short and e.get("modelType") == "MultiLanguageProperty":
            return _mlp_text(e)
    return None


def _smc(elements: list[AnyDict], id_short: str) -> AnyDict | None:
    for e in elements:
        if e.get("idShort") == id_short and e.get("modelType") == "SubmodelElementCollection":
            return e
    return None


def _reference_last_key(el: AnyDict) -> str | None:
    """Last key's `value` off a ReferenceElement -- the referenced idShort."""
    keys = ((el.get("value") or {}).get("keys")) or []
    return keys[-1].get("value") if keys else None


def _reference_key_at(el: AnyDict, index: int) -> str | None:
    """`value` of the key at `index` off a ReferenceElement's key chain."""
    keys = ((el.get("value") or {}).get("keys")) or []
    return keys[index].get("value") if 0 <= index < len(keys) else None


def _semantic_id_value(ref: AnyDict | None) -> str | None:
    """First key's `value` off a semanticId/supplementalSemanticId Reference."""
    if not ref:
        return None
    keys = ref.get("keys") or []
    return keys[0].get("value") if keys else None


# ── DigitalNameplate — mirrors nameplate_builder.py ─────────────────────────

def parse_nameplate(sm: AnyDict) -> AnyDict:
    result: AnyDict = {}
    for el in _elements(sm):
        id_short = el.get("idShort")
        model_type = el.get("modelType")
        if not id_short:
            continue

        if model_type == "MultiLanguageProperty":
            text = _mlp_text(el)
            if text is not None:
                result[id_short] = text
        elif model_type == "Property":
            if el.get("value") is not None:
                result[id_short] = el["value"]
        elif model_type == "SubmodelElementCollection" and id_short == "ContactInformation":
            address: AnyDict = {}
            for field in ("Street", "ZipCode", "CityTown", "NationalCode"):
                text = _mlp_val(_smc_value(el), field)
                if text:
                    address[field] = text
            if address:
                result["AddressInformation"] = address

    return result


# ── HierarchicalStructures — mirrors hierarchical_structures_builder.py ────

def parse_hierarchical_structures(sm: AnyDict) -> AnyDict:
    archetype = "OneUp"
    entry_node: AnyDict | None = None
    for el in _elements(sm):
        if el.get("idShort") == "ArcheType" and el.get("modelType") == "Property":
            archetype = el.get("value") or "OneUp"
        elif el.get("modelType") == "Entity":
            entry_node = el

    result: AnyDict = {"Archetype": archetype}
    name = _mlp_text({"value": sm.get("displayName")}) if sm.get("displayName") else None
    if name:
        result["Name"] = name
    if not entry_node:
        return result

    # RelationshipElement statements ("IsPartOf_<name>"/"HasPart_<name>") decide
    # each Entity's group -- archetype 'Full' has both. Mirrors _create_entry_node
    # in hierarchical_structures_builder.py.
    statements = entry_node.get("statements") or []
    entity_group: dict[str, str] = {}
    for stmt in statements:
        if stmt.get("modelType") != "RelationshipElement":
            continue
        rel_id_short = stmt.get("idShort") or ""
        for prefix in ("IsPartOf", "HasPart"):
            if rel_id_short.startswith(f"{prefix}_"):
                entity_group[rel_id_short[len(prefix) + 1:]] = prefix
                break

    groups: dict[str, AnyDict] = {"IsPartOf": {}, "HasPart": {}}
    for stmt in statements:
        if stmt.get("modelType") != "Entity":
            continue
        entity_name = stmt.get("idShort")
        if not entity_name:
            continue
        entry: AnyDict = {}
        global_asset_id = stmt.get("globalAssetId")
        if global_asset_id:
            entry["globalAssetId"] = global_asset_id
        # Fall back to the single-direction default when no RelationshipElement
        # matched (shouldn't happen for builder output, but stay lossless).
        prefix = entity_group.get(entity_name, "IsPartOf" if archetype == "OneUp" else "HasPart")
        groups[prefix][entity_name] = entry

    for prefix, entities in groups.items():
        if entities:
            result[prefix] = entities
    return result


# ── Skills — mirrors skills_builder.py ──────────────────────────────────────

def parse_skills(sm: AnyDict) -> AnyDict:
    result: AnyDict = {}
    skills_smc = _smc(_elements(sm), "Skills")
    if not skills_smc:
        return result

    for skill_el in _smc_value(skills_smc):
        if skill_el.get("modelType") != "SubmodelElementCollection":
            continue
        skill_name = skill_el.get("idShort")
        if not skill_name:
            continue
        inner = _smc_value(skill_el)

        semantic_id = _prop_val(inner, "SemanticId")
        interface = None
        interface_key = None
        iface_ref = next(
            (e for e in inner if e.get("idShort") == "InterfaceReference" and e.get("modelType") == "ReferenceElement"),
            None,
        )
        if iface_ref:
            interface = _reference_last_key(iface_ref)
            # keys: [Submodel(AID), SMC(<interface idShort>), SMC(InteractionMetadata), SMC(actions), SMC(<action>)]
            interface_key = _reference_key_at(iface_ref, 1)

        entry: AnyDict = {}
        if semantic_id:
            entry["semantic_id"] = semantic_id
        # skills_builder.py defaults interface_name = skill_data.get('interface', skill_name)
        # when no explicit interface is configured -- preserve that default on round trip.
        entry["interface"] = interface or skill_name
        if interface_key:
            entry["interfaceKey"] = interface_key

        desc_list = skill_el.get("description")
        if desc_list:
            desc = next((d.get("text") for d in desc_list if d.get("language") == "en"), desc_list[0].get("text"))
            if desc and desc != f"Skill: {skill_name}":
                entry["description"] = desc

        result[skill_name] = entry

    return result


# ── Capabilities — mirrors capabilities_builder.py ──────────────────────────

def parse_capabilities(sm: AnyDict) -> AnyDict:
    result: AnyDict = {}
    cap_set = _smc(_elements(sm), "CapabilitySet")
    if not cap_set:
        return result

    for container in _smc_value(cap_set):
        if container.get("modelType") != "SubmodelElementCollection":
            continue
        inner = _smc_value(container)
        cap_el = next((e for e in inner if e.get("modelType") == "Capability"), None)
        if not cap_el:
            continue
        cap_name = cap_el.get("idShort")
        if not cap_name:
            continue

        semantic_id = _prop_val(inner, "SemanticId")
        realized_by: list[str] = []
        realized_by_list = next(
            (e for e in inner if e.get("idShort") == "realizedBy" and e.get("modelType") == "SubmodelElementList"),
            None,
        )
        if realized_by_list:
            for rel in _smc_value(realized_by_list):
                if rel.get("modelType") != "RelationshipElement":
                    continue
                second_keys = ((rel.get("second") or {}).get("keys")) or []
                if second_keys:
                    realized_by.append(second_keys[-1].get("value"))

        entry: AnyDict = {}
        if semantic_id:
            entry["semantic_id"] = semantic_id
        if realized_by:
            # The TS Capability type models a single realizing skill.
            entry["realizedBy"] = realized_by[0]
        result[cap_name] = entry

    return result


# ── OperationalData / Parameters — mirrors variables_builder.py /
#    parameters_builder.py (identical InterfaceReference+semanticId shape) ──

def _parse_interface_reference_collections(sm: AnyDict) -> AnyDict:
    result: AnyDict = {}
    for el in _elements(sm):
        if el.get("modelType") != "SubmodelElementCollection":
            continue
        name = el.get("idShort")
        if not name:
            continue
        inner = _smc_value(el)
        entry: AnyDict = {}

        iface_ref = next(
            (e for e in inner if e.get("idShort") == "InterfaceReference" and e.get("modelType") == "ReferenceElement"),
            None,
        )
        if iface_ref:
            last = _reference_last_key(iface_ref)
            if last:
                entry["InterfaceReference"] = last

        semantic_id_keys = ((el.get("semanticId") or {}).get("keys")) or []
        if semantic_id_keys:
            entry["semanticId"] = semantic_id_keys[-1].get("value")

        if entry:
            result[name] = entry

    return result


def parse_operational_data(sm: AnyDict) -> AnyDict:
    return _parse_interface_reference_collections(sm)


def parse_parameters(sm: AnyDict) -> AnyDict:
    return _parse_interface_reference_collections(sm)


# ── AID — mirrors asset_interfaces_builder.py ───────────────────────────────

def _parse_forms(forms_el: AnyDict) -> AnyDict:
    forms: AnyDict = {}
    for e in _smc_value(forms_el):
        if e.get("idShort") == "response" and e.get("modelType") == "SubmodelElementCollection":
            forms["response"] = {
                inner.get("idShort"): inner.get("value")
                for inner in _smc_value(e)
                if inner.get("modelType") == "Property"
            }
        elif e.get("modelType") == "Property":
            forms[e.get("idShort")] = e.get("value")
    return forms


def _parse_affordance_collection(coll_el: AnyDict) -> AnyDict:
    """actions/properties SMC -> {name: {key?, title?, synchronous?, input?, output?, forms?}}."""
    result: AnyDict = {}
    for el in _smc_value(coll_el):
        if el.get("modelType") != "SubmodelElementCollection":
            continue
        name = el.get("idShort")
        if not name:
            continue
        inner = _smc_value(el)
        entry: AnyDict = {}

        key = _prop_val(inner, "Key")
        if key is not None:
            entry["key"] = key
        title = _prop_val(inner, "Title")
        if title is not None:
            entry["title"] = title
        synchronous = _prop_val(inner, "Synchronous")
        if synchronous is not None:
            entry["synchronous"] = synchronous

        input_file = next((e for e in inner if e.get("idShort") == "input" and e.get("modelType") == "File"), None)
        if input_file:
            entry["input"] = input_file.get("value")
        output_file = next((e for e in inner if e.get("idShort") == "output" and e.get("modelType") == "File"), None)
        if output_file:
            entry["output"] = output_file.get("value")

        forms_el = _smc(inner, "Forms")
        if forms_el:
            forms = _parse_forms(forms_el)
            if forms:
                entry["forms"] = forms

        result[name] = entry

    return result


def _interface_protocol(iface_el: AnyDict) -> str:
    """Determine an Interface SMC's protocol from its supplementalSemanticIds
    (the WoT binding URI the builder writes), falling back to sniffing a
    legacy fixed idShort for AIDs built before free-form interface naming."""
    for ref in iface_el.get("supplementalSemanticIds") or []:
        uri = _semantic_id_value(ref)
        if uri in _PROTOCOL_BY_BINDING_URI:
            return _PROTOCOL_BY_BINDING_URI[uri]
    return _LEGACY_IDSHORT_PROTOCOL.get(iface_el.get("idShort"), "MQTT")


def _parse_one_interface(iface_el: AnyDict) -> AnyDict:
    protocol = _interface_protocol(iface_el)
    inner = _smc_value(iface_el)
    result: AnyDict = {"protocol": protocol}

    title = _prop_val(inner, "title")
    if title is not None:
        result["Title"] = title

    endpoint_el = _smc(inner, "EndpointMetadata")
    if endpoint_el:
        ep_inner = _smc_value(endpoint_el)
        endpoint: AnyDict = {}
        if protocol == "OPCUA":
            for field in _OPCUA_ENDPOINT_FIELDS:
                val = _prop_val(ep_inner, field)
                if val is not None:
                    endpoint[field] = val
        else:
            base = _prop_val(ep_inner, "base")
            if base is not None:
                endpoint["base"] = base
            content_type = _prop_val(ep_inner, "contentType")
            if content_type is not None:
                endpoint["contentType"] = content_type
            if protocol == "MODBUS":
                for field in ("modv_mostSignificantByte", "modv_mostSignificantWord"):
                    val = _prop_val(ep_inner, field)
                    if val is not None:
                        endpoint[field] = val
        if endpoint:
            result["EndpointMetadata"] = endpoint

    interaction_el = _smc(inner, "InteractionMetadata")
    if interaction_el:
        interaction_inner = _smc_value(interaction_el)
        interaction: AnyDict = {}
        actions_el = _smc(interaction_inner, "actions")
        if actions_el:
            actions = _parse_affordance_collection(actions_el)
            if actions:
                interaction["actions"] = actions
        properties_el = _smc(interaction_inner, "properties")
        if properties_el:
            properties = _parse_affordance_collection(properties_el)
            if properties:
                interaction["properties"] = properties
        events_el = _smc(interaction_inner, "events")
        if events_el:
            events = _parse_affordance_collection(events_el)
            if events:
                interaction["events"] = events
        if interaction:
            result["InteractionMetadata"] = interaction

    return result


def parse_aid(sm: AnyDict) -> AnyDict:
    """Every Interface SMC in the submodel becomes its own entry, keyed by
    its (now free-form, see aid.ttl arso:InterfaceSMC) idShort -- an AID can
    describe several communication interfaces at once."""
    result: AnyDict = {}
    for el in _elements(sm):
        if el.get("modelType") != "SubmodelElementCollection":
            continue
        if _semantic_id_value(el.get("semanticId")) != _AID_INTERFACE_SEMANTIC_ID:
            continue
        iface_id_short = el.get("idShort")
        if not iface_id_short:
            continue
        result[iface_id_short] = _parse_one_interface(el)
    return result


# ── top-level orchestrator ──────────────────────────────────────────────────

def _derive_base_url(shell_id: str) -> str:
    """Inverse of AASGenerator._extract_base_url (AAS_generation/core/generate_aas.py)."""
    if shell_id and (shell_id.startswith("http://") or shell_id.startswith("https://")):
        parts = shell_id.rsplit("/aas/", 1)
        if len(parts) == 2 and parts[0]:
            return parts[0]
        return shell_id.rsplit("/", 1)[0]
    return "https://smartproductionlab.aau.dk"



# ── TechnicalData — mirrors technical_data_builder.py ───────────────────────

def parse_technical_data(sm: AnyDict) -> AnyDict:
    """Invert the TechnicalData submodel into its profile section.

    Args:
        sm: TechnicalData submodel JSON.

    Returns:
        Profile section with GeneralInformation / ProductClassifications /
        TechnicalProperties / FurtherInformation, each only when present.
    """
    out: AnyDict = {}
    for el in _elements(sm):
        id_short = el.get("idShort")
        if id_short == "GeneralInformation":
            general = {c.get("idShort"): _text_of(c) for c in _smc_value(el)
                       if c.get("idShort") and _text_of(c)}
            if general:
                out["GeneralInformation"] = general
        elif id_short == "ProductClassifications":
            entries = []
            for item in _smc_value(el):
                entry = {c.get("idShort"): _text_of(c) for c in _smc_value(item)
                         if c.get("idShort") and _text_of(c)}
                if entry:
                    entries.append(entry)
            if entries:
                out["ProductClassifications"] = entries
        elif id_short == "TechnicalPropertyAreas":
            # Positional area SMCs hold the named sections.
            sections: AnyDict = {}
            for area in _smc_value(el):
                for section in _smc_value(area):
                    if section.get("idShort"):
                        sections[section["idShort"]] = _parse_arbitrary(section)
            if sections:
                out["TechnicalProperties"] = sections
        elif id_short == "FurtherInformation":
            further: AnyDict = {}
            statements = []
            for child in _smc_value(el):
                if child.get("idShort") == "TextStatement" and _text_of(child):
                    statements.append(_text_of(child))
                elif child.get("idShort") == "ValidDate":
                    further["ValidDate"] = _text_of(child)
            if statements:
                further["TextStatement"] = statements[0] if len(statements) == 1 else statements
            if further:
                out["FurtherInformation"] = further
    return out


def _parse_arbitrary(container: AnyDict) -> AnyDict:
    """Invert an arbitrary property tree into plain nested values."""
    out: AnyDict = {}
    for el in _smc_value(container):
        name = el.get("idShort")
        if not name:
            continue
        if el.get("modelType") == "SubmodelElementCollection":
            out[name] = _parse_arbitrary(el)
        elif el.get("modelType") == "Range":
            out[name] = {"min": el.get("min"), "max": el.get("max")}
        else:
            out[name] = _text_of(el)
    return out


# ── AIMC — mirrors aimc_builder.py ─────────────────────────────────────────

def parse_aimc(sm: AnyDict) -> AnyDict:
    """Invert the AIMC submodel into its profile section.

    Args:
        sm: AssetInterfacesMappingConfiguration submodel JSON.

    Returns:
        Dict of AID interface name -> {DefaultPollingInterval, Mappings}, where
        Sources and Sinks are re-paired by position.
    """
    out: AnyDict = {}
    for el in _elements(sm):
        if el.get("idShort") != "MappingConfigurations":
            continue
        for config in _smc_value(el):
            iface_name = None
            entry: AnyDict = {}
            sources: list[AnyDict] = []
            sinks: list[AnyDict] = []
            for child in _smc_value(config):
                name = child.get("idShort")
                if name == "InterfaceReference":
                    iface_name = _last_key(child)
                elif name == "DefaultPollingInterval":
                    entry["DefaultPollingInterval"] = _text_of(child)
                elif name == "Sources":
                    for src in _smc_value(child):
                        fields = {c.get("idShort"): c for c in _smc_value(src)}
                        sources.append({
                            "source": _text_of(fields.get("SourceId")) or _last_key(fields.get("Source")),
                            "pollingInterval": _text_of(fields.get("PollingInterval")),
                        })
                elif name == "Sinks":
                    for snk in _smc_value(child):
                        fields = {c.get("idShort"): c for c in _smc_value(snk)}
                        sinks.append({
                            "sink": _text_of(fields.get("SinkId")) or _last_key(fields.get("Sink")),
                            "sinkSubmodel": _submodel_of(fields.get("Sink")),
                        })
            mappings = []
            # Builder emits one Source and one Sink per mapping, in order.
            for i, src in enumerate(sources):
                if not src["source"]:
                    continue
                snk = sinks[i] if i < len(sinks) else {}
                mapping: AnyDict = {"source": src["source"], "sink": snk.get("sink") or src["source"]}
                if snk.get("sinkSubmodel") and snk["sinkSubmodel"] != "OperationalData":
                    mapping["sinkSubmodel"] = snk["sinkSubmodel"]
                if src.get("pollingInterval"):
                    mapping["pollingInterval"] = src["pollingInterval"]
                mappings.append(mapping)
            if iface_name and mappings:
                entry["Mappings"] = mappings
                out[iface_name] = entry
    return out


def _text_of(el) -> str | None:
    """Scalar text of a Property or MultiLanguageProperty, else None."""
    if not isinstance(el, dict):
        return None
    value = el.get("value")
    if isinstance(value, list):
        return value[0].get("text") if value and isinstance(value[0], dict) else None
    return None if value is None else str(value)


def _last_key(ref_el) -> str | None:
    """Last key value of a ReferenceElement's reference."""
    value = ref_el.get("value") if isinstance(ref_el, dict) else None
    keys = value.get("keys") if isinstance(value, dict) else None
    return keys[-1].get("value") if keys else None


def _submodel_of(ref_el) -> str | None:
    """Last id segment of the submodel a ReferenceElement points into."""
    value = ref_el.get("value") if isinstance(ref_el, dict) else None
    keys = value.get("keys") if isinstance(value, dict) else None
    return str(keys[0].get("value", "")).rstrip("/").split("/")[-1] if keys else None


# idShort -> parser; each is the inverse of a builder in AAS_generation/submodels/.
_PARSER_BY_ID_SHORT = {
    "DigitalNameplate": parse_nameplate,
    "HierarchicalStructures": parse_hierarchical_structures,
    "AID": parse_aid,
    "Skills": parse_skills,
    "Capabilities": parse_capabilities,
    "OperationalData": parse_operational_data,
    "Parameters": parse_parameters,
    "TechnicalData": parse_technical_data,
    "AssetInterfacesMappingConfiguration": parse_aimc,
}


def aas_json_to_profile(json_text: str) -> AnyDict:
    """Parse full AAS environment JSON into {asset_name, base_url, selected_submodels, profile}.

    `profile` has the exact shape profile_document_to_aas_json(document, cfg)
    consumes, so the result of this function can be fed straight back into it
    (round trip, no reshaping needed on the caller's side).
    """
    data = json.loads(json_text)
    shells = data.get("assetAdministrationShells") or []
    if not shells:
        raise ValueError("AAS JSON has no assetAdministrationShells")
    shell = shells[0]

    shell_id_short = shell.get("idShort") or ""
    shell_id = shell.get("id") or ""
    asset_info = shell.get("assetInformation") or {}
    global_asset_id = asset_info.get("globalAssetId") or ""
    asset_type = asset_info.get("assetType")

    system_id = re.sub(r"_AAS$", "", shell_id_short, flags=re.IGNORECASE).strip() or shell_id_short
    base_url = _derive_base_url(shell_id)

    system_config: AnyDict = {
        "idShort": shell_id_short,
        "id": shell_id,
        "globalAssetId": global_asset_id,
    }
    if asset_type:
        system_config["assetType"] = asset_type

    selected_submodels: list[str] = []
    for sm in data.get("submodels") or []:
        id_short = sm.get("idShort")
        if not id_short:
            continue

        key = _SUBMODEL_IDSHORT_TO_KEY.get(id_short)
        if key:
            selected_submodels.append(key)

        parser = _PARSER_BY_ID_SHORT.get(id_short)
        if parser:
            # Canonical profile section, e.g. DigitalNameplate for Nameplate.
            system_config[SPEC_BY_ID_SHORT[id_short].profile_keys[0]] = parser(sm)

    return {
        "asset_name": system_id,
        "base_url": base_url,
        "selected_submodels": selected_submodels,
        "profile": {system_id: system_config},
    }
