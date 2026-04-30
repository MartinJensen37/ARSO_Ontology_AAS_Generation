# ARSO Ontology AAS Generation

Ontology-grounded generation and validation of Asset Administration Shells (AAS) using Large Language Models (LLMs), RDF projection, SHACL validation, and human-in-the-loop correction.

This repository contains the framework, ontology modules, validation logic, and evaluation material for generating AAS instances from technical equipment documentation. The project is centred around the **AAS Resource Structure Ontology (ARSO)**, which provides semantic grounding for AAS generation and formal validation through SHACL constraints.

---

## Project Overview

Creating high-quality and interoperable Asset Administration Shells is a manual and knowledge-intensive task. Engineers need to understand the AAS metamodel, relevant IDTA submodel templates, equipment documentation, communication interfaces, and domain-specific modelling conventions.

This project explores how Large Language Models can support this process when combined with ontology-based grounding and formal validation. Instead of asking an LLM to generate a complete AAS JSON document directly, the framework generates a compact **AAS profile** containing the asset-specific information. This profile is then transformed into a full AAS JSON structure and validated against ontology-derived SHACL constraints.

The framework consists of three main layers:

1. **Generation layer**  
   Builds the LLM context from user input, selected submodels, source documents, examples, and ontology-derived guidance. The LLM generates a compact AAS profile.

2. **Transformation layer**  
   Normalises the generated profile and expands it into a complete AAS JSON representation using deterministic builder logic.

3. **Validation layer**  
   Projects the generated AAS into RDF and validates it against SHACL constraints derived from ARSO and the AAS ontology. If validation fails, structured feedback can be returned to the LLM for correction.

The framework also includes an interactive editor where users can inspect, correct, and finalise the generated AAS with live validation feedback.

---

## Key Features

- LLM-based generation of compact AAS profiles
- Ontology-grounded prompt context using ARSO
- Transformation from profile JSON to full AAS JSON
- RDF projection of generated AAS instances
- SHACL validation against ARSO and AAS constraints
- Iterative feedback loop based on validation reports
- Interactive editor for final human verification and correction
- Live validation feedback during manual editing
- Modular structure for adding new submodels, rules, and model providers
- Evaluation material for synthetic industrial use cases

---

## Architecture

<!-- Add architecture figure here -->

```text
User input + documents
        |
        v
Generation layer
        |
        v
Compact AAS profile
        |
        v
Transformation layer
        |
        v
Full AAS JSON
        |
        v
AAS-to-RDF projection
        |
        v
SHACL validation
        |
        +--> feedback to LLM if violations remain
        |
        v
Interactive editor and final export
```

The framework is designed to keep the LLM task focused and controllable. The LLM generates only the information that must be authored explicitly, while the deterministic transformation layer handles the full AAS structure, semantic identifiers, and JSON serialisation.

This reduces the risk of malformed AAS JSON and makes the output easier to validate, correct, and extend.

---

## ARSO Ontology

The **AAS Resource Structure Ontology (ARSO)** provides the semantic foundation for the framework. It describes how resources, submodels, and submodel elements should be organised, and it defines dependencies between selected AAS submodels.

ARSO is used in two ways:

- **Generation guidance**  
  Relevant ontology concepts, submodel structures, and constraints are included in the LLM context.

- **Formal validation**  
  Ontology constraints are converted into SHACL shapes and used to validate generated AAS instances after RDF projection.

ARSO currently includes ontology modules aligned with selected IDTA submodel templates and custom submodels, including:

- Digital Nameplate
- Hierarchical Structures
- Asset Interfaces Description
- Capabilities
- Skills / Control Component structures
- Operational Data
- Parameters
- Technical Data

<!-- Add ontology figure here -->

---

## Generation Pipeline

The generation pipeline prepares the context needed for the LLM to generate a compact AAS profile.

The prompt context can include:

- user-provided asset information
- selected submodel configuration
- equipment datasheets
- communication specifications
- AAS profile examples
- submodel-specific context templates
- ontology-derived guidance
- summaries of relevant validation constraints

The LLM output is a compact JSON profile that captures the semantic content of the selected submodels. This profile is intentionally smaller and simpler than a full AAS JSON document.

---

## Transformation Pipeline

The transformation layer converts the generated profile into a complete AAS JSON document.

