# ARSO Ontology AAS Generation

Ontology-grounded generation, transformation, and validation of Asset Administration Shells (AAS) using Large Language Models (LLMs), RDF projection, SHACL validation, and human-in-the-loop correction.

This repository contains the implementation of a modular framework for generating AAS instances from technical equipment documentation. The framework is centred around the **AAS Resource Structure Ontology (ARSO)**, which provides semantic grounding for LLM-based generation and formal validation through SHACL constraints.

---

## Project Overview

Creating high-quality and interoperable Asset Administration Shells is a manual and knowledge-intensive task. Engineers need to understand the AAS metamodel, relevant IDTA submodel templates, equipment documentation, communication interfaces, and domain-specific modelling conventions.

This project explores how LLMs can support this process when combined with ontology-based grounding and validation. Instead of asking an LLM to generate a complete AAS JSON document directly, the framework generates a compact **AAS profile** containing the asset-specific information. This profile is then normalised, transformed into a full AAS JSON structure, projected to RDF, and validated against ontology-derived SHACL constraints.

The framework consists of three main layers:

1. **Generation**
   - Builds the LLM context from user input, selected submodels, source documents, examples, and ontology-derived guidance.
   - Calls the configured LLM provider.
   - Produces a compact AAS profile.

2. **Transformation**
   - Normalises the generated profile.
   - Expands the profile into a full AAS JSON representation.
   - Builds submodels using dedicated builder classes.
   - Converts the generated AAS into RDF for validation.

3. **Validation**
   - Validates the RDF representation against SHACL constraints derived from ARSO and the AAS ontology.
   - Produces structured validation results.
   - Supports iterative feedback to the LLM and live validation in the editor.

The framework also includes testing material for both SHACL validation and LLM-based AAS generation.

---

## Key Features

- LLM-based generation of compact AAS profiles
- Context construction from submodel-specific Markdown guidance
- Prompt configuration through YAML files
- Support for technical documents such as PDFs and OPC UA NodeSet XML files
- Deterministic transformation from profile JSON to full AAS JSON
- Dedicated builder classes for supported AAS submodels
- RDF projection of generated AAS instances
- SHACL validation against ARSO and AAS constraints
- Structured validation feedback for iterative correction
- Test cases for SHACL validation
- Evaluation scripts for comparing model performance
- Modular folder structure for extending ontology modules, submodels, and validation rules

---

## Architecture

<!-- Add architecture figure here -->

```text
User input + documents
        |
        v
Generation
        |
        v
Compact AAS profile
        |
        v
Transformation / AAS Builder
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
Final AAS JSON / manual correction
```

The framework is designed to keep the LLM task focused and controllable. The LLM generates only the information that must be authored explicitly, while the deterministic transformation layer handles the full AAS structure, semantic identifiers, and serialisation.

This reduces the risk of malformed AAS JSON and makes the generated output easier to validate, correct, and extend.

---

## Repository Structure

The repository is organised into five main parts:

- `Generation/` — LLM configuration, prompting, context building, parsing, RAG support, and LLM client logic.
- `Ontology/` — AAS, CSS, ARSO, and SHACL ontology resources.
- `Transformation/` — AAS profile transformation, AAS JSON construction, submodel builders, and RDF projection.
- `Validation/` — SHACL validation logic.
- `Testing/` — SHACL test cases, generation test assets, ground truth files, and evaluation scripts.

