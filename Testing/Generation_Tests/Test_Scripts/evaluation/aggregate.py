"""aggregate.py — JSONL of experiments → derived metrics ready for plotting.

Reads `evaluation/results/<run_id>/results.jsonl` (or any merged file) and
produces:
  - `aggregate.csv`        flat table with one row per experiment + cost/tokens
  - `derived.json`         per-(provider, model, ablation, equipment) means and stddevs
  - `improvement.json`     `improvement_with_feedback` and `improvement_with_templates`
                           computed by joining ablation cells

This module has zero plotting dependencies — `plot_results.py` consumes the
outputs here. Pure stdlib for portability.

Usage:
    python -m evaluation.aggregate <results.jsonl> [--out-dir <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


# Numeric metrics worth aggregating with mean ± stddev across repetitions.
_AGG_METRICS = (
    "shacl_conforms",
    "shacl_metamodel_count",
    "shacl_ontology_count",
    "shacl_violation_count",
    "submodel_coverage",
    "sme_coverage",
    "mandatory_sme_coverage",
    "optional_sme_coverage",
    "sme_precision",
    "sme_recall",
    "sme_f1",
    "hallucination_rate",
    "semanticid_present_rate",
    "semanticid_idta_alignment",
    "semanticid_exact_match",
    "value_substring_match",
    "verify_rate",
    "idshort_format_violations",
    "value_format_violations",
    "skill_links_to_aid_action",
    "capability_realizedby_skill",
    "attempts",
    "wallclock_seconds",
    "input_tokens_estimate",
    "output_tokens_estimate",
    "cost_estimate_usd",
)

# Columns flattened into the CSV.
_FLAT_COLS = (
    "timestamp",
    "equipment_id", "asset_name", "protocol",
    "provider", "model", "mode", "pipeline", "ablation", "repetition",
    "max_attempts", "use_rag", "use_example",
    "experiment_dir",
    "error",
    *_AGG_METRICS,
)


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _flatten(row: dict) -> dict:
    out: dict[str, Any] = {}
    for col in _FLAT_COLS:
        if col in row:
            out[col] = row[col]
        elif col in (row.get("metrics") or {}):
            out[col] = row["metrics"].get(col)
        else:
            out[col] = None
    return out


def write_csv(rows: list[dict], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_FLAT_COLS))
        w.writeheader()
        for row in rows:
            w.writerow(_flatten(row))


# --------------------------------------------------------------------- group stats


def _cell_key(row: dict) -> tuple:
    return (
        row.get("provider"),
        row.get("model"),
        row.get("ablation"),
        row.get("equipment_id"),
        row.get("mode"),
        row.get("pipeline"),
    )


def _group_by_cell(rows: list[dict]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[_cell_key(r)].append(r)
    return groups


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean": math.nan, "stddev": math.nan, "min": math.nan, "max": math.nan}
    return {
        "n":       len(values),
        "mean":    float(statistics.fmean(values)),
        "stddev":  float(statistics.pstdev(values)) if len(values) > 1 else 0.0,
        "min":     float(min(values)),
        "max":     float(max(values)),
    }


def _coerce_numeric(v: Any) -> float | None:
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    return None


def derive_cell_stats(rows: list[dict]) -> list[dict]:
    """Return [{cell, n_runs, conformance_rate, metric_stats: {…}}] per cell."""
    groups = _group_by_cell(rows)
    out: list[dict] = []
    for key, group in groups.items():
        provider, model, ablation, equipment_id, mode, pipeline = key
        cell_id = f"{provider}/{model}/{ablation}/{equipment_id}/{mode}/{pipeline}"
        metric_stats: dict[str, Any] = {}
        for metric in _AGG_METRICS:
            values: list[float] = []
            for r in group:
                src = (r.get("metrics") or {})
                v = _coerce_numeric(src.get(metric))
                if v is not None:
                    values.append(v)
            metric_stats[metric] = _stats(values)
        first_pass_count = sum(
            1 for r in group
            if (r.get("metrics") or {}).get("attempts") == 1
            and (r.get("metrics") or {}).get("shacl_conforms")
        )
        final_count = sum(
            1 for r in group
            if (r.get("metrics") or {}).get("shacl_conforms")
        )
        n = len(group)
        out.append({
            "cell": cell_id,
            "provider": provider, "model": model,
            "ablation": ablation, "equipment_id": equipment_id,
            "mode": mode, "pipeline": pipeline,
            "n_runs": n,
            "first_pass_conformance_rate": first_pass_count / n if n else 0.0,
            "final_conformance_rate":      final_count / n if n else 0.0,
            "error_rate":                  sum(1 for r in group if r.get("error")) / n if n else 0.0,
            "metric_stats": metric_stats,
        })
    return out


# --------------------------------------------------------------------- ablation deltas


def derive_improvement(cell_stats: list[dict]) -> dict[str, list[dict]]:
    """Compute pairwise ablation deltas:
       improvement_with_feedback   = full vs no-feedback   (same model+equipment)
       improvement_with_templates  = full vs no-templates  (same model+equipment)
       improvement_v2_over_v1      = pipeline=v2 vs v1     (same model+equipment+ablation)
       improvement_with_rag        = use_rag/example deltas (when available)
    """
    by_key: dict[tuple, dict] = {}
    for c in cell_stats:
        key = (c["provider"], c["model"], c["equipment_id"], c["mode"], c["ablation"], c["pipeline"])
        by_key[key] = c

    def _get(provider: str, model: str, equipment: str, mode: str, ablation: str, pipeline: str) -> dict | None:
        return by_key.get((provider, model, equipment, mode, ablation, pipeline))

    feedback: list[dict] = []
    templates: list[dict] = []
    pipeline_delta: list[dict] = []

    seen_axes: set[tuple] = set()
    for (provider, model, equipment, mode, ablation, pipeline), cell in by_key.items():
        axis = (provider, model, equipment, mode, pipeline)
        if axis in seen_axes:
            continue
        seen_axes.add(axis)
        full = _get(provider, model, equipment, mode, "full", pipeline)
        no_fb = _get(provider, model, equipment, mode, "no-feedback", pipeline)
        no_tpl = _get(provider, model, equipment, mode, "no-templates", pipeline)
        if full and no_fb:
            feedback.append({
                "axis": list(axis),
                "delta_final_conformance":     full["final_conformance_rate"] - no_fb["final_conformance_rate"],
                "delta_first_pass_conformance": full["first_pass_conformance_rate"] - no_fb["first_pass_conformance_rate"],
                "delta_sme_f1":                full["metric_stats"]["sme_f1"]["mean"] - no_fb["metric_stats"]["sme_f1"]["mean"],
                "delta_attempts":              full["metric_stats"]["attempts"]["mean"] - no_fb["metric_stats"]["attempts"]["mean"],
            })
        if full and no_tpl:
            templates.append({
                "axis": list(axis),
                "delta_final_conformance":     full["final_conformance_rate"] - no_tpl["final_conformance_rate"],
                "delta_semanticid_match":      full["metric_stats"]["semanticid_exact_match"]["mean"] - no_tpl["metric_stats"]["semanticid_exact_match"]["mean"],
                "delta_sme_f1":                full["metric_stats"]["sme_f1"]["mean"] - no_tpl["metric_stats"]["sme_f1"]["mean"],
            })

    # v1 vs v2 (same provider+model+equipment+mode+ablation, different pipeline).
    seen_p_axes: set[tuple] = set()
    for (provider, model, equipment, mode, ablation, pipeline), cell in by_key.items():
        axis = (provider, model, equipment, mode, ablation)
        if axis in seen_p_axes:
            continue
        seen_p_axes.add(axis)
        v1 = _get(provider, model, equipment, mode, ablation, "v1")
        v2 = _get(provider, model, equipment, mode, ablation, "v2")
        if v1 and v2:
            pipeline_delta.append({
                "axis": list(axis),
                "v1_final_conformance":  v1["final_conformance_rate"],
                "v2_final_conformance":  v2["final_conformance_rate"],
                "delta_final_conformance": v2["final_conformance_rate"] - v1["final_conformance_rate"],
                "delta_sme_f1":          v2["metric_stats"]["sme_f1"]["mean"] - v1["metric_stats"]["sme_f1"]["mean"],
            })

    return {
        "improvement_with_feedback":  feedback,
        "improvement_with_templates": templates,
        "improvement_v2_over_v1":     pipeline_delta,
    }


# --------------------------------------------------------------------- CLI


def main() -> int:
    p = argparse.ArgumentParser(description="Aggregate evaluation JSONL into CSV + derived JSON.")
    p.add_argument("results", type=Path, help="Path to results.jsonl (or merged JSONL).")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Where to write aggregate.csv / derived.json / improvement.json. "
                        "Defaults to the results file's parent directory.")
    args = p.parse_args()

    rows = _load_jsonl(args.results)
    if not rows:
        print(f"No rows loaded from {args.results}")
        return 1

    out_dir = args.out_dir or args.results.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "aggregate.csv"
    write_csv(rows, csv_path)
    print(f"  wrote {csv_path}  ({len(rows)} rows)")

    cells = derive_cell_stats(rows)
    derived_path = out_dir / "derived.json"
    derived_path.write_text(json.dumps(cells, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {derived_path}  ({len(cells)} cells)")

    improvement = derive_improvement(cells)
    imp_path = out_dir / "improvement.json"
    imp_path.write_text(json.dumps(improvement, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"  wrote {imp_path}  "
        f"feedback={len(improvement['improvement_with_feedback'])}  "
        f"templates={len(improvement['improvement_with_templates'])}  "
        f"v2vsv1={len(improvement['improvement_v2_over_v1'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
