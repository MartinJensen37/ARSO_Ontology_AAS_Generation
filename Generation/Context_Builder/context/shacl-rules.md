# SHACL Validation Rules — Human-Readable Summary

The AAS is projected to RDF and validated with pyshacl against three shape files:

- `Ontology/SHACL/Manual/aas-shacl-schema.ttl` — AAS v3.1 metamodel constraints
- `Ontology/SHACL/Generated/shapes.generated.shacl.ttl` — domain shapes derived from the ARSO
  modules' OWL restrictions
- `Ontology/SHACL/Manual/arso-rules.shacl.ttl` — hand-written rules OWL cannot express

Every violation is fed back as corrective context for the next attempt.

---

## Mandatory Submodels

- **[VIOLATION]** DigitalNameplate: exactly one.
- **[VIOLATION]** HierarchicalStructures: exactly one.
- **[VIOLATION]** Every other submodel: at most one.

## Submodel Dependencies (arso-rules)

- **[VIOLATION]** Skills → AID
- **[VIOLATION]** OperationalData → AID
- **[VIOLATION]** Parameters → AID
- **[VIOLATION]** AIMC → AID
- **[VIOLATION]** Capabilities → Skills, and Skills → Capabilities

## Cross-Submodel References (arso-rules, SPARQL)

- **[VIOLATION]** A Skill's `InterfaceReference` must resolve to an AID interface, and one of its
  keys must name an action under `actions`.
- **[VIOLATION]** Every Skill must be realized by at least one Capability.
- **[VIOLATION]** A Capability `realizedBy` relationship's `second` must resolve to a Skill.
- **[VIOLATION]** An OperationalData or Parameters `InterfaceReference` must resolve to an AID property.
- **[VIOLATION]** An AIMC `InterfaceReference` must resolve to an AID interface, and each AIMC
  `Source` to an AID property.

## Values and Patterns (arso-rules)

- **[VIOLATION]** `ArcheType` is exactly `Full`, `OneDown` or `OneUp`.
- **[VIOLATION]** Every AID `Forms` collection has `href`, `opc_node_id` or `modv_address`.
- **[VIOLATION]** These semanticIds start with `https://smartproductionlab.aau.dk/`: Skill
  Operation, Capability element, OperationalData variable, Parameter entry.
- **[WARNING]** An `EntryNode` with no statements.

## Domain Structure (ARSO module restrictions)

- **DigitalNameplate**: `URIOfTheProduct`, `ManufacturerName`, `ManufacturerProductDesignation`,
  `ContactInformation` (with `Street`, `ZipCode`, `CityTown`, `NationalCode`),
  `OrderCodeOfManufacturer`.
- **HierarchicalStructures**: exactly one `ArcheType` and one `EntryNode`; the `EntryNode` holds
  at least one Node.
- **AID**: at least one interface, each with `title` and `EndpointMetadata`; `EndpointMetadata`
  has `base`, `security` and `securityDefinitions`; every affordance has `Forms`.
- **Skills**: exactly one each of `Interfaces`, `Skills` and `Errors`; each skill has `SemanticId`,
  an Operation and `InterfaceReference`.
- **Capabilities**: at least one `CapabilitySet` holding at least one container with a Capability.
- **TechnicalData**: exactly one `GeneralInformation` with the four manufacturer fields.
- **AIMC**: exactly one `MappingConfigurations`; each configuration has `Sources` and `Sinks`; each
  Source and Sink has its reference and its id.

These are enforced as of the last regeneration of the generated shapes
(`python Transformation/Generate_Shapes/generate_shapes.py`).

## Format Check (profile validation, not SHACL)

- `DateOfManufacture` must match `YYYY-MM-DD`.

---

## Quick Checklist Before Outputting

- [ ] DigitalNameplate and HierarchicalStructures present, with every mandatory element
- [ ] `ArcheType` is `OneUp`, `OneDown` or `Full`
- [ ] AID present if Skills, OperationalData, Parameters or AIMC is
- [ ] Skills and Capabilities both present or both absent
- [ ] Every Skill references an AID action and is realized by a Capability
- [ ] OperationalData, Parameters and AIMC sources reference AID **properties**
- [ ] Lab semanticIds start with `https://smartproductionlab.aau.dk/`
- [ ] Every submodel id is referenced from the shell's `submodels` array