The process includes:

- normalising raw LLM output
- mapping naming variants to canonical profile keys
- scaffolding missing submodel sections
- removing unrequested sections
- creating typed AAS submodel elements
- assigning semantic identifiers
- generating the full AAS structure
- serialising the completed AAS as JSON

The transformation step is deterministic and implemented separately from the LLM. This ensures that the LLM does not need to generate low-level AAS JSON structures directly.

---

## RDF Projection and SHACL Validation

After transformation, the generated AAS JSON is projected into RDF. The RDF graph is then validated against SHACL constraints derived from ARSO and the AAS ontology.

The validation layer can detect issues such as:

- missing mandatory submodels
- missing mandatory submodel elements
- invalid submodel structures
- incomplete hierarchical structures
- missing cross-submodel dependencies
- incorrect relations between submodels
- remaining ontology-level inconsistencies

If validation fails, the framework creates a structured validation report. This report can be used as feedback for the next LLM generation attempt or displayed in the interactive editor for manual correction.

---

## Feedback Loop

The feedback loop enables iterative correction of generated AAS profiles.

When SHACL violations are detected, the validation layer returns a structured report containing information such as:

- violated constraint
- affected focus node
- relevant path
- validation message
- remaining conformance status

This report is added to the next LLM prompt so that the model can revise the AAS profile. The loop continues until SHACL conformance is reached or the configured retry budget is exhausted.

If violations remain after the retry budget is exhausted, the latest AAS and validation messages are returned to the interactive editor for manual correction.

---

## Interactive Editor

<!-- Add UI figure here -->

The interactive editor supports human-in-the-loop verification and correction of generated AAS instances.

The editor allows users to:

- inspect the generated AAS structure
- add or modify submodel content
- correct remaining validation issues
- view live validation feedback
- identify missing or invalid elements
- finalise the AAS model
- export the completed AAS as JSON

Once finalised, the exported AAS JSON can be deployed to an AAS server or similar infrastructure.

---

## Evaluation Material

The repository includes evaluation material for synthetic industrial use cases inspired by aseptic pharmaceutical production.

The evaluated use-case assets include:

- **LinFill-120**  
  A syringe filling module using MQTT interface documentation.

- **PlungerSet-80**  
  An automated stoppering module using OPC UA NodeSet documentation.

The evaluation considers:

- SHACL conformance
- violations across generation attempts
- mandatory-field coverage
- value accuracy against ground truth
- manual correction effort
- runtime

The evaluation material is intended to support reproducibility and further development of ontology-grounded AAS generation workflows.

---

## Repository Structure

The repository is organised around the main framework components.

```text
.
├── ontology/
│   ├── arso/
│   │   ├── modules/
│   │   └── imports/
│   └── README.md
│
├── shacl/
│   ├── generated/
│   ├── manual/
│   └── README.md
│
├── generation/
│   ├── context_builder/
│   ├── prompts/
│   ├── providers/
│   ├── orchestrator/
│   └── README.md
│
├── transformation/
│   ├── builders/
│   ├── factories/
│   ├── normalisation/
│   └── README.md
│
├── validation/
│   ├── aas_to_rdf/
│   ├── shacl_validator/
│   ├── reports/
│   └── README.md
│
├── ui/
│   ├── frontend/
│   ├── backend/
│   └── README.md
│
├── examples/
│   ├── profiles/
│   ├── aas_json/
│   ├── rdf/
│   └── validation_reports/
│
├── evaluation/
│   ├── use_cases/
│   ├── ground_truth/
│   ├── results/
│   └── scripts/
│
├── docs/
│   ├── figures/
│   ├── architecture/
│   └── notes/
│
├── configs/
│   └── example_config.yaml
│
├── tests/
│   ├── validation/
│   ├── transformation/
│   └── generation/
│
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

> Note: The exact folder names may differ depending on the current implementation. Update this section if the repository structure changes.

---

## Installation

Installation instructions will be added later.

Basic setup:

```bash
git clone https://github.com/MartinJensen37/ARSO_Ontology_AAS_Generation.git
cd ARSO_Ontology_AAS_Generation
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If the project uses a `pyproject.toml`, install it in editable mode:

```bash
pip install -e .
```

---

## Configuration

Configuration details will be added later.

