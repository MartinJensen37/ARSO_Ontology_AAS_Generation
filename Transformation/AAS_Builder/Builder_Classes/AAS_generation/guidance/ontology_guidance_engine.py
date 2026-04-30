"""
Ontology-driven SHACL guidance engine for the ResourceAAS editor.

Converts a YAML generator-profile config to a lightweight RDF graph and runs
the project's SHACL shapes against it.  Violations become "hint" suggestions
that are surfaced in the UI guidance panel.

Because the SHACL shapes are the single source of truth, this module does
NOT duplicate any constraint logic — if the shapes change, guidance updates
automatically.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace, RDF, URIRef
from pyshacl import validate

from .yaml_to_rdf_lite import config_to_rdf

SH   = Namespace("http://www.w3.org/ns/shacl#")
AASV = Namespace("http://www.w3id.org/aau-ra/resourceaas-validation#")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SHACL_DIR    = _PROJECT_ROOT / "shacl"
_ONTOLOGY_DIR = _PROJECT_ROOT

_SHACL_FILES = [
    _SHACL_DIR / "resourceaas-core.shacl.ttl",
    _SHACL_DIR / "resourceaas-dependencies.shacl.ttl",
    _SHACL_DIR / "resourceaas-semantics.shacl.ttl",
    _SHACL_DIR / "resourceaas-bom.shacl.ttl",
]

# Maps SHACL result messages → YAML field dot-paths for UI field highlighting.
# Patterns are tried in order; first match wins.
_MESSAGE_TO_FIELD: list[tuple[re.Pattern, str]] = [
    (re.compile(r"DigitalNameplate submodel is mandatory",          re.I), "DigitalNameplate"),
    (re.compile(r"HierarchicalStructures.*submodel is mandatory",   re.I), "HierarchicalStructures"),
    # Cross-submodel structural hints: field = the ABSENT submodel that must be added.
    # This makes them visible on the submodels selection step only when the required
    # submodel is not yet selected, and invisible once it is added.
    (re.compile(r"AID submodel must be present",                    re.I), "AID"),
    (re.compile(r"SoftwareInterface must be present",               re.I), "AID"),
    (re.compile(r"ResourceInterface must be mapped",                re.I), "AID.InterfaceMQTT"),
    (re.compile(r"SkillInterface.*must use.*ResourceInterface",     re.I), "Skills"),
    (re.compile(r"exactly one SkillInterface",                      re.I), "Skills"),
    (re.compile(r"Skills submodel.*Capabilities submodel",          re.I), "Capabilities"),
    (re.compile(r"Capabilities submodel.*Skills submodel",          re.I), "Skills"),
    (re.compile(r"provides Skills.*must provide.*Capabilit",        re.I), "Capabilities"),
    (re.compile(r"provides Capabilit.*must provide.*Skill",         re.I), "Skills"),
    (re.compile(r"Capabilit.*isRealizedBySkill",                    re.I), "Capabilities"),
    (re.compile(r"serialNumber.*manufacturerName",                  re.I), "DigitalNameplate"),
    # BoM (HierarchicalStructures) hints
    (re.compile(r"HierarchicalStructures.*Name is required",        re.I), "HierarchicalStructures.Name"),
    (re.compile(r"BoM entity.*globalAssetId",                       re.I), "HierarchicalStructures"),
    (re.compile(r"Archetype.*no entity entries",                    re.I), "HierarchicalStructures"),
    (re.compile(r"sourceSemanticId.*capabilit",                     re.I), "Capabilities"),
    (re.compile(r"sourceSemanticId.*skill",                         re.I), "Skills"),
    (re.compile(r"yearOfConstruction",                              re.I), "DigitalNameplate.YearOfConstruction"),
    (re.compile(r"dateOfManufacture",                               re.I), "DigitalNameplate.DateOfManufacture"),
    (re.compile(r"serialNumber",                                    re.I), "DigitalNameplate.SerialNumber"),
    (re.compile(r"manufacturerName",                                re.I), "DigitalNameplate.ManufacturerName"),
]

# Module-level shapes cache — loaded once per process
_shapes_cache: Graph | None = None


def _get_shapes() -> Graph:
    global _shapes_cache
    if _shapes_cache is None:
        g = Graph()
        for path in _SHACL_FILES:
            if path.exists():
                g.parse(str(path), format="turtle")
        _shapes_cache = g
    return _shapes_cache


def _map_message_to_field(message: str) -> str:
    for pattern, field in _MESSAGE_TO_FIELD:
        if pattern.search(message):
            return field
    return ""


def check_config(system_id: str, config: dict) -> list[dict[str, Any]]:
    """
    Run SHACL pre-validation on a YAML config dict.

    Returns a list of hint suggestions (action="hint") derived directly from
    SHACL constraint violations.  No constraint logic is hardcoded here.

    Args:
        system_id: The top-level key from the YAML config (used for URI generation).
        config:    The system-level config dict (value under system_id key).

    Returns:
        List of suggestion dicts: {field, action, description, proposed_value}.
    """
    data_graph = config_to_rdf(system_id, config)
    shapes_graph = _get_shapes()

    if len(shapes_graph) == 0:
        # SHACL files not found — fail gracefully
        return []

    conforms, results_graph, _ = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )

    if conforms:
        return []

    hints: list[dict[str, Any]] = []
    seen_messages: set[str] = set()

    SH_VALIDATION_RESULT = URIRef("http://www.w3.org/ns/shacl#ValidationResult")
    SH_RESULT_MESSAGE    = URIRef("http://www.w3.org/ns/shacl#resultMessage")
    SH_RESULT_PATH       = URIRef("http://www.w3.org/ns/shacl#resultPath")
    SH_SEVERITY          = URIRef("http://www.w3.org/ns/shacl#resultSeverity")
    SH_VIOLATION         = URIRef("http://www.w3.org/ns/shacl#Violation")

    for result_node in results_graph.subjects(RDF.type, SH_VALIDATION_RESULT):
        for message_node in results_graph.objects(result_node, SH_RESULT_MESSAGE):
            message = str(message_node)
            if message in seen_messages:
                continue
            seen_messages.add(message)

            field = _map_message_to_field(message)

            # Severity — default to Violation if not present
            severity_uri = next(
                results_graph.objects(result_node, SH_SEVERITY), SH_VIOLATION
            )
            severity = str(severity_uri).split("#")[-1]  # "Violation", "Warning", "Info"

            hints.append({
                "field": field,
                "action": "hint",
                "description": f"[{severity}] {message}",
                "proposed_value": None,
            })

    return hints


def invalidate_shapes_cache() -> None:
    """Force reload of SHACL shapes on next call (useful after shapes files change)."""
    global _shapes_cache
    _shapes_cache = None
