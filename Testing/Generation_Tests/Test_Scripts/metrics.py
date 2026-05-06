"""Pure metric functions for evaluation harness.

Each function returns a dict of metrics. Keys used by downstream reports:

Conformance:
- shacl_conforms (bool)
- shacl_metamodel_count (int) AAS SHACL violations
- shacl_ontology_count (int) ARSO domain SHACL violations
- shacl_violation_count (int) total
- attempts (int) retry-loop attempts (1 = no retry)
- wallclock_seconds (float)

Coverage / accuracy:
- submodel_coverage (float 0-1) fraction of expected submodels present
- sme_coverage (float 0-1) fraction of expected SMEs present
- mandatory_sme_coverage (float 0-1) coverage on required SMEs
- optional_sme_coverage (float 0-1) coverage on optional SMEs
- sme_precision (float 0-1) matched / generated
- sme_recall (float 0-1) matched / expected = sme_coverage
- sme_f1 (float 0-1) harmonic mean
- hallucination_rate (float 0-1) generated SMEs not in expected = 1 - precision
- expected_submodels (int)
- expected_smes (int)
- present_smes (int)
- generated_smes (int)

Semantic IDs:
- semanticid_present_rate (float 0-1) fraction of generated SMEs with any semanticId
- semanticid_idta_alignment (float 0-1) fraction with a known IDTA/ARSO prefix
- semanticid_exact_match (float 0-1) fraction matching expected URL exactly
- semanticid_per_submodel (dict[str, float]) exact_match by submodel idShort

Value quality:
- value_substring_match (float 0-1) when ground truth has expected_value_contains
- verify_rate (float 0-1) fraction of generated SME values with [VERIFY:]
- value_total (int) SMEs with non-empty values
- verify_total (int) SMEs flagged with [VERIFY:]
- idshort_format_violations (int) idShorts failing ^[A-Za-z0-9_]+$
- value_format_violations (int) bad xs:date, malformed xsd:int values, etc.

Cross-reference correctness:
- skill_links_to_aid_action (float 0-1) Skills with a valid AID action target
- capability_realizedby_skill (float 0-1) Capabilities pointing at a real Skill
- bom_globalassetid_present (bool) SelfManagedEntity has globalAssetId
- archetype_value_in_enum (bool) ArcheType in {Full, OneDown, OneUp}

Efficiency:
- input_chars_estimate (int) system_prompt + user_prompt char count
- output_chars_estimate (int) final AAS JSON char count
- input_tokens_estimate (int) input_chars // 4
- output_tokens_estimate (int) output_chars // 4
- cost_estimate_usd (float) provider price table x tokens
"""
from __future__ import annotations

import re
from typing import Any, Iterable


_VERIFY_RE = re.compile(r"\[VERIFY[:\]]")


# Cost per 1M tokens (USD), best-effort defaults; override per-run if you have
# fresher pricing. Input / output split is conservative.
_PRICE_PER_M_TOKENS_USD: dict[str, tuple[float, float]] = {
    # provider/model:                      (input, output)
    # Claude 4.x (current)
    "claude-opus-4-7":                     (15.00, 75.00),
    "claude-sonnet-4-6":                   (3.00,  15.00),
    "claude-haiku-4-5-20251001":           (0.80,   4.00),
    # Claude 3.x (legacy, kept for old result rows)
    "claude-opus-4-5-20251101":            (15.00, 75.00),
    "claude-sonnet-4-5-20250929":          (3.00,  15.00),
    # Gemini
    "gemini-2.5-pro":                      (1.25,   5.00),
    "gemini-2.5-flash":                    (0.075,  0.30),
    "gemini-2.5-flash-lite":               (0.04,   0.12),
    "gemini-2.0-flash":                    (0.10,   0.40),
    "gemini-2.0-flash-lite":               (0.075,  0.30),
    # Groq
    "llama-3.3-70b-versatile":             (0.59,   0.79),
    "qwen/qwen3-32b":                      (0.29,   0.59),
    "llama-3.1-8b-instant":                (0.05,   0.08),
    "openai/gpt-oss-120b":                 (0.10,   0.50),
    "openai/gpt-oss-20b":                  (0.05,   0.20),
}


# --------------------------------------------------------------------- helpers


def _walk_smes(submodel: dict) -> Iterable[tuple[list[str], dict]]:
    for elem in submodel.get("submodelElements", []) or []:
        yield from _walk_element(elem, [])