Typical configuration options include:

- LLM provider
- LLM model
- maximum number of generation attempts
- selected AAS submodels
- input document paths
- output paths
- base URI settings
- ontology paths
- SHACL shape paths
- validation settings

Example placeholder:

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-6
  max_attempts: 3

input:
  asset_name: LinFill-120
  documents:
    - path/to/datasheet.pdf
    - path/to/interface_specification.pdf

generation:
  selected_submodels:
    - DigitalNameplate
    - HierarchicalStructures
    - AssetInterfacesDescription
    - Capabilities
    - Skills
    - OperationalData

validation:
  ontology_path: ontology/arso/
  shacl_path: shacl/
```

---

## Usage

Usage instructions will be added later.

Example placeholder for running generation:

```bash
python run_generation.py --config configs/example_config.yaml
```

Example placeholder for validating an existing AAS JSON file:

```bash
python validate_aas.py --input examples/aas_json/example.json
```

Example placeholder for converting AAS JSON to RDF:

```bash
python aas_to_rdf.py --input examples/aas_json/example.json --output examples/rdf/example.ttl
```

---

## Running the Interactive Editor

Instructions for running the interactive editor will be added later.

Example placeholder:

```bash
cd ui
npm install
npm run dev
```

or, if the editor is served through a Python backend:

```bash
python app.py
```

Update this section with the actual commands used by the project.

---

## Running Tests

Test instructions will be added later.

Example placeholder:

```bash
pytest
```

Possible test categories:

- transformation tests
- RDF projection tests
- SHACL validation tests
- generation pipeline tests
- end-to-end use-case tests

---

## Adding a New Submodel

The framework is designed to be modular. Adding a new submodel may require changes in several components.

Typical steps:

1. Add or extend an ARSO ontology module.
2. Add or generate SHACL constraints.
3. Define the compact AAS profile structure.
4. Add prompt/context guidance for the new submodel.
5. Implement builder logic for the full AAS JSON output.
6. Add RDF projection mappings if needed.
7. Add UI support for editing and validation.
8. Add examples and tests.

---

## Development Notes

Recommended development practices:

- Keep ontology modules modular and aligned with individual submodel templates.
- Keep deterministic AAS construction separate from LLM output.
- Validate generated AAS instances after each transformation.
- Prefer structured validation reports over free-text error messages.
- Add tests for each new ontology rule, projection mapping, and builder component.
- Keep generated examples and ground truth data versioned where possible.

---

## Roadmap

Potential future extensions include:

- evaluation on real industrial equipment
- support for additional IDTA submodel templates
- richer semantic modelling in ARSO
- ontology reasoning for inferred relations
- graph database integration with Neo4j
- MCP-based access to ARSO and AAS graphs for LLM agents
- integration with AAS registries and repositories
- automated deployment to AAS servers
- improved interactive correction workflows
- expanded benchmarking across additional LLM providers and model sizes

---

## Known Limitations

Current limitations include:

- evaluation is based on a limited number of synthetic use cases
- generated values may still require manual verification
- SHACL conformance does not guarantee full deployment readiness
- some semantically valid values may not match ground truth strings exactly
- smaller LLMs may struggle with complex output formats and feedback correction
- ontology coverage is limited to the currently implemented ARSO modules

---

## Contributing

Contributions are welcome.

Possible contribution areas include:

- new ARSO modules
- additional SHACL constraints
- support for new AAS submodel templates
- improved RDF projection mappings
- additional LLM provider integrations
- UI improvements
- validation test cases
- documentation improvements
- evaluation on additional industrial assets

Before contributing, please:

1. Open an issue describing the proposed change.
2. Keep changes modular and documented.
3. Add tests where relevant.
4. Follow the existing project structure and naming conventions.

---

## Acknowledgements

This work was supported by **Novo Nordisk AMSAT**.

The project builds on concepts from the Asset Administration Shell ecosystem, semantic web technologies, SHACL validation, and ontology-based modelling for industrial digital twins.

---

## Licence

Licence information will be added later.

If no licence has been selected yet, please add one before public reuse of the repository.

---

## Contact

For questions, issues, or collaboration requests, please open an issue in this repository.

Repository:

```text
https://github.com/MartinJensen37/ARSO_Ontology_AAS_Generation
```
