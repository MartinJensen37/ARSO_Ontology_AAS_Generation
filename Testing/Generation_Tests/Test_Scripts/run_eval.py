"""Evaluation runner — calls the v2 pipeline directly (no HTTP/SSE) and saves
a complete reproducible dossier per experiment.

Output layout:
    evaluation/results/<run_id>/
        manifest.json              run-level metadata + counts + matrix snapshot
        results.jsonl              one row per experiment (analysis-friendly)
        <experiment_dir>/
            metrics.json           the same row, broken out for browsability
            aas_output.json        generated AAS JSON (final attempt)
            prompts/
                system_prompt.txt
                user_prompt.txt
                spec_text.md       combined datasheet + interface text fed in
                profile_attempt_N.json  raw LLM profile JSON for attempt N (json-description mode)
            shacl/
                data.ttl           the AAS-as-RDF projection
                report.ttl         the SHACL validation report
                issues.json        parsed list of {severity, message, focus_node, source}
            log.txt                pipeline progress_callback log
            config_snapshot.json   resolved Config minus API keys
            equipment_snapshot.yaml
            ground_truth_snapshot.yaml
            error.txt              present only when something failed

The JSONL is the analysis primitive — `plot_results.py` and `aggregate.py` read
it. The per-experiment subfolders give you something to point at when a row
looks weird ("which prompt produced this output?").

Usage:
    python -m evaluation.run_eval --equipment ca18clc12bpm1 --provider claude \\
        --model claude-opus-4-5-20251101 --ablation full \\
        --run-id paper-quickcheck-2026-04-25

    python -m evaluation.run_eval --matrix evaluation/matrix.yaml \\
        --run-id paper-fullsweep-2026-04-25
"""
from __future__ import annotations

import argparse
import base64
import dataclasses
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Generation.config import load_config, Config  
from Generation.Context_Builder.context_loader import load_context  
from Generation.Context_Builder.RAG.rag_loader import load_rag  
from Generation.Context_Builder.RAG.prompt_builder import build_system_instruction, build_user_prompt  
from Generation.Context_Builder.Parsing.pdf_extractor import extract_pdf_text  
from Generation.pipeline import run_pipeline  
from Validation.Validator.validator import run_shacl  

from Testing.Generation_Tests.Test_Scripts import metrics as M  


_EVAL_DIR = Path(__file__).resolve().parent
_EQUIPMENT_DIR = _EVAL_DIR / "equipment"
_GROUND_TRUTH_DIR = _EVAL_DIR / "ground_truth"
_RESULTS_DIR = _EVAL_DIR / "results"


# --------------------------------------------------------------------- helpers


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf_base64(path: Path | None) -> str | None:
    if path is None or not path.exists() or path.suffix.lower() != ".pdf":
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _safe_segment(text: str) -> str:
    """Make a string safe for use as a file/folder name on Windows + Linux."""
    keep = []
    for ch in text:
        if ch.isalnum() or ch in "-._":
            keep.append(ch)
        elif ch in "/\\: ":
            keep.append("-")
        # silently drop anything else
    out = "".join(keep).strip("-._")
    return out or "x"


def _experiment_dir_name(equipment_id: str, provider: str, model: str | None,
                         mode: str, ablation: str, pipeline_label: str,
                         repetition: int) -> str:
    model_seg = _safe_segment(model) if model else "default"
    return (
        f"{_safe_segment(equipment_id)}"
        f"__{_safe_segment(provider)}-{model_seg}"
        f"__{_safe_segment(mode)}"
        f"__{_safe_segment(ablation)}"
        f"__{_safe_segment(pipeline_label)}"
        f"__rep{repetition:02d}"
    )


def _config_snapshot(cfg: Config) -> dict:
    """Serialize Config for the dossier — strip secrets, stringify Paths."""
    raw = dataclasses.asdict(cfg)
    for sensitive in ("api_key", "gemini_api_key", "groq_api_key", "claude_api_key"):
        if sensitive in raw and raw[sensitive]:
            raw[sensitive] = "<redacted>"
    for key, value in list(raw.items()):
        if isinstance(value, Path):
            raw[key] = str(value)
        elif isinstance(value, list):
            raw[key] = [str(v) if isinstance(v, Path) else v for v in value]
    return raw