```text
.
├── README.md
├── __init__.py
│
├── Generation/
│   ├── config.py
│   ├── pipeline.py
│   ├── prompts.yaml
│   ├── __init__.py
│   │
│   ├── Context_Builder/
│   │   ├── context_loader.py
│   │   ├── __init__.py
│   │   │
│   │   ├── context/
│   │   │   ├── 00-preamble.md
│   │   │   ├── shacl-rules.md
│   │   │   ├── valid-example.json
│   │   │   │
│   │   │   └── submodels/
│   │   │       ├── aid.md
│   │   │       ├── aimc.md
│   │   │       ├── capabilities.md
│   │   │       ├── hierarchicalstructures.md
│   │   │       ├── nameplate.md
│   │   │       ├── parameters.md
│   │   │       ├── skills.md
│   │   │       └── variables.md
│   │   │
│   │   ├── Parsing/
│   │   │   ├── json_description_generation.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── profile_structure.py
│   │   │   ├── text_parsing.py
│   │   │   └── __init__.py
│   │   │
│   │   └── RAG/
│   │       ├── prompt_builder.py
│   │       ├── rag_loader.py
│   │       └── __init__.py
│   │
│   └── LLM_Client/
│       ├── llm_client.py
│       └── __init__.py
│
├── Ontology/
│   ├── AAS/
│   │   └── aas-rdf-ontology.ttl
│   │
│   ├── ARSO/
│   │   └── ARSO_AAS.ttl
│   │
│   ├── CSS/
│   │   └── CSS-Ontology.ttl
│   │
│   └── SHACL/
│       ├── Generated/
│       │   └── shapes.generated.shacl.ttl
│       │
│       └── Manual/
│           ├── aas-shacl-schema.ttl
│           └── arso-rules.shacl.ttl
│
├── Testing/
│   ├── __init__.py
│   │
│   ├── Generation_Tests/
│   │   ├── __init__.py
│   │   │
│   │   ├── equipment/
│   │   │   ├── filling_module/
│   │   │   │   ├── EA-LC-LF120-EN_Lifecycle.pdf
│   │   │   │   ├── EA-LN-SPL01-EN_Line_BOM.pdf
│   │   │   │   ├── EA-MI-LF120-EN_MQTT_Interface.pdf
│   │   │   │   ├── equipment.yaml
│   │   │   │   └── linfill120_ground_truth.yaml
│   │   │   │
│   │   │   ├── ground_truth/
│   │   │   │   ├── filling_module.yaml
│   │   │   │   └── stoppering_module.yaml
│   │   │   │
│   │   │   └── stoppering_module/
│   │   │       ├── EA-LC-PS080-EN_Lifecycle.pdf
│   │   │       ├── EA-LN-SPL01-EN_Line_BOM.pdf
│   │   │       ├── EA-NS-PS080.NodeSet2.xml
│   │   │       ├── equipment.yaml
│   │   │       └── plungerset80_ground_truth.yaml
│   │   │
│   │   ├── Test_Matrix/
│   │   │   └── matrix.yaml
│   │   │
│   │   └── Test_Scripts/
│   │       └── evaluation/
│   │           ├── aggregate.py
│   │           ├── effort_check.py
│   │           ├── matrix.yaml
│   │           ├── metrics.py
│   │           ├── plot_results.py
│   │           ├── run_eval.py
│   │           └── __init__.py
│   │
│   └── SHACL_Tests/
│       ├── __init__.py
│       │
│       ├── Test_Cases/
│       │   └── tests/
│       │       ├── invalid_address_missing_city.aas.json
│       │       ├── invalid_aid_empty_interface.aas.json
│       │       ├── invalid_capabilities_missing_capability_element.aas.json
│       │       ├── invalid_entry_node_empty_statements.aas.json
│       │       ├── invalid_missing_hierarchical_structures.aas.json
│       │       ├── invalid_missing_nameplate.aas.json
│       │       ├── invalid_nameplate_missing_address.aas.json
│       │       ├── invalid_nameplate_missing_mandatory_elements.aas.json
│       │       └── invalid_skills_without_aid.aas.json
│       │
│       └── Test_Scripts/
│           └── validate_aas.py
│
├── Transformation/
│   ├── __init__.py
│   │
│   └── AAS_Builder/
│       ├── AAS_builder.py
│       ├── __init__.py
│       │
│       ├── AAS_to_RDF/
│       │   ├── aas_to_rdf.py
│       │   └── __init__.py
│       │
│       └── Builder_Classes/
│           ├── __init__.py
│           │
│           └── AAS_generation/
│               ├── __init__.py
│               │
│               ├── cli/
│               │   ├── generate_aas.py
│               │   └── __init__.py
│               │
│               ├── core/
│               │   ├── aas_builder.py
│               │   ├── element_factory.py
│               │   ├── schema_handler.py
│               │   ├── semantic_ids.py
│               │   └── __init__.py
│               │
│               ├── guidance/
│               │   ├── ontology_guidance_engine.py
│               │   ├── yaml_to_rdf_lite.py
│               │   └── __init__.py
│               │
│               └── submodels/
│                   ├── asset_interfaces_builder.py
│                   ├── capabilities_builder.py
│                   ├── hierarchical_structures_builder.py
│                   ├── nameplate_builder.py
│                   ├── parameters_builder.py
│                   ├── process_submodels_builder.py
│                   ├── skills_builder.py
│                   ├── variables_builder.py
│                   └── __init__.py
│
└── Validation/
    ├── __init__.py
    │
    └── Validator/
        ├── validator.py
        └── __init__.py
```

