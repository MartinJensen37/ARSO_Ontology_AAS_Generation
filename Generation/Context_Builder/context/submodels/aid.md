# Submodel Template: AID (Asset Interfaces Description)

- **idShort**: `AID`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/AID`
- **semanticId**: `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Describes the communication interfaces of the resource using the W3C Web of Things (WoT) Thing Description structure. Each interface (MQTT, OPC UA, HTTP, MODBUS) is a SubmodelElementCollection. Choose the interface type based on the equipment's communication protocol — see the preamble section "Input Document Types" for how to derive AID content from NodeSet XML, MQTT spec sheets, and other input documents.

## DEPENDENCY RULES (Critical)

- AID is required if Skills, OperationalData, or Parameters are present.
- AID must have at least one Interface (ResourceInterface) — SHACL violation if empty.
- Each interface must contain an `InteractionMetadata` SMC with at least one affordance (property, action, or event).
- Each Skill in the Skills submodel must be represented as an Action affordance in the AID.

## Interface Structure

Each Interface SMC:
- `idShort`: interface name — `InterfaceMQTT`, `InterfaceOPCUA`, or `InterfaceHTTP` depending on the equipment's protocol
- `semanticId`: `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface`
- `supplementalSemanticIds`: protocol-specific (see Protocol Supplemental Semantic IDs table below)
- `value`: array containing:
  1. `title` Property (optional)
  2. `EndpointMetadata` SMC — base URL and content type this url can also be hostnames like fillingmodule.local and so on.
  3. `InteractionMetadata` SMC — properties, actions, events

## InteractionMetadata Structure

```json
{
  "modelType": "SubmodelElementCollection",
  "idShort": "InteractionMetadata",
  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"}]},
  "supplementalSemanticIds": [{"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#InteractionAffordance"}]}],
  "value": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "properties",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#PropertyAffordance"}]},
      "value": [ ... property SMCs ... ]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "actions",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#ActionAffordance"}]},
      "value": [ ... action SMCs ... ]
    }
  ]
}
```

## Property Affordance SMC

```json
{
  "modelType": "SubmodelElementCollection",
  "idShort": "{propertyKey}",
  "value": [
    {"modelType": "Property", "idShort": "Key", "valueType": "xs:string", "value": "{propertyKey}"},
    {"modelType": "Property", "idShort": "Title", "valueType": "xs:string", "value": "Human-readable title"},
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "Forms",
      "value": [
        {"modelType": "Property", "idShort": "href", "valueType": "xs:string", "value": "device/topic/path"},
        {"modelType": "Property", "idShort": "op", "valueType": "xs:string", "value": "observeproperty"},
        {"modelType": "Property", "idShort": "mqv_retain", "valueType": "xs:string", "value": "false"}
      ]
    }
  ]
}
```

## Action Affordance SMC (one per Skill)

```json
{
  "modelType": "SubmodelElementCollection",
  "idShort": "{skillName}",
  "value": [
    {"modelType": "Property", "idShort": "Key", "valueType": "xs:string", "value": "{skillName}"},
    {"modelType": "Property", "idShort": "Title", "valueType": "xs:string", "value": "Human-readable title"},
    {"modelType": "Property", "idShort": "Synchronous", "valueType": "xs:boolean", "value": "true"},
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "Forms",
      "value": [
        {"modelType": "Property", "idShort": "href", "valueType": "xs:string", "value": "device/skills/skillname"},
        {"modelType": "Property", "idShort": "op", "valueType": "xs:string", "value": "invokeaction"},
        {"modelType": "Property", "idShort": "contentType", "valueType": "xs:string", "value": "application/json"}
      ]
    }
  ]
}
```

## Protocol Supplemental Semantic IDs

| Protocol | idShort for interface | supplementalSemanticIds values |
|---|---|---|
| MQTT | `InterfaceMQTT` | `["https://www.w3.org/2019/wot/td/v1/binding/mqtt", "https://www.w3.org/2019/wot/td/v1"]` |
| HTTP | `InterfaceHTTP` | `["https://www.w3.org/2019/wot/td/v1/binding/http", "https://www.w3.org/2019/wot/td/v1"]` |
| OPC UA | `InterfaceOPCUA` | `["http://opcfoundation.org/UA/WoT-Binding/", "https://www.w3.org/2019/wot/td/v1"]` |
| MODBUS | `InterfaceMODBUS` | `["https://www.w3.org/2019/wot/td/v1/binding/modbus", "https://www.w3.org/2019/wot/td/v1"]` |

## MQTT-Specific Forms Fields

| idShort | valueType | Description |
|---|---|---|
| `href` | `xs:string` | MQTT topic (e.g. `"device/sensors/temperature"`) |
| `op` | `xs:string` | `"observeproperty"` for subscribe, `"invokeaction"` for publish |
| `mqv_retain` | `xs:string` | `"true"` or `"false"` |
| `mqv_controlPacket` | `xs:string` | MQTT packet type |
| `mqv_qos` | `xs:string` | `"0"`, `"1"`, or `"2"` |

## OPC UA EndpointMetadata Fields

For OPC UA interfaces use `InterfaceOPCUA` as the SMC idShort. The `EndpointMetadata` SMC contains transport-layer binding properties (not MQTT-style `base`/`contentType`):

