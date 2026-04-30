"""
Convert AAS JSON to RDF/Turtle for ARSO-based validation.

"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD


AAS  = Namespace("https://admin-shell.io/aas/3/1/")
CSS  = Namespace("http://www.w3id.org/hsu-aut/css#")
ARSO = Namespace("https://w3id.org/2025/arso#")

# ---------------------------------------------------------------------------
# Semantic ID constants -- all known variants per submodel/SME type.
# Multiple variants exist because the generation pipeline and the IDTA spec
# have diverged over time. The converter recognises all of them.
# ---------------------------------------------------------------------------

# Submodel-level semantic IDs
_SM_NAMEPLATE_IDS = frozenset({
    "https://admin-shell.io/idta/nameplate/3/0/Nameplate",  # IDTA 02006-3-0 (canonical)
    "https://admin-shell.io/zvei/nameplate/2/0/Nameplate",  # ZVEI v2 (legacy pipeline)
})
_SM_HS_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel",
})
_SM_AID_IDS = frozenset({
    "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel",
})
_SM_CAPABILITIES_IDS = frozenset({
    "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0",  # ontology
    "https://admin-shell.io/idta/CapabilityDescription/1/0",                    # legacy pipeline
})
_SM_SKILLS_IDS = frozenset({
    "https://admin-shell.io/idta/ControlComponentType/1/0",           # ontology (IDTA 02015)
    "https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel",    # legacy pipeline
})
_SM_OPERATIONAL_DATA_IDS = frozenset({
    "https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel",
})
_SM_PARAMETERS_IDS = frozenset({
    "https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel",
})

# SME-level semantic IDs (nameplate elements)
_NP_MANUFACTURER_NAME_IDS = frozenset({
    "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerName",
    "0112/2///61987#ABA565#009",  # IRDI from IDTA 02006-3-0 template
})
_NP_MANUFACTURER_PRODUCT_DESIGNATION_IDS = frozenset({
    "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerProductDesignation",
    "0112/2///61987#ABA567#009",
})
_NP_CONTACT_INFORMATION_IDS = frozenset({
    "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ContactInformation",
    "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation",
})
_NP_ORDER_CODE_IDS = frozenset({
    "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/OrderCodeOfManufacturer",
    "0112/2///61987#ABA950#008",
})
_NP_URI_OF_PRODUCT_IDS = frozenset({
    "0112/2///61987#ABN590#002",
})

# SME-level semantic IDs (hierarchical structures elements)
_HS_ARCHETYPE_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0",
})
_HS_ENTRY_NODE_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0",
})
_HS_NODE_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0",
})
_HS_HAS_PART_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0",
})
_HS_IS_PART_OF_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0",
})
_HS_SAME_AS_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0",
})
_HS_BULK_COUNT_IDS = frozenset({
    "https://admin-shell.io/idta/HierarchicalStructures/BulkCount/1/0",
})

# SME-level semantic IDs (AddressInformation child elements — ECLASS IRDIs per IDTA 02002)
_NP_ADDRESS_STREET_IDS = frozenset({
    "0173-1#02-AAO128#002",
})
_NP_ADDRESS_ZIPCODE_IDS = frozenset({
    "0173-1#02-AAO129#002",
})
_NP_ADDRESS_CITY_TOWN_IDS = frozenset({
    "0173-1#02-AAO132#002",
})
_NP_ADDRESS_NATIONAL_CODE_IDS = frozenset({
    "0173-1#02-AAO134#002",
})

# SME-level semantic IDs (Capabilities elements)
_CAP_SET_IDS = frozenset({
    "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0",
})
_CAP_CONTAINER_IDS = frozenset({
    "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0",
})
_CAP_ELEMENT_IDS = frozenset({
    "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0",
})
_CAP_REALIZED_BY_IDS = frozenset({
    "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0",
})

# SME-level semantic IDs (AID elements)
_AID_INTERFACE_IDS = frozenset({
    "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface",
})
_AID_ENDPOINT_METADATA_IDS = frozenset({
    "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata",
})
_AID_INTERACTION_METADATA_IDS = frozenset({
    "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata",
})


def _build_sid_map(pairs: list[tuple[frozenset[str], URIRef]]) -> dict[str, URIRef]:
    """Flatten a list of (id_set, arso_type) pairs into a single lookup dict."""
    out: dict[str, URIRef] = {}
    for ids, arso_type in pairs:
        for sid in ids:
            out[sid] = arso_type
    return out


# Submodel-level semanticId -> ARSO subclass (all known variants)
SUBMODEL_TYPE_BY_SEMANTIC_ID: dict[str, URIRef] = _build_sid_map([
    (_SM_NAMEPLATE_IDS,        ARSO.DigitalNameplateSubmodel),
    (_SM_HS_IDS,               ARSO.HierarchicalStructuresSubmodel),
    (_SM_AID_IDS,              ARSO.AIDSubmodel),
    (_SM_CAPABILITIES_IDS,     ARSO.CapabilitiesSubmodel),
    (_SM_SKILLS_IDS,           ARSO.SkillsSubmodel),
    (_SM_OPERATIONAL_DATA_IDS, ARSO.OperationalDataSubmodel),
    (_SM_PARAMETERS_IDS,       ARSO.ParametersSubmodel),
])

# SME-level semanticId -> ARSO subclass (all known variants)
SME_TYPE_BY_SEMANTIC_ID: dict[str, URIRef] = _build_sid_map([
    (_NP_MANUFACTURER_NAME_IDS,                ARSO.ManufacturerNameMLP),
    (_NP_MANUFACTURER_PRODUCT_DESIGNATION_IDS, ARSO.ManufacturerProductDesignationMLP),
    (_NP_CONTACT_INFORMATION_IDS,              ARSO.AddressInformationSMC),
    (_NP_ORDER_CODE_IDS,                       ARSO.OrderCodeProperty),
    (_NP_URI_OF_PRODUCT_IDS,                   ARSO.URIOfTheProductProperty),
    (_NP_ADDRESS_STREET_IDS,                   ARSO.AddressStreetMLP),
    (_NP_ADDRESS_ZIPCODE_IDS,                  ARSO.AddressZipcodeMLP),
    (_NP_ADDRESS_CITY_TOWN_IDS,                ARSO.AddressCityTownMLP),
    (_NP_ADDRESS_NATIONAL_CODE_IDS,            ARSO.AddressNationalCodeMLP),
    (_HS_ARCHETYPE_IDS,                        ARSO.ArcheTypeProperty),
    (_HS_ENTRY_NODE_IDS,                       ARSO.EntryNodeEntity),
    (_HS_NODE_IDS,                             ARSO.NodeEntity),
    (_HS_HAS_PART_IDS,                         ARSO.HasPartRelationship),
    (_HS_IS_PART_OF_IDS,                       ARSO.IsPartOfRelationship),
    (_HS_SAME_AS_IDS,                          ARSO.SameAsRelationship),
    (_HS_BULK_COUNT_IDS,                       ARSO.BulkCountProperty),
    (_AID_INTERFACE_IDS,                       ARSO.InterfaceSMC),
    (_AID_ENDPOINT_METADATA_IDS,               ARSO.EndpointMetadataSMC),
    (_AID_INTERACTION_METADATA_IDS,            ARSO.InteractionMetadataSMC),
    (_CAP_SET_IDS,                             ARSO.CapabilitySetSMC),
    (_CAP_CONTAINER_IDS,                       ARSO.CapabilityContainerSMC),
    (_CAP_ELEMENT_IDS,                         ARSO.CapabilityElement),
    (_CAP_REALIZED_BY_IDS,                     ARSO.CapabilityRealizedBySML),
])

# Submodel subclass -> typed-link property on AAS shell (drives SHACL constraints)
_TYPED_LINK_BY_SUBTYPE: dict[URIRef, URIRef] = {
    ARSO.DigitalNameplateSubmodel:       ARSO.hasDigitalNameplateSubmodel,
    ARSO.HierarchicalStructuresSubmodel: ARSO.hasHierarchicalStructuresSubmodel,
    ARSO.AIDSubmodel:                    ARSO.hasAIDSubmodel,
    ARSO.CapabilitiesSubmodel:           ARSO.hasCapabilitiesSubmodel,
    ARSO.SkillsSubmodel:                 ARSO.hasSkillsSubmodel,
    ARSO.OperationalDataSubmodel:        ARSO.hasOperationalDataSubmodel,
    ARSO.ParametersSubmodel:             ARSO.hasParametersSubmodel,
}

# AAS modelType -> official AAS class IRI
_AAS_CLASS_BY_MODEL_TYPE: dict[str, URIRef] = {
    "AssetAdministrationShell":     AAS.AssetAdministrationShell,
    "Submodel":                     AAS.Submodel,
    "Property":                     AAS.Property,
    "MultiLanguageProperty":        AAS.MultiLanguageProperty,
    "SubmodelElementCollection":    AAS.SubmodelElementCollection,
    "SubmodelElementList":          AAS.SubmodelElementList,
    "ReferenceElement":             AAS.ReferenceElement,
    "RelationshipElement":          AAS.RelationshipElement,
    "AnnotatedRelationshipElement": AAS.AnnotatedRelationshipElement,
    "Entity":                       AAS.Entity,
    "File":                         AAS.File,
    "Blob":                         AAS.Blob,
    "Range":                        AAS.Range,
    "Operation":                    AAS.Operation,
    "BasicEventElement":            AAS.BasicEventElement,
    "Capability":                   AAS.Capability,
}

# Property IRIs (AAS metamodel) used for containment / values
P_SUBMODEL_ELEMENTS     = AAS["Submodel/submodelElements"]
P_SMC_VALUE             = AAS["SubmodelElementCollection/value"]
P_SML_VALUE             = AAS["SubmodelElementList/value"]
P_SML_TYPE_VALUE        = AAS["SubmodelElementList/typeValueListElement"]

# AAS enum individuals for SubmodelElementList/typeValueListElement
_SML_ELEMENT_TYPE_IRI: dict[str, URIRef] = {
    name: AAS[f"AasSubmodelElements/{name}"]
    for name in (
        "AnnotatedRelationshipElement", "BasicEventElement", "Blob", "Capability",
        "DataElement", "Entity", "EventElement", "File", "MultiLanguageProperty",
        "Operation", "Property", "Range", "ReferenceElement", "RelationshipElement",
        "SubmodelElement", "SubmodelElementCollection", "SubmodelElementList",
    )
}
P_ENTITY_STATEMENTS     = AAS["Entity/statements"]
P_ENTITY_TYPE           = AAS["Entity/entityType"]
P_ENTITY_GLOBAL_ID      = AAS["Entity/globalAssetId"]
P_HAS_SEMANTIC_ID       = AAS["HasSemantics/semanticId"]
P_HAS_SUPPL_SEMANTIC_ID = AAS["HasSemantics/supplementalSemanticIds"]
P_PROP_VALUE            = AAS["Property/value"]
P_PROP_VALUE_TYPE       = AAS["Property/valueType"]
P_MLP_VALUE             = AAS["MultiLanguageProperty/value"]
P_RANGE_MIN             = AAS["Range/min"]
P_RANGE_MAX             = AAS["Range/max"]
P_FILE_VALUE            = AAS["File/value"]
P_FILE_CONTENT_TYPE     = AAS["File/contentType"]
P_REL_FIRST             = AAS["RelationshipElement/first"]
P_REL_SECOND            = AAS["RelationshipElement/second"]
P_REF_ELEM_VALUE        = AAS["ReferenceElement/value"]
P_REFERABLE_ID_SHORT    = AAS["Referable/idShort"]
P_IDENTIFIABLE_ID       = AAS["Identifiable/id"]
P_AAS_ASSET_INFO        = AAS["AssetAdministrationShell/assetInformation"]
P_AAS_SUBMODELS         = AAS["AssetAdministrationShell/submodels"]
P_AAS_DERIVED_FROM      = AAS["AssetAdministrationShell/derivedFrom"]

P_AI_ASSET_KIND         = AAS["AssetInformation/assetKind"]
P_AI_GLOBAL_ASSET_ID    = AAS["AssetInformation/globalAssetId"]
P_AI_SPECIFIC_IDS       = AAS["AssetInformation/specificAssetIds"]
P_AI_ASSET_TYPE         = AAS["AssetInformation/assetType"]

P_SAI_NAME              = AAS["SpecificAssetId/name"]
P_SAI_VALUE             = AAS["SpecificAssetId/value"]
P_SAI_EXTERNAL          = AAS["SpecificAssetId/externalSubjectId"]

P_REF_TYPE              = AAS["Reference/type"]
P_REF_KEYS              = AAS["Reference/keys"]
P_KEY_TYPE              = AAS["Key/type"]
P_KEY_VALUE             = AAS["Key/value"]

P_LS_LANGUAGE           = AAS["AbstractLangString/language"]
P_LS_TEXT               = AAS["AbstractLangString/text"]
P_LS_TEXT_TYPED         = AAS["LangStringTextType/text"]

P_ADMIN_VERSION         = AAS["AdministrativeInformation/version"]
P_ADMIN_REVISION        = AAS["AdministrativeInformation/revision"]
P_HAS_ADMIN             = AAS["Identifiable/administration"]


def _enum_iri(enum_class: str, member: str) -> URIRef:
    return AAS[f"{enum_class}/{member}"]


def _emit_enum(g: Graph, subject: URIRef, predicate: URIRef, enum_class: str, member: str) -> None:
    """Emit an enum triple and type the enum value as its enum class (needed without OWL inference)."""
    val = _enum_iri(enum_class, member)
    g.add((subject, predicate, val))
    g.add((val, RDF.type, AAS[enum_class]))


_VALUE_TYPE_TO_AAS_DATATYPE: dict[str, URIRef] = {
    "xs:string":   AAS["DataTypeDefXsd/String"],
    "xs:boolean":  AAS["DataTypeDefXsd/Boolean"],
    "xs:int":      AAS["DataTypeDefXsd/Int"],
    "xs:integer":  AAS["DataTypeDefXsd/Integer"],
    "xs:double":   AAS["DataTypeDefXsd/Double"],
    "xs:float":    AAS["DataTypeDefXsd/Float"],
    "xs:decimal":  AAS["DataTypeDefXsd/Decimal"],
    "xs:date":     AAS["DataTypeDefXsd/Date"],
    "xs:dateTime": AAS["DataTypeDefXsd/DateTime"],
    "xs:long":     AAS["DataTypeDefXsd/Long"],
    "xs:short":    AAS["DataTypeDefXsd/Short"],
    "xs:byte":     AAS["DataTypeDefXsd/Byte"],
    "string":      AAS["DataTypeDefXsd/String"],
    "boolean":     AAS["DataTypeDefXsd/Boolean"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_local(text: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    return safe or "x"


def _semantic_ids(node: dict) -> list[str]:
    out: list[str] = []
    semantic = node.get("semanticId") if isinstance(node, dict) else None
    if isinstance(semantic, dict):
        for key in semantic.get("keys", []) or []:
            value = key.get("value") if isinstance(key, dict) else None
            if value:
                out.append(str(value))
    return out


def _first_semantic_id(node: dict) -> str | None:
    ids = _semantic_ids(node)
    return ids[0] if ids else None


def _mint_child_uri(parent: URIRef, idshort: str | None, index: int) -> URIRef:
    seg = _safe_local(idshort) if idshort else f"item-{index}"
    sep = "/" if "#" in str(parent) else "#"
    return URIRef(f"{parent}{sep}{seg}")


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

_BNODE_COUNTER = [0]


def _next_anon(parent: URIRef, kind: str) -> URIRef:
    _BNODE_COUNTER[0] += 1
    sep = "/" if "#" in str(parent) else "#"
    return URIRef(f"{parent}{sep}_{kind}-{_BNODE_COUNTER[0]}")


def _emit_referable(g: Graph, node_uri: URIRef, node: dict) -> None:
    idshort = node.get("idShort")
    if idshort:
        g.add((node_uri, P_REFERABLE_ID_SHORT, Literal(str(idshort), datatype=XSD.string)))
        g.add((node_uri, RDFS.label, Literal(str(idshort))))


def _emit_reference(g: Graph, parent_uri: URIRef, predicate: URIRef, ref: dict | None) -> URIRef | None:
    if not isinstance(ref, dict):
        return None
    keys = ref.get("keys") or []
    if not keys:
        return None

    ref_uri = _next_anon(parent_uri, "ref")
    g.add((parent_uri, predicate, ref_uri))
    g.add((ref_uri, RDF.type, AAS.Reference))

    ref_type = ref.get("type") or "ExternalReference"
    _emit_enum(g, ref_uri, P_REF_TYPE, "ReferenceTypes", str(ref_type))

    for key in keys:
        if not isinstance(key, dict):
            continue
        key_type = key.get("type")
        key_value = key.get("value")
        if key_value is None:
            continue
        key_uri = _next_anon(ref_uri, "key")
        g.add((ref_uri, P_REF_KEYS, key_uri))
        g.add((key_uri, RDF.type, AAS.Key))
        if key_type:
            _emit_enum(g, key_uri, P_KEY_TYPE, "KeyTypes", str(key_type))
        g.add((key_uri, P_KEY_VALUE, Literal(str(key_value), datatype=XSD.string)))
    return ref_uri


def _emit_semantic_id(g: Graph, node_uri: URIRef, node: dict) -> None:
    semantic = node.get("semanticId") if isinstance(node, dict) else None
    if isinstance(semantic, dict):
        _emit_reference(g, node_uri, P_HAS_SEMANTIC_ID, semantic)
    for suppl in node.get("supplementalSemanticIds", []) or []:
        if isinstance(suppl, dict):
            _emit_reference(g, node_uri, P_HAS_SUPPL_SEMANTIC_ID, suppl)
    for sid in _semantic_ids(node):
        sme_subtype = SME_TYPE_BY_SEMANTIC_ID.get(sid)
        if sme_subtype is not None:
            g.add((node_uri, RDF.type, sme_subtype))


def _emit_property_value(g: Graph, node_uri: URIRef, node: dict) -> None:
    value = node.get("value")
    value_type = node.get("valueType")
    if value_type:
        dt = _VALUE_TYPE_TO_AAS_DATATYPE.get(str(value_type))
        if dt is not None:
            g.add((node_uri, P_PROP_VALUE_TYPE, dt))
            g.add((dt, RDF.type, AAS.DataTypeDefXsd))
        else:
            g.add((node_uri, P_PROP_VALUE_TYPE, Literal(str(value_type))))
    # AAS metamodel: Property/value is always xs:string; valueType is a separate predicate.
    if value is not None and value != "":
        g.add((node_uri, P_PROP_VALUE, Literal(str(value), datatype=XSD.string)))


def _emit_mlp_value(g: Graph, node_uri: URIRef, node: dict) -> None:
    value = node.get("value")
    if not isinstance(value, list):
        return
    for entry in value:
        if not isinstance(entry, dict):
            continue
        text = entry.get("text")
        if not text:
            continue
        lang = entry.get("language") or "en"
        ls_uri = _next_anon(node_uri, "lang")
        g.add((node_uri, P_MLP_VALUE, ls_uri))
        g.add((ls_uri, RDF.type, AAS.LangStringTextType))
        g.add((ls_uri, P_LS_LANGUAGE, Literal(str(lang), datatype=XSD.string)))
        g.add((ls_uri, P_LS_TEXT, Literal(str(text), datatype=XSD.string)))
        g.add((ls_uri, P_LS_TEXT_TYPED, Literal(str(text), datatype=XSD.string)))


def _emit_range_value(g: Graph, node_uri: URIRef, node: dict) -> None:
    if "min" in node and node["min"] is not None:
        g.add((node_uri, P_RANGE_MIN, Literal(str(node["min"]), datatype=XSD.string)))
    if "max" in node and node["max"] is not None:
        g.add((node_uri, P_RANGE_MAX, Literal(str(node["max"]), datatype=XSD.string)))
    value_type = node.get("valueType")
    if value_type:
        dt = _VALUE_TYPE_TO_AAS_DATATYPE.get(str(value_type))
        if dt is not None:
            g.add((node_uri, P_PROP_VALUE_TYPE, dt))
            g.add((dt, RDF.type, AAS.DataTypeDefXsd))


def _emit_file_value(g: Graph, node_uri: URIRef, node: dict) -> None:
    value = node.get("value")
    if value:
        g.add((node_uri, P_FILE_VALUE, Literal(str(value), datatype=XSD.string)))
    content_type = node.get("contentType")
    if content_type:
        g.add((node_uri, P_FILE_CONTENT_TYPE, Literal(str(content_type), datatype=XSD.string)))


def _emit_relationship(g: Graph, node_uri: URIRef, node: dict) -> None:
    _emit_reference(g, node_uri, P_REL_FIRST, node.get("first"))
    _emit_reference(g, node_uri, P_REL_SECOND, node.get("second"))


def _emit_reference_element(g: Graph, node_uri: URIRef, node: dict) -> None:
    _emit_reference(g, node_uri, P_REF_ELEM_VALUE, node.get("value"))


def _emit_entity(g: Graph, node_uri: URIRef, node: dict) -> None:
    entity_type = node.get("entityType")
    if entity_type:
        _emit_enum(g, node_uri, P_ENTITY_TYPE, "EntityType", str(entity_type))
    global_asset_id = node.get("globalAssetId")
    if global_asset_id:
        g.add((node_uri, P_ENTITY_GLOBAL_ID, Literal(str(global_asset_id), datatype=XSD.string)))


def _emit_administration(g: Graph, node_uri: URIRef, node: dict) -> None:
    admin = node.get("administration")
    if not isinstance(admin, dict):
        return
    admin_uri = _next_anon(node_uri, "admin")
    g.add((node_uri, P_HAS_ADMIN, admin_uri))
    g.add((admin_uri, RDF.type, AAS.AdministrativeInformation))
    if admin.get("version"):
        g.add((admin_uri, P_ADMIN_VERSION, Literal(str(admin["version"]), datatype=XSD.string)))
    if admin.get("revision"):
        g.add((admin_uri, P_ADMIN_REVISION, Literal(str(admin["revision"]), datatype=XSD.string)))


def _emit_asset_information(g: Graph, shell_uri: URIRef, asset_info: dict) -> URIRef | None:
    if not isinstance(asset_info, dict):
        return None
    ai_uri = _next_anon(shell_uri, "assetInformation")
    g.add((shell_uri, P_AAS_ASSET_INFO, ai_uri))
    g.add((ai_uri, RDF.type, AAS.AssetInformation))

    asset_kind = asset_info.get("assetKind") or "Instance"
    _emit_enum(g, ai_uri, P_AI_ASSET_KIND, "AssetKind", str(asset_kind))

    if asset_info.get("globalAssetId"):
        g.add((ai_uri, P_AI_GLOBAL_ASSET_ID, Literal(str(asset_info["globalAssetId"]), datatype=XSD.string)))
    if asset_info.get("assetType"):
        g.add((ai_uri, P_AI_ASSET_TYPE, Literal(str(asset_info["assetType"]), datatype=XSD.string)))

    for sai in asset_info.get("specificAssetIds", []) or []:
        if not isinstance(sai, dict):
            continue
        sai_uri = _next_anon(ai_uri, "specificAssetId")
        g.add((ai_uri, P_AI_SPECIFIC_IDS, sai_uri))
        g.add((sai_uri, RDF.type, AAS.SpecificAssetId))
        if sai.get("name"):
            g.add((sai_uri, P_SAI_NAME, Literal(str(sai["name"]), datatype=XSD.string)))
        if sai.get("value"):
            g.add((sai_uri, P_SAI_VALUE, Literal(str(sai["value"]), datatype=XSD.string)))
        external = sai.get("externalSubjectId")
        if isinstance(external, dict):
            _emit_reference(g, sai_uri, P_SAI_EXTERNAL, external)
    return ai_uri


def _walk_element(g: Graph, parent_uri: URIRef, parent_container_prop: URIRef,
                  element: dict, index: int) -> None:
    if not isinstance(element, dict):
        return

    idshort = element.get("idShort")
    elem_uri = _mint_child_uri(parent_uri, idshort, index)
    g.add((parent_uri, parent_container_prop, elem_uri))

    model_type = element.get("modelType")
    aas_class = _AAS_CLASS_BY_MODEL_TYPE.get(model_type or "")
    if aas_class is not None:
        g.add((elem_uri, RDF.type, aas_class))


    _emit_referable(g, elem_uri, element)
    _emit_semantic_id(g, elem_uri, element)

    if model_type == "Property":
        _emit_property_value(g, elem_uri, element)
    elif model_type == "MultiLanguageProperty":
        _emit_mlp_value(g, elem_uri, element)
    elif model_type == "Range":
        _emit_range_value(g, elem_uri, element)
    elif model_type == "File":
        _emit_file_value(g, elem_uri, element)
    elif model_type == "RelationshipElement":
        _emit_relationship(g, elem_uri, element)
    elif model_type == "AnnotatedRelationshipElement":
        _emit_relationship(g, elem_uri, element)
        for i, child in enumerate(element.get("annotations", []) or []):
            _walk_element(g, elem_uri, P_SMC_VALUE, child, i)
    elif model_type == "ReferenceElement":
        _emit_reference_element(g, elem_uri, element)
    elif model_type == "SubmodelElementCollection":
        for i, child in enumerate(element.get("value", []) or []):
            _walk_element(g, elem_uri, P_SMC_VALUE, child, i)
    elif model_type == "SubmodelElementList":
        tvle = element.get("typeValueListElement")
        if tvle and tvle in _SML_ELEMENT_TYPE_IRI:
            tvle_iri = _SML_ELEMENT_TYPE_IRI[tvle]
            g.add((elem_uri, P_SML_TYPE_VALUE, tvle_iri))
            g.add((tvle_iri, RDF.type, AAS.AasSubmodelElements))
        for i, child in enumerate(element.get("value", []) or []):
            _walk_element(g, elem_uri, P_SML_VALUE, child, i)
    elif model_type == "Entity":
        _emit_entity(g, elem_uri, element)
        for i, child in enumerate(element.get("statements", []) or []):
            _walk_element(g, elem_uri, P_ENTITY_STATEMENTS, child, i)


def _apply_structural_typing(g: Graph) -> None:
    """Add ARSO types that depend on element position/modelType rather than semanticId.

    Called once after all elements are walked.  Covers three patterns:
    1. aas:Capability instances → always arso:CapabilityElement
    2. Children of arso:InterfaceSMC typed by idShort
    3. Children of arso:EndpointMetadataSMC typed by idShort
    """
    # 1. All Capability elements → arso:CapabilityElement
    for cap_uri in list(g.subjects(RDF.type, AAS.Capability)):
        g.add((cap_uri, RDF.type, ARSO.CapabilityElement))

    # 2+3. idShort-based typing for AID child elements
    _IDSHORT_TYPE_BY_PARENT: dict[URIRef, dict[str, URIRef]] = {
        ARSO.InterfaceSMC: {
            "title":   ARSO.InterfaceTitleProperty,
        },
        ARSO.EndpointMetadataSMC: {
            "base":                  ARSO.EndpointBaseProperty,
            "contentType":           ARSO.ContentTypeProperty,
            "securityDefinitions":   ARSO.SecurityDefinitionsSMC,
            "security":              ARSO.SecuritySML,
        },
    }

    for parent_arso_type, idshort_map in _IDSHORT_TYPE_BY_PARENT.items():
        for parent_uri in g.subjects(RDF.type, parent_arso_type):
            for child_uri in g.objects(parent_uri, P_SMC_VALUE):
                id_short_vals = list(g.objects(child_uri, P_REFERABLE_ID_SHORT))
                if not id_short_vals:
                    continue
                id_short = str(id_short_vals[0])
                arso_type = idshort_map.get(id_short)
                if arso_type is not None:
                    g.add((child_uri, RDF.type, arso_type))

    # CCType containers: type the three mandatory top-level SMCs of SkillsSubmodel
    # by idShort (they use P_SUBMODEL_ELEMENTS, not P_SMC_VALUE).
    _CC_CONTAINER_TYPES = {
        "Interfaces": ARSO.CCInterfacesSMC,
        "Skills":     ARSO.CCSkillsSMC,
        "Errors":     ARSO.CCErrorsSMC,
    }
    for sm_uri in g.subjects(RDF.type, ARSO.SkillsSubmodel):
        for child_uri in g.objects(sm_uri, P_SUBMODEL_ELEMENTS):
            id_short_vals = list(g.objects(child_uri, P_REFERABLE_ID_SHORT))
            if not id_short_vals:
                continue
            arso_type = _CC_CONTAINER_TYPES.get(str(id_short_vals[0]))
            if arso_type is not None:
                g.add((child_uri, RDF.type, arso_type))

    # SecuritySchemeSMC: every direct child of SecurityDefinitionsSMC is a scheme SMC
    for sec_def_uri in g.subjects(RDF.type, ARSO.SecurityDefinitionsSMC):
        for scheme_uri in g.objects(sec_def_uri, P_SMC_VALUE):
            g.add((scheme_uri, RDF.type, ARSO.SecuritySchemeSMC))

    # SchemeProperty: the "scheme" Property inside any SecuritySchemeSMC
    for scheme_smc_uri in g.subjects(RDF.type, ARSO.SecuritySchemeSMC):
        for child_uri in g.objects(scheme_smc_uri, P_SMC_VALUE):
            id_short_vals = list(g.objects(child_uri, P_REFERABLE_ID_SHORT))
            if id_short_vals and str(id_short_vals[0]) == "scheme":
                g.add((child_uri, RDF.type, ARSO.SchemeProperty))


def _walk_submodel(g: Graph, shell_uri: URIRef, submodel: dict) -> URIRef | None:
    submodel_id = submodel.get("id")
    if not submodel_id:
        return None

    sm_uri = URIRef(submodel_id)
    g.add((sm_uri, RDF.type, AAS.Submodel))
    g.add((sm_uri, P_IDENTIFIABLE_ID, Literal(submodel_id, datatype=XSD.string)))
    _emit_referable(g, sm_uri, submodel)
    _emit_semantic_id(g, sm_uri, submodel)
    _emit_administration(g, sm_uri, submodel)

    sid = _first_semantic_id(submodel)
    subtype = SUBMODEL_TYPE_BY_SEMANTIC_ID.get(sid) if sid else None
    if subtype is not None:
        g.add((sm_uri, RDF.type, subtype))
        g.add((shell_uri, ARSO.hasSubmodel, sm_uri))
        typed_link = _TYPED_LINK_BY_SUBTYPE.get(subtype)
        if typed_link is not None:
            g.add((shell_uri, typed_link, sm_uri))
    else:
        g.add((shell_uri, ARSO.hasSubmodel, sm_uri))

    for i, element in enumerate(submodel.get("submodelElements", []) or []):
        _walk_element(g, sm_uri, P_SUBMODEL_ELEMENTS, element, i)

    return sm_uri


def _walk_shell(g: Graph, shell: dict, submodels_by_id: dict[str, dict]) -> None:
    shell_id = shell.get("id")
    if not shell_id:
        return

    shell_uri = URIRef(shell_id)
    g.add((shell_uri, RDF.type, AAS.AssetAdministrationShell))
    g.add((shell_uri, P_IDENTIFIABLE_ID, Literal(shell_id, datatype=XSD.string)))
    _emit_referable(g, shell_uri, shell)
    _emit_administration(g, shell_uri, shell)

    asset_info = shell.get("assetInformation") or {}
    if isinstance(asset_info, dict):
        _emit_asset_information(g, shell_uri, asset_info)
    global_asset_id = asset_info.get("globalAssetId") if isinstance(asset_info, dict) else None
    resource_iri = global_asset_id or f"{shell_id}#asset"
    resource_uri = URIRef(resource_iri)
    g.add((resource_uri, RDF.type, CSS.Resource))
    g.add((shell_uri, ARSO.representsResource, resource_uri))
    g.add((resource_uri, ARSO.hasAAS, shell_uri))

    if isinstance(shell.get("derivedFrom"), dict):
        _emit_reference(g, shell_uri, P_AAS_DERIVED_FROM, shell["derivedFrom"])

    for ref in shell.get("submodels", []) or []:
        if isinstance(ref, dict):
            _emit_reference(g, shell_uri, P_AAS_SUBMODELS, ref)
        keys = ref.get("keys", []) if isinstance(ref, dict) else []
        if not keys:
            continue
        target_id = keys[-1].get("value") if isinstance(keys[-1], dict) else None
        if not target_id:
            continue
        submodel = submodels_by_id.get(str(target_id))
        if submodel:
            _walk_submodel(g, shell_uri, submodel)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize(document: dict) -> Graph:
    """Build an RDF graph from a parsed AAS JSON document."""
    _BNODE_COUNTER[0] = 0
    g = Graph()
    g.bind("aas",  AAS)
    g.bind("css",  CSS)
    g.bind("arso", ARSO)
    g.bind("xsd",  XSD)
    g.bind("rdfs", RDFS)

    submodels = document.get("submodels", []) or []
    submodels_by_id: dict[str, dict] = {}
    for sm in submodels:
        if isinstance(sm, dict) and sm.get("id"):
            submodels_by_id[str(sm["id"])] = sm

    for shell in document.get("assetAdministrationShells", []) or []:
        if isinstance(shell, dict):
            _walk_shell(g, shell, submodels_by_id)

    referenced: set[str] = set()
    for shell in document.get("assetAdministrationShells", []) or []:
        for ref in (shell or {}).get("submodels", []) or []:
            keys = ref.get("keys", []) if isinstance(ref, dict) else []
            if keys and isinstance(keys[-1], dict):
                value = keys[-1].get("value")
                if value:
                    referenced.add(str(value))
    for sm_id, sm in submodels_by_id.items():
        if sm_id in referenced:
            continue
        sm_uri = URIRef(sm_id)
        g.add((sm_uri, RDF.type, AAS.Submodel))
        g.add((sm_uri, P_IDENTIFIABLE_ID, Literal(sm_id, datatype=XSD.string)))
        _emit_referable(g, sm_uri, sm)
        _emit_semantic_id(g, sm_uri, sm)
        _emit_administration(g, sm_uri, sm)
        sid = _first_semantic_id(sm)
        subtype = SUBMODEL_TYPE_BY_SEMANTIC_ID.get(sid) if sid else None
        if subtype is not None:
            g.add((sm_uri, RDF.type, subtype))
        for i, element in enumerate(sm.get("submodelElements", []) or []):
            _walk_element(g, sm_uri, P_SUBMODEL_ELEMENTS, element, i)

    _apply_structural_typing(g)
    return g


def convert(aas_json_path: Path, output_ttl_path: Path) -> None:
    """Read AAS JSON from aas_json_path, write Turtle RDF to output_ttl_path."""
    with open(aas_json_path, "r", encoding="utf-8") as fh:
        document = json.load(fh)
    g = serialize(document)
    output_ttl_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_ttl_path), format="turtle")


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serialize AAS JSON to RDF aligned with ARSO_AAS.ttl.")
    parser.add_argument("--input",  required=True, help="Path to AAS JSON.")
    parser.add_argument("--output", required=True, help="Path to output Turtle file.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    convert(Path(args.input), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
