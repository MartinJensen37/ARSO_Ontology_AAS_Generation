# Submodel Template: AIMC (Asset Interfaces Mapping Configuration, IDTA 02027)

- **idShort**: `AssetInterfacesMappingConfiguration`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration`
- **semanticId**: `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "2", "revision": "0"}`

## Purpose

Wires AID interface affordances to the submodel elements that consume them: each
mapping declares one or more **sources** (AID properties being read) and one or
more **sinks** (the elements receiving the value), optionally with a polling
interval and a payload transformation.

AIMC is meaningless without AID. Emit it only when an AID submodel exists and you
can point at concrete affordances inside it.

## DEPENDENCY RULES (Critical)

- Every `Source` ReferenceElement must resolve to a real AID property under
  `AID/{interface}/InteractionMetadata/properties/{key}`.
- Every `Sink` ReferenceElement must resolve to a real element in this AAS —
  typically an OperationalData or Parameters entry.
- `MappingConfigurations` is mandatory and appears exactly once.
- Each `MappingConfiguration` must carry both a `Sources` and a `Sinks` list.

## Structure

```
AssetInterfacesMappingConfiguration (Submodel)
  └─ MappingConfigurations [SML, 1]
       └─ MappingConfiguration [SMC, 0..*]
            ├─ InterfaceReference [ReferenceElement, 1]
            ├─ DefaultPollingInterval [Property/xs:double, 0..1]
            ├─ Transformation [Blob, 0..1]
            ├─ Sources [SML, 1]
            │    └─ Source [SMC, 1..*]
            │         ├─ Source [ReferenceElement, 1]
            │         ├─ SourceId [Property/xs:string, 1]
            │         └─ PollingInterval [Property/xs:double, 0..1]
            └─ Sinks [SML, 1]
                 └─ Sink [SMC, 1..*]
                      ├─ Sink [ReferenceElement, 1]
                      └─ SinkId [Property/xs:string, 1]
```

`MappingConfigurations` is a **SubmodelElementList**, not a collection. Its
children are positional, so their `idShort` is omitted inside the list.

## semanticIds

| Element | semanticId |
|---|---|
| Submodel | `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel` |
| `MappingConfigurations` | `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations` |
| `MappingConfiguration` | `.../2/0/MappingConfiguration` |
| `DefaultPollingInterval` | `.../2/0/MappingConfiguration/DefaultPollingInterval` |
| `Transformation` | `.../2/0/MappingConfiguration/Transformation` |
| `Sources` | `.../2/0/MappingConfiguration/Sources` |
| `Source` (SMC) | `.../2/0/MappingConfiguration/Source` |
| `Source` (ReferenceElement) | `.../2/0/MappingConfiguration/Source/Source` |
| `SourceId` | `.../2/0/MappingConfiguration/Source/SourceId` |
| `PollingInterval` | `.../2/0/MappingConfiguration/Source/PollingInterval` |
| `Sinks` | `.../2/0/MappingConfiguration/Sinks` |
| `Sink` (SMC) | `.../2/0/MappingConfiguration/Sink` |
| `Sink` (ReferenceElement) | `.../2/0/MappingConfiguration/Sink/Sink` |
| `SinkId` | `.../2/0/MappingConfiguration/Sink/SinkId` |

`MappingConfigurations` keeps the `1/0` namespace in IDTA 02027 while everything
below it moved to `2/0`. That is not a typo — copy it as shown.

## Reference shape

Both `Source` and `Sink` are ModelReferences into this AAS, so the first key is
the submodel and the rest are fragment keys:

```json
{
  "modelType": "ReferenceElement",
  "idShort": "Source",
  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/Source"}]},
  "value": {
    "type": "ModelReference",
    "keys": [
      {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
      {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
      {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
      {"type": "SubmodelElementCollection", "value": "properties"},
      {"type": "SubmodelElementCollection", "value": "stationState"}
    ]
  }
}
```

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration",
  "idShort": "AssetInterfacesMappingConfiguration",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"}]
  },
  "administration": {"version": "2", "revision": "0"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementList",
      "idShort": "MappingConfigurations",
      "typeValueListElement": "SubmodelElementCollection",
      "orderRelevant": false,
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations"}]},
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"}]},
          "value": [
            {
              "modelType": "ReferenceElement",
              "idShort": "InterfaceReference",
              "value": {
                "type": "ModelReference",
                "keys": [
                  {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
                  {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"}
                ]
              }
            },
            {
              "modelType": "Property",
              "idShort": "DefaultPollingInterval",
              "valueType": "xs:double",
              "value": "1000",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/DefaultPollingInterval"}]}
            },
            {
              "modelType": "SubmodelElementList",
              "idShort": "Sources",
              "typeValueListElement": "SubmodelElementCollection",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sources"}]},
              "value": [
                {
                  "modelType": "SubmodelElementCollection",
                  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source"}]},
                  "value": [
                    {
                      "modelType": "ReferenceElement",
                      "idShort": "Source",
                      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/Source"}]},
                      "value": {
                        "type": "ModelReference",
                        "keys": [
                          {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
                          {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
                          {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
                          {"type": "SubmodelElementCollection", "value": "properties"},
                          {"type": "SubmodelElementCollection", "value": "<aid property key>"}
                        ]
                      }
                    },
                    {
                      "modelType": "Property",
                      "idShort": "SourceId",
                      "valueType": "xs:string",
                      "value": "<aid property key>",
                      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/SourceId"}]}
                    }
                  ]
                }
              ]
            },
            {
              "modelType": "SubmodelElementList",
              "idShort": "Sinks",
              "typeValueListElement": "SubmodelElementCollection",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sinks"}]},
              "value": [
                {
                  "modelType": "SubmodelElementCollection",
                  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink"}]},
                  "value": [
                    {
                      "modelType": "ReferenceElement",
                      "idShort": "Sink",
                      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/Sink"}]},
                      "value": {
                        "type": "ModelReference",
                        "keys": [
                          {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/OperationalData"},
                          {"type": "SubmodelElementCollection", "value": "<variable name>"}
                        ]
                      }
                    },
                    {
                      "modelType": "Property",
                      "idShort": "SinkId",
                      "valueType": "xs:string",
                      "value": "<variable name>",
                      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/SinkId"}]}
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Notes

- One `MappingConfiguration` per AID interface. Do not mix affordances from two
  interfaces into one configuration.
- `SourceId` / `SinkId` are the handles a `Transformation` uses to address each
  end. Keep them equal to the affordance key and the sink's idShort unless the
  datasheet gives explicit mapping names.
- Polling intervals are milliseconds. Set `DefaultPollingInterval` once per
  configuration and override per source only where the datasheet differs.
- Omit `Transformation` entirely unless the datasheet describes an actual payload
  conversion — an empty Blob is worse than no Blob.
