"""Validate an AAS JSON file against the combined ARSO SHACL shapes.

Usage:
    python tools/validate_aas.py <path-to-aas.json>

Converts the AAS JSON to RDF via aas_to_rdf.py, then validates against
both aas-shacl-schema.ttl and shacl/generated/shapes.generated.shacl.ttl.
Prints a human-readable violation report.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

# ---------------------------------------------------------------------------
# Stub out basyx so aas_to_rdf can be imported without the full basyx install
# ---------------------------------------------------------------------------
for _mod in ["basyx", "basyx.aas", "basyx.aas.model"]:
    sys.modules.setdefault(_mod, ModuleType(_mod))

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

# Import aas_to_rdf directly from its file so we bypass any package __init__
_spec = importlib.util.spec_from_file_location("aas_to_rdf", _HERE / "aas_to_rdf.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
serialize = _mod.serialize

SHAPES = [
    _WORKSPACE / "shacl" / "manual" / "aas-shacl-schema.ttl",
    _WORKSPACE / "shacl" / "generated" / "shapes.generated.shacl.ttl",
    _WORKSPACE / "shacl" / "manual" / "arso-rules.shacl.ttl",
]

AAS_ONTOLOGY = _WORKSPACE / "ontology" / "aas-rdf-ontology.ttl"


def _expand_dash_has_value_with_class(shapes_graph) -> int:
    """Expand dash:hasValueWithClass into standard SHACL qualifiedValueShape constraints.

    pyshacl silently ignores dash:hasValueWithClass.  This function rewrites each
    occurrence into an equivalent sh:qualifiedValueShape / sh:qualifiedMinCount 1
    property shape attached to the *parent node shape*, so the check fires during
    normal SHACL evaluation.

    dash:hasValueWithClass on a property shape P means:
      "among all values of P's sh:path, at least one must be an instance of class C"
    Standard SHACL equivalent added to the parent node shape N:
      N sh:property [
          sh:path P_path ;
          sh:qualifiedValueShape [ sh:class C ] ;
          sh:qualifiedMinCount 1 ;
      ] .

    Returns the number of expansions performed.
    """
    from rdflib import BNode, Literal, URIRef
    from rdflib.namespace import RDF, SH

    _DASH_HVC = URIRef("http://datashapes.org/dash#hasValueWithClass")
    # OperationalData allows any structure — skip enforcing its Datapoint constraint.
    _SKIP_CLASSES = frozenset({URIRef("https://w3id.org/2025/arso#Datapoint")})

    # Build: prop_shape -> parent node shape(s)
    prop_to_parents: dict = {}
    for node_shape, _, prop_shape in shapes_graph.triples((None, SH["property"], None)):
        prop_to_parents.setdefault(prop_shape, []).append(node_shape)

    to_remove = []
    to_add = []
    expansions = 0

    for prop_shape, _, cls_uri in list(shapes_graph.triples((None, _DASH_HVC, None))):
        to_remove.append((prop_shape, _DASH_HVC, cls_uri))
        if cls_uri in _SKIP_CLASSES:
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


def validate(aas_json_path: Path) -> bool:
    from rdflib import Graph, URIRef
    from rdflib.namespace import SH
    from pyshacl import validate as shacl_validate

    with open(aas_json_path, encoding="utf-8") as fh:
        document = json.load(fh)

    data_graph = serialize(document)
    print(f"Data graph  : {len(data_graph)} triples")

    shapes_graph = Graph()
    for sf in SHAPES:
        shapes_graph.parse(str(sf), format="turtle")

    # Strip sh:class constraints on AAS abstract classes — these require RDFS
    # inference to satisfy (via subclass chain) but enabling inference triggers
    # the AAS schema's SPARQL guards for abstract types. Consistent with what
    # generate_arso_shapes.py does for the generated shapes file.
    _AAS_NS = "https://admin-shell.io/aas/3/1/"
    _AAS_ABSTRACT = frozenset(
        URIRef(f"{_AAS_NS}{name}") for name in (
            "SubmodelElement", "DataElement", "AbstractLangString",
            "DataSpecificationContent", "EventElement", "HasDataSpecification",
            "HasExtensions", "HasKind", "HasSemantics",
            "Identifiable", "Qualifiable", "Referable",
        )
    )
    to_remove = [(s, p, o) for s, p, o in shapes_graph if p == SH["class"] and o in _AAS_ABSTRACT]
    for triple in to_remove:
        shapes_graph.remove(triple)
    if to_remove:
        print(f"Stripped {len(to_remove)} abstract-class sh:class constraints (require inference)")

    # Expand dash:hasValueWithClass into standard SHACL (pyshacl ignores the DASH extension)
    n_expanded = _expand_dash_has_value_with_class(shapes_graph)
    if n_expanded:
        print(f"Expanded    : {n_expanded} dash:hasValueWithClass -> sh:qualifiedValueShape")

    print(f"Shapes graph: {len(shapes_graph)} triples")

    conforms, _, report_text = shacl_validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="none",
        abort_on_first=False,
        advanced=True,
    )

    print(f"\nConforms: {conforms}")
    if not conforms:
        print()
        print(report_text)
    return conforms


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/validate_aas.py <path-to-aas.json>")
        sys.exit(1)
    ok = validate(Path(sys.argv[1]))
    sys.exit(0 if ok else 1)
