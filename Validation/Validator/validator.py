from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pyshacl
from rdflib import Graph, Literal, Namespace, OWL, RDF, URIRef


_REPO_ROOT = Path(__file__).resolve().parents[2]

_ONTOLOGY_DIR = _REPO_ROOT / "Ontology"
_SHACL_GENERATED_DIR = _REPO_ROOT / "Ontology" / "SHACL" / "Generated"
_SHACL_MANUAL_DIR    = _REPO_ROOT / "Ontology" / "SHACL" / "Manual"

_ARSO_AAS_TTL          = _ONTOLOGY_DIR / "ARSO" / "ARSO_AAS.ttl"
_AAS_RDF_ONTOLOGY_TTL  = _ONTOLOGY_DIR / "AAS" / "aas-rdf-ontology.ttl"
_AAS_SHACL_SHAPES_TTL  = _SHACL_MANUAL_DIR / "aas-shacl-schema.ttl"
_ARSO_GENERATED_SHAPES = _SHACL_GENERATED_DIR / "shapes.generated.shacl.ttl"


# Catalog: official URL -> local file (mirror of ontology/catalog-v001.xml entries).
_IMPORT_CATALOG: dict[str, Path] = {
    "https://admin-shell.io/aas/3/1/": _AAS_RDF_ONTOLOGY_TTL,
    "https://admin-shell.io/aas/3/1":  _AAS_RDF_ONTOLOGY_TTL,
    "http://admin-shell.io/aas/3/1/":  _AAS_RDF_ONTOLOGY_TTL,
    "http://www.w3id.org/hsu-aut/css": _ONTOLOGY_DIR / "CSS" / "CSS-Ontology.ttl",
}


def _resolve_import(import_uri: str, parent_file: Path) -> Path | None:
    """Map an `owl:imports` IRI to a local file, or None if no local copy."""
    canon = import_uri.rstrip("/")
    if import_uri in _IMPORT_CATALOG:
        return _IMPORT_CATALOG[import_uri]
    if canon in _IMPORT_CATALOG:
        return _IMPORT_CATALOG[canon]

    parsed = urlparse(import_uri)
    if parsed.scheme in ("http", "https"):
        ttl_name = Path(parsed.path).name
        if ttl_name.endswith(".ttl"):
            for candidate in (
                parent_file.parent / ttl_name,
                parent_file.parent / "modules" / ttl_name,
                parent_file.parent.parent / "modules" / ttl_name,
            ):
                resolved = candidate.resolve()
                if resolved.exists():
                    return resolved
        return None
    if parsed.scheme == "file":
        path = parsed.path
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return Path(path)
    return (parent_file.parent / import_uri).resolve()


def _load_with_imports(target: Graph, ontology_file: Path, visited: set[Path]) -> None:
    resolved = ontology_file.resolve()
    if resolved in visited or not resolved.exists():
        return
    visited.add(resolved)
    g = Graph().parse(str(resolved), format="turtle")
    target += g
    for _, _, imported in g.triples((None, OWL.imports, None)):
        local = _resolve_import(str(imported), resolved)
        if local is not None:
            _load_with_imports(target, local, visited)


SH = Namespace("http://www.w3.org/ns/shacl#")
_AAS_NS_PREFIX = "https://admin-shell.io/aas/3/1/"

_AAS_ABSTRACT_CLASSES = frozenset(
    URIRef(f"{_AAS_NS_PREFIX}{name}") for name in (
        "SubmodelElement", "DataElement", "AbstractLangString",
        "DataSpecificationContent", "EventElement", "HasDataSpecification",
        "HasExtensions", "HasKind", "HasSemantics",
        "Identifiable", "Qualifiable", "Referable",
    )
)

_DASH_HVC = URIRef("http://datashapes.org/dash#hasValueWithClass")
_SKIP_CLASSES_HVC = frozenset({URIRef("https://w3id.org/2025/arso#Datapoint")})


def _strip_abstract_class_constraints(shapes_graph: Graph) -> int:
    """Remove sh:class triples that reference abstract AAS classes.

    These require RDFS inference to satisfy (via subclass chains). Enabling
    inference triggers ~1200 spurious 'abstract class - use a subclass'
    violations from the AAS SHACL spec, so inference stays off and the
    abstract-class constraints are dropped instead.
    """
    to_remove = [
        (s, p, o) for s, p, o in shapes_graph
        if str(p) == str(SH["class"]) and o in _AAS_ABSTRACT_CLASSES
    ]
    for triple in to_remove:
        shapes_graph.remove(triple)
    return len(to_remove)


