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
| `technical-data.ttl` | 02003 | 26 | 0 | **Inert — see below** |
| `control-component.ttl` | 02015 (not supplied) | 11 | 1 | ARSO-flattened |
| `operational-data.ttl` | none (ARSO-specific) | 5 | 1 | n/a |
| `parameters.ttl` | none (ARSO-specific) | 3 | 1 | n/a |
| — | 02027 AIMC | — | — | **No ARSO module** |

## Added to the ontology

`arso:semanticId` is multi-valued and the converter reads every value, so all of
these are additive: they let an externally authored, IDTA-conformant document be
typed, without changing how documents this pipeline generates are typed. The
SHACL fixture suite produces identical results before and after.

**`aid.ttl` — 28 classes.** The submodel gained the 1/1 template id alongside
its existing 1/0 one. Element classes gained their W3C WoT / IDTA ids:
`td#title`, `dcterms:created`, `dcterms:modified`, `td#supportContact`,
`td#baseURI`, `hypermedia#forContentType`, `td#hasSecurityConfiguration`,
`td#definesSecurityScheme`, `security#SecurityScheme`, `td#PropertyAffordance`,
`td#ActionAffordance`, `td#EventAffordance`, `td#hasForm`,
`hypermedia#hasTarget`, `http#methodName`, the `modbus#`/`mqtt#` binding terms,
the OPC UA `WoT-Binding/` terms, and the IDTA `PropertyDefinition` /
`ExternalDescriptor` / `externalDescriptorName` ids.

**`capabilities.ttl` — 20 classes.** Every element class except the five that
already had one; all from `https://admin-shell.io/idta/CapabilityDescription/`.
`CapabilitySetSMC` and `CapabilityContainerSMC` keep their existing
`smartfactory.de` ids and gain the IDTA ones.

## Where ARSO is deliberately stricter

Requirements ARSO enforces that the templates do not. These are intentional and
should stay; they are listed so the delta is visible.

1. **Nameplate address fields.** `AddressInformationSMC` requires Street,
   ZipCode, CityTown and NationalCode (`owl:someValuesFrom`). IDTA 02006-3-0
   ships `AddressInformation` as an *empty* SMC and delegates its contents to
   IDTA 02002, so the template itself states no inner cardinality at all.
2. **Nameplate submodel is mandatory.** `ARSO_AAS.ttl` requires exactly one
   `DigitalNameplateSubmodel` per AAS. IDTA 02006-3-0 carries no submodel-level
   cardinality qualifier.
3. **HierarchicalStructures submodel is mandatory.** `ARSO_AAS.ttl` requires
   exactly one. The IDTA 02011-1-1 template marks the submodel `ZeroToOne`.
4. **At least one interface.** `AIDSubmodel` requires `some InterfaceSMC`; every
   `InterfaceTemplateFor*` in IDTA 02017-1-1 is `ZeroToMany`.
5. **Cross-submodel reference targets.** The SPARQL rules in
   `SHACL/Manual/arso-rules.shacl.ttl` require a Skill's `InterfaceReference` to
   resolve to a real AID action, a Capability's `realizedBy` to resolve to a real
   Skill, and OperationalData/Parameters `InterfaceReference` to resolve to a
   real AID property. No IDTA template expresses cross-submodel constraints.
6. **Flattened Skills.** `control-component.ttl` adapts IDTA 02015 CCType to a
   flatter shape; see the design note in that file.

## Where ARSO is looser than the template

1. **`contentType`.** IDTA 02017-1-1 marks it `One` inside `EndpointMetadata`;
   `EndpointMetadataSMC` does not require it.
2. **No upper bounds on optional Nameplate elements.** The template marks most
   Nameplate elements `ZeroToOne`; ARSO adds `max 1` only for
   `AddressInformation`, `Markings` and `AssetSpecificProperties`, so the rest
   could legally repeat.
3. **`CapabilityComposedOf` is `TwoToMany`** in IDTA 02020. ARSO places no
   cardinality on it.

## Divergences worth fixing

1. **`FormsSMC` uses idShort `"Forms"`; IDTA 02017-1-1 uses `forms`.** The
   builder emits `"Forms"` too, so the pipeline is self-consistent — but a
   conformant third-party AID submodel would never match, and its `FormsSMC`
   restriction would fail. Not fixable by adding a second `arso:idShort`: the
   converter reads only `idshorts[0]` (`aas_to_rdf.py`, `_StructuralRules`) and
   rdflib does not order multiple values, so a second value picks arbitrarily.
   Fixing this means changing both the ontology and the builder together, or
   making the converter match a set of idShorts.
2. **`semantic_ids.py` still emits only the `smartfactory.de` ids** for
   CapabilitySet/CapabilityContainer, and its comment claims IDTA defines none.
   IDTA 02020 does define both; the ontology now accepts either.
3. **`CapabilityRealizedBy` is wrapped in an SML** (`CapabilityRealizedBySML`).
   IDTA 02020 places repeated `CapabilityRealizedBy` RelationshipElements
   directly under `CapabilityRelations`, with no list wrapper.
4. **`technical-data.ttl` is inert.** 26 classes, zero `arso:semanticId` /
   `arso:idShort` / `arso:parentClass` annotations, so the converter can never
   type anything as a TechnicalData class and its OWL restrictions never fire.
   Nothing in the pipeline builds this submodel either. It needs the IDTA 02003
   ids (submodel `0173-1#01-AHX837#002`, elements under `0173-1#02-…`) before it
   does anything.
5. **`TechnicalManufacturerNameMLP` is modelled as a MultiLanguageProperty.**
   IDTA 02003 declares `ManufacturerName` a `Property/xs:string`.
6. **Legacy AID idShorts with no IDTA counterpart:** `modv_address`
   (02017-1-1 has `modv_entity`, `modv_function`, `modv_type`,
   `modv_pollingTime`, `modv_timeout`, `modv_zeroBasedAddressing`),
   `opc_node_id` (template uses `uav_browsePath`), and `MqvTopicProperty`
   (no `mqv_topic` in the template — the MQTT topic belongs in `href`).
7. **No AIMC module.** IDTA 02027 is supplied and `aas_to_profile.py` maps an
   `AssetInterfacesMappingConfiguration` submodel to the key `AIMC`, but no
   ontology module, builder or UI submodel key exists for it.

## Not modelled, intentionally

IDTA 02006-3-0 defines `ArbitraryProperty` / `ArbitraryMLP` / `ArbitraryFile`
(`https://admin-shell.io/SMT/General/Arbitrary*`) as generic extension slots
under `AssetSpecificProperties`. They are placeholders for arbitrary vendor
content, not real elements, so ARSO does not model them.
