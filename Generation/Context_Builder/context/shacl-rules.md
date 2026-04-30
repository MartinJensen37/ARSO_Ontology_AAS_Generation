# SHACL Validation Rules — Human-Readable Summary

The generated AAS JSON is validated by pyshacl against three shape files:
- `shacl/manual/aas-shacl-schema.ttl` — AAS v3.1 metamodel constraints
- `shacl/generated/shapes.generated.shacl.ttl` — ARSO domain shapes (auto-derived from ARSO_AAS.ttl)
- `shacl/manual/arso-rules.shacl.ttl` — manual SPARQL cross-submodel rules

All rules below are checked; violations are fed back as corrective context for the next attempt.

---

## Mandatory Submodels

- **[VIOLATION]** `DigitalNameplate` submodel MUST be present (minCount 1).
- **[VIOLATION]** `HierarchicalStructures` submodel MUST be present (minCount 1).

---

## Submodel Dependency Rules (R5–R8, arso-rules.shacl.ttl)

These fire on `aas:AssetAdministrationShell` and rely on typed-link properties
(`arso:hasSkillsSubmodel`, `arso:hasAIDSubmodel`, etc.) emitted by the RDF converter.

- **R5 [VIOLATION]** Skills present → AID (`AssetInterfacesDescription`) MUST also be present.
- **R6 [VIOLATION]** OperationalData present → AID MUST also be present.
- **R7 [VIOLATION]** Parameters present → AID MUST also be present.
- **R8a [VIOLATION]** Capabilities present → Skills MUST also be present.
- **R8b [VIOLATION]** Skills present → Capabilities MUST also be present.

---

## Cross-Submodel Reference Rules (R1–R2, arso-rules.shacl.ttl)

- **R1 [VIOLATION]** A `SkillInterfaceRef` ReferenceElement inside the Skills submodel MUST resolve
  to an `arso:InterfaceSMC` in the same AAS's AID submodel.
- **R2 [VIOLATION]** A `RealizedByRef` ReferenceElement inside the Capabilities submodel MUST
  resolve to a Skill SMC in the same AAS's Skills submodel.

---

## BOM / HierarchicalStructures Rules

- **R3 [VIOLATION]** A BOM Entity with `entityType: SelfManagedEntity` MUST have a `globalAssetId`.
- **R4 [VIOLATION]** The `ArcheType` Property value MUST be exactly `"Full"`, `"OneDown"`, or `"OneUp"`.
- **R9 [WARNING]** If an EntryNode exists but has no statements (empty BOM), a warning is raised.

---

## Domain Shape Constraints (shapes.generated.shacl.ttl)

Generated from ARSO_AAS.ttl via OWL→SHACL. Key checks:

- Each `DigitalNameplate` submodel MUST contain `ManufacturerName` (MultiLanguageProperty),
  `ManufacturerProductDesignation`, `ContactInformation` SMC, and `OrderCodeOfManufacturer`.
- The `ContactInformation` SMC MUST contain `Street`, `ZipCode`, `CityTown`, and `NationalCode` properties.
- Each `Capabilities` submodel MUST contain at least one `arso:CapabilityContainerSMC`,
  which in turn MUST contain at least one `arso:CapabilityElement` (a `Capability` model type).
- Each AID submodel MUST contain at least one `Interface` SMC in its `submodelElements`.
- Each `Interface` SMC MUST contain `EndpointMetadata` and `InteractionMetadata` child SMCs.

---

## Semantic / Value Rules (aas-shacl-schema.ttl)

- **[VIOLATION]** `YearOfConstruction` value must match pattern `^[0-9]{4}$` (e.g. `"2023"`).
- **[VIOLATION]** `DateOfManufacture` value must match pattern `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`.
- **[VIOLATION]** Each Skill's `SemanticId` Property value MUST start with
  `https://smartproductionlab.aau.dk/` or `http://smartproductionlab.aau.dk/`.
- **[VIOLATION]** Each Capability's `SemanticId` Property value MUST start with
  `https://smartproductionlab.aau.dk/` or `http://smartproductionlab.aau.dk/`.

---

## Quick Checklist Before Outputting

- [ ] `DigitalNameplate` submodel present with `ManufacturerName` (MLP), `ManufacturerProductDesignation` (MLP), `ContactInformation` SMC (with Street, ZipCode, CityTown, NationalCode), and `OrderCodeOfManufacturer`
- [ ] `HierarchicalStructures` submodel present with `ArcheType` property (`"OneUp"` / `"OneDown"` / `"Full"`) and an `EntryNode` Entity
- [ ] If Skills → Capabilities also present (R8)
- [ ] If Capabilities → Skills also present (R8a)
- [ ] If Skills / OperationalData / Parameters → AID also present (R5–R7)
- [ ] All Capability `SemanticId` Property values start with `https://smartproductionlab.aau.dk/`
- [ ] All Skill `SemanticId` Property values start with `https://smartproductionlab.aau.dk/`
- [ ] AID has at least one `Interface` SMC in `submodelElements`
- [ ] All submodel IDs are referenced in the shell's `submodels` array
- [ ] `ArcheType` value is exactly `"Full"`, `"OneDown"`, or `"OneUp"` (no other strings)
