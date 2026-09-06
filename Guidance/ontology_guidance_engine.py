"""
Ontology-driven SHACL guidance engine for the ResourceAAS editor.

Runs the project's canonical SHACL shapes (via
Validation.Validator.validator.validate_rdf_graph) against the *real* AAS
RDF projection (Transformation.AAS_to_RDF.aas_to_rdf.serialize) of a
best-effort AAS dict built from the in-progress config — the same dict shape
and the same RDF projection used for final validation, so a guidance hint can
never disagree with what generation will ultimately enforce.

Violations become "hint" suggestions surfaced in the UI guidance panel.
Because the SHACL shapes are the single source of truth, no constraint
logic is duplicated here — if the shapes change, guidance updates automatically.

This replaces an earlier version that built its own lightweight RDF graph
(via a now-removed config_to_rdf module) using ad hoc vocabulary terms that
never matched any real SHACL shape target — so it silently never produced a
meaningful hint. Feeding the real AAS-to-RDF projection is what makes the
shapes actually able to fire.
"""
from __future__ import annotations

from typing import Any

from Validation.Validator.validator import map_issue_to_field


def check_aas_dict(aas_dict: dict) -> list[dict[str, Any]]:
    """
    Run SHACL pre-validation on a best-effort AAS dict (same shape as the
    final generated AAS JSON, just possibly incomplete).

    Projects the dict to RDF with the real AAS-to-RDF converter and validates
    it using the project's canonical SHACL shapes from
    Validation.Validator.validator.

    Returns a list of hint suggestions (action="hint") derived directly from
    SHACL constraint violations.

    Args:
        aas_dict: A dict shaped like the final generated AAS JSON
            (assetAdministrationShells / submodels), typically built by
            AASGenerator._build_object_store() + _serialize_to_dict() on the
            in-progress config, before all fields are necessarily filled in.

    Returns:
        List of suggestion dicts: {field, action, description, proposed_value}.
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
        field = _map_issue_to_field(
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
