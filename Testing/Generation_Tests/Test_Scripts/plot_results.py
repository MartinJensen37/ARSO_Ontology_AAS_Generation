"""plot_results.py — generate the key evaluation plots from a results JSONL
and the derived aggregates produced by aggregate.py.

Plots produced (each saved as PNG + PDF in the output dir):

  1. conformance_bars.png        first-pass vs final SHACL conformance per
                                 (provider+model, ablation), grouped bars,
                                 error bars from per-equipment variance.

  2. semanticid_stack.png        stacked bar — IDTA-aligned vs exact_match
                                 vs missing — per (provider+model, ablation).
                                 Shows whether the framework gets close-to-IDTA
                                 or just template-echo.

  3. convergence_hist.png        histogram of `attempts` values per ablation.
                                 Bimodal at 1 and max_attempts means feedback
                                 helps the medium-difficulty cases but not the
                                 hard ones.

If matplotlib is unavailable, the script writes a `_plot_data_<name>.json` for
each plot so the user can render with another tool.

Usage:
    python -m evaluation.plot_results <results.jsonl> [--out-dir <dir>]

If `aggregate.py` hasn't been run yet, this script invokes it first.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Testing.Generation_Tests.Test_Scripts.aggregate import _load_jsonl, derive_cell_stats, write_csv  # noqa: E402

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


def _fall_back_dump(out_dir: Path, name: str, data: dict | list) -> None:
    target = out_dir / f"_plot_data_{name}.json"
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  matplotlib missing — wrote raw plot data to {target}")


def _save(fig, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{name}.{ext}", bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  wrote {out_dir / (name + '.png')}")


# --------------------------------------------------------------------- plots


def plot_conformance_bars(cells: list[dict], out_dir: Path) -> None:
    """Plot 1: first-pass vs final conformance per (provider+model, ablation)."""
    if not cells:
        return
    by_label: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for c in cells:
        label = f"{c['provider']}/{(c['model'] or '?')[:32]}"
        ablation = c.get("ablation", "full")
        by_label[label][ablation + "/first"].append(c["first_pass_conformance_rate"])
        by_label[label][ablation + "/final"].append(c["final_conformance_rate"])

    labels = sorted(by_label.keys())
    ablations = sorted({k for d in by_label.values() for k in d.keys()})

    if not _HAS_MPL:
        _fall_back_dump(out_dir, "conformance_bars",
                        {"labels": labels, "ablations": ablations,
                         "by_label": {l: {k: v for k, v in d.items()} for l, d in by_label.items()}})
        return

    n_groups = len(labels)
    n_bars = len(ablations)
    width = 0.8 / max(n_bars, 1)
    x = list(range(n_groups))

    fig, ax = plt.subplots(figsize=(max(8, 1.6 * n_groups), 5))
    for i, ab in enumerate(ablations):
        means = []
        errs = []
        for label in labels:
            vals = by_label[label].get(ab, [])
            means.append(statistics_mean(vals))
            errs.append(statistics_stddev(vals))
        offsets = [xi + (i - (n_bars - 1) / 2) * width for xi in x]
        ax.bar(offsets, means, width, yerr=errs, label=ab, capsize=2)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Conformance rate")
    ax.set_title("SHACL conformance: first-pass vs final, per LLM × ablation")
    ax.legend(fontsize=7, loc="upper left", ncol=2)
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    _save(fig, out_dir, "conformance_bars")


def plot_semanticid_stack(cells: list[dict], out_dir: Path) -> None:
    """Plot 2: stacked bar of semanticId quality per (provider+model, ablation)."""
    if not cells:
        return
    rows: list[tuple[str, str, float, float, float]] = []
    for c in cells:
        label = f"{c['provider']}/{(c['model'] or '?')[:24]}/{c['ablation']}"
        ms = c["metric_stats"]
        idta = ms["semanticid_idta_alignment"]["mean"]
        exact = ms["semanticid_exact_match"]["mean"]
        present = ms["semanticid_present_rate"]["mean"]
        # Stack: bottom = exact, middle = idta_only (idta − exact), top = present_but_unaligned (present − idta), missing = 1 − present
        rows.append((
            label,
            c.get("equipment_id", ""),
            max(0.0, exact),
            max(0.0, idta - exact),
            max(0.0, present - idta),
        ))
    rows.sort(key=lambda r: (r[0], r[1]))

    if not _HAS_MPL:
        _fall_back_dump(out_dir, "semanticid_stack", [{"label": r[0], "equipment": r[1],
                                                       "exact": r[2], "idta_only": r[3], "present_unaligned": r[4]}
                                                       for r in rows])
        return

    fig, ax = plt.subplots(figsize=(max(8, 0.5 * len(rows)), 5))
    x = list(range(len(rows)))
    exact = [r[2] for r in rows]
    idta = [r[3] for r in rows]
    pres = [r[4] for r in rows]
    miss = [max(0.0, 1.0 - (r[2] + r[3] + r[4])) for r in rows]

    ax.bar(x, exact, label="exact match", color="#2a9d8f")
    ax.bar(x, idta, bottom=exact, label="IDTA-aligned (no exact)", color="#8ab17d")
    ax.bar(x, pres, bottom=[a + b for a, b in zip(exact, idta)],
           label="semanticId present but unaligned", color="#e9c46a")
    ax.bar(x, miss, bottom=[a + b + c for a, b, c in zip(exact, idta, pres)],
           label="missing semanticId", color="#e76f51")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{r[0]}\n{r[1]}" for r in rows], rotation=70, ha="right", fontsize=7)
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Fraction of expected SMEs")
    ax.set_title("Semantic-ID correctness per LLM × ablation × equipment")
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    _save(fig, out_dir, "semanticid_stack")


def plot_convergence_hist(rows: list[dict], out_dir: Path) -> None:
    """Plot 3: histogram of `attempts` per ablation, faceted lightly."""
    by_ab: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        v = (r.get("metrics") or {}).get("attempts")
        ab = r.get("ablation", "?")
        if isinstance(v, int) and v > 0:
            by_ab[ab].append(v)

    if not _HAS_MPL:
        _fall_back_dump(out_dir, "convergence_hist", by_ab)
        return

    if not by_ab:
        return
    max_a = max(max(v) for v in by_ab.values())
    bins = list(range(1, max_a + 2))
    fig, ax = plt.subplots(figsize=(8, 5))
    for ab, values in sorted(by_ab.items()):
        ax.hist(values, bins=bins, alpha=0.55, label=ab, edgecolor="white")
    ax.set_xlabel("attempts used")
    ax.set_ylabel("count of experiments")
    ax.set_xticks(bins[:-1])
    ax.set_title("Pipeline convergence — distribution of attempts to conformance")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    _save(fig, out_dir, "convergence_hist")



# --------------------------------------------------------------------- helpers


def statistics_mean(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    return sum(xs) / len(xs)


def statistics_stddev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = statistics_mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


# --------------------------------------------------------------------- CLI


def main() -> int:
    p = argparse.ArgumentParser(description="Generate evaluation plots from results.jsonl.")
    p.add_argument("results", type=Path, help="Path to results.jsonl.")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Where to write plots. Defaults to results file's parent dir / 'plots'.")
    args = p.parse_args()

    rows = _load_jsonl(args.results)
    if not rows:
        print(f"No rows loaded from {args.results}")
        return 1

    out_dir = args.out_dir or (args.results.parent / "plots")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out_dir / "aggregate.csv")

    cells = derive_cell_stats(rows)
    (out_dir / "derived.json").write_text(json.dumps(cells, indent=2, ensure_ascii=False), encoding="utf-8")

    if not _HAS_MPL:
        print("matplotlib not installed — falling back to JSON dumps under", out_dir)

    plot_conformance_bars(cells, out_dir)
    plot_semanticid_stack(cells, out_dir)
    plot_convergence_hist(rows, out_dir)

    print(f"\nPlots in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
