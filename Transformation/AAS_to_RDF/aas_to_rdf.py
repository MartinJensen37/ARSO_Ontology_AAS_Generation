"""
Convert AAS JSON to RDF/Turtle for ARSO-based validation.

"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD


AAS  = Namespace("https://admin-shell.io/aas/3/1/")
CSS  = Namespace("http://www.w3id.org/hsu-aut/css#")
ARSO = Namespace("https://w3id.org/2025/arso#")

# ---------------------------------------------------------------------------
# Ontology-driven typing.
#
# Everything the converter needs to know about *which* semanticId or
# structural position identifies *which* ARSO class is read directly out of
# the ontology (via the arso:semanticId / arso:idShort / arso:parentClass /
# arso:transitiveParentClass / arso:unconditionalAasType annotations declared
# on each class -- see Ontology/ARSO/ARSO_AAS.ttl) rather than hand-copied
# into Python. Adding a new submodel or element type that follows this
# annotation convention needs no change here.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ONTOLOGY_DIR = _REPO_ROOT / "Ontology"
_ARSO_AAS_TTL = _ONTOLOGY_DIR / "ARSO" / "ARSO_AAS.ttl"
_AAS_RDF_TTL = _ONTOLOGY_DIR / "AAS" / "aas-rdf-ontology.ttl"
_CSS_TTL = _ONTOLOGY_DIR / "CSS" / "CSS-Ontology.ttl"

# External (non-ARSO-module) owl:imports that aren't reachable by relative
# path guessing -- mirrors the catalog in Validation/Validator/validator.py
# and Transformation/Generate_Shapes/generate_shapes.py.
_EXTERNAL_IMPORT_CATALOG: dict[str, Path] = {
    "https://admin-shell.io/aas/3/1/": _AAS_RDF_TTL,
    "https://admin-shell.io/aas/3/1":  _AAS_RDF_TTL,
    "http://admin-shell.io/aas/3/1/":  _AAS_RDF_TTL,
    "http://www.w3id.org/hsu-aut/css": _CSS_TTL,
    "http://www.w3id.org/hsu-aut/css/": _CSS_TTL,
}

ARSO_SEMANTIC_ID              = ARSO["semanticId"]
ARSO_ID_SHORT                 = ARSO["idShort"]
ARSO_PARENT_CLASS             = ARSO["parentClass"]
ARSO_TRANSITIVE_PARENT_CLASS  = ARSO["transitiveParentClass"]
ARSO_UNCONDITIONAL_AAS_TYPE   = ARSO["unconditionalAasType"]
ARSO_HAS_SUBMODEL             = ARSO["hasSubmodel"]


def _resolve_ontology_import(import_uri: str, parent_file: Path) -> Path | None:
    canon = import_uri.rstrip("/")
    if import_uri in _EXTERNAL_IMPORT_CATALOG:
        return _EXTERNAL_IMPORT_CATALOG[import_uri]
    if canon in _EXTERNAL_IMPORT_CATALOG:
        return _EXTERNAL_IMPORT_CATALOG[canon]
    parsed = urlparse(import_uri)
    if parsed.scheme in ("http", "https"):
        # ARSO module imports (e.g. .../modules/nameplate) carry no file
        # extension; the AAS/CSS externals above are caught by the catalog.
        last_segment = Path(parsed.path).name
        ttl_name = last_segment if last_segment.endswith(".ttl") else f"{last_segment}.ttl"
        for candidate in (
            parent_file.parent / ttl_name,
            parent_file.parent / "Modules" / ttl_name,
            parent_file.parent.parent / "Modules" / ttl_name,
        ):
            resolved = candidate.resolve()
            if resolved.exists():
                return resolved
    return None


def _load_ontology_with_imports(target: Graph, ontology_file: Path, visited: set[Path]) -> None:
    resolved = ontology_file.resolve()
    if resolved in visited or not resolved.exists():
        return
    visited.add(resolved)
    sub_graph = Graph().parse(str(resolved), format="turtle")
    target += sub_graph
    for _, _, imported in sub_graph.triples((None, OWL.imports, None)):
        local = _resolve_ontology_import(str(imported), resolved)
        if local is not None:
            _load_ontology_with_imports(target, local, visited)


_ONTOLOGY_GRAPH_CACHE: Graph | None = None


def _ontology_graph() -> Graph:
    """Load and cache ARSO_AAS.ttl plus every module/base ontology it imports."""
    global _ONTOLOGY_GRAPH_CACHE
    if _ONTOLOGY_GRAPH_CACHE is None:
        g = Graph()
        _load_ontology_with_imports(g, _ARSO_AAS_TTL, set())
        _ONTOLOGY_GRAPH_CACHE = g
    return _ONTOLOGY_GRAPH_CACHE


def _subclass_closure(ontology_g: Graph, cls: URIRef) -> Iterable[URIRef]:
    """Yield cls and every class it transitively rdfs:subClassOf, in the ontology graph."""
    stack = [cls]
    seen: set[URIRef] = set()
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        yield current
        for parent in ontology_g.objects(current, RDFS.subClassOf):
            if isinstance(parent, URIRef):
                stack.append(parent)


def _is_submodel_class(ontology_g: Graph, cls: URIRef) -> bool:
    return AAS.Submodel in _subclass_closure(ontology_g, cls)


_CONTAINMENT_PROP_BY_AAS_BASE: dict[URIRef, URIRef] = {
    AAS.Submodel:                  AAS["Submodel/submodelElements"],
    AAS.SubmodelElementCollection: AAS["SubmodelElementCollection/value"],
    AAS.SubmodelElementList:       AAS["SubmodelElementList/value"],
    AAS.Entity:                    AAS["Entity/statements"],
}


def _containment_prop_for(ontology_g: Graph, cls: URIRef) -> URIRef | None:
    """The AAS containment property (submodelElements/value/statements) through
    which direct children of an RDF node typed `cls` are reached, derived from
    which of the four base AAS container types `cls` is a subclass of."""
    for ancestor in _subclass_closure(ontology_g, cls):
        prop = _CONTAINMENT_PROP_BY_AAS_BASE.get(ancestor)
        if prop is not None:
            return prop
    return None


def _direct_aas_supertype(ontology_g: Graph, cls: URIRef) -> URIRef | None:
    """The nearest ancestor of `cls` that is itself in the AAS namespace
    (e.g. the official aas:Operation for arso:SkillOperationElement)."""
    for ancestor in _subclass_closure(ontology_g, cls):
        if str(ancestor).startswith(str(AAS)):
            return ancestor
    return None


def _build_semantic_id_maps(ontology_g: Graph) -> tuple[dict[str, URIRef], dict[str, URIRef]]:
    """Submodel-level and element-level semanticId -> ARSO class, read from
    every `arso:semanticId` annotation in the ontology."""
    submodel_map: dict[str, URIRef] = {}
    element_map: dict[str, URIRef] = {}
    for cls, _, value in ontology_g.triples((None, ARSO_SEMANTIC_ID, None)):
        if not isinstance(cls, URIRef):
            continue
        target = submodel_map if _is_submodel_class(ontology_g, cls) else element_map
        target[str(value)] = cls
    return submodel_map, element_map


def _build_typed_link_map(ontology_g: Graph) -> dict[URIRef, URIRef]:
    """Submodel-subclass -> typed arso:hasXSubmodel link property on the AAS
    shell, derived from each such property's declared rdfs:range."""
    out: dict[URIRef, URIRef] = {}
    for prop, _, submodel_cls in ontology_g.triples((None, RDFS.range, None)):
        if (prop, RDFS.subPropertyOf, ARSO_HAS_SUBMODEL) in ontology_g:
            out[submodel_cls] = prop
    return out