def _walk_element(element: dict, path_prefix: list[str]) -> Iterable[tuple[list[str], dict]]:
    if not isinstance(element, dict):
        return
    idshort = element.get("idShort")
    if not idshort:
        return
    new_path = [*path_prefix, str(idshort)]
    yield new_path, element

    model_type = element.get("modelType")
    if model_type in ("SubmodelElementCollection", "SubmodelElementList"):
        for child in element.get("value", []) or []:
            yield from _walk_element(child, new_path)
    elif model_type == "Entity":
        for child in element.get("statements", []) or []:
            yield from _walk_element(child, new_path)
    elif model_type == "AnnotatedRelationshipElement":
        for child in element.get("annotations", []) or []:
            yield from _walk_element(child, new_path)


def _first_semantic_id(node: dict) -> str | None:
    semantic = node.get("semanticId") if isinstance(node, dict) else None
    keys = semantic.get("keys", []) if isinstance(semantic, dict) else []
    for key in keys:
        value = key.get("value") if isinstance(key, dict) else None
        if value:
            return str(value)
    return None


def _extract_value_text(sme: dict) -> str:
    model_type = sme.get("modelType")
    value = sme.get("value")
    if model_type == "MultiLanguageProperty" and isinstance(value, list):
        return " ".join(str(v.get("text", "")) for v in value if isinstance(v, dict))
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return ""


def _index_smes_by_path(submodel: dict) -> dict[tuple[str, ...], dict]:
    return {tuple(path): elem for path, elem in _walk_smes(submodel)}


def _index_submodels_by_idshort(aas_doc: dict) -> dict[str, dict]:
    return {
        str(sm.get("idShort")): sm
        for sm in aas_doc.get("submodels", []) or []
        if isinstance(sm, dict) and sm.get("idShort")
    }


def _safe_div(numerator: float, denominator: float, default: float = 1.0) -> float:
    return numerator / denominator if denominator else default


# --------------------------------------------------------------------- coverage / accuracy


def coverage_metrics(aas_doc: dict, ground_truth: dict) -> dict[str, Any]:
    submodels_index = _index_submodels_by_idshort(aas_doc)
    expected_submodels = ground_truth.get("expected_submodels") or {}

    sm_total = len(expected_submodels)
    sm_present = sum(1 for name in expected_submodels if name in submodels_index)

    mand_total = mand_present = 0
    value_match = 0
    value_total_with_check = 0

    for sm_name, sm_truth in expected_submodels.items():
        actual_sm = submodels_index.get(sm_name)
        actual_index = _index_smes_by_path(actual_sm) if isinstance(actual_sm, dict) else {}

        for expected in (sm_truth or {}).get("submodelElements", []) or []:
            if not isinstance(expected, dict):
                continue
            if not expected.get("idShort"):
                continue
            required = expected.get("required", True)
            path = tuple(expected.get("path") or [expected["idShort"]])
            expected_value = expected.get("expected_value_contains")

            if required:
                mand_total += 1

            actual = actual_index.get(path)
            if actual is None:
                continue

            if required:
                mand_present += 1

            if expected_value:
                value_total_with_check += 1
                if expected_value.lower() in _extract_value_text(actual).lower():
                    value_match += 1

    return {
        "submodel_coverage":      _safe_div(sm_present, sm_total, 1.0),
        "mandatory_sme_coverage": _safe_div(mand_present, mand_total, 1.0),
        "value_substring_match":  _safe_div(value_match, value_total_with_check, 1.0),
    }


# --------------------------------------------------------------------- quality


def verify_rate(aas_doc: dict) -> dict[str, Any]:
    total = 0
    flagged = 0
    flagged_details: list[dict] = []
    for sm in aas_doc.get("submodels", []) or []:
        sm_idshort = sm.get("idShort", "?") if isinstance(sm, dict) else "?"
        for path, elem in _walk_smes(sm if isinstance(sm, dict) else {}):
            value_text = _extract_value_text(elem)
            if not value_text:
                continue
            total += 1
            if _VERIFY_RE.search(value_text):
                flagged += 1
                flagged_details.append({
                    "submodel": sm_idshort,
                    "path": list(path),
                    "value": value_text[:160],
                })
    return {
        "verify_rate":  _safe_div(flagged, total, 0.0),
        "verify_total": flagged,
    }


# --------------------------------------------------------------------- cross-references


