"""
Loads generation/config.yaml and exposes a single Config dataclass.
All other modules import from here â€” no scattered os.environ calls elsewhere.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_GEN_DIR  = Path(__file__).parent
_ROOT     = _GEN_DIR.parent
_DEFAULT_SHACL_SHAPES = [
    Path("Ontology/SHACL/Generated/shapes.generated.shacl.ttl"),
    Path("Ontology/SHACL/Manual/arso-rules.shacl.ttl"),
]
_DEFAULT_ONTOLOGIES = [
    Path("Ontology/CSS/CSS-Ontology.ttl"),
    Path("Ontology/ARSO/ARSO_AAS.ttl"),
]

# Add project root to sys.path so sibling top-level packages can be imported.
for _p in [str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Config:
    # Provider
    provider: str                   # "gemini" | "groq" | "claude"
    api_key: str                    # resolved for the chosen provider

    # Asset
    asset_name: str
    base_url: str
    pdf_path: Optional[Path]        # None = text-only mode

    # Submodels
    submodels: list[str]

    # Generation mode
    generation_mode: str            # "json" | "json-description"
    profile_example_path: Optional[Path]

    # Options
    use_rag: bool
    use_example: bool
    force_full_aas_output: bool
    max_pdf_chars: Optional[int]
    max_attempts: int

    # Model fallback lists
    models: list[str]

    # Paths (resolved at load time)
    gen_dir: Path                   # generation/
    root_dir: Path                  # repo root
    context_dir: Path               # api/context/
    rag_dir: Path                   # generation/RAG/
    output_json: Path
    output_issues: Path
    shacl_shapes: list[Path]
    ontology_paths: list[Path]

    # Raw model lists (both providers kept for reference)
    gemini_models: list[str] = field(default_factory=list)
    groq_models: list[str]   = field(default_factory=list)
    claude_models: list[str] = field(default_factory=list)

    # Both API keys kept so CLI provider-override can switch cleanly
    gemini_api_key: str = ""
    groq_api_key: str   = ""
    claude_api_key: str = ""



def load_config(yaml_path: Path | None = None) -> Config:
    path = yaml_path or (_GEN_DIR / "config.yaml")
    if not path.exists():
        sys.exit(f"ERROR: config file not found: {path}")

    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    provider = raw.get("provider", "gemini").lower()
    keys     = raw.get("api_keys", {})

    if provider == "gemini":
        api_key = keys.get("google_ai_studio", "")
        if not api_key:
            sys.exit("ERROR: api_keys.google_ai_studio is empty in config.yaml")
    elif provider == "groq":
        api_key = keys.get("groq", "")
        if not api_key:
            sys.exit("ERROR: api_keys.groq is empty in config.yaml\n"
                     "  Get a free key at https://console.groq.com")
    elif provider == "claude":
        # Claude Code CLI can use its own local auth/session; key is optional here.
        api_key = keys.get("anthropic", "")
    else:
        sys.exit(f"ERROR: Unknown provider '{provider}'. Use 'gemini', 'groq' or 'claude'.")

    asset    = raw.get("asset", {})
    pdf_raw  = asset.get("pdf_path")
    pdf_path = Path(pdf_raw) if pdf_raw else None

    opts          = raw.get("options", {})
    model_cfg     = raw.get("models", {})
    gemini_models = model_cfg.get("gemini", [])
    groq_models   = model_cfg.get("groq", [])
    claude_models = model_cfg.get("claude", [])
    if provider == "gemini":
        models = gemini_models
    elif provider == "groq":
        models = groq_models
    else:
        models = claude_models

    gemini_api_key = keys.get("google_ai_studio", "")
    groq_api_key   = keys.get("groq", "")
    claude_api_key = keys.get("anthropic", "")

    out_cfg = raw.get("output", {})
    paths_cfg = raw.get("paths", {})
    generation_mode = str(opts.get("generation_mode", "json")).strip().lower()
    if generation_mode not in {"json", "json-description"}:
        sys.exit("ERROR: options.generation_mode must be 'json' or 'json-description'.")

    profile_example_raw = opts.get("profile_example_path")
    profile_example_path = Path(profile_example_raw) if profile_example_raw else None

    shacl_shapes_raw = paths_cfg.get("shacl_shapes")
    if isinstance(shacl_shapes_raw, list) and shacl_shapes_raw:
        shacl_shapes = [(_ROOT / Path(item)).resolve() for item in shacl_shapes_raw]
    else:
        shacl_shapes = [(_ROOT / item).resolve() for item in _DEFAULT_SHACL_SHAPES]

    ontologies_raw = paths_cfg.get("ontologies")
    if isinstance(ontologies_raw, list) and ontologies_raw:
        ontology_paths = [(_ROOT / Path(item)).resolve() for item in ontologies_raw]
    else:
        ontology_paths = [(_ROOT / item).resolve() for item in _DEFAULT_ONTOLOGIES]

    return Config(
        provider      = provider,
        api_key       = api_key,
        asset_name    = asset.get("name", "UnknownAsset"),
        base_url      = asset.get("base_url", "https://smartproductionlab.aau.dk"),
        pdf_path      = pdf_path,
        submodels     = raw.get("submodels", ["Nameplate", "HierarchicalStructures"]),
        generation_mode = generation_mode,
        profile_example_path = profile_example_path,
        use_rag       = opts.get("use_rag", False),
        use_example   = opts.get("use_example", False),
        force_full_aas_output = opts.get("force_full_aas_output", False),
        max_pdf_chars = opts.get("max_pdf_chars"),
        max_attempts  = opts.get("max_attempts", 1),
        models        = models,
        gemini_models  = gemini_models,
        groq_models    = groq_models,
        claude_models  = claude_models,
        gemini_api_key = gemini_api_key,
        groq_api_key   = groq_api_key,
        claude_api_key = claude_api_key,
        gen_dir       = _GEN_DIR,
        root_dir      = _ROOT,
        context_dir   = _GEN_DIR / "Context_Builder" / "context",
        rag_dir       = _GEN_DIR / "Context_Builder" / "RAG",
        output_json   = _ROOT / out_cfg.get("json_file", "Generation/output/aas_output.json"),
        output_issues = _ROOT / out_cfg.get("issues_file", "Generation/output/aas_issues.json"),
        shacl_shapes  = shacl_shapes,
        ontology_paths = ontology_paths,
    )


def load_validation_paths(yaml_path: Path | None = None) -> tuple[list[Path], list[Path]]:
    """Load SHACL shape and ontology paths without validating provider/API keys."""
    path = yaml_path or (_GEN_DIR / "config.yaml")

    if not path.exists():
        return [(_ROOT / item).resolve() for item in _DEFAULT_SHACL_SHAPES], [
            (_ROOT / item).resolve() for item in _DEFAULT_ONTOLOGIES
        ]

    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    paths_cfg = raw.get("paths", {}) if isinstance(raw, dict) else {}

    shacl_shapes_raw = paths_cfg.get("shacl_shapes") if isinstance(paths_cfg, dict) else None
    if isinstance(shacl_shapes_raw, list) and shacl_shapes_raw:
        shacl_shapes = [(_ROOT / Path(item)).resolve() for item in shacl_shapes_raw]
    else:
        shacl_shapes = [(_ROOT / item).resolve() for item in _DEFAULT_SHACL_SHAPES]

    ontologies_raw = paths_cfg.get("ontologies") if isinstance(paths_cfg, dict) else None
    if isinstance(ontologies_raw, list) and ontologies_raw:
        ontology_paths = [(_ROOT / Path(item)).resolve() for item in ontologies_raw]
    else:
        ontology_paths = [(_ROOT / item).resolve() for item in _DEFAULT_ONTOLOGIES]

    return shacl_shapes, ontology_paths


