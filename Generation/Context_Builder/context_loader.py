"""
Loads context files from api/context/ into a single Markdown string.
Provider-agnostic — always returns plain text.
"""
from __future__ import annotations

from pathlib import Path

from ..config import Config


def load_context(cfg: Config) -> str:
    """Return concatenated context text for use in the system instruction."""
    ctx_dir = cfg.context_dir
    parts: list[str] = []

    # 1. Shared preamble and SHACL rules
    for fname in ("00-preamble.md", "shacl-rules.md"):
        p = ctx_dir / fname
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
            print(f"  [OK] {fname}  ({p.stat().st_size // 1024} KB)")
        else:
            print(f"  [MISSING] {fname}")

    # 2. Complete valid AAS example (optional — large, ~4k tokens)
    example = ctx_dir / "valid-example.json"
    if cfg.use_example and example.exists():
        parts.append(
            "## Complete Valid AAS JSON Example\n```json\n"
            + example.read_text(encoding="utf-8")
            + "\n```"
        )
        print(f"  [OK] valid-example.json  ({example.stat().st_size // 1024} KB)")
    elif not cfg.use_example:
        print("  [SKIP] valid-example.json  (use_example=false in config)")

    # 3. Per-submodel template files
    mandatory = {"Nameplate", "HierarchicalStructures"}
    all_submodels = list(dict.fromkeys([*mandatory, *cfg.submodels]))
    for sm in all_submodels:
        f = ctx_dir / "submodels" / f"{sm.lower()}.md"
        if f.exists():
            parts.append(f.read_text(encoding="utf-8"))
            print(f"  [OK] submodels/{sm.lower()}.md  ({f.stat().st_size // 1024} KB)")

    context_text = "\n\n---\n\n".join(parts)
    print(f"\n  Total context: {len(context_text):,} chars")
    return context_text