class _StructuralRules:
    """Ontology-derived rules driving `_apply_structural_typing`.

    direct / transitive: {(parent_cls, idshort_or_None): child_cls}. A None
    idshort means "apply unconditionally to every matching child of that
    parent" (see arso:parentClass's doc comment in ARSO_AAS.ttl).
    unconditional_aas_type: {aas_base_cls: arso_cls}, from arso:unconditionalAasType.
    """

    def __init__(self, ontology_g: Graph) -> None:
        self.direct: dict[tuple[URIRef, str | None], URIRef] = {}
        self.transitive: dict[tuple[URIRef, str | None], URIRef] = {}
        self.unconditional_aas_type: dict[URIRef, URIRef] = {}

        for child, _, parent in ontology_g.triples((None, ARSO_PARENT_CLASS, None)):
            idshorts = list(ontology_g.objects(child, ARSO_ID_SHORT))
            self.direct[(parent, str(idshorts[0]) if idshorts else None)] = child
        for child, _, parent in ontology_g.triples((None, ARSO_TRANSITIVE_PARENT_CLASS, None)):
            idshorts = list(ontology_g.objects(child, ARSO_ID_SHORT))
            self.transitive[(parent, str(idshorts[0]) if idshorts else None)] = child
        for child, _, aas_cls in ontology_g.triples((None, ARSO_UNCONDITIONAL_AAS_TYPE, None)):
            self.unconditional_aas_type[aas_cls] = child


