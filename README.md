# ARSO Ontology AAS Generation Structure

This folder is a reorganized project layout aligned with generation, transformation, validation, testing, and ontology concerns.

## Top-level structure

- `Generation/`
  - `Context_Builder/`
    - `Parsing/`
    - `RAG/`
  - `LLM_Client/`
  - `pipeline.py`
  - `config.py`
- `Transformation/`
  - `AAS_Builder/`
    - `Builder_Classes/`
    - `AAS_to_RDF/`
- `Validation/`
  - `Validator/`
- `Testing/`
  - `Generation_Tests/`
    - `Test_Matrix/`
    - `Test_Scripts/`
  - `SHACL_Tests/`
    - `Test_Cases/`
    - `Test_Scripts/`
- `Ontology/`
  - `ARSO/`
  - `CSS/`
  - `AAS/`
  - `SHACL/`
    - `Generated/`
    - `Manual/`

## Compatibility

`Generation/` includes compatibility wrapper modules (`prompt_builder.py`, `rag_loader.py`, etc.) so existing import paths continue to work while implementation files live in the reorganized subfolders.
