from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from rdflib import Graph, OWL


def import_uri_to_local_path(import_uri: str, parent_file: Path) -> Path | None:
    parsed = urlparse(import_uri)
    if parsed.scheme in ("http", "https"):
        ttl_name = Path(parsed.path).name
        if ttl_name.endswith(".ttl"):
            candidates = [
                (parent_file.parent / ttl_name).resolve(),
                (parent_file.parent / "modules" / ttl_name).resolve(),
                (parent_file.parent / "Modules" / ttl_name).resolve(),
                (parent_file.parent.parent / "Modules" / ttl_name).resolve(),
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
        return None
    if parsed.scheme == "file":
        file_path = parsed.path
        if len(file_path) >= 3 and file_path[0] == "/" and file_path[2] == ":":
            file_path = file_path[1:]
        return Path(file_path)
    if parsed.scheme:
        return None
    return (parent_file.parent / import_uri).resolve()


def load_ontology_with_imports(target_graph: Graph, ontology_file: Path, visited: set[Path]) -> None:
    resolved_file = ontology_file.resolve()
    if resolved_file in visited or not resolved_file.exists():
        return

    visited.add(resolved_file)
    local_graph = Graph().parse(str(resolved_file), format="turtle")
    target_graph += local_graph

    for _, _, imported in local_graph.triples((None, OWL.imports, None)):
        imported_path = import_uri_to_local_path(str(imported), resolved_file)
        if imported_path is not None:
            load_ontology_with_imports(target_graph, imported_path, visited)


def run_owl2shacl_rules(ontology_graph: Graph, rules_graph: Graph) -> Graph:
    try:
        from pyshacl import shacl_rules
    except ImportError as exc:
        raise RuntimeError(
            "pyshacl with SHACL-AF support is required. Install project validation requirements first."
        ) from exc

    rules_result = shacl_rules(
        ontology_graph,
        shacl_graph=rules_graph,
        inference="none",
        advanced=True,
        iterate_rules=False,
        inplace=False,
    )

    if isinstance(rules_result, tuple):
        for item in rules_result:
            if isinstance(item, Graph):
                return item
        raise RuntimeError("Unexpected pyshacl.shacl_rules return value: no graph produced.")

    if not isinstance(rules_result, Graph):
        raise RuntimeError("Unexpected pyshacl.shacl_rules return type.")

    return rules_result


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ONTOLOGY_DIR = _REPO_ROOT / "Ontology"

ONTOLOGY_FILES = [
    _ONTOLOGY_DIR / "ARSO" / "ARSO_AAS.ttl",
    _ONTOLOGY_DIR / "AAS" / "aas-rdf-ontology.ttl",
    _ONTOLOGY_DIR / "CSS" / "CSS-Ontology.ttl",
]
OWL2SHACL_RULESET = _ONTOLOGY_DIR / "SHACL" / "owl2shacl" / "owl2sh-semi-closed.ttl"
GENERATED_OUTPUT = _ONTOLOGY_DIR / "SHACL" / "Generated" / "shapes.generated.shacl.ttl"
MANUAL_SPARQL_INPUT = _ONTOLOGY_DIR / "SHACL" / "Manual" / "arso-rules.shacl.ttl"


def main() -> None:
    for ontology_file in ONTOLOGY_FILES:
        if not ontology_file.exists():
            raise FileNotFoundError(f"Ontology file not found: {ontology_file}")

    if not OWL2SHACL_RULESET.exists():
        raise FileNotFoundError(f"OWL2SHACL ruleset not found: {OWL2SHACL_RULESET}")

    if not MANUAL_SPARQL_INPUT.exists():
        raise FileNotFoundError(f"Manual SHACL rules file not found: {MANUAL_SPARQL_INPUT}")

    ontology_graph = Graph()
    visited: set[Path] = set()
    for ontology in ONTOLOGY_FILES:
        load_ontology_with_imports(ontology_graph, ontology, visited)

    rules_graph = Graph().parse(str(OWL2SHACL_RULESET), format="turtle")
    generated_shapes = run_owl2shacl_rules(ontology_graph, rules_graph)

    GENERATED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generated_shapes.serialize(destination=str(GENERATED_OUTPUT), format="turtle")

    print(f"Generated ontology-derived shapes: {GENERATED_OUTPUT}")
    print(f"Manual SHACL rules source: {MANUAL_SPARQL_INPUT}")


if __name__ == "__main__":
    main()
