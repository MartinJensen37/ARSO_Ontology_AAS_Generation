# Submodel Template: AIMC (Asset Interfaces Mapping Configuration, IDTA 02027)

- **idShort**: `AssetInterfacesMappingConfiguration`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration`
- **semanticId**: `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "2", "revision": "0"}`

## Purpose

Wires AID properties to the submodel elements that consume them. Each mapping configuration
covers one AID interface and pairs **sources** (AID properties being read) with **sinks** (the
elements receiving the values), optionally with polling intervals.

## Dependency Rules (Critical)

- AIMC requires AID.
- Each configuration's `InterfaceReference` must name an AID interface.
- Each `Source` must name an AID **property** under `InteractionMetadata/properties` — never an
  action or event.
- A `Sink` may target any element in this AAS, typically an OperationalData or Parameters entry.

## Structure

```
AssetInterfacesMappingConfiguration (Submodel)
  └─ MappingConfigurations [SML, 1]
       └─ (no idShort) [SMC]                  one per AID interface
            ├─ InterfaceReference [ReferenceElement]   -> [AID submodel, {Interface}]
            ├─ DefaultPollingInterval [Property, xs:double, 0..1]   ms
            ├─ Sources [SML]
            │    └─ (no idShort) [SMC]
            │         ├─ Source [ReferenceElement]       -> AID/{Interface}/InteractionMetadata/properties/{Property}
            │         ├─ SourceId [Property, xs:string]
            │         └─ PollingInterval [Property, xs:double, 0..1]
            └─ Sinks [SML]
                 └─ (no idShort) [SMC]
                      ├─ Sink [ReferenceElement]         -> [{Sink submodel}, {Entry}]
                      └─ SinkId [Property, xs:string]
```

List children carry no idShort (AASd-120). Every semanticId sits under
`https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/`, except
`MappingConfigurations`, which keeps IDTA 02027's `.../1/0/MappingConfigurations`.

## JSON Template

```json
{
  "idShort": "AssetInterfacesMappingConfiguration",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration",
  "administration": {"version": "2", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "MappingConfigurations",
      "modelType": "SubmodelElementList",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations"
          }
        ]
      },
      "orderRelevant": false,
      "typeValueListElement": "SubmodelElementCollection",
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"
              }
            ]
          },
          "value": [
            {
              "idShort": "InterfaceReference",
              "modelType": "ReferenceElement",
              "value": {
                "type": "ModelReference",
                "keys": [
                  {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
                  {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"}
                ]
              }
            },
            {
              "idShort": "DefaultPollingInterval",
              "modelType": "Property",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/DefaultPollingInterval"
                  }
                ]
              },
              "value": "1000.0",
              "valueType": "xs:double"
            },
            {
              "idShort": "Sources",
              "modelType": "SubmodelElementList",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sources"
                  }
                ]
              },
              "orderRelevant": true,
              "typeValueListElement": "SubmodelElementCollection",
              "value": [
                {
                  "modelType": "SubmodelElementCollection",
                  "semanticId": {
                    "type": "ExternalReference",
                    "keys": [
                      {
                        "type": "GlobalReference",
                        "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source"
                      }
                    ]
                  },
                  "value": [
                    {
                      "idShort": "Source",
                      "modelType": "ReferenceElement",
                      "semanticId": {
                        "type": "ExternalReference",
                        "keys": [
                          {
                            "type": "GlobalReference",
                            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/Source"
                          }
                        ]
                      },
                      "value": {
                        "type": "ModelReference",
                        "keys": [
                          {
                            "type": "Submodel",
                            "value": "{base_url}/submodels/instances/{systemId}/AID"
                          },
                          {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
                          {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
                          {"type": "SubmodelElementCollection", "value": "properties"},
                          {"type": "SubmodelElementCollection", "value": "State"}
                        ]
                      }
                    },
                    {
                      "idShort": "SourceId",
                      "modelType": "Property",
                      "semanticId": {
                        "type": "ExternalReference",
                        "keys": [
                          {
                            "type": "GlobalReference",
                            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/SourceId"
                          }
                        ]
                      },
                      "value": "State",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "PollingInterval",
                      "modelType": "Property",
                      "semanticId": {
                        "type": "ExternalReference",
                        "keys": [
                          {
                            "type": "GlobalReference",
                            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/PollingInterval"
                          }
                        ]
                      },
                      "value": "500.0",
                      "valueType": "xs:double"
                    }
                  ]
                }
              ]
            },
            {
              "idShort": "Sinks",
              "modelType": "SubmodelElementList",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sinks"
                  }
                ]
              },
              "orderRelevant": true,
              "typeValueListElement": "SubmodelElementCollection",
              "value": [
                {
                  "modelType": "SubmodelElementCollection",
                  "semanticId": {
                    "type": "ExternalReference",
                    "keys": [
                      {
                        "type": "GlobalReference",
                        "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink"
                      }
                    ]
                  },
                  "value": [
                    {
                      "idShort": "Sink",
                      "modelType": "ReferenceElement",
                      "semanticId": {
                        "type": "ExternalReference",
                        "keys": [
                          {
                            "type": "GlobalReference",
                            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/Sink"
                          }
                        ]
                      },
                      "value": {
                        "type": "ModelReference",
                        "keys": [
                          {
                            "type": "Submodel",
                            "value": "{base_url}/submodels/instances/{systemId}/OperationalData"
                          },
                          {"type": "SubmodelElementCollection", "value": "State"}
                        ]
                      }
                    },
                    {
                      "idShort": "SinkId",
                      "modelType": "Property",
                      "semanticId": {
                        "type": "ExternalReference",
                        "keys": [
                          {
                            "type": "GlobalReference",
                            "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/SinkId"
                          }
                        ]
                      },
                      "value": "State",
                      "valueType": "xs:string"
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

- Use one configuration per AID interface; never mix affordances from two interfaces.
- `SourceId` / `SinkId` equal the AID property key and the sink's idShort unless the source
  material names the mapping explicitly.
- Polling intervals are milliseconds. Set `DefaultPollingInterval` once and override per source
  only where the source material differs.
- Omit the whole submodel if the source material describes no data mapping.