_ONTOLOGY = _ontology_graph()
SUBMODEL_TYPE_BY_SEMANTIC_ID, SME_TYPE_BY_SEMANTIC_ID = _build_semantic_id_maps(_ONTOLOGY)
_TYPED_LINK_BY_SUBTYPE: dict[URIRef, URIRef] = _build_typed_link_map(_ONTOLOGY)
_STRUCTURAL_RULES = _StructuralRules(_ONTOLOGY)

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


_ALL_CONTAINMENT_PROPS: tuple[URIRef, ...] = (
    P_SUBMODEL_ELEMENTS, P_SMC_VALUE, P_SML_VALUE, P_ENTITY_STATEMENTS,
)


def _transitive_descendants(g: Graph, node: URIRef) -> Iterable[URIRef]:
    """Every node transitively reachable from `node` via any AAS containment
    property (submodelElements / SMC-value / SML-value / Entity-statements)."""
    stack = [node]
    seen: set[URIRef] = set()
    while stack:
        current = stack.pop()
        for prop in _ALL_CONTAINMENT_PROPS:
            for child in g.objects(current, prop):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
                    yield child


def _idshort_of(g: Graph, node: URIRef) -> str | None:
    values = list(g.objects(node, P_REFERABLE_ID_SHORT))
    return str(values[0]) if values else None


def _apply_structural_typing(g: Graph) -> None:
    """Add ARSO types that depend on element position/modelType rather than
    semanticId, entirely from the ontology-derived rules in _STRUCTURAL_RULES
    (see the arso:parentClass / arso:transitiveParentClass /
    arso:unconditionalAasType annotations in the ontology modules)."""

    # 1. Unconditional-AAS-type rules (e.g. every aas:Capability -> arso:CapabilityElement).
    #    Safe only for AAS modelTypes specific to one concept -- see
    #    arso:unconditionalAasType's doc comment in ARSO_AAS.ttl.
    for aas_cls, arso_cls in _STRUCTURAL_RULES.unconditional_aas_type.items():
        for node in list(g.subjects(RDF.type, aas_cls)):
            g.add((node, RDF.type, arso_cls))

    # 2. Direct-child rules, run to a fixpoint: typing a child can make it the
    #    parent for a subsequent rule (e.g. CCInterfacesSMC -> CCInterfaceSMC
    #    -> CCInterfaceReferenceRef is two direct-child hops deep).
    changed = True
    while changed:
        changed = False
        for (parent_cls, idshort), child_cls in _STRUCTURAL_RULES.direct.items():
            containment_prop = _containment_prop_for(_ONTOLOGY, parent_cls)
            if containment_prop is None:
                continue
            # Without an idShort anchor, still require the child's own official
            # AAS modelType to match child_cls's declared AAS supertype, so an
            # unconditional rule can't swallow unrelated siblings of a
            # different modelType (e.g. a SubmodelElementCollection sibling
            # of the intended Property).
            base_aas_type = None if idshort is not None else _direct_aas_supertype(_ONTOLOGY, child_cls)
            for parent_node in list(g.subjects(RDF.type, parent_cls)):
                for child_node in g.objects(parent_node, containment_prop):
                    if (child_node, RDF.type, child_cls) in g:
                        continue
                    if idshort is not None:
                        if _idshort_of(g, child_node) != idshort:
                            continue
                    elif base_aas_type is not None:
                        if (child_node, RDF.type, base_aas_type) not in g:
                            continue
                    g.add((child_node, RDF.type, child_cls))
                    changed = True

    # 3. Transitive rules, for the rare case where the real containment path
    #    passes through an intermediate node the converter doesn't otherwise
    #    type (e.g. a flat Skill SMC holding an Operation directly, rather
    #    than the full nested CCType Interfaces/Skills/Errors structure).
    #    Without an idShort anchor, disambiguation falls back to the child's
    #    own official AAS modelType (e.g. aas:Operation).
    for (parent_cls, idshort), child_cls in _STRUCTURAL_RULES.transitive.items():
        base_aas_type = None if idshort is not None else _direct_aas_supertype(_ONTOLOGY, child_cls)
        for parent_node in list(g.subjects(RDF.type, parent_cls)):
            for descendant in list(_transitive_descendants(g, parent_node)):
                if idshort is not None:
                    if _idshort_of(g, descendant) != idshort:
                        continue
                elif base_aas_type is not None:
                    if (descendant, RDF.type, base_aas_type) not in g:
                        continue
                g.add((descendant, RDF.type, child_cls))


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