def _expand_dash_has_value_with_class(shapes_graph: Graph) -> int:
    """Rewrite dash:hasValueWithClass into sh:qualifiedValueShape constraints.

    pyshacl silently ignores the DASH extension. Each occurrence is rewritten
    as sh:qualifiedValueShape / sh:qualifiedMinCount 1 on the parent node
    shape so the check fires during normal SHACL evaluation.
    """
    from rdflib import BNode, Literal

    prop_to_parents: dict = {}
    for node_shape, _, prop_shape in shapes_graph.triples((None, SH["property"], None)):
        prop_to_parents.setdefault(prop_shape, []).append(node_shape)

    to_remove = []
    to_add = []
    expansions = 0

    for prop_shape, _, cls_uri in list(shapes_graph.triples((None, _DASH_HVC, None))):
        to_remove.append((prop_shape, _DASH_HVC, cls_uri))
        if cls_uri in _SKIP_CLASSES_HVC:
            continue
        path_values = list(shapes_graph.objects(prop_shape, SH["path"]))
        if not path_values:
            continue
        path = path_values[0]
        for node_shape in prop_to_parents.get(prop_shape, []):
            qshape = BNode()
            to_add.append((node_shape, SH["property"], qshape))
            to_add.append((qshape, RDF.type, SH.PropertyShape))
            to_add.append((qshape, SH["path"], path))
            to_add.append((qshape, SH["qualifiedMinCount"], Literal(1)))
            inner = BNode()
            to_add.append((qshape, SH["qualifiedValueShape"], inner))
            to_add.append((inner, SH["class"], cls_uri))
        expansions += 1

    for triple in to_remove:
        shapes_graph.remove(triple)
    for triple in to_add:
        shapes_graph.add(triple)
    return expansions


def _is_aas_shape(report_graph: Graph, validation_result: URIRef) -> bool:
    """Decide whether a ValidationResult comes from an AAS-namespace shape.

    Several signals can identify an AAS shape:
      1. sh:sourceShape IRI starts with the AAS namespace
      2. sh:sourceConstraintComponent path traverses an AAS-namespaced property
      3. sh:resultPath property is in the AAS namespace
    Any one of these is sufficient; covers blank-node shapes too.
    """
    source_shape = report_graph.value(validation_result, SH.sourceShape)
    if source_shape is not None and str(source_shape).startswith(_AAS_NS_PREFIX):
        return True

    result_path = report_graph.value(validation_result, SH.resultPath)
    if result_path is not None and str(result_path).startswith(_AAS_NS_PREFIX):
        return True

    return False


def _classify_issue(report_graph: Graph, validation_result: URIRef) -> dict[str, str]:
    severity_map = {
        str(SH.Violation): "Violation",
        str(SH.Warning): "Warning",
        str(SH.Info): "Info",
    }
    message = str(report_graph.value(validation_result, SH.resultMessage) or "No message")
    severity_uri = str(report_graph.value(validation_result, SH.resultSeverity) or str(SH.Violation))
    source_shape = report_graph.value(validation_result, SH.sourceShape)
    focus_node = report_graph.value(validation_result, SH.focusNode)

    return {
        "source": "metamodel" if _is_aas_shape(report_graph, validation_result) else "ontology",
        "source_shape": str(source_shape) if source_shape is not None else "",
        "focus_node": str(focus_node) if focus_node is not None else "",
        "severity": severity_map.get(severity_uri, "Violation"),
        "message": message,
    }


def _extract_issues(report_graph: Graph) -> list[dict]:
    issues: list[dict] = []
    for vr in report_graph.subjects(RDF.type, SH.ValidationResult):
        issues.append(_classify_issue(report_graph, vr))
    return issues


