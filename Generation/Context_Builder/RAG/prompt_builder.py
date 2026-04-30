"""
Assembles system_instruction and user_prompt strings.
Loads static prompt templates from prompts.yaml and composes runtime strings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ...config import Config
from ..Parsing.json_description_generation import (
    assemble_profile_example_json,
    assemble_profile_semantic_guide_json,
)


PROMPTS_PATH = Path(__file__).resolve().parents[2] / "prompts.yaml"


@lru_cache(maxsize=1)
def _load_prompt_templates() -> dict:
    if not PROMPTS_PATH.exists():
        raise FileNotFoundError(f"Prompt template file not found: {PROMPTS_PATH}")

    with PROMPTS_PATH.open(encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle) or {}

    required_keys = {
        "uncertainty_rules",
        "system_base",
        "system_base_json_description",
        "user_prompt_base",
        "user_prompt_base_json_description",
        "user_spec_note_gemini_with_pdf",
        "user_spec_note_no_pdf",
        "user_spec_note_text_with_pdf",
        "retry_template",
        "retry_template_json_description",
    }
    missing = sorted(required_keys - set(data.keys()))
    if missing:
        raise ValueError(f"Missing keys in prompts.yaml: {', '.join(missing)}")

    return data


def _template(name: str) -> str:
    value = _load_prompt_templates().get(name, "")
    if not isinstance(value, str):
        raise ValueError(f"Template '{name}' must be a string in prompts.yaml")
    return value


def build_system_instruction(
    cfg: Config,
    context_text: str,
    rag_text_blocks: list[str],
) -> str:
    uncertainty_rules = _template("uncertainty_rules")
    if cfg.generation_mode == "json-description":
        system_base = _template("system_base_json_description")
    else:
        system_base = _template("system_base")

    instruction = system_base.format(uncertainty_rules=uncertainty_rules) + "\n\n---\n\n" + context_text

    # For text-based providers, append RAG blocks to the system instruction
    if cfg.provider != "gemini" and rag_text_blocks:
        instruction += "\n\n---\n\n" + "\n\n---\n\n".join(rag_text_blocks)

    return instruction


def build_user_prompt(
    cfg: Config,
    pdf_base64: str | None,
    pdf_text: str | None,
    spec_sheet_text: str | None = None,
    supplemental_context: str | None = None,
) -> str:
    mandatory     = {"Nameplate", "HierarchicalStructures"}
    all_submodels = list(dict.fromkeys([*mandatory, *cfg.submodels]))

    extra_sections: list[str] = []
    if spec_sheet_text and spec_sheet_text.strip():
        extra_sections.append(
            "User-provided specification text:\n"
            + spec_sheet_text.strip()
        )
    if supplemental_context and supplemental_context.strip():
        extra_sections.append(
            "Extracted supplemental file context (XML/JSON/NodeSet/PDF):\n"
            + supplemental_context.strip()
        )

    if cfg.provider == "gemini":
        spec_note = (
            _template("user_spec_note_gemini_with_pdf")
            if pdf_base64
            else _template("user_spec_note_no_pdf").format(asset_name=cfg.asset_name)
        )
    else:
        spec_note = (
            _template("user_spec_note_text_with_pdf").format(pdf_text=pdf_text)
            if pdf_text
            else _template("user_spec_note_no_pdf").format(asset_name=cfg.asset_name)
        )

    if extra_sections:
        spec_note = (
            spec_note
            + "\n\nUse the following additional source material as ground truth when available:\n\n"
            + "\n\n---\n\n".join(extra_sections)
            + "\n\nIf OPC UA NodeSet information is present, prioritise mapping methods/skills into Skills, variables into Variables, and endpoint/address/interface details into AssetInterfacesDescription (AID) whenever those submodels are selected."
        )

    if cfg.generation_mode == "json-description":
        profile_example_json = assemble_profile_example_json(cfg)
        profile_semantic_guide_json = assemble_profile_semantic_guide_json(cfg)
        return _template("user_prompt_base_json_description").format(
            asset_name=cfg.asset_name,
            base_url=cfg.base_url,
            submodels=", ".join(all_submodels),
            spec_note=spec_note,
            profile_semantic_guide_json=profile_semantic_guide_json,
            profile_example_json=profile_example_json,
        )

    return _template("user_prompt_base").format(
        asset_name=cfg.asset_name,
        base_url=cfg.base_url,
        submodels=", ".join(all_submodels),
        spec_note=spec_note,
    )


def _format_issue_lines(issues: list[dict]) -> str:
    if not issues:
        return "- None"
    return "\n".join(f"- [{i.get('severity', '?')}] {i.get('message', '')}" for i in issues)


def build_retry_message(
    cfg: Config,
    attempt: int,
    max_attempts: int,
    metamodel_issues: list[dict],
    ontology_issues: list[dict],
) -> str:
    if cfg.generation_mode == "json-description":
        retry_template_name = "retry_template_json_description"
    else:
        retry_template_name = "retry_template"
    retry_template = _template(retry_template_name)
    required_placeholders = ("{attempt}", "{max_attempts}", "{metamodel_issue_lines}", "{ontology_issue_lines}")
    for placeholder in required_placeholders:
        if placeholder not in retry_template:
            raise ValueError(f"retry_template in prompts.yaml is missing placeholder: {placeholder}")

    return retry_template.format(
        attempt=attempt,
        max_attempts=max_attempts,
        metamodel_issue_lines=_format_issue_lines(metamodel_issues),
        ontology_issue_lines=_format_issue_lines(ontology_issues),
    )
