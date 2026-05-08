"""
Ontology-driven SHACL guidance engine for the ResourceAAS editor.

Converts a YAML generator-profile config to a lightweight RDF graph and
validates it using the project's canonical SHACL shapes (via
Validation.Validator.validator.validate_rdf_graph).

Violations become "hint" suggestions surfaced in the UI guidance panel.
Because the SHACL shapes are the single source of truth, no constraint
logic is duplicated here — if the shapes change, guidance updates automatically.
"""
from __future__ import annotations

import re
from typing import Any

from .config_to_rdf import config_to_rdf

# Maps SHACL result messages → YAML field dot-paths for UI field highlighting.
# Patterns are tried in order; first match wins.
_MESSAGE_TO_FIELD: list[tuple[re.Pattern, str]] = [
    (re.compile(r"DigitalNameplate submodel is mandatory",          re.I), "DigitalNameplate"),
    (re.compile(r"HierarchicalStructures.*submodel is mandatory",   re.I), "HierarchicalStructures"),
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


def _map_message_to_field(message: str) -> str:
    for pattern, field in _MESSAGE_TO_FIELD:
        if pattern.search(message):
            return field
    return ""


def check_config(system_id: str, config: dict) -> list[dict[str, Any]]:
    """
    Run SHACL pre-validation on a YAML config dict.

    Converts the config to a lightweight RDF graph and validates it using
    the project's canonical SHACL shapes from Validation.Validator.validator.

    Returns a list of hint suggestions (action="hint") derived directly from
    SHACL constraint violations.

    Args:
        system_id: The top-level key from the YAML config (used for URI generation).
        config:    The system-level config dict (value under system_id key).

    Returns:
        List of suggestion dicts: {field, action, description, proposed_value}.
    """
    data_graph = config_to_rdf(system_id, config)

    try:
        from Validation.Validator.validator import validate_rdf_graph
        _, issues = validate_rdf_graph(data_graph)
    except ImportError:
        return []

    hints: list[dict[str, Any]] = []
    seen_messages: set[str] = set()

    for issue in issues:
        message = issue.get("message", "")
        if message in seen_messages:
            continue
        seen_messages.add(message)
        field = _map_message_to_field(message)
        hints.append({
            "field": field,
            "action": "hint",
            "description": f"[{issue.get('severity', 'Violation')}] {message}",
            "proposed_value": None,
        })

    return hints


def invalidate_shapes_cache() -> None:
    """No-op — shapes cache is managed by Validation.Validator.validator."""