def _interface_summary(equipment: dict, equipment_dir: Path) -> str:
    """Build a text block of all interface files for inclusion in the prompt.

    PDFs are extracted to Markdown text (Claude / text path).
    For Gemini, PDFs are sent separately as inline_data via
    _collect_extra_pdf_gemini_parts(); only their filename is noted here so
    the model knows the document exists without re-embedding the bytes as text.
    """
    blocks: list[str] = []
    for entry in equipment.get("interface_files", []) or []:
        rel = entry.get("path") if isinstance(entry, dict) else None
        if not rel:
            continue
        kind = (entry.get("kind") or "").lower()
        path = (equipment_dir / rel).resolve()
        if not path.exists():
            continue
        if kind.startswith("opcua") or path.suffix.lower() == ".xml":
            xml_text = _read_text(path)
            blocks.append(f"### Interface: {path.name} (OPC UA NodeSet XML)\n```xml\n{xml_text}\n```")
        elif kind.startswith("csv") or path.suffix.lower() == ".csv":
            csv_text = _read_text(path)
            blocks.append(f"### Interface: {path.name} (CSV register / signal list)\n```csv\n{csv_text}\n```")
        elif kind.startswith("openplc") or path.suffix.lower() == ".plcopen":
            xml_text = _read_text(path)
            blocks.append(f"### Interface: {path.name} (OpenPLC / PLCopen XML)\n```xml\n{xml_text}\n```")
        elif path.suffix.lower() == ".pdf":
            try:
                pdf_text = extract_pdf_text(path, max_chars=40_000)
                kind_label = kind or "PDF Specification"
                blocks.append(f"### Interface: {path.name} ({kind_label})\n{pdf_text}")
            except Exception as exc:
                blocks.append(f"### Interface: {path.name} (PDF — extraction failed: {exc})")
        else:
            text = _read_text(path)
            blocks.append(f"### Interface: {path.name}\n```\n{text}\n```")
    return "\n\n".join(blocks)


def _collect_extra_pdf_gemini_parts(equipment: dict, equipment_dir: Path) -> list[dict]:
    """Return Gemini inline_data parts for every PDF listed in interface_files.

    The main datasheet PDF is handled separately by run_eval (sent as pdf_b64).
    This function covers additional PDFs (interface specs, BOM sheets, etc.) so
    Gemini receives all documents natively rather than as extracted text.
    """
    parts = []
    for entry in equipment.get("interface_files", []) or []:
        rel = entry.get("path") if isinstance(entry, dict) else None
        if not rel:
            continue
        path = (equipment_dir / rel).resolve()
        if path.suffix.lower() == ".pdf" and path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
            parts.append({"inline_data": {"mime_type": "application/pdf", "data": b64}})
            print(f"  [PDF] {path.name} ({path.stat().st_size // 1024} KB) queued for Gemini inline_data")
    return parts


# --------------------------------------------------------------------- ablations


def _apply_ablation(cfg: Config, ablation: str) -> Config:
    cfg = dataclasses.replace(cfg)
    if ablation == "full":
        return cfg
    if ablation == "no-feedback":
        cfg.max_attempts = 1
        return cfg
    if ablation in ("no-templates", "zero-shot"):
        stub_dir = _EVAL_DIR / "_ablation_minimal_context"
        stub_dir.mkdir(exist_ok=True)
        (stub_dir / "00-preamble.md").write_text(
            "# Generation context (minimal — ablation: no-templates)\n\n"
            "Generate an AAS Part 2 v3.1 JSON document for the asset described in the user prompt. "
            "Use the AAS metamodel correctly: assetAdministrationShells, submodels, conceptDescriptions. "
            "Output ONLY a single valid JSON object. Use [VERIFY: reason] only on mandatory fields you cannot determine.\n",
            encoding="utf-8",
        )
        (stub_dir / "shacl-rules.md").write_text("(no domain rules in this ablation)\n", encoding="utf-8")
        (stub_dir / "submodels").mkdir(exist_ok=True)
        cfg.context_dir = stub_dir
        if ablation == "zero-shot":
            cfg.use_rag = False
            cfg.use_example = False
        return cfg
    raise ValueError(f"Unknown ablation: {ablation}")


# --------------------------------------------------------------------- one experiment


