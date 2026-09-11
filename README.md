# ARSO Ontology AAS Generation

Ontology-grounded generation, transformation, and validation of Asset Administration Shells (AAS) using LLMs, RDF projection, SHACL validation, and human-in-the-loop correction.

The framework is centred on the **AAS Resource Structure Ontology (ARSO)**, which provides semantic grounding for LLM generation and formal validation through SHACL constraints.

---

## Overview

Authoring a high-quality AAS by hand requires knowing the AAS metamodel, the relevant IDTA submodel templates, the equipment documentation, and the asset's communication interfaces.

Rather than asking an LLM for a complete AAS JSON document, this framework has it produce a compact **AAS profile** holding only the asset-specific facts. The profile is then normalised, expanded into full AAS JSON by deterministic builders, projected to RDF, and validated against ontology-derived SHACL shapes. This keeps the LLM task small and makes the output easy to validate and correct.

| Layer | Path | Role |
| --- | --- | --- |
| Generation | `Generation/` | Builds LLM context from input, submodels, documents and ontology guidance; calls the provider; retries with structured validation feedback. |
| Transformation | `Transformation/` | Normalises the profile, expands it to full AAS JSON via per-submodel builders, projects AAS to RDF, and inverts AAS back to a profile. |
| Validation | `Validation/` | Runs the RDF against SHACL shapes derived from ARSO and the AAS ontology, returning per-field results. |
| API + UI | `api/`, `ui/` | FastAPI backend exposing generation, validation and profile↔AAS conversion; React canvas editor with live validation. |

![Simplified architecture for the generation pipeline.](images/architecture.png)

## Demonstration Video

