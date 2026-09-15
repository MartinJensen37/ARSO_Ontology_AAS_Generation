# ARSO vs. IDTA submodel templates

Comparison of the ARSO ontology against the IDTA submodel templates and PDFs in
`Generation/Context_Builder/context/submodels/SMTs/`. Cardinalities quoted from
the templates are the `SMT/Cardinality` qualifiers carried in the template JSON.

Scope: ARSO only (ARSO_AAS.ttl + Modules/), with its AAS v3.1 and CSS imports.
APSO is out of scope.

## Coverage

| ARSO module | IDTA source | Classes | `arso:semanticId` | Status |
| --- | --- | --- | --- | --- |
| `nameplate.ttl` | 02006-3-0 | 35 | 40 | Complete |
| `hierarchical-structures.ttl` | 02011-1-1 | 8 | 8 | Complete |
| `aid.ttl` | 02017-1-1 | 44 | 32 (was 4) | Filled in |
| `capabilities.ttl` | 02020 | 25 | 26 (was 5) | Filled in |
| `technical-data.ttl` | 02003 | 26 | 26 (was 0) | Filled in; now built |
| `aimc.ttl` | 02027 | 15 | 15 | New; built |
| `control-component.ttl` | 02015 (not supplied) | 11 | 2 | ARSO-flattened |
| `operational-data.ttl` | none (ARSO-specific) | 5 | 1 | n/a |
| `parameters.ttl` | none (ARSO-specific) | 3 | 1 | n/a |

## Added to the ontology

`arso:semanticId` is multi-valued and the converter reads every value, so these
additions let an externally authored, IDTA-conformant document be typed without
changing how the pipeline's own documents are typed.

- **`aid.ttl` — 28 classes.** The submodel gained the 1/1 template id beside its
  1/0 one. Element classes gained their W3C WoT / IDTA ids (`td#title`,
  `td#hasForm`, `hypermedia#hasTarget`, the `modbus#` / `mqtt#` / OPC UA
  `WoT-Binding/` terms, and the IDTA `PropertyDefinition` / `ExternalDescriptor`
  ids).
- **`capabilities.ttl` — 20 classes**, all from
  `https://admin-shell.io/idta/CapabilityDescription/`. `CapabilitySetSMC` and
  `CapabilityContainerSMC` keep their `smartfactory.de` ids and accept both.
- **`technical-data.ttl` — 26 classes** gained their IDTA 02003 ECLASS IRDIs.
  The module previously carried no annotations at all, so nothing could be typed
  as a TechnicalData class.
- **`aimc.ttl` — new module** for IDTA 02027 (MappingConfigurations, Sources,
  Sinks). `ARSO_AAS.ttl` imports it and adds `arso:hasTechnicalDataSubmodel` /
  `arso:hasAIMCSubmodel` with at-most-one restrictions.
- **`arso-rules.shacl.ttl`** — AIMC requires AID; an AIMC `InterfaceReference`
  must resolve to an AID interface and each `Source` to an AID property.

## Where ARSO is deliberately stricter

Requirements ARSO enforces that the templates do not. These are intentional and
should stay; they are listed so the delta is visible.

1. **Nameplate address fields.** `AddressInformationSMC` requires Street,
   ZipCode, CityTown and NationalCode. IDTA 02006-3-0 ships `AddressInformation`
   as an *empty* SMC and delegates its contents to IDTA 02002, so the template
   states no inner cardinality at all.
2. **Nameplate submodel is mandatory.** `ARSO_AAS.ttl` requires exactly one
   `DigitalNameplateSubmodel` per AAS; IDTA 02006-3-0 has no submodel-level
   cardinality qualifier.
3. **HierarchicalStructures submodel is mandatory.** ARSO requires exactly one;
   the IDTA 02011-1-1 template marks it `ZeroToOne`.
4. **At least one interface.** `AIDSubmodel` requires `some InterfaceSMC`; every
   `InterfaceTemplateFor*` in IDTA 02017-1-1 is `ZeroToMany`.
5. **Cross-submodel reference targets.** The SPARQL rules in
   `arso-rules.shacl.ttl` require Skill, Capability, OperationalData, Parameters
   and AIMC references to resolve inside the same AAS. No IDTA template
   expresses cross-submodel constraints.
6. **Flattened Skills.** `control-component.ttl` adapts IDTA 02015 CCType to a
   flatter shape; see the design note in that file.
7. **AIMC sources are AID properties only.** IDTA 02027 lets a Source reference
   any interface element; ARSO rejects actions and events. Sinks are unchecked,
   as IDTA allows any submodel element there.

## Where ARSO is looser than the template