def _run_one(
    *,
    equipment_id: str,
    provider: str,
    model: str | None,
    mode: str,
    ablation: str,
    repetition: int,
    pipeline_label: str,
    run_dir: Path,
) -> dict[str, Any]:
    """Run a single experiment, write the dossier, return the metrics row."""
    equipment_dir_src = _EQUIPMENT_DIR / equipment_id
    equipment_yaml = equipment_dir_src / "equipment.yaml"
    if not equipment_yaml.exists():
        raise FileNotFoundError(f"equipment.yaml missing: {equipment_yaml}")

    equipment = _read_yaml(equipment_yaml)

    # Ground truth: prefer a path declared in equipment.yaml (relative to its dir),
    # fall back to the central ground_truth/<equipment_id>.yaml convention.
    ground_truth_rel = equipment.get("ground_truth")
    if ground_truth_rel:
        ground_truth_yaml = (equipment_dir_src / ground_truth_rel).resolve()
    else:
        ground_truth_yaml = _GROUND_TRUTH_DIR / f"{equipment_id}.yaml"
    if not ground_truth_yaml.exists():
        raise FileNotFoundError(f"ground truth missing: {ground_truth_yaml}")

    ground_truth = _read_yaml(ground_truth_yaml)

    pdf_path = equipment.get("datasheet")
    pdf_full = (equipment_dir_src / pdf_path).resolve() if pdf_path else None
    spec_md_path = equipment_dir_src / "spec.md"
    interface_summary = _interface_summary(equipment, equipment_dir_src)
    spec_text = _read_text(spec_md_path)
    spec_text_combined = "\n\n---\n\n".join(s for s in (spec_text, interface_summary) if s)

    # ------ Config tailored to this experiment ------
    base_cfg = load_config()
    cfg = dataclasses.replace(
        base_cfg,
        provider=provider,
        api_key=getattr(base_cfg, f"{provider}_api_key", "") or base_cfg.api_key,
        asset_name=str(equipment.get("asset_name", equipment_id)),
        base_url=str(equipment.get("base_url", base_cfg.base_url)),
        pdf_path=pdf_full,
        submodels=list(equipment.get("selected_submodels", base_cfg.submodels)),
        generation_mode=mode,
        max_attempts=int(equipment.get("max_attempts", base_cfg.max_attempts)),
        models=[model] if model else base_cfg.models,
    )
    cfg = _apply_ablation(cfg, ablation)

    # ------ assemble inputs ------
    pdf_b64 = _read_pdf_base64(pdf_full) if cfg.provider == "gemini" else None
    pdf_text = ""
    if cfg.provider != "gemini" and pdf_full is not None and pdf_full.exists():
        pdf_text = extract_pdf_text(pdf_full, max_chars=cfg.max_pdf_chars)

    rag_gemini_parts, rag_text_blocks = load_rag(cfg) if cfg.use_rag else ([], [])

    # For Gemini: prepend any additional PDFs from interface_files as inline_data parts
    # so the model receives all documents natively (not as extracted text).
    if cfg.provider == "gemini":
        extra_pdf_parts = _collect_extra_pdf_gemini_parts(equipment, equipment_dir_src)
        rag_gemini_parts = [*extra_pdf_parts, *rag_gemini_parts]

    system_instruction = build_system_instruction(cfg, load_context(cfg), rag_text_blocks)
    user_prompt = build_user_prompt(
        cfg,
        pdf_b64,
        pdf_text,
        spec_sheet_text=spec_text_combined,
        supplemental_context=interface_summary or None,
    )

    # ------ artifact dir for this experiment ------
    exp_dir = run_dir / _experiment_dir_name(
        equipment_id, provider, model, mode, ablation, pipeline_label, repetition
    )
    (exp_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (exp_dir / "shacl").mkdir(parents=True, exist_ok=True)

    # Save inputs up-front so even a crashed run leaves a useful trace.
    (exp_dir / "prompts" / "system_prompt.txt").write_text(system_instruction, encoding="utf-8")
    (exp_dir / "prompts" / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")
    (exp_dir / "prompts" / "spec_text.md").write_text(spec_text_combined or "(empty)\n", encoding="utf-8")
    (exp_dir / "config_snapshot.json").write_text(json.dumps(_config_snapshot(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
    (exp_dir / "equipment_snapshot.yaml").write_text(equipment_yaml.read_text(encoding="utf-8"), encoding="utf-8")
    (exp_dir / "ground_truth_snapshot.yaml").write_text(ground_truth_yaml.read_text(encoding="utf-8"), encoding="utf-8")

    # ------ run pipeline ------
    log_lines: list[str] = []
    def _capture(msg: str) -> None:
        log_lines.append(msg)

    t0 = time.time()
    error: str | None = None
    aas_json = ""
    conforms = False
    issues: list[dict] = []
    attempts = 0
    attempt_snapshots: list[dict] = []
    try:
        aas_json, conforms, issues, attempts, attempt_snapshots = run_pipeline(
            cfg, system_instruction, user_prompt, pdf_b64, rag_gemini_parts,
            progress_callback=_capture,
        )
    except SystemExit as exc:
        error = f"SystemExit: {exc}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
    wallclock = time.time() - t0

    (exp_dir / "log.txt").write_text("\n".join(log_lines), encoding="utf-8")

    # ------ persist AAS output + parse ------
    if aas_json:
        (exp_dir / "aas_output.json").write_text(aas_json, encoding="utf-8")
    aas_doc: dict = {}
    if aas_json:
        try:
            aas_doc = json.loads(aas_json)
        except Exception as exc:
            error = (error + " | " if error else "") + f"AAS JSON parse failed: {exc}"

    # ------ re-run validation into the artifact dir so we have data.ttl + report.ttl ------
    if aas_json and not error:
        try:
            with tempfile.TemporaryDirectory() as _t:
                tmp = Path(_t)
                run_shacl(aas_json, tmp)
                # run_shacl wrote input.json + data.ttl + report.ttl to tmp.
                for fname in ("data.ttl", "report.ttl"):
                    src = tmp / fname
                    if src.exists():
                        shutil.copy2(src, exp_dir / "shacl" / fname)
        except Exception as exc:
            (exp_dir / "shacl" / "_re_validate_error.txt").write_text(
                f"Re-validation failed: {exc}\n{traceback.format_exc()}", encoding="utf-8"
            )

    # Compute per-attempt coverage from the stored aas_json in each snapshot.
    # Both aas_json and profile_text are stripped after use to keep results.jsonl compact.
    for snap in attempt_snapshots:
        snap_profile_text = snap.pop("profile_text", None)
        if snap_profile_text:
            profile_path = exp_dir / "prompts" / f"profile_attempt_{snap['attempt']}.json"
            profile_path.write_text(snap_profile_text, encoding="utf-8")

        snap_aas_json = snap.pop("aas_json", None)
        if snap_aas_json:
            try:
                snap_doc = json.loads(snap_aas_json)
                cov = M.coverage_metrics(snap_doc, ground_truth)
                snap["mandatory_sme_coverage"] = cov["mandatory_sme_coverage"]
                snap["value_substring_match"]  = cov["value_substring_match"]
            except Exception:
                pass

    metamodel = [i for i in issues if (i.get("source") == "metamodel" or "metamodel" in i.get("source",""))]
    ontology = [i for i in issues if i.get("source") == "ontology"]
    if not metamodel and not ontology and issues:
        metamodel = issues
    (exp_dir / "shacl" / "issues.json").write_text(
        json.dumps({"conforms": bool(conforms), "metamodel": metamodel, "ontology": ontology}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ------ metrics ------
    metric_row = M.all_metrics(
        aas_doc, ground_truth,
        conforms=conforms,
        metamodel_issues=metamodel,
        ontology_issues=ontology,
        attempts=attempts,
        wallclock_seconds=wallclock,
        system_prompt=system_instruction,
        user_prompt=user_prompt,
        output_text=aas_json,
        provider=cfg.provider,
        model=(model or (cfg.models[0] if cfg.models else "")),
    )

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "equipment_id": equipment_id,
        "asset_name": cfg.asset_name,
        "protocol": equipment.get("protocol", ""),
        "provider": cfg.provider,
        "model": model or (cfg.models[0] if cfg.models else "default"),
        "mode": cfg.generation_mode,
        "pipeline": pipeline_label,
        "ablation": ablation,
        "repetition": repetition,
        "max_attempts": cfg.max_attempts,
        "use_rag": cfg.use_rag,
        "use_example": cfg.use_example,
        "experiment_dir": exp_dir.name,
        "metrics": metric_row,
        "attempts_detail": attempt_snapshots,
        "error": error,
    }

    (exp_dir / "metrics.json").write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
    if error:
        (exp_dir / "error.txt").write_text(error, encoding="utf-8")

    return row


# --------------------------------------------------------------------- run-level


def _open_run(run_id: str | None, matrix: dict | None, label: str | None) -> Path:
    """Create a run dir under evaluation/results and seed manifest.json."""
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + (f"_{_safe_segment(label)}" if label else "")
    run_dir = _RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": label,
        "matrix_snapshot": matrix or None,
        "experiments": [],          # populated as we go
        "n_total": 0,
        "n_completed": 0,
        "n_errors": 0,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return run_dir


def _append_to_run(run_dir: Path, row: dict) -> None:
    with (run_dir / "results.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["experiments"].append({
        "experiment_dir": row.get("experiment_dir"),
        "equipment_id": row.get("equipment_id"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "ablation": row.get("ablation"),
        "repetition": row.get("repetition"),
        "conforms": row.get("metrics", {}).get("shacl_conforms"),
        "error": bool(row.get("error")),
    })
    manifest["n_completed"] += 1
    if row.get("error"):
        manifest["n_errors"] += 1
    manifest["last_updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _set_run_total(run_dir: Path, total: int) -> None:
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["n_total"] = total
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------- matrix sweep


def _run_matrix(matrix: dict, run_dir: Path) -> None:
    repetitions = int(matrix.get("repetitions", 1))
    equipment_ids = matrix.get("equipment", [])
    configs = matrix.get("configs", [])
    total = len(equipment_ids) * len(configs) * repetitions
    _set_run_total(run_dir, total)

    n = 0
    for rep in range(repetitions):
        for eq in equipment_ids:
            for c in configs:
                n += 1
                pipeline_label = c.get("pipeline", "v2")
                tag = (
                    f"[{n}/{total}]  {eq}  {c.get('provider')}/{c.get('model','*')}  "
                    f"{c.get('ablation','full')}  rep={rep+1}"
                )
                print(tag)
                try:
                    row = _run_one(
                        equipment_id=eq,
                        provider=c["provider"],
                        model=c.get("model"),
                        mode=c.get("mode", "json-description"),
                        ablation=c.get("ablation", "full"),
                        repetition=rep + 1,
                        pipeline_label=pipeline_label,
                        run_dir=run_dir,
                    )
                except Exception as exc:
                    row = {
                        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "equipment_id": eq,
                        "provider": c.get("provider"),
                        "model": c.get("model"),
                        "ablation": c.get("ablation", "full"),
                        "repetition": rep + 1,
                        "metrics": {},
                        "error": f"runner exception: {type(exc).__name__}: {exc}",
                    }
                _append_to_run(run_dir, row)
    print(f"\nWrote {n} result rows to {run_dir / 'results.jsonl'}")


# --------------------------------------------------------------------- CLI


def main() -> int:
    p = argparse.ArgumentParser(description="Run evaluation experiments and save full dossiers.")
    p.add_argument("--equipment", help="Equipment ID under evaluation/equipment/")
    p.add_argument("--provider", choices=["gemini", "groq", "claude"], default="claude")
    p.add_argument("--model", default=None, help="Specific model id; defaults to config.yaml's first model for the provider.")
    p.add_argument("--mode", choices=["json", "json-description"], default="json-description")
    p.add_argument("--ablation", choices=["full", "no-feedback", "no-templates", "zero-shot"], default="full")
    p.add_argument("--pipeline", default="v2", help="Pipeline label (free text — kept on the row).")
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--matrix", type=Path, help="Path to a YAML sweep matrix (overrides single-experiment flags).")
    p.add_argument("--run-id", default=None, help="Override the auto-generated run dir name (under evaluation/results/).")
    p.add_argument("--label", default=None, help="Free-text label embedded into the auto run-id.")
    args = p.parse_args()

    if args.matrix:
        matrix = _read_yaml(args.matrix)
        run_dir = _open_run(args.run_id, matrix, args.label)
        # Snapshot the matrix YAML next to the manifest so the run is reproducible.
        shutil.copy2(args.matrix, run_dir / "matrix.yaml")
        _run_matrix(matrix, run_dir)
        return 0

    if not args.equipment:
        p.error("either --equipment or --matrix is required")

    run_dir = _open_run(args.run_id, None, args.label)
    _set_run_total(run_dir, args.repetitions)
    for rep in range(args.repetitions):
        print(f"[{rep+1}/{args.repetitions}] {args.equipment}  {args.provider}/{args.model or '*'}  {args.ablation}")
        try:
            row = _run_one(
                equipment_id=args.equipment,
                provider=args.provider,
                model=args.model,
                mode=args.mode,
                ablation=args.ablation,
                repetition=rep + 1,
                pipeline_label=args.pipeline,
                run_dir=run_dir,
            )
        except Exception as exc:
            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "equipment_id": args.equipment,
                "provider": args.provider,
                "model": args.model,
                "ablation": args.ablation,
                "repetition": rep + 1,
                "metrics": {},
                "error": f"runner exception: {type(exc).__name__}: {exc}",
            }
        _append_to_run(run_dir, row)
        m = row.get("metrics") or {}
        snaps = row.get("attempts_detail") or []
        if m:
            v_per_attempt = " -> ".join(
                f"A{s['attempt']}:{s['violations']}v" for s in snaps
            ) or "n/a"
            print(
                f"  -> conforms={m.get('shacl_conforms')}, "
                f"violations/attempt=[{v_per_attempt}], "
                f"mand_cov={m.get('mandatory_sme_coverage', 0):.0%}, "
                f"val_acc={m.get('value_substring_match', 0):.0%}, "
                f"verify={m.get('verify_total', 0)}, "
                f"wallclock={m.get('wallclock_seconds', 0):.1f}s"
            )
    print(f"\nDossier: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