---

## Main Components

### Generation

The `Generation/` folder contains the logic for preparing prompts, loading context, parsing input documents, and calling LLM providers.

Important files and folders:

- `Generation/config.py`  
  Configuration handling for the generation pipeline.

- `Generation/pipeline.py`  
  Main generation pipeline.

- `Generation/prompts.yaml`  
  Prompt configuration.

- `Generation/Context_Builder/context_loader.py`  
  Loads static and submodel-specific context.

- `Generation/Context_Builder/context/`  
  Markdown and JSON files used as prompt context.

- `Generation/Context_Builder/Parsing/`  
  Utilities for parsing PDFs, text, and profile structures.

- `Generation/Context_Builder/RAG/`  
  Prompt-building and retrieval-related utilities.

- `Generation/LLM_Client/llm_client.py`  
  LLM provider interface.

---

### Ontology

The `Ontology/` folder contains the semantic resources used for grounding and validation.

Important files:

- `Ontology/AAS/aas-rdf-ontology.ttl`  
  RDF representation of the AAS ontology.

- `Ontology/CSS/CSS-Ontology.ttl`  
  CSS ontology used as part of the resource modelling context.

- `Ontology/ARSO/ARSO_AAS.ttl`  
  Main ARSO ontology.

- `Ontology/SHACL/Generated/shapes.generated.shacl.ttl`  
  Automatically generated SHACL shapes.

- `Ontology/SHACL/Manual/aas-shacl-schema.ttl`  
  Manually defined AAS SHACL constraints.

- `Ontology/SHACL/Manual/arso-rules.shacl.ttl`  
  Manually defined ARSO rules, including constraints that require graph-pattern logic.

---

### Transformation

The `Transformation/` folder contains the deterministic conversion from generated AAS profiles to complete AAS JSON documents.

Important files and folders:

- `Transformation/AAS_Builder/AAS_builder.py`  
  Main AAS builder entry point.

- `Transformation/AAS_Builder/AAS_to_RDF/aas_to_rdf.py`  
  Converts full AAS JSON documents to RDF/Turtle for validation.

- `Transformation/AAS_Builder/Builder_Classes/AAS_generation/core/`  
  Core AAS building utilities, including element creation, schema handling, and semantic identifiers.

- `Transformation/AAS_Builder/Builder_Classes/AAS_generation/submodels/`  
  Dedicated builder classes for supported submodels.

- `Transformation/AAS_Builder/Builder_Classes/AAS_generation/cli/generate_aas.py`  
  CLI entry point for generating AAS JSON from profile data.

---

### Validation

The `Validation/` folder contains SHACL validation logic.

Important file:

- `Validation/Validator/validator.py`  
  Runs validation against the generated RDF graph and returns conformance results and violation reports.