1. **`contentType`.** IDTA 02017-1-1 marks it `One` inside `EndpointMetadata`;
   `EndpointMetadataSMC` does not require it.
2. **No upper bounds on optional Nameplate elements.** Most are `ZeroToOne` in
   the template; ARSO adds `max 1` only for `AddressInformation`, `Markings` and
   `AssetSpecificProperties`.
3. **`CapabilityComposedOf` is `TwoToMany`** in IDTA 02020; ARSO places no
   cardinality on it.

## Open divergences

1. **`FormsSMC` uses idShort `"Forms"`; IDTA 02017-1-1 uses `forms`.** The
   builder emits `"Forms"` too, so the pipeline is self-consistent, but a
   conformant third-party AID submodel would never match. A second
   `arso:idShort` cannot fix it: the converter reads only `idshorts[0]`
   (`aas_to_rdf.py`, `_StructuralRules`), and rdflib does not order multiple
   values. The ontology and builder must change together, or the converter must
   match a set of idShorts.
2. **`semantic_ids.py` still emits the `smartfactory.de` ids** for
   CapabilitySet/CapabilityContainer. IDTA 02020 defines both; ARSO accepts either.
3. **`CapabilityRealizedBy` is wrapped in an SML.** IDTA 02020 places repeated
   `CapabilityRealizedBy` RelationshipElements directly under
   `CapabilityRelations`.
4. **`TechnicalManufacturerNameMLP` is modelled as a MultiLanguageProperty.** IDTA
   02003 and the builder both emit `ManufacturerName` as a `Property`.
5. **Legacy AID idShorts with no IDTA counterpart:** `modv_address`,
   `opc_node_id` and `MqvTopicProperty`. IDTA 02017-1-1 uses `modv_entity` /
   `modv_function` / `modv_type`, `uav_browsePath`, and carries the MQTT topic
   in `href`. `FormsAddressingShape` and the OPC UA builder both depend on
   `opc_node_id`, so this is a coordinated change.
6. **HierarchicalStructures `SameAs` is emitted as a ReferenceElement.** IDTA
   02011-1-1 models it as a RelationshipElement, and ARSO's `SameAsRelationship`
   subclasses `aas:RelationshipElement`, so the emitted node is typed with a
   class its model type contradicts.
7. **Nameplate optional elements.** The builder emits them without semanticIds
   (so ARSO never types them), emits `ManufacturerProductFamily` as a Property
   where IDTA uses an MLP, and accepts `ManufacturerArticleNumber`, which is not
   an IDTA 02006 element. It ignores the IDTA optional elements
   `ProductArticleNumberOfManufacturer`, `ManufacturerProductRoot`,
   `ManufacturerProductType`, `FirmwareVersion`, `UniqueFacilityIdentifier`,
   `CompanyLogo`, `Markings` and `AssetSpecificProperties`.
8. **OperationalData.** `OperationalDataSubmodel` requires `some arso:Datapoint`
   (a Decimal Property), but the builder emits `OperationalDataVariableSMC`
   collections. It passes today only because the generated shapes do not enforce
   that restriction.
9. **Generated shapes are stale.** `shapes.generated.shacl.ttl` predates the
   TechnicalData annotations and the AIMC module, so their OWL restrictions
   (for example exactly one `GeneralInformation` or `MappingConfigurations`)
   are not enforced until it is regenerated. Regenerating may also surface item 8.

## Resolved

- **`technical-data.ttl` was inert** — now annotated, built, inverted and editable.
- **No AIMC module** — added with builder, parser, SHACL rules and UI.
- **HierarchicalStructures relationships** carried
  `.../HierarchicalStructures/Relationship/1/0`, which IDTA 02011 does not
  define; the builder now emits the `HasPart` / `IsPartOf` ids.
- **`SkillInterfaceRefTargetShape`** targeted `arso:CCInterfaceReferenceRef`, a
  class that does not exist, so it never fired; it now targets
  `arso:SkillInterfaceReferenceRef`.
- **`aas_to_rdf.py`** emitted `aas:Property/valueType` for a Range instead of
  `aas:Range/valueType`, failing every Range's MinCount shape.
- **UI protocol binding ids** in `semanticIds.ts` had drifted from
  `semantic_ids.py`.

## Not modelled, intentionally

- IDTA 02006-3-0's `ArbitraryProperty` / `ArbitraryMLP` / `ArbitraryFile`
  (`https://admin-shell.io/SMT/General/Arbitrary*`) are generic extension slots
  for vendor content, not real elements.
- IDTA 02003's sample gives `TechnicalPropertyAreas` children idShorts such as
  `ECLASS`, which AASd-120 forbids inside a list. The pipeline follows the
  template instead: one positional area collection holding named sections.