| idShort | valueType | Description |
|---|---|---|
| `protocol` | `xs:string` | Transport protocol, e.g. `"OPC UA"` |
| `encoding` | `xs:string` | Encoding, typically `"TCP Binary"` |
| `base` | `xs:anyURI` | OPC UA endpoint URL, e.g. `"opc.tcp://hostname:4840"` |
| `port` | `xs:string` | Port number, typically `"4840"` |
| `security_mode` | `xs:string` | Security mode: `"None"`, `"Sign"`, or `"SignAndEncrypt"` |
| `security_policy` | `xs:string` | Security policy URI, e.g. `"Basic256Sha256"` |
| `namespace_uri` | `xs:string` | OPC UA application namespace URI from the NodeSet |
| `namespace_index` | `xs:string` | Namespace index for application nodes, typically `"1"` |

## OPC UA Action Forms Fields

For OPC UA actions (Skills), the Forms SMC uses node identifiers:

| idShort | valueType | Description |
|---|---|---|
| `href` | `xs:string` | OPC UA method node ID, e.g. `"ns=1;s=PlungerSet80/Methods/Start"` |
| `op` | `xs:string` | `"invokeaction"` |
| `opc_node_id` | `xs:string` | Full node ID string |
| `opc_namespace` | `xs:string` | Namespace index |

## OPC UA Property Forms Fields

For OPC UA properties (OperationalData), the Forms SMC uses:

| idShort | valueType | Description |
|---|---|---|
| `href` | `xs:string` | OPC UA variable node ID, e.g. `"ns=1;s=PlungerSet80/Variables/State"` |
| `op` | `xs:string` | `"readproperty"` or `"observeproperty"` |
| `opc_node_id` | `xs:string` | Full node ID string |

## JSON Template (MQTT interface)

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/AID",
  "idShort": "AID",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "InterfaceMQTT",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"}]
      },
      "supplementalSemanticIds": [
        {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td/v1/binding/mqtt"}]},
        {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td/v1"}]}
      ],
      "value": [
        {"modelType": "Property", "idShort": "title", "valueType": "xs:string", "value": "MQTT Interface"},
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "EndpointMetadata",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"}]},
          "value": [
            {"modelType": "Property", "idShort": "base", "valueType": "xs:anyURI", "value": "mqtt://broker.example.com"},
            {"modelType": "Property", "idShort": "contentType", "valueType": "xs:string", "value": "application/json"}
          ]
        },
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "InteractionMetadata",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"}]},
          "supplementalSemanticIds": [{"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#InteractionAffordance"}]}],
          "value": [
            {
              "modelType": "SubmodelElementCollection",
              "idShort": "properties",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#PropertyAffordance"}]},
              "value": []
            },
            {
              "modelType": "SubmodelElementCollection",
              "idShort": "actions",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#ActionAffordance"}]},
              "value": []
            }
          ]
        }
      ]
    }
  ]
}
```

## JSON Template (OPC UA interface)

```json
{
  "modelType": "SubmodelElementCollection",
  "idShort": "InterfaceOPCUA",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"}]
  },
  "supplementalSemanticIds": [
    {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "http://opcfoundation.org/UA/WoT-Binding/"}]},
    {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td/v1"}]}
  ],
  "value": [
    {"modelType": "Property", "idShort": "title", "valueType": "xs:string", "value": "OPC UA Interface"},
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "EndpointMetadata",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"}]},
      "value": [
        {"modelType": "Property", "idShort": "protocol", "valueType": "xs:string", "value": "OPC UA"},
        {"modelType": "Property", "idShort": "encoding", "valueType": "xs:string", "value": "TCP Binary"},
        {"modelType": "Property", "idShort": "base", "valueType": "xs:anyURI", "value": "opc.tcp://{hostname}:4840"},
        {"modelType": "Property", "idShort": "port", "valueType": "xs:string", "value": "4840"},
        {"modelType": "Property", "idShort": "security_mode", "valueType": "xs:string", "value": "SignAndEncrypt"},
        {"modelType": "Property", "idShort": "security_policy", "valueType": "xs:string", "value": "Basic256Sha256"},
        {"modelType": "Property", "idShort": "namespace_uri", "valueType": "xs:string", "value": "http://example.com/UA/{AssetName}/"},
        {"modelType": "Property", "idShort": "namespace_index", "valueType": "xs:string", "value": "1"}
      ]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "InteractionMetadata",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"}]},
      "supplementalSemanticIds": [{"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#InteractionAffordance"}]}],
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "properties",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#PropertyAffordance"}]},
          "value": []
        },
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "actions",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td#ActionAffordance"}]},
          "value": []
        }
      ]
    }
  ]
}
```

## Notes

- Choose the interface type based on the equipment's communication protocol:
  - MQTT → `InterfaceMQTT` with MQTT broker URL as `base` (e.g. `mqtt://broker.example.com`)
  - OPC UA → `InterfaceOPCUA` with OPC UA endpoint URL (e.g. `opc.tcp://hostname:4840`) and full `EndpointMetadata` fields including `namespace_uri` and `security_mode` from the NodeSet
  - HTTP/REST → `InterfaceHTTP`
- The `EndpointMetadata` SMC **must** be present and carry the semanticId `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata` — it is required by SHACL validation.
- Add one Action entry per Skill defined in the Skills submodel.
- Add Property entries for each runtime variable (from OperationalData) if interface details are available.
- For OPC UA, derive the `namespace_uri` from the `<NamespaceUri>` element in the NodeSet XML; derive node IDs from `<UAMethod>` and `<UAVariable>` elements.
