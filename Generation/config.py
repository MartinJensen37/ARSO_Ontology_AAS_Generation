"""
Loads Generation/config.yaml and exposes a Config dataclass.
All modules import from here - no scattered os.environ calls elsewhere.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from .LLM_Client.llm_client import OPENAI_COMPATIBLE_BASE_URLS

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

# Providers with a non-OpenAI-compatible transport (their own SDK / CLI).
# Anything else is assumed to be an OpenAI-compatible provider — see
# OPENAI_COMPATIBLE_BASE_URLS in llm_client.py — and needs no entry here.
_KNOWN_NON_OPENAI_PROVIDERS = frozenset({"gemini", "claude"})

# provider name -> the key used under `api_keys:` in config.yaml, for
# providers whose YAML key doesn't match the provider name for historical/
# branding reasons. Anything not listed here uses the provider name itself
# (e.g. "groq" -> api_keys.groq, "openrouter" -> api_keys.openrouter).
_API_KEY_YAML_KEY: dict[str, str] = {"gemini": "google_ai_studio", "claude": "anthropic"}

# Add project root to sys.path so sibling top-level packages can be imported.
for _p in [str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _api_key_for(provider: str, keys: dict) -> str:
    return keys.get(_API_KEY_YAML_KEY.get(provider, provider), "")


@dataclass
class Config:
    # Provider
    provider: str                   # "gemini" | "claude" | any OpenAI-compatible provider (groq, openrouter, ...)
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
    context_dir: Path               # Generation/Context_Builder/context
    rag_dir: Path                   # generation/RAG/
    output_json: Path
    output_issues: Path
    shacl_shapes: list[Path]
    ontology_paths: list[Path]

    # Every configured provider's model list / API key, keyed by provider
    # name (matching config.yaml's `models:` section and `provider` field).
    # Kept for reference so a CLI/API provider override can switch cleanly
    # without reloading config.yaml. Adding a new provider needs no change
    # here — just a config.yaml entry (see _api_key_for above).
    provider_models: dict[str, list[str]] = field(default_factory=dict)
    provider_api_keys: dict[str, str] = field(default_factory=dict)



def load_config(yaml_path: Path | None = None) -> Config:
    path = yaml_path or (_GEN_DIR / "config.yaml")
    if not path.exists():
        sys.exit(f"ERROR: config file not found: {path}")

    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    provider = raw.get("provider", "gemini").lower()
    keys     = raw.get("api_keys", {})
    model_cfg = raw.get("models", {})

    known_providers = _KNOWN_NON_OPENAI_PROVIDERS | set(OPENAI_COMPATIBLE_BASE_URLS)
    if provider not in known_providers:
        sys.exit(
            f"ERROR: Unknown provider '{provider}'. Use 'gemini', 'claude', or one of "
            f"{sorted(OPENAI_COMPATIBLE_BASE_URLS)}."
        )

    api_key = _api_key_for(provider, keys)
    if provider == "gemini" and not api_key:
        sys.exit("ERROR: api_keys.google_ai_studio is empty in config.yaml")
    if provider in OPENAI_COMPATIBLE_BASE_URLS and not api_key:
        sys.exit(
            f"ERROR: api_keys.{provider} is empty in config.yaml\n"
            f"  Configured base URL: {OPENAI_COMPATIBLE_BASE_URLS[provider]}"
        )
    # claude: Claude Code CLI can use its own local auth/session, so an empty
    # key here is allowed.

    asset    = raw.get("asset", {})
    pdf_raw  = asset.get("pdf_path")
    pdf_path = Path(pdf_raw) if pdf_raw else None

    opts = raw.get("options", {})

    # Every provider mentioned anywhere in config.yaml (models: section keys,
    # plus the known ones even if not yet listed) gets a models/api_key entry.
    all_provider_names = known_providers | set(model_cfg.keys())
    provider_models: dict[str, list[str]] = {
        name: model_cfg.get(name, []) for name in all_provider_names
    }
    provider_api_keys: dict[str, str] = {
        name: _api_key_for(name, keys) for name in all_provider_names
    }
    models = provider_models.get(provider, [])

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
        provider_models   = provider_models,
        provider_api_keys = provider_api_keys,
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