---

### Testing

The `Testing/` folder contains test cases, input documents, ground truth files, and evaluation scripts.

Main areas:

- `Testing/SHACL_Tests/`  
  Contains invalid AAS JSON fixtures used to verify that the SHACL validation layer detects expected violations.

- `Testing/Generation_Tests/equipment/`  
  Contains synthetic equipment documentation and ground truth files for the filling and stoppering modules.

- `Testing/Generation_Tests/Test_Matrix/matrix.yaml`  
  Defines model and test configurations.

- `Testing/Generation_Tests/Test_Scripts/evaluation/`  
  Contains scripts for running experiments, computing metrics, aggregating results, checking effort, and plotting results.

---

## ARSO Ontology

The **AAS Resource Structure Ontology (ARSO)** provides the semantic foundation for the framework. It describes how resources, submodels, and submodel elements should be organised, and defines dependencies between selected AAS submodels.

ARSO is used in two ways:

- **Generation guidance**  
  Relevant ontology concepts, submodel structures, and constraints are included in the LLM context.

- **Formal validation**  
  Ontology constraints are converted into SHACL shapes and used to validate generated AAS instances after RDF projection.

The ontology imports or aligns with AAS and CSS concepts and provides additional ARSO-specific constraints for resource-oriented AAS generation.

---

## Supported Submodel Context

The generation context currently includes Markdown guidance for the following submodel areas:

- Asset Interfaces Description (`aid.md`)
- AIMC (`aimc.md`)
- Capabilities (`capabilities.md`)
- Hierarchical Structures (`hierarchicalstructures.md`)
- Digital Nameplate (`nameplate.md`)
- Parameters (`parameters.md`)
- Skills (`skills.md`)
- Variables (`variables.md`)

The transformation layer contains dedicated builders for:

- Asset Interfaces
- Capabilities
- Hierarchical Structures
- Nameplate
- Parameters
- Process-related submodels
- Skills
- Variables

---

## Generation Pipeline

The generation pipeline prepares the context needed for the LLM to generate a compact AAS profile.

The prompt context may include:

- user-provided asset information
- selected submodel configuration
- equipment datasheets
- communication specifications
- validated AAS examples
- submodel-specific Markdown guidance
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

After transformation, the generated AAS JSON is projected into RDF using:

```text
Transformation/AAS_Builder/AAS_to_RDF/aas_to_rdf.py
```

The RDF graph is then validated against SHACL constraints from:

```text
Ontology/SHACL/Generated/shapes.generated.shacl.ttl
Ontology/SHACL/Manual/aas-shacl-schema.ttl
Ontology/SHACL/Manual/arso-rules.shacl.ttl
```

The validation layer can detect issues such as:

- missing mandatory submodels
- missing mandatory submodel elements
- invalid submodel structures
- incomplete hierarchical structures
- missing cross-submodel dependencies
- incorrect relations between submodels
- remaining ontology-level inconsistencies

---

## Feedback Loop

When SHACL violations are detected, the validation layer returns structured feedback. This feedback can be added to the next LLM prompt so that the model can revise the generated AAS profile.

The loop continues until SHACL conformance is reached or the configured retry budget is exhausted. If violations remain, the latest AAS and validation messages can be inspected and corrected manually.

---

## Evaluation Material

The repository includes evaluation material for two synthetic industrial use cases inspired by aseptic pharmaceutical production.

### LinFill-120

Located in:

```text
Testing/Generation_Tests/equipment/filling_module/
```

Includes:

- lifecycle datasheet
- line BOM document
- MQTT interface specification
- equipment configuration
- ground truth file

### PlungerSet-80

Located in:

```text
Testing/Generation_Tests/equipment/stoppering_module/
```

Includes:

- lifecycle datasheet
- line BOM document
- OPC UA NodeSet XML file
- equipment configuration
- ground truth file

### Metrics and Evaluation Scripts

