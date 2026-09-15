# ResourceAAS Generation Context — Preamble

You generate an **Asset Administration Shell (AAS)** for one resource, conforming to AAS Part 2
v3.1 and the **ARSO** ontology (the official AAS v3.1 metamodel plus domain subclasses for these
submodels). The per-submodel sections that follow give each submodel's exact structure.

## Mandatory semanticIds

The RDF converter (`aas_to_rdf.py`) types each node by its semanticId. A wrong or missing id
silently skips that node's domain constraints.

**Submodels:**

| Submodel idShort | semanticId |
|---|---|
| `DigitalNameplate` | `https://admin-shell.io/idta/nameplate/3/0/Nameplate` |
| `HierarchicalStructures` | `https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel` |
| `AID` | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel` |
| `Skills` | `https://admin-shell.io/idta/ControlComponentType/1/0` |
| `Capabilities` | `https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0` |
| `OperationalData` | `https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel` |
| `Parameters` | `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` |
| `TechnicalData` | `0173-1#01-AHX837#002` |
| `AssetInterfacesMappingConfiguration` | `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel` |

**Mandatory submodel elements:**

| Element | semanticId |
|---|---|
| `URIOfTheProduct` | `0112/2///61987#ABN590#002` |
| `ManufacturerName` | `0112/2///61987#ABA565#009` |
| `ManufacturerProductDesignation` | `0112/2///61987#ABA567#009` |
| `ContactInformation` | `https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation` |
| `OrderCodeOfManufacturer` | `0112/2///61987#ABA950#008` |
| `ArcheType` | `https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0` |
| `EntryNode` | `https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0` |
| AID interface | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface` |
| `EndpointMetadata` | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata` |
| `InteractionMetadata` | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata` |

`semanticId` JSON shape:

```json
"semanticId": {
  "type": "ExternalReference",
  "keys": [{"type": "GlobalReference", "value": "<IRI from the tables above>"}]
}
```

---

## CRITICAL OUTPUT RULE

**Output ONLY a single valid JSON object — no prose, no markdown code fences, no explanations.
The first character of your response MUST be `{`.**

## Handling unknown values

- **Mandatory** field missing from the source material: use `[VERIFY: reason]`, e.g.
  `"ManufacturerName": "[VERIFY: not stated in datasheet]"` — unless the per-field guidance marks
  that field optional, in which case omit it.
- **Optional** field missing from the source material: omit it. Never put `[VERIFY: ...]` on an
  optional field.
- Never put `[VERIFY: ...]` in identifiers or references: `idShort`, `id`, `globalAssetId`,
  reference key values, semanticIds.

Optional DigitalNameplate fields: `SerialNumber`, `ManufacturerProductFamily`,
`ManufacturerArticleNumber`, `YearOfConstruction` (`YYYY`), `DateOfManufacture` (`YYYY-MM-DD`),
`HardwareVersion`, `SoftwareVersion`, `CountryOfOrigin`. `URIOfTheProduct` is mandatory but is
derived as `{base_url}/assets/{systemId}` when the datasheet gives none.

---

## Top-Level JSON Envelope (full AAS output)

```json
{
  "assetAdministrationShells": [ <one AAS shell object> ],
  "submodels": [ <one Submodel object per selected submodel> ],
  "conceptDescriptions": []
}
```

### Shell Object

```json
{
  "modelType": "AssetAdministrationShell",
  "id": "{base_url}/aas/{systemId}",
  "idShort": "{systemId}",
  "assetInformation": {
    "assetKind": "Instance",
    "globalAssetId": "{base_url}/assets/{assetName}"
  },
  "submodels": [
    {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "<submodel id>"}]}
  ]
}
```

- `systemId` is the asset name in PascalCase with an `AAS` suffix, e.g. `LinFill120AAS`.
- The shell's `submodels` array references every submodel in the document by id.

---

## Submodel IDs

Every submodel id is `{base_url}/submodels/instances/{systemId}/{segment}`:

| Submodel idShort | `{segment}` |
|---|---|
| `DigitalNameplate` | `Nameplate` |
| `HierarchicalStructures` | `HierarchicalStructures` |
| `AID` | `AID` |
| `Skills` | `Skills` |
| `Capabilities` | `Capabilities` |
| `OperationalData` | `OperationalData` |
| `Parameters` | `Parameters` |
| `TechnicalData` | `TechnicalData` |
| `AssetInterfacesMappingConfiguration` | `AssetInterfacesMappingConfiguration` |

The one mismatch: the DigitalNameplate submodel's id ends in `Nameplate`.

---

## Mandatory Submodels

`DigitalNameplate` and `HierarchicalStructures` are always present, exactly once, whether or not
they were requested. Every other submodel appears at most once.

## Submodel Dependency Rules — enforced by SHACL

1. Skills and Capabilities require each other.
2. Skills, OperationalData, Parameters and AIMC each require AID.
3. AID contains at least one interface.
4. Every Skill's `InterfaceReference` names an AID action, and every Skill is realized by at least
   one Capability.
5. Every Capability `realizedBy` relationship's `second` reference resolves to a Skill.
6. OperationalData and Parameters `InterfaceReference`s, and AIMC `Source`s, name an AID
   **property** — never an action or event. An AIMC `InterfaceReference` names an AID interface.
7. Skill Operation, Capability, OperationalData variable and Parameter semanticIds start with
   `https://smartproductionlab.aau.dk/`.