[Ontology_grounded_AAS_gen_720p.webm](https://github.com/user-attachments/assets/57838bc5-169b-48e5-b690-b0683bc1d920)

---

## Repository Structure

```text
.
├── api/                                FastAPI backend
│   ├── main.py                         App entry point (uvicorn api.main:app), /health
│   ├── models.py                       Shared response models
│   └── routers/
│       ├── generate_aas.py             POST /api/generate-aas (SSE), GET /api/generation-config
│       ├── validate.py                 POST /api/validate
│       ├── profile_to_aas.py           POST /api/profile-to-aas
│       └── aas_to_profile.py           POST /api/aas-to-profile
│
├── Generation/                         LLM-based AAS profile generation
│   ├── pipeline.py                     LLM call + retry-on-violation loop
│   ├── config.py                       Config dataclass + config.yaml loader
│   ├── config.yaml                     Local config: provider, API keys, models (gitignored)
│   ├── prompts.yaml                    System/user prompt templates
│   ├── Context_Builder/
│   │   ├── context_loader.py           Assembles the static context bundle
│   │   ├── context/                    Prompt fragments
│   │   │   ├── 00-preamble.md
│   │   │   ├── shacl-rules.md
│   │   │   ├── valid-example.json
│   │   │   └── submodels/              Per-submodel guidance (aid, nameplate, skills, ...)
│   │   ├── Parsing/
│   │   │   ├── pdf_extractor.py        pdfplumber extraction, PyMuPDF fallback
│   │   │   ├── profile_structure.py    Profile scaffolding + field-alias normalisation
│   │   │   ├── json_description_generation.py   Profile JSON checks and repair
│   │   │   └── text_parsing.py         Outer-JSON extraction from LLM output
│   │   └── RAG/
│   │       ├── rag_loader.py           Loads optional retrieval corpus
│   │       └── prompt_builder.py       Injects RAG blocks into the prompt
│   └── LLM_Client/
│       └── llm_client.py               OpenAI-compatible / Gemini / Claude CLI client
│
├── Ontology/                           Semantic grounding and validation models
│   ├── AAS/aas-rdf-ontology.ttl        RDF projection of the AAS metamodel
│   ├── ARSO/                           AAS Resource Structure Ontology
│   │   ├── ARSO_AAS.ttl                Root: converter annotations + AAS→submodel links
│   │   └── Modules/                    aid, capabilities, control-component,
│   │                                   hierarchical-structures, nameplate,
│   │                                   operational-data, parameters, technical-data
│   ├── APSO/                           Product AAS blueprint ontology (draft, not yet
│   │   ├── APSO_AAS.ttl                wired into the pipeline)
│   │   └── Modules/                    batch_information, bill_of_materials, bill_of_process
│   ├── CSS/CSS-Ontology.ttl            Capability-Skill-Service ontology
│   └── SHACL/
│       ├── Generated/shapes.generated.shacl.ttl   Derived from the ARSO OWL restrictions
│       ├── Manual/
│       │   ├── arso-rules.shacl.ttl    Hand-written SPARQL-based cross-submodel rules
│       │   └── aas-shacl-schema.ttl    AAS metamodel shapes
│       └── owl2shacl/                  owl2sh-closed / owl2sh-semi-closed rulesets
│
├── Transformation/                     AAS construction and RDF projection
│   ├── AAS_Builder/
│   │   ├── AAS_builder.py              profile_document_to_aas_json() entry point
│   │   ├── AAS_generation/
│   │   │   ├── core/                   aas_builder, generate_aas, element_factory,
│   │   │   │                           schema_handler, semantic_ids
│   │   │   └── submodels/              One builder per submodel: asset_interfaces,
│   │   │                               capabilities, hierarchical_structures, nameplate,
│   │   │                               parameters, process_submodels, skills, variables
│   │   └── AAS_to_Profile/aas_to_profile.py   Full AAS JSON → profile (inverse)
│   ├── AAS_to_RDF/
│   │   ├── aas_to_rdf.py               AAS JSON → RDF/Turtle, ontology-annotation-driven
│   │   └── Examples/                   Reference Turtle output
│   └── Generate_Shapes/
│       ├── generate_shapes.py          Regenerates Ontology/SHACL/Generated/
│       └── generate_shapes_from_ontology.py
│
├── Validation/Validator/validator.py   run_shacl(): the single validation entry point
│
├── Guidance/ontology_guidance_engine.py   Ontology-derived inline authoring hints
│
├── Testing/
│   ├── SHACL_Tests/
│   │   ├── Test_Cases/                 12 invalid_*.aas.json conformance fixtures
│   │   └── Test_Scripts/
│   │       ├── validate_aas.py         Validate one AAS JSON file
│   │       └── run_test_cases.py       Run the whole fixture suite
│   └── Generation_Tests/
│       ├── equipment/                  Fixtures: datasheet PDFs, interface specs,
│       │                               equipment.yaml + ground-truth profile per asset
│       │                               (filling_module, stoppering_module)
│       ├── Test_Matrix/matrix.yaml     Equipment × provider/model sweep definition
│       └── Test_Scripts/
│           ├── run_eval.py             Runs experiments, writes results/<run-id>/
│           ├── metrics.py              Coverage, cross-reference and conformance scoring
│           ├── aggregate.py            results.jsonl → aggregate.csv + derived.json
│           ├── plot_results.py         Evaluation plots (PNG + PDF)
│           ├── effort_check.py         Sanity-checks a run's effort/cost figures
│           └── generate_linfill120_mqtt_pdf.py   Regenerates an interface-spec fixture
│
├── ui/                                 AAS editor frontend (React + TypeScript + Vite)
│   ├── src/
│   │   ├── App.tsx, main.tsx, App.css, index.css
│   │   ├── aas/semanticIds.ts          Semantic ID constants mirroring semantic_ids.py
│   │   ├── api/client.ts               Typed backend client (incl. SSE generation stream)
│   │   ├── types/resourceaas.ts        Profile type definitions
│   │   ├── store/                      useAppStore (profile state), useModelStore (canvas)
│   │   ├── hooks/                      useValidation (debounced), useGenerateAI
│   │   └── components/
│   │       ├── modelbuilder/           ModelBuilder canvas, BuilderToolbar, CatalogPanel,
│   │       │                           GenerateAIDialog, addAasShell, submodelLayout,
│   │       │                           nodes/, edges/, modals/
│   │       ├── submodels/              One form per submodel (AID, Capabilities,
│   │       │                           DigitalNameplate, HierarchicalStructures,
│   │       │                           OperationalData, Parameters, Skills)
│   │       └── shared/                 GuidancePanel, SemanticIdInput, AdvField,
│   │                                   SubmodelAdvancedPanel, AdvancedContext
│   ├── vite.config.ts                  Dev proxy /api → backend, polling watcher
│   ├── Dockerfile, package.json, tsconfig*.json, eslint.config.js
│   └── README.md                       UI-specific documentation
│
├── images/                             Architecture and UI figures
├── Dockerfile, docker-compose.yml, .dockerignore   Backend container
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Getting Started

**Prerequisites:** Python 3.11+, an API key for at least one LLM provider, and either Docker Desktop or Node.js 20+.

### Option A — Docker (recommended)

Runs backend and frontend together with hot-reload, the whole repo bind-mounted so code, ontology and SHACL changes apply without a rebuild.

1. Create `Generation/config.yaml` (see [Configuration](#configuration)). It is gitignored and reaches the container only via the bind mount.
2. `docker compose up`
3. Backend at [localhost:8000](http://localhost:8000) (`/health`, `/docs`) · Frontend at [localhost:5173](http://localhost:5173)

Notes:
- Rebuild after changing `requirements.txt` or `ui/package.json`: `docker compose build`.
- The frontend container keeps `node_modules` in an anonymous volume, so no local install is needed.
- Inside the containers the frontend reaches the backend at `http://backend:8000` (`VITE_API_PROXY_TARGET`).
- Stop with `docker compose down`; add `-v` only to drop the `node_modules` volume too.

### Option B — Native

```bash
git clone https://github.com/MartinJensen37/ARSO_Ontology_AAS_Generation.git
cd ARSO_Ontology_AAS_Generation
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd ui && npm install && npm run dev
```

Vite proxies `/api/*` to `http://localhost:8000`. See `ui/README.md` for frontend detail.

---

## Configuration

Create `Generation/config.yaml` yourself — it is gitignored because it holds API keys.

```yaml
provider: deepseek   # or: gemini, claude, groq, openrouter, or any provider in
                     # OPENAI_COMPATIBLE_BASE_URLS (Generation/LLM_Client/llm_client.py)

api_keys:
  deepseek: "YOUR_API_KEY_HERE"
  # google_ai_studio: "..."   # provider: gemini
  # anthropic: "..."          # provider: claude (optional — the Claude Code CLI can use its own session)

models:
  deepseek:
    - "deepseek-chat"

asset:
  name: "UnknownAsset"
  base_url: "https://smartproductionlab.aau.dk"
  # pdf_path: "path/to/datasheet.pdf"   # optional; the UI/API also accept uploads

submodels:
  - Nameplate
  - HierarchicalStructures
  - AID
  - Skills
  - Capabilities
  - OperationalData

options:
  generation_mode: "json-description"   # "json" | "json-description"
  use_rag: false
  use_example: false
  force_full_aas_output: false
  max_attempts: 2
```

Adding an OpenAI-compatible provider needs only a `base_url` in `OPENAI_COMPATIBLE_BASE_URLS` plus matching `api_keys`/`models` entries — no other code changes.

`paths.shacl_shapes` / `paths.ontologies` can override the shapes and ontology files used for validation; the defaults (`Ontology/SHACL/Generated/shapes.generated.shacl.ttl` + `Ontology/SHACL/Manual/arso-rules.shacl.ttl`) are almost always correct.

---

## Usage

**Editor:** open the frontend, build or import a profile on the canvas, and validation runs live as you edit. "Generate with AI" drafts submodels from an uploaded datasheet.

**API:**

```bash
# Generate an AAS from a PDF + selected submodels (streams progress via SSE)
curl -N -X POST http://localhost:8000/api/generate-aas \
  -H "Content-Type: application/json" \
  -d '{"asset_name": "MyAsset", "selected_submodels": ["Nameplate", "AID"], ...}'

# Validate a full AAS JSON document
curl -X POST http://localhost:8000/api/validate -H "Content-Type: application/json" \
  -d '{"json_text": "..."}'

# Build a profile into a full AAS + validate in one round trip
curl -X POST http://localhost:8000/api/profile-to-aas -H "Content-Type: application/json" \
  -d '{"asset_name": "MyAsset", "selected_submodels": ["Nameplate"], "profile": {...}}'

# Invert a full AAS JSON back into a profile (what the editor's import uses)
curl -X POST http://localhost:8000/api/aas-to-profile -H "Content-Type: application/json" \
  -d '{"aas_json_text": "..."}'
```

Exact request/response models are in `api/routers/*.py`, or the interactive docs at `http://localhost:8000/docs`.

---

## Validation & Testing

**Validate one file** — a thin wrapper around the same `run_shacl` that `/api/validate` and the generation retry loop use:

```bash
python Testing/SHACL_Tests/Test_Scripts/validate_aas.py path/to/your.aas.json
```

**SHACL regression suite** — `Testing/SHACL_Tests/Test_Cases/` holds deliberately-broken fixtures, each exercising one shape. All are expected to fail; the runner exits non-zero if any unexpectedly conforms:

```bash
python Testing/SHACL_Tests/Test_Scripts/run_test_cases.py
```

**Regenerate SHACL shapes** from the OWL restrictions in `Ontology/ARSO/Modules/*.ttl`:

```bash
python Transformation/Generate_Shapes/generate_shapes.py
```

> **Known issue:** the generator has a `pyparsing`/SPARQL bottleneck in the owl2shacl ruleset that can make it impractically slow. If a run hangs, note that the shapes file has been hand-patched before — diff the shape you changed against its ontology restriction rather than waiting on a full regeneration.

**LLM generation evaluation** — `Testing/Generation_Tests/` runs the full pipeline against real equipment fixtures and scores the result. Each `equipment/<id>/` holds an `equipment.yaml` (asset name, protocol, submodels, source documents) and a ground-truth **profile** plus a small `required_paths`/`must_not_contain` scoring-hints block. The harness builds that profile into a reference AAS through the real pipeline and diffs the generated AAS against it by semanticId/path, so ground truth cannot drift from what the pipeline actually produces.

```bash
# One experiment
python -m Testing.Generation_Tests.Test_Scripts.run_eval \
  --equipment filling_module --provider claude --model claude-sonnet-4-6 --run-id my-test-run

# Full matrix sweep
python -m Testing.Generation_Tests.Test_Scripts.run_eval \
  --matrix Testing/Generation_Tests/Test_Matrix/matrix.yaml --run-id my-sweep
```

Results land in `Testing/Generation_Tests/results/<run-id>/`: `results.jsonl` (one row per experiment — coverage, cross-reference correctness, SHACL conformance, verify-marker rate, cost estimate) plus a per-experiment folder with the prompts, raw LLM output, generated and reference AAS, and SHACL report. `aggregate.py` and `plot_results.py` summarise a run.

---

## Ontology

`Ontology/ARSO/Modules/` holds one `.ttl` per submodel. Each class declares how it is identified in an AAS JSON document through `arso:semanticId` / `arso:idShort` / `arso:parentClass` / `arso:transitiveParentClass` annotations. Both `Transformation/AAS_to_RDF/aas_to_rdf.py` and the shape generator read these directly, so extending a submodel with an element that follows the convention needs no Python changes.

Mandatory-field and structural constraints are OWL restrictions (`owl:someValuesFrom`, `owl:qualifiedCardinality`, `owl:oneOf`) on those classes, converted to SHACL by the owl2shacl generator. Constraints needing graph traversal beyond a single class — cross-submodel reference targets such as "a Skill's InterfaceReference must resolve to a real AID action" — are hand-written as SPARQL-based rules in `Ontology/SHACL/Manual/arso-rules.shacl.ttl`.

`Ontology/APSO/` is a separate draft ontology describing a **Product** AAS blueprint (BatchInformation, Bill of Materials, Bill of Process). It is not yet referenced by the generation pipeline.

---

## Acknowledgements

This work was supported by **Novo Nordisk AMSAT**.

## Licence

MIT — see [LICENSE](LICENSE).