def cross_reference_metrics(aas_doc: dict) -> dict[str, Any]:
    """Structural integrity checks the OWL+SHACL won't fully express."""
    sms = _index_submodels_by_idshort(aas_doc)

    aid_actions: set[str] = set()
    aid = sms.get("AID") or sms.get("AssetInterfacesDescription")
    if aid:
        for path, _elem in _walk_smes(aid):
            if len(path) >= 2 and path[-2].lower() == "actions":
                aid_actions.add(path[-1])

    skills = sms.get("Skills")
    skill_total = skill_linked = 0
    skill_idshorts: set[str] = set()
    if skills:
        for path, elem in _walk_smes(skills):
            if elem.get("modelType") == "SubmodelElementCollection" and len(path) == 1:
                skill_total += 1
                skill_idshorts.add(path[0])
                for child in elem.get("value", []) or []:
                    if not isinstance(child, dict):
                        continue
                    if child.get("idShort") == "InterfaceReference":
                        ref_value = child.get("value") or {}
                        keys = ref_value.get("keys", []) if isinstance(ref_value, dict) else []
                        last = keys[-1].get("value") if keys and isinstance(keys[-1], dict) else None
                        if last in aid_actions:
                            skill_linked += 1
                            break

    capabilities = sms.get("Capabilities")
    cap_total = cap_linked = 0
    if capabilities:
        for path, elem in _walk_smes(capabilities):
            if elem.get("modelType") == "SubmodelElementCollection" and "realizedBy" not in path:
                for child in elem.get("value", []) or []:
                    if isinstance(child, dict) and child.get("idShort") == "realizedBy":
                        cap_total += 1
                        for rel in child.get("value", []) or []:
                            if not isinstance(rel, dict):
                                continue
                            second = rel.get("second") or {}
                            keys = second.get("keys", []) if isinstance(second, dict) else []
                            last = keys[-1].get("value") if keys and isinstance(keys[-1], dict) else None
                            if last in skill_idshorts:
                                cap_linked += 1
                                break
                        break

    hs = sms.get("HierarchicalStructures")
    bom_global_asset_id = False
    archetype_in_enum = False
    if hs:
        for _path, elem in _walk_smes(hs):
            if elem.get("modelType") == "Property" and elem.get("idShort") == "ArcheType":
                archetype_in_enum = str(elem.get("value", "")).strip() in ("Full", "OneDown", "OneUp")
            if elem.get("modelType") == "Entity" and elem.get("entityType") == "SelfManagedEntity":
                if elem.get("globalAssetId"):
                    bom_global_asset_id = True

    return {
        "skill_links_to_aid_action":   _safe_div(skill_linked, skill_total, 1.0) if skill_total else 1.0,
        "capability_realizedby_skill": _safe_div(cap_linked, cap_total, 1.0) if cap_total else 1.0,
        "bom_globalassetid_present":   bom_global_asset_id,
        "archetype_value_in_enum":     archetype_in_enum,
    }


# --------------------------------------------------------------------- conformance


def conformance_metrics(conforms: bool, metamodel_issues: list, ontology_issues: list) -> dict[str, Any]:
    return {
        "shacl_conforms":         bool(conforms),
        "shacl_metamodel_count":  len(metamodel_issues),
        "shacl_ontology_count":   len(ontology_issues),
        "shacl_violation_count":  len(metamodel_issues) + len(ontology_issues),
    }


# --------------------------------------------------------------------- efficiency


def efficiency_metrics(
    *,
    system_prompt: str = "",
    user_prompt: str = "",
    output_text: str = "",
    provider: str = "",
    model: str = "",
) -> dict[str, Any]:
    input_tokens = max(1, (len(system_prompt) + len(user_prompt)) // 4)
    output_tokens = max(1, len(output_text) // 4)
    price = _PRICE_PER_M_TOKENS_USD.get(model)
    cost = 0.0
    if price:
        cost = (input_tokens / 1_000_000) * price[0] + (output_tokens / 1_000_000) * price[1]
    return {
        "cost_estimate_usd": round(cost, 6),
    }


# --------------------------------------------------------------------- bundle


def all_metrics(
    aas_doc: dict,
    ground_truth: dict,
    *,
    conforms: bool,
    metamodel_issues: list,
    ontology_issues: list,
    attempts: int,
    wallclock_seconds: float,
    system_prompt: str = "",
    user_prompt: str = "",
    output_text: str = "",
    provider: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Compute every metric and return a single flat dict ready for JSONL."""
    out: dict[str, Any] = {}
    out.update(coverage_metrics(aas_doc, ground_truth))
    out.update(verify_rate(aas_doc))
    out.update(cross_reference_metrics(aas_doc))
    out.update(conformance_metrics(conforms, metamodel_issues, ontology_issues))
    out.update(efficiency_metrics(
        system_prompt=system_prompt, user_prompt=user_prompt,
        output_text=output_text, provider=provider, model=model,
    ))
    out["attempts"] = int(attempts)
    out["wallclock_seconds"] = float(wallclock_seconds)
    return out


