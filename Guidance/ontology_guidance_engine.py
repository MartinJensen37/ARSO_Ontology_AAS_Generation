"""Ontology-driven SHACL guidance engine for the ResourceAAS editor.

Validates the real AAS-to-RDF projection of an in-progress AAS dict against the
project's canonical SHACL shapes, so a hint can never disagree with what final
validation enforces. Violations become "hint" suggestions in the UI guidance
panel; no constraint logic is duplicated here.
"""
from __future__ import annotations

from typing import Any

from Validation.Validator.validator import map_issue_to_field


def check_aas_dict(aas_dict: dict) -> list[dict[str, Any]]:
    """Run SHACL pre-validation on a best-effort, possibly incomplete AAS dict.

    Projects the dict to RDF with the real AAS-to-RDF converter and validates it
    against the project's canonical SHACL shapes.

    Args:
        aas_dict: Dict shaped like the final AAS JSON (assetAdministrationShells
            / submodels), typically built from an in-progress config.

    Returns:
        Suggestion dicts {field, action, description, proposed_value}, action="hint".
    """
    try:
        from Transformation.AAS_to_RDF.aas_to_rdf import serialize as aas_to_rdf_serialize
        from Validation.Validator.validator import validate_rdf_graph
    except ImportError:
        return []

    try:
        data_graph = aas_to_rdf_serialize(aas_dict)
        _, issues = validate_rdf_graph(data_graph)
    except Exception:
        # Guidance is best-effort: an incomplete in-progress config that the
        # converter can't handle yet should never block editing.
        return []

    hints: list[dict[str, Any]] = []
    seen_messages: set[str] = set()

    for issue in issues:
        message = issue.get("message", "")
        if message in seen_messages:
            continue
        seen_messages.add(message)
        field = map_issue_to_field(
            message, issue.get("result_path", ""), issue.get("focus_node", "")
        )
        hints.append({
            "field": field,
            "action": "hint",
            "description": f"[{issue.get('severity', 'Violation')}] {message}",
            "proposed_value": None,
        })

    return hints


def invalidate_shapes_cache() -> None:
    """No-op — shapes cache is managed by Validation.Validator.validator."""
