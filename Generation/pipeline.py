"""pipeline_v2 — v2 generation + validation retry loop.

Byte-for-byte parallel of generation/pipeline.py with two import lines flipped:
  - profile_json_text_to_aas_json comes from AAS_builder_v2 (uses v2 AASGenerator)
  - run_shacl is replaced by run_shacl_v2 (single pyshacl call, no basyx step)

Anything else (progress_callback, generation_mode plumbing, profile-issue
continue-on-failure logic) is identical to v1 so that a `validation.profile`
flip is a clean A/B test.
"""
from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path

from .config import Config
from .Context_Builder.Parsing.json_description_generation import (
	profile_json_text_to_document,
	validate_profile_document,
)
from .LLM_Client.llm_client import call_llm
from .Context_Builder.RAG.prompt_builder import build_retry_message
from .Context_Builder.Parsing.text_parsing import extract_outer_json_object, strip_code_fences

from Transformation.AAS_Builder.AAS_builder import profile_json_text_to_aas_json
from Validation.Validator.validator import run_shacl


def run_pipeline(
	cfg: Config,
	system_instruction: str,
	user_prompt: str,
	pdf_base64: str | None,
	rag_gemini_parts: list[dict],
	progress_callback=None,
) -> tuple[str, bool, list[dict], int, list[dict]]:
	"""
	progress_callback: optional callable(str) called with each log message.
	Used by the FastAPI endpoint to stream progress via SSE.
	"""
	def _log(msg: str) -> None:
		print(msg)
		if progress_callback is not None:
			try:
				progress_callback(msg)
			except Exception:
				pass

	model_idx = 0
	aas_json = ""
	conforms = False
	issues: list[dict] = []
	metamodel_issues: list[dict] = []
	ontology_issues: list[dict] = []
	attempt = 0
	attempt_snapshots: list[dict] = []

	if cfg.provider == "gemini":
		first_parts: list[dict] = []
		first_parts.extend(rag_gemini_parts)
		if pdf_base64:
			first_parts.append({"inline_data": {"mime_type": "application/pdf", "data": pdf_base64}})
		first_parts.append({"text": user_prompt})
		gemini_contents: list[dict] = [{"role": "user", "parts": first_parts}]
		groq_history: list[dict] = []
	else:
		gemini_contents = []
		groq_history = [{"role": "user", "content": user_prompt}]

	with tempfile.TemporaryDirectory() as _tmp:
		tmp_dir = Path(_tmp)

		while attempt < cfg.max_attempts:
			attempt += 1
			_log(f"\n  -- Attempt {attempt}/{cfg.max_attempts} (v2) " + "-" * 30)

			raw_text, model_idx = call_llm(
				provider=cfg.provider,
				api_key=cfg.api_key,
				models=cfg.models,
				model_idx=model_idx,
				system_instruction=system_instruction,
				gemini_contents=gemini_contents if cfg.provider == "gemini" else None,
				groq_history=groq_history if cfg.provider != "gemini" else None,
				generation_mode=cfg.generation_mode,
			)

			if not raw_text:
				attempt -= 1
				continue

			if cfg.provider == "gemini":
				gemini_contents.append({"role": "model", "parts": [{"text": raw_text}]})
			else:
				groq_history.append({"role": "assistant", "content": raw_text})

			if cfg.generation_mode == "json-description":
				raw_text = strip_code_fences(raw_text)
				aas_json = raw_text
			else:
				raw_text = extract_outer_json_object(raw_text)
				aas_json = raw_text

			verify_count = len(re.findall(r'\[VERIFY:', raw_text))
			_log(f"  Response: {len(raw_text):,} chars" + (f"  |  [VERIFY] markers: {verify_count}" if verify_count else ""))

			if cfg.generation_mode == "json-description":
				try:
					document = profile_json_text_to_document(raw_text)
				except Exception as exc:
					_log(f"  Profile JSON parse FAILED: {exc}")
					issues = [{"severity": "Violation", "message": f"Profile JSON parse failed: {exc}"}]
					metamodel_issues = issues
					ontology_issues = []
					conforms = False
				else:
					if isinstance(document, dict) and "assetAdministrationShells" in document:
						issues = [{
							"severity": "Violation",
							"message": "LLM returned full AAS JSON. In json-description mode, return profile JSON only.",
						}]
						metamodel_issues = issues
						ontology_issues = []
						conforms = False
						_log("  Full AAS JSON detected in json-description mode — requesting profile JSON instead.")
					else:
						profile_issues = validate_profile_document(document, cfg)
						profile_issue_dicts = [{"severity": "Violation", "message": message} for message in profile_issues]

						try:
							aas_json, _ = profile_json_text_to_aas_json(raw_text, cfg)
						except Exception as exc:
							_log(f"  Profile-to-AAS conversion FAILED: {exc}")
							issues = [
								*profile_issue_dicts,
								{"severity": "Violation", "message": f"Profile to AAS conversion failed: {exc}"},
							]
							metamodel_issues = issues
							ontology_issues = []
							conforms = False
						else:
							if profile_issue_dicts:
								_log(
									"  Profile JSON checks reported issues; converted to AAS anyway for downstream validation."
								)
							else:
								_log("  Profile conversion OK — running unified pyshacl validation (v2)...")

							t0 = time.time()
							shacl_conforms, shacl_issues, shacl_meta, shacl_onto = run_shacl(aas_json, tmp_dir)

							metamodel_issues = [*profile_issue_dicts, *shacl_meta]
							ontology_issues = shacl_onto
							issues = [*metamodel_issues, *ontology_issues]
							conforms = shacl_conforms and not profile_issue_dicts

							_log(f"  Validation: conforms={conforms}, total_issues={len(issues)}  ({time.time()-t0:.1f}s)")
							_log(
								f"    Profile issues: {len(profile_issue_dicts)}  |  Metamodel issues: {len(shacl_meta)}  |  Ontology issues: {len(ontology_issues)}"
							)
			else:
				try:
					json.loads(raw_text)
				except json.JSONDecodeError as exc:
					_log(f"  JSON parse FAILED: {exc}")
					issues = [{"severity": "Violation", "message": f"Not valid JSON: {exc}"}]
					conforms = False
				else:
					_log("  JSON parse OK — running unified pyshacl validation (v2)...")
					t0 = time.time()
					conforms, issues, metamodel_issues, ontology_issues = run_shacl(raw_text, tmp_dir)
					_log(f"  Validation: conforms={conforms}, total_issues={len(issues)}  ({time.time()-t0:.1f}s)")
					_log(f"    Metamodel issues: {len(metamodel_issues)}  |  Ontology issues: {len(ontology_issues)}")

			attempt_snapshots.append({
				"attempt":      attempt,
				"conforms":     conforms,
				"violations":   len(issues),
				"metamodel":    len(metamodel_issues),
				"ontology":     len(ontology_issues),
				"verify_count": verify_count,
				"aas_json":     aas_json,
				"profile_text": raw_text if cfg.generation_mode == "json-description" else None,
			})

			if conforms:
				_log("  Validation passed!")
				break

			if metamodel_issues:
				_log("  Metamodel validation issues:")
				for issue in metamodel_issues[:10]:
					_log(f"    [{issue.get('severity','?')}] {issue.get('message','')[:120]}")
				if len(metamodel_issues) > 10:
					_log(f"    ... and {len(metamodel_issues) - 10} more")

			if ontology_issues:
				_log("  Ontology validation issues:")
				for issue in ontology_issues[:10]:
					_log(f"    [{issue.get('severity','?')}] {issue.get('message','')[:120]}")
				if len(ontology_issues) > 10:
					_log(f"    ... and {len(ontology_issues) - 10} more")

			if attempt < cfg.max_attempts:
				retry_msg = build_retry_message(
					cfg,
					attempt,
					cfg.max_attempts,
					metamodel_issues,
					ontology_issues,
				)
				if cfg.provider == "gemini":
					gemini_contents.append({"role": "user", "parts": [{"text": retry_msg}]})
				else:
					groq_history.append({"role": "user", "content": retry_msg})

	return aas_json, conforms, issues, attempt, attempt_snapshots
