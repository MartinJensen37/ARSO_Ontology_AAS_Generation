"""
Finish the shapes the owl2sh-closed ruleset produces, so that they are valid SHACL.

The ruleset writes sh:ignoredProperties and sh:or as one value per member and leaves it to the
caller to gather them into the RDF list SHACL requires, because a SHACL rule cannot CONSTRUCT a
list of unknown length. Without that step a closed shape ignores nothing and rejects every
property it does not declare itself, including the ones its subclasses add.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from rdflib import BNode, Graph, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SH


# Carried by every projected node, whatever its class.
_ALWAYS_IGNORED = (RDF.type, RDFS.label, RDFS.comment)


def _closure(start: URIRef, step: dict[URIRef, set[URIRef]]) -> set[URIRef]:
    seen, todo = {start}, [start]
    while todo:
        for nxt in step[todo.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen


def _declared_paths(shapes: Graph, declared: Iterable[Graph]) -> dict[URIRef, set[URIRef]]:
    """The property paths each class declares: its own property shapes (a generated shape is the
    class itself) and those of hand-written shapes that target the class."""
    paths: dict[URIRef, set[URIRef]] = defaultdict(set)
    for shape, prop in shapes.subject_objects(SH.property):
        for path in shapes.objects(prop, SH.path):
            if isinstance(shape, URIRef) and isinstance(path, URIRef):
                paths[shape].add(path)
    for graph in declared:
        for shape, cls in graph.subject_objects(SH.targetClass):
            for prop in graph.objects(shape, SH.property):
                for path in graph.objects(prop, SH.path):
                    if isinstance(cls, URIRef) and isinstance(path, URIRef):
                        paths[cls].add(path)
    return paths


def gather_ignored_properties(shapes: Graph, declared: Iterable[Graph] = ()) -> int:
    """Give every closed node shape one sh:ignoredProperties list. Returns the number of shapes.

    A shape is applied to every instance of its class, so it has to ignore the properties of every
    class such an instance can also belong to: its descendants and all of their ancestors. The
    ruleset only names ancestors and descendants, which leaves out the other parents of a
    descendant (aas:Submodel is Identifiable, HasSemantics, Qualifiable, ... at once).

    `declared` are further shape graphs whose property shapes count as declared on their target
    class (the AAS metamodel's SHACL schema declares paths the AAS ontology does not).
    """
    parents: dict[URIRef, set[URIRef]] = defaultdict(set)
    children: dict[URIRef, set[URIRef]] = defaultdict(set)
    for child, parent in shapes.subject_objects(RDFS.subClassOf):
        if isinstance(child, URIRef) and isinstance(parent, URIRef):
            parents[child].add(parent)
            children[parent].add(child)
    paths = _declared_paths(shapes, declared)

    closed = sorted(s for s in set(shapes.subjects(SH.closed, None)) if isinstance(s, URIRef))
    for shape in closed:
        related: set[URIRef] = set()
        for descendant in _closure(shape, children):
            related |= _closure(descendant, parents)
        ignored = set(_ALWAYS_IGNORED)
        for cls in related:
            ignored |= paths[cls]
        ignored -= paths[shape]

        for old in list(shapes.objects(shape, SH.ignoredProperties)):
            shapes.remove((shape, SH.ignoredProperties, old))
            if isinstance(old, BNode):
                Collection(shapes, old).clear()
        head = BNode()
        Collection(shapes, head, sorted(ignored))
        shapes.add((shape, SH.ignoredProperties, head))
    return len(closed)


def gather_or_members(shapes: Graph) -> int:
    """Gather the sh:or values of a shape into one list. Returns the number of shapes."""
    members: dict[URIRef | BNode, list] = defaultdict(list)
    for shape, member in shapes.subject_objects(SH["or"]):
        if (member, RDF.first, None) not in shapes and member != RDF.nil:
            members[shape].append(member)
    for shape, found in members.items():
        for member in found:
            shapes.remove((shape, SH["or"], member))
        head = BNode()
        Collection(shapes, head, sorted(found))
        shapes.add((shape, SH["or"], head))
    return len(members)


def finish_closed_shapes(shapes: Graph, declared: Iterable[Graph] = ()) -> Graph:
    """Do what the owl2sh-closed ruleset leaves to its caller. Changes `shapes` and returns it."""
    gather_or_members(shapes)
    gather_ignored_properties(shapes, declared)
    return shapes


_SHACL_DIR = Path(__file__).resolve().parents[2] / "Ontology" / "SHACL"
_GENERATED = _SHACL_DIR / "Generated" / "shapes.generated.shacl.ttl"
_AAS_SHACL_SCHEMA = _SHACL_DIR / "Manual" / "aas-shacl-schema.ttl"


def main() -> None:
    """Finish the generated shapes file again, in place: after a property shape was added or
    removed by hand, the lists of the related closed shapes have to follow."""
    shapes = Graph().parse(str(_GENERATED), format="turtle")
    finish_closed_shapes(shapes, [Graph().parse(str(_AAS_SHACL_SCHEMA), format="turtle")])
    shapes.serialize(destination=str(_GENERATED), format="turtle")
    print(f"Finished closed shapes: {_GENERATED}")
    print(f"Closed node shapes: {len(set(shapes.subjects(SH.closed, None)))}")


if __name__ == "__main__":
    main()