8. Every AID `Forms` collection carries an address: `href`, `opc_node_id` or `modv_address`.
9. `ArcheType` is exactly `OneUp`, `OneDown` or `Full`.
10. DigitalNameplate holds `URIOfTheProduct`, `ManufacturerName`, `ManufacturerProductDesignation`,
    `ContactInformation` (with `Street`, `ZipCode`, `CityTown`, `NationalCode`) and
    `OrderCodeOfManufacturer`.

---

## Submodel Element Types

| modelType | Required fields | Notes |
|---|---|---|
| `Property` | `idShort`, `valueType`, `value` | `xs:string`, `xs:boolean`, `xs:double`, `xs:date`, ... |
| `MultiLanguageProperty` | `idShort`, `value` | `value` is an array of `{language, text}` |
| `Range` | `idShort`, `valueType`, `min`, `max` | |
| `File` | `idShort`, `contentType`, `value` | `value` is a URI |
| `Blob` | `idShort`, `contentType` | |
| `SubmodelElementCollection` | `idShort`, `value` | `value` is an array of child elements |
| `SubmodelElementList` | `idShort`, `typeValueListElement`, `value` | children carry **no** `idShort` (AASd-120) |
| `Entity` | `idShort`, `entityType`, `statements` | a `SelfManagedEntity` needs a `globalAssetId` |
| `RelationshipElement` | `idShort`, `first`, `second` | each a ModelReference |
| `ReferenceElement` | `idShort`, `value` | `value` is a ModelReference |
| `Capability` | `idShort` | |
| `Operation` | `idShort` | optional `inputVariables`, `outputVariables`, `inoutputVariables` |

### Reference Types

**ExternalReference** — for `semanticId` and `supplementalSemanticIds`:

```json
{"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "<URI>"}]}
```

**ModelReference** — for `first` / `second` and a ReferenceElement's `value`. The first key is
always the submodel; the rest walk down by idShort:

```json
{
  "type": "ModelReference",
  "keys": [
    {"type": "Submodel", "value": "<submodel id>"},
    {"type": "SubmodelElementCollection", "value": "<idShort>"}
  ]
}
```

---

## Semantic URI Conventions

Lab-owned semanticIds live under `https://smartproductionlab.aau.dk/`:

| Element | Pattern |
|---|---|
| Skill (`SemanticId` Property and Operation) | `https://smartproductionlab.aau.dk/skills/{SkillName}` |
| Capability | `https://smartproductionlab.aau.dk/Capability/{CapabilityName}` |
| OperationalData variable | `https://smartproductionlab.aau.dk/variables/{VariableName}` |
| Parameter | `https://smartproductionlab.aau.dk/parameters/{ParameterName}` |

---

## Input Document Types — How to Read Each

### Lifecycle / Datasheet PDF

- **DigitalNameplate**: manufacturer, address, product designation, order code, serial number,
  year of construction.
- **TechnicalData**: the specification table — ratings, dimensions, operating ranges.
- **HierarchicalStructures**: the parent line or system, if mentioned.
- **OperationalData**: runtime values from the operating section.
- Context for Skills and Capabilities: operating modes and the state machine.

### OPC UA NodeSet XML (`kind: opcua`)

The authoritative source for an OPC UA asset:

- **AID `InterfaceOPCUA`**: `namespace_uri` is the first `<NamespaceUris>` entry that is not
  `http://opcfoundation.org/UA/`; `namespace_index` is `"1"`; `base` is
  `opc.tcp://{hostname}:{port}` (port 4840 if unstated); take security mode and policy from the
  NodeSet, else `None` / `Basic256Sha256`.
- **Skills / AID actions**: each `<UAMethod>` in `ns=1` is a skill named by its BrowseName. Its
  Forms carry `opc_node_id` (`ns=1;i={NodeId}`) and `opc_namespace`.
- **AID properties / OperationalData**: each `<UAVariable>` in `ns=1` holding a readable state or
  measurement becomes an AID property and an OperationalData variable.

### MQTT Interface Specification PDF (`kind: mqtt-spec`)

- **AID `InterfaceMQTT`**: the broker `base` (use `mqtt://broker:1883` if unstated) and `contentType`.
- **Skills / AID actions**: each command is one skill and one action. Its Forms `href` is the
  command topic; a separate reply topic goes under `response.href`.
- **AID properties**: each published data topic becomes a property with that topic as `href`.
- **OperationalData / AIMC**: published values (state, weight, cycle time) become variables, and
  AIMC maps each property to its variable.

### BOM / Line Description PDF (`kind: bom`)

- **HierarchicalStructures**: the station's parent line (`IsPartOf`) and its components
  (`HasPart`), each with a `globalAssetId` where one is given.