Located in:

```text
Testing/Generation_Tests/Test_Scripts/evaluation/
```

Includes scripts for:

- running evaluations
- computing metrics
- aggregating results
- checking manual effort
- plotting results

The evaluation considers:

- SHACL conformance
- violations across generation attempts
- mandatory-field coverage
- value accuracy against ground truth
- manual correction effort
- runtime

---

## SHACL Test Fixtures

The SHACL test fixtures are located in:

```text
Testing/SHACL_Tests/Test_Cases/tests/
```

These fixtures contain intentionally invalid AAS JSON files used to verify that the validation layer catches expected violation classes, such as:

- missing Digital Nameplate
- missing mandatory nameplate fields
- missing Hierarchical Structures
- empty AID interface definitions
- skills without AID
- incomplete capability elements
- incomplete entity statements

The validation script is located in:

```text
Testing/SHACL_Tests/Test_Scripts/validate_aas.py
```

---

## Installation

Installation instructions may depend on the local Python environment and the LLM providers used.

Basic setup:

```bash
git clone https://github.com/MartinJensen37/ARSO_Ontology_AAS_Generation.git
cd ARSO_Ontology_AAS_Generation
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If the repository is configured as an editable Python package, install it with:

```bash
pip install -e .
```

---

## Configuration

Generation settings are handled through:

```text
Generation/config.py
Generation/prompts.yaml
Testing/Generation_Tests/Test_Matrix/matrix.yaml
```

Typical configuration options include:

- LLM provider
- LLM model
- maximum number of generation attempts
- selected AAS submodels
- input document paths
- equipment configuration files
- ground truth files
- ontology paths
- SHACL shape paths
- output paths

---

## Usage

The exact commands may depend on the current configuration and environment.

Potential entry points include:

```text
Generation/pipeline.py
Transformation/AAS_Builder/Builder_Classes/AAS_generation/cli/generate_aas.py
Testing/Generation_Tests/Test_Scripts/evaluation/run_eval.py
Testing/SHACL_Tests/Test_Scripts/validate_aas.py
```

Example placeholders:

Run the generation pipeline:

```bash
python Generation/pipeline.py
```

Generate AAS JSON from profile data:

```bash
python Transformation/AAS_Builder/Builder_Classes/AAS_generation/cli/generate_aas.py
```

Run SHACL validation tests:

```bash
python Testing/SHACL_Tests/Test_Scripts/validate_aas.py
```

Run evaluation:

```bash
python Testing/Generation_Tests/Test_Scripts/evaluation/run_eval.py
```

Update this section with the exact commands for your local setup.

---

## Adding a New Submodel

The framework is designed to be modular. Adding a new submodel may require changes in several places.

Typical steps:

1. Add or update submodel guidance in:

```text
Generation/Context_Builder/context/submodels/
```

2. Add or update ontology definitions in:

```text
Ontology/ARSO/ARSO_AAS.ttl
```

3. Add or update SHACL constraints in:

```text
Ontology/SHACL/
```

4. Add transformation logic in:

```text
Transformation/AAS_Builder/Builder_Classes/AAS_generation/submodels/
```

5. Add semantic identifiers or schema handling if required in:

```text
Transformation/AAS_Builder/Builder_Classes/AAS_generation/core/
```

6. Add or update RDF projection logic in:

```text
Transformation/AAS_Builder/AAS_to_RDF/
```

7. Add tests and examples in:

```text
Testing/
```

---

## Development Notes

Recommended development practices:

- Keep ontology rules and generated SHACL shapes versioned.
- Keep deterministic AAS construction separate from LLM output.
- Validate generated AAS instances after transformation.
- Prefer structured validation reports over free-text error messages.
- Add tests for each new ontology rule, projection mapping, and builder component.
- Keep test equipment documents and ground truth files organised by use case.
- Ensure prompt context and builder logic stay aligned when new submodels are added.

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