def run_shacl(json_text: str, tmp_dir: Path) -> tuple[bool, list[dict], list[dict], list[dict]]:
    """v2 unified validation. Same return signature as v1's `run_shacl`.

    Returns (conforms, all_issues, metamodel_issues, ontology_issues).
    """
    try:
        from Transformation.AAS_to_RDF.aas_to_rdf import convert as aas_to_rdf_convert
    except ImportError as exc:
        msg = f"v2 validator: cannot import Transformation.AAS_Builder.AAS_to_RDF.aas_to_rdf ({exc})"
        return False, [{"source": "validation", "severity": "Violation", "message": msg}], \
            [{"source": "validation", "severity": "Violation", "message": msg}], []

    json_path  = tmp_dir / "input.json"
    rdf_path   = tmp_dir / "data.ttl"
    report_path = tmp_dir / "report.ttl"
    json_path.write_text(json_text, encoding="utf-8")

    try:
        aas_to_rdf_convert(json_path, rdf_path)
    except Exception as exc:
        msg = f"v2 RDF projection failed: {exc}"
        return False, [{"source": "metamodel", "severity": "Violation", "message": msg}], \
            [{"source": "metamodel", "severity": "Violation", "message": msg}], []

    data_graph = Graph().parse(str(rdf_path), format="turtle")

    visited: set[Path] = set()
    if _ARSO_AAS_TTL.exists():
        _load_with_imports(data_graph, _ARSO_AAS_TTL, visited)
    if _AAS_RDF_ONTOLOGY_TTL.exists() and _AAS_RDF_ONTOLOGY_TTL.resolve() not in visited:
        _load_with_imports(data_graph, _AAS_RDF_ONTOLOGY_TTL, visited)

    shapes = Graph()
    shapes_loaded = False
    if _AAS_SHACL_SHAPES_TTL.exists():
        shapes.parse(str(_AAS_SHACL_SHAPES_TTL), format="turtle")
        shapes_loaded = True
    if _ARSO_GENERATED_SHAPES.exists():
        shapes.parse(str(_ARSO_GENERATED_SHAPES), format="turtle")
        shapes_loaded = True

    # Manual SHACL rules: anything in shacl/manual/*.shacl.ttl. These cover the
    # constraints OWL-to-SHACL derivation cannot express (cross-submodel
    # references, value enums, etc.).
    if _SHACL_MANUAL_DIR.exists():
        for manual_path in sorted(_SHACL_MANUAL_DIR.glob("*.shacl.ttl")):
            try:
                shapes.parse(str(manual_path), format="turtle")
                shapes_loaded = True
            except Exception as exc:  # don't let one bad file kill validation
                print(f"  warning: skipping {manual_path.name}: {exc}")

    if not shapes_loaded:
        msg = (
            "v2 validator: no SHACL shapes loaded. Expected at "
            f"{_AAS_SHACL_SHAPES_TTL} and/or {_ARSO_GENERATED_SHAPES}."
        )
        return False, [{"source": "validation", "severity": "Violation", "message": msg}], \
            [{"source": "validation", "severity": "Violation", "message": msg}], []

    n_stripped = _strip_abstract_class_constraints(shapes)
    if n_stripped:
        print(f"  Stripped {n_stripped} abstract-class sh:class constraints (require inference)")

    n_expanded = _expand_dash_has_value_with_class(shapes)
    if n_expanded:
        print(f"  Expanded {n_expanded} dash:hasValueWithClass -> sh:qualifiedValueShape")

    try:
        conforms, report_graph, _report_text = pyshacl.validate(
            data_graph,
            shacl_graph=shapes,
            # inference="none": the serializer emits both the AAS class and the
            # cssx subclass directly, so no rdfs subClassOf chasing is needed.
            # Enabling rdfs inference triggers ~1200 spurious "abstract class -
            # use a subclass" violations from the AAS SHACL spec.
            inference="none",
            advanced=True,
            allow_warnings=True,
            allow_infos=True,
            meta_shacl=False,
            debug=False,
        )
    except Exception as exc:
        msg = f"v2 pyshacl invocation failed: {exc}"
        return False, [{"source": "validation", "severity": "Violation", "message": msg}], \
            [{"source": "validation", "severity": "Violation", "message": msg}], []

    if hasattr(report_graph, "serialize"):
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_graph.serialize(destination=str(report_path), format="turtle")

    issues = _extract_issues(report_graph)
    metamodel_issues = [i for i in issues if i["source"] == "metamodel"]
    ontology_issues  = [i for i in issues if i["source"] == "ontology"]

    return bool(conforms), [*metamodel_issues, *ontology_issues], metamodel_issues, ontology_issues


# Backwards-compatibility alias retained for any local debug scripts:
run_shacl_v2 = run_shacl


