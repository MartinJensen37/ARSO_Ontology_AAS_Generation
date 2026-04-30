# ResourceAAS Generation Context â€” Preamble (v2 â€” IDTA-aligned)

You are generating an **Asset Administration Shell (AAS) JSON document** conforming to the AAS
Part 2 v3.1 specification and the **ARSO_AAS** ontology (which imports the official AAS v3.1
metamodel and adds domain-specific subclasses for our submodels).

## Mandatory semanticIds (canonical — matches ARSO_AAS.ttl and the AAS builder)

Every submodel and every mandatory submodel element MUST include a `semanticId` whose key value
is **exactly one of the IRIs below**. The RDF converter (`aas_to_rdf.py`) uses these to assign
the correct ARSO subclass to each node; a wrong or missing ID causes domain constraints to be
skipped.

**Submodel-level (set on each Submodel's `semanticId`):**

| Submodel idShort         | semanticId IRI |
|---|---|
| `DigitalNameplate`       | `https://admin-shell.io/idta/nameplate/3/0/Nameplate` |
| `HierarchicalStructures` | `https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel` |
| `AID`                    | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel` |
| `Capabilities`           | `https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0` |
| `Skills`                 | `https://admin-shell.io/idta/ControlComponentType/1/0` |
| `OperationalData`        | `https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel` |
| `Parameters`             | `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` |

**Submodel-element-level (mandatory SMEs — set on each SME's `semanticId`):**

| SME idShort                       | semanticId IRI |
|---|---|
| `ManufacturerName`                | `0112/2///61987#ABA565#009` |
| `ManufacturerProductDesignation`  | `0112/2///61987#ABA567#009` |
| `ContactInformation`              | `https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation` |
| `OrderCodeOfManufacturer`         | `0112/2///61987#ABA950#008` |
| `ArcheType`                       | `https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0` |
| `EntryNode`                       | `https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0` |
| `Interface` (in AID)              | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface` |
| `EndpointMetadata`                | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata` |
| `InteractionMetadata`             | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata` |

`semanticId` JSON shape:

```json
"semanticId": {
  "type": "ExternalReference",
  "keys": [{"type": "GlobalReference", "value": "<IRI from table above>"}]
}
```

Use this exact structure â€” `type: ExternalReference` at the reference level and
`type: GlobalReference` inside each key.

---

## CRITICAL OUTPUT RULE

**Output ONLY a single valid JSON object â€” no prose, no markdown code fences, no explanations
before or after. The first character of your response MUST be `{`.**

## Handling unknown values

For **mandatory** fields where the spec sheet genuinely lacks the value, use `[VERIFY: reason]` as a placeholder — e.g. `"ManufacturerName": "[VERIFY: not stated in datasheet]"`.

For **optional** fields, OMIT the field entirely from the JSON when the value is not in the spec — do NOT use `[VERIFY: ...]` on optional fields.

Optional Nameplate fields (omit if unknown):
`DateOfManufacture`, `YearOfConstruction`, `HardwareVersion`, `SoftwareVersion`,
`FirmwareVersion`, `CountryOfOrigin`, `ManufacturerProductFamily`, `BatchNumber`,
`URIOfTheProduct`, `ManufacturerArticleNumber`.

Format constraint when present: `DateOfManufacture` must be `YYYY-MM-DD` (xsd:date).
`YearOfConstruction` must be exactly `YYYY` (4 digits).

---

## Top-Level JSON Envelope

The document MUST follow exactly this envelope structure:

```json
{
  "assetAdministrationShells": [ <one AAS shell object> ],
  "submodels": [ <array of Submodel objects â€” one per selected submodel> ],
  "conceptDescriptions": []
}
```

### Shell Object Structure

```json
{
  "modelType": "AssetAdministrationShell",
  "id": "{base_url}/aas/{systemId}",
  "idShort": "{systemId}_AAS",
  "assetInformation": {
    "assetKind": "Instance",
    "globalAssetId": "{base_url}/assets/{systemId}"
  },
  "submodels": [
    {
      "type": "ModelReference",
      "keys": [{ "type": "Submodel", "value": "<submodel-id>" }]
    }
  ]
}
```

- **`id`**: use the pattern `{base_url}/aas/{systemId}` â€” derive `systemId` from the asset name
  (no spaces, camelCase or PascalCase)
- **`idShort`**: `{systemId}_AAS`
- **`globalAssetId`**: `{base_url}/assets/{systemId}`
- The `submodels` array in the shell MUST reference EVERY submodel in the `submodels` array by id

---

## Submodel ID Convention

Every submodel id follows:
```
{base_url}/submodels/instances/{systemId}/{idShort}
```

Example for base_url = `https://smartproductionlab.aau.dk`, systemId = `MyRobot`:
- DigitalNameplate â†’ `https://smartproductionlab.aau.dk/submodels/instances/MyRobot/DigitalNameplate`
- Skills â†’ `https://smartproductionlab.aau.dk/submodels/instances/MyRobot/Skills`
- OperationalData â†’ `https://smartproductionlab.aau.dk/submodels/instances/MyRobot/OperationalData`

---

## Mandatory Submodels â€” ALWAYS Required

**DigitalNameplate** and **HierarchicalStructures** MUST always be present, even if not explicitly
listed. They are required by the SHACL core shape for all ResourceAAS instances.

---

## Submodel Dependency Rules â€” ENFORCE STRICTLY

These rules are validated by SHACL and will cause violations if broken:

1. **Skills â†” Capabilities are mutually required**: If Skills is present â†’ Capabilities MUST be
   present. If Capabilities is present â†’ Skills MUST be present.

2. **AID required when Skills/OperationalData/Parameters exist**: If any of Skills, OperationalData,
   or Parameters are present â†’ AID submodel MUST be present.

3. **Skills require AID interface link**: Each Skill MUST be accessible through a SkillInterface
   that is linked to a ResourceInterface in the AID submodel.

4. **Each Skill gets exactly one SkillInterface**: Validate that each skill has exactly one
   `accessibleThrough` relation.

5. **AID requires at least one ResourceInterface**: If AID exists, at least one interface must be
   present in the InteractionMetadata.

6. **Capabilities must link to Skills via realizedBy**: Each Capability MUST have a `realizedBy`
   SubmodelElementList containing a RelationshipElement pointing to the corresponding Skill.

7. **Semantic IDs must use the smartproductionlab.aau.dk base**: The `SemanticId` Property inside
   each Skill SMC and each Capability SMC MUST be a URI starting with
   `https://smartproductionlab.aau.dk/` (or `http://smartproductionlab.aau.dk/`).

8. **SerialNumber and ManufacturerName are mandatory in DigitalNameplate**.

9. **YearOfConstruction format**: exactly 4 digits `YYYY` (e.g. `"2023"`).

10. **DateOfManufacture format**: `YYYY-MM-DD` (e.g. `"2023-01-15"`).

---

## Submodel Element Types Reference

| modelType | Required fields | Notes |
|---|---|---|
| `Property` | `idShort`, `valueType`, `value` | valueType: `xs:string`, `xs:anyURI`, `xs:boolean`, `xs:integer`, etc. |
| `MultiLanguageProperty` | `idShort`, `value` | `value` is array of `{language, text}` |
| `SubmodelElementCollection` | `idShort`, `value` | `value` is array of child elements |
| `SubmodelElementList` | `idShort`, `typeValueListElement`, `value` | ordered list of same-type elements |
| `Entity` | `idShort`, `entityType`, `statements` | `entityType`: `SelfManagedEntity` or `CoManagedEntity` |
| `RelationshipElement` | `idShort`, `first`, `second` | each is a ModelReference |
| `ReferenceElement` | `idShort`, `value` | value is a ModelReference |
| `Capability` | `idShort` | formal AAS Capability model type |
| `Operation` | `idShort` | may have `inputVariables`, `outputVariables`, `inoutputVariables` |
| `File` | `idShort`, `contentType`, `value` | value is a URI |

### Reference Types

**ExternalReference** (for semanticId, supplementalSemanticIds):
```json
{
  "type": "ExternalReference",
  "keys": [{ "type": "GlobalReference", "value": "<URI>" }]
}
```

**ModelReference** (for first/second in RelationshipElement, value in ReferenceElement):
```json
{
  "type": "ModelReference",
  "keys": [
    { "type": "Submodel", "value": "<submodel-id>" },
    { "type": "SubmodelElementCollection", "value": "<idShort>" }
  ]
}
```

---

## Additional Semantic IDs (AID / HS / WoT)

| Purpose | URI |
|---|---|
| AID Interface SMC | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface` |
| AID EndpointMetadata SMC | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata` |
| AID InteractionMetadata SMC | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata` |
| AID InterfaceReference property | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InterfaceReference` |
| HS ArcheType | `https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0` |
| HS EntryNode | `https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0` |
| HS Node | `https://admin-shell.io/idta/HierarchicalStructures/Node/1/0` |
| HS HasPart relationship | `https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0` |
| HS IsPartOf relationship | `https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0` |
| HS SameAs | `https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0` |
| Capability element | `https://admin-shell.io/idta/CapabilityDescription/Capability/1/0` |
| Capability realizedBy list | `https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0` |
| WoT Thing Description | `https://www.w3.org/2019/wot/td` |
| WoT PropertyAffordance | `https://www.w3.org/2019/wot/td#PropertyAffordance` |
| WoT ActionAffordance | `https://www.w3.org/2019/wot/td#ActionAffordance` |
| WoT InteractionAffordance | `https://www.w3.org/2019/wot/td#InteractionAffordance` |
| MQTT protocol binding | `https://www.w3.org/2019/wot/td/v1/binding/mqtt` |
| OPC UA protocol binding | `http://opcfoundation.org/UA/WoT-Binding/` |
| HTTP protocol binding | `https://www.w3.org/2019/wot/td/v1/binding/http` |
| WoT Thing Description base | `https://www.w3.org/2019/wot/td/v1` |

---

## Input Document Types — How to Read Each

The specification context may include several documents. Use each one as follows:

### Lifecycle / Datasheet PDF
General product documentation. Extract:
- **DigitalNameplate**: manufacturer name, product designation, serial number format, article number, year of construction, certifications
- **HierarchicalStructures**: parent line/system references (if mentioned)
- **OperationalData**: runtime variables, sensor values, cycle times mentioned in the operating section
- **General context** for Skills and Capabilities (state machine descriptions, operating modes)

### OPC UA NodeSet XML (`kind: opcua`)
Formal machine-readable OPC UA address space. This is the authoritative source for:
- **AID `InterfaceOPCUA`**: derive `namespace_uri` from the first `<Uri>` in `<NamespaceUris>` that is NOT the OPC UA base (`http://opcfoundation.org/UA/`). Use `namespace_index: "1"` for application nodes.
- **Skills**: each `<UAMethod>` with `ns=1` is a callable skill. Use the `BrowseName` as the skill name. Derive the `href` Forms field as `ns=1;i={NodeId}` or `ns=1;s={BrowseName}`.
- **OperationalData / AID properties**: each `<UAVariable>` with `ns=1` that represents a readable state or measurement maps to a property affordance in the AID and an entry in OperationalData.
- **`EndpointMetadata`**: set `base` to `opc.tcp://{hostname}:{port}` (default port 4840 if not specified), `protocol: "OPC UA"`, `encoding: "TCP Binary"`. Derive security mode and policy from the NodeSet `<SecurityMode>` elements or set to `None` / `Basic256Sha256` if not specified.
- **`InteractionMetadata` node IDs**: use `ns=1;i={numericId}` or `ns=1;s={stringId}` format.

### MQTT Interface Specification PDF (`kind: mqtt-spec`)
Documents the MQTT topic structure and command interface. Extract:
- **AID `InterfaceMQTT`**: broker `base` URL (use `mqtt://broker.example.com` as placeholder if not given), `contentType: "application/json"`
- **Skills / AID actions**: each command topic entry (e.g. START, STOP, HOME, RESET) maps to one Skill and one Action affordance. Use the command topic path as `href`.
- **AID properties**: each published data topic maps to a property affordance. Set `op: "observeproperty"` and populate `mqv_retain` and `mqv_qos` from the spec.
- **OperationalData**: published data values (cycle time, weight, state) map to OperationalData variables.

### BOM / Line Description PDF (`kind: bom`)
Bill of Materials or line structure document. Use for:
- **HierarchicalStructures**: the line, cell, or station hierarchy. The BOM's top-level system is the `EntryNode`; listed components become child `Node` entities linked with `HasPart` relationships.
- Each BOM component should reference its `globalAssetId` if available; use `[VERIFY: globalAssetId]` otherwise.
- Match component names/part numbers from the BOM to populate `idShort` and entity descriptions.

---

## Skill SemanticId URI Convention

Skill SemanticId values (the `Property` named `SemanticId` inside each Skill SMC, and the
`semanticId` on the Operation element) MUST start with `https://smartproductionlab.aau.dk/`.

Example: `https://smartproductionlab.aau.dk/skills/Dispense`

Capability SemanticId values follow the same pattern:
Example: `https://smartproductionlab.aau.dk/capabilities/Dispensing`


