# Submodel Template: AID (Asset Interfaces Description, IDTA 02017)

- **idShort**: `AID`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/AID`
- **semanticId**: `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel` (ExternalReference; the ontology also accepts IDTA 02017-1-1's `.../1/1/Submodel`)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Purpose

The resource's communication interfaces, as W3C Web of Things (WoT) Thing Descriptions: one
SubmodelElementCollection per interface (MQTT, OPC UA, HTTP, Modbus). The preamble's "Input
Document Types" explains how to derive it from NodeSet XML and MQTT specifications.

## Dependency Rules (Critical)

- AID is required whenever Skills, OperationalData, Parameters or AIMC is present.
- AID contains at least one interface.
- Every Skill's `InterfaceReference` names an action under `InteractionMetadata/actions`.
- OperationalData, Parameters and AIMC sources name a property under
  `InteractionMetadata/properties` — never an action or event.
- Every `Forms` collection carries an address: `href` (MQTT/HTTP/Modbus) or `opc_node_id` (OPC UA).

## Interface Structure

```
Interface{Protocol} [SMC]
  ├─ title [Property]
  ├─ EndpointMetadata [SMC]
  │    ├─ protocol-specific endpoint fields (table below)
  │    ├─ securityDefinitions [SMC] └─ nosec_sc [SMC] └─ scheme = "nosec"
  │    └─ security [SML] └─ "nosec_sc"
  └─ InteractionMetadata [SMC]
       ├─ actions [SMC]    └─ {Action} [SMC]:   Key, Title, Synchronous, Forms
       ├─ properties [SMC] └─ {Property} [SMC]: Key, Title, Forms
       └─ events [SMC]     └─ {Event} [SMC]:    Key, Title, Forms
```

| Element | semanticId | supplementalSemanticIds |
|---|---|---|
| Interface | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface` | protocol binding, `https://www.w3.org/2019/wot/td` |
| `EndpointMetadata` | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata` | — |
| `InteractionMetadata` | `https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata` | `https://www.w3.org/2019/wot/td#InteractionAffordance` |
| `properties` | `https://www.w3.org/2019/wot/td#PropertyAffordance` | — |
| `actions` | `https://www.w3.org/2019/wot/td#ActionAffordance` | — |
| `events` | `https://www.w3.org/2019/wot/td#EventAffordance` | — |

| Protocol | Interface idShort | Binding supplementalSemanticId |
|---|---|---|
| MQTT | `InterfaceMQTT` | `https://www.w3.org/2019/wot/td/v1/binding/mqtt` |
| OPC UA | `InterfaceOPCUA` | `http://opcfoundation.org/UA/WoT-Binding/` |
| HTTP | `InterfaceHTTP` | `https://www.w3.org/2019/wot/td/v1/binding/http` |
| Modbus | `InterfaceMODBUS` | `https://www.w3.org/2019/wot/td/v1/binding/modbus` |

`securityDefinitions` and `security` are always emitted with the `nosec` scheme; IDTA requires both.

## Endpoint and Forms fields per protocol

| Protocol | EndpointMetadata | Forms |
|---|---|---|
| MQTT | `base` (e.g. `mqtt://broker:1883`), `contentType` | `href` (topic), `contentType`, optional `response` SMC with the reply topic's `href` and `contentType` |
| HTTP | `base`, `contentType` | `href` (path), `contentType`, `htv_methodName` |
| Modbus | `base`, `contentType`, optional `modv_mostSignificantByte` / `modv_mostSignificantWord` | `href` (register address), `modv_function`, `modv_entity` |
| OPC UA | `protocol`, `encoding`, `base` (`opc.tcp://{hostname}:4840`), `port`, `security_mode`, `security_policy`, `namespace_uri`, `namespace_index` | `opc_node_id` (e.g. `ns=1;i=4010`), `opc_namespace` |

Forms fields are passed through as given, so only include those the source material states.
Actions also carry `Synchronous` (`"true"` / `"false"`). All values are `xs:string`.

## JSON Template (MQTT)

```json
{
  "idShort": "AID",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/AID",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "InterfaceMQTT",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
          }
        ]
      },
      "supplementalSemanticIds": [
        {
          "type": "ExternalReference",
          "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td/v1/binding/mqtt"}]
        },
        {
          "type": "ExternalReference",
          "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td"}]
        }
      ],
      "value": [
        {
          "idShort": "title",
          "modelType": "Property",
          "value": "EX-100 MQTT Interface",
          "valueType": "xs:string"
        },
        {
          "idShort": "EndpointMetadata",
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
              }
            ]
          },
          "value": [
            {
              "idShort": "base",
              "modelType": "Property",
              "value": "mqtt://broker:1883",
              "valueType": "xs:string"
            },
            {
              "idShort": "contentType",
              "modelType": "Property",
              "value": "application/json",
              "valueType": "xs:string"
            },
            {
              "idShort": "securityDefinitions",
              "modelType": "SubmodelElementCollection",
              "value": [
                {
                  "idShort": "nosec_sc",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "scheme",
                      "modelType": "Property",
                      "value": "nosec",
                      "valueType": "xs:string"
                    }
                  ]
                }
              ]
            },
            {
              "idShort": "security",
              "modelType": "SubmodelElementList",
              "orderRelevant": true,
              "typeValueListElement": "Property",
              "valueTypeListElement": "xs:string",
              "value": [{"modelType": "Property", "value": "nosec_sc", "valueType": "xs:string"}]
            }
          ]
        },
        {
          "idShort": "InteractionMetadata",
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
              }
            ]
          },
          "supplementalSemanticIds": [
            {
              "type": "ExternalReference",
              "keys": [
                {
                  "type": "GlobalReference",
                  "value": "https://www.w3.org/2019/wot/td#InteractionAffordance"
                }
              ]
            }
          ],
          "value": [
            {
              "idShort": "actions",
              "modelType": "SubmodelElementCollection",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://www.w3.org/2019/wot/td#ActionAffordance"
                  }
                ]
              },
              "value": [
                {
                  "idShort": "Start",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "Key",
                      "modelType": "Property",
                      "value": "start",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Title",
                      "modelType": "Property",
                      "value": "Start fill cycle",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Synchronous",
                      "modelType": "Property",
                      "value": "true",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Forms",
                      "modelType": "SubmodelElementCollection",
                      "value": [
                        {
                          "idShort": "href",
                          "modelType": "Property",
                          "value": "CMD/Start",
                          "valueType": "xs:string"
                        },
                        {
                          "idShort": "contentType",
                          "modelType": "Property",
                          "value": "application/json",
                          "valueType": "xs:string"
                        },
                        {
                          "idShort": "response",
                          "modelType": "SubmodelElementCollection",
                          "value": [
                            {
                              "idShort": "href",
                              "modelType": "Property",
                              "value": "DATA/Start",
                              "valueType": "xs:string"
                            },
                            {
                              "idShort": "contentType",
                              "modelType": "Property",
                              "value": "application/json",
                              "valueType": "xs:string"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ]
            },
            {
              "idShort": "properties",
              "modelType": "SubmodelElementCollection",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://www.w3.org/2019/wot/td#PropertyAffordance"
                  }
                ]
              },
              "value": [
                {
                  "idShort": "State",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "Key",
                      "modelType": "Property",
                      "value": "state",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Title",
                      "modelType": "Property",
                      "value": "Operational state",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Forms",
                      "modelType": "SubmodelElementCollection",
                      "value": [
                        {
                          "idShort": "href",
                          "modelType": "Property",
                          "value": "DATA/State",
                          "valueType": "xs:string"
                        },
                        {
                          "idShort": "contentType",
                          "modelType": "Property",
                          "value": "application/json",
                          "valueType": "xs:string"
                        }
                      ]
                    }
                  ]
                },
                {
                  "idShort": "FillVolume",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "Key",
                      "modelType": "Property",
                      "value": "fillVolume",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Title",
                      "modelType": "Property",
                      "value": "Target fill volume",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "Forms",
                      "modelType": "SubmodelElementCollection",
                      "value": [
                        {
                          "idShort": "href",
                          "modelType": "Property",
                          "value": "CMD/FillVolume",
                          "valueType": "xs:string"
                        },
                        {
                          "idShort": "contentType",
                          "modelType": "Property",
                          "value": "application/json",
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
  ]
}
```

## JSON Template (OPC UA interface)

```json
{
  "idShort": "InterfaceOPCUA",
  "modelType": "SubmodelElementCollection",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
      }
    ]
  },
  "supplementalSemanticIds": [
    {
      "type": "ExternalReference",
      "keys": [{"type": "GlobalReference", "value": "http://opcfoundation.org/UA/WoT-Binding/"}]
    },
    {
      "type": "ExternalReference",
      "keys": [{"type": "GlobalReference", "value": "https://www.w3.org/2019/wot/td"}]
    }
  ],
  "value": [
    {
      "idShort": "title",
      "modelType": "Property",
      "value": "PlungerSet-80 OPC UA Interface",
      "valueType": "xs:string"
    },
    {
      "idShort": "EndpointMetadata",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
          }
        ]
      },
      "value": [
        {
          "idShort": "protocol",
          "modelType": "Property",
          "value": "OPC UA",
          "valueType": "xs:string"
        },
        {
          "idShort": "encoding",
          "modelType": "Property",
          "value": "TCP Binary",
          "valueType": "xs:string"
        },
        {
          "idShort": "base",
          "modelType": "Property",
          "value": "opc.tcp://{hostname}:4840",
          "valueType": "xs:string"
        },
        {"idShort": "port", "modelType": "Property", "value": "4840", "valueType": "xs:string"},
        {
          "idShort": "security_mode",
          "modelType": "Property",
          "value": "SignAndEncrypt",
          "valueType": "xs:string"
        },
        {
          "idShort": "security_policy",
          "modelType": "Property",
          "value": "Basic256Sha256",
          "valueType": "xs:string"
        },
        {
          "idShort": "namespace_uri",
          "modelType": "Property",
          "value": "http://elara-automation.de/UA/PlungerSet80/",
          "valueType": "xs:string"
        },
        {
          "idShort": "namespace_index",
          "modelType": "Property",
          "value": "1",
          "valueType": "xs:string"
        },
        {
          "idShort": "securityDefinitions",
          "modelType": "SubmodelElementCollection",
          "value": [
            {
              "idShort": "nosec_sc",
              "modelType": "SubmodelElementCollection",
              "value": [
                {
                  "idShort": "scheme",
                  "modelType": "Property",
                  "value": "nosec",
                  "valueType": "xs:string"
                }
              ]
            }
          ]
        },
        {
          "idShort": "security",
          "modelType": "SubmodelElementList",
          "orderRelevant": true,
          "typeValueListElement": "Property",
          "valueTypeListElement": "xs:string",
          "value": [{"modelType": "Property", "value": "nosec_sc", "valueType": "xs:string"}]
        }
      ]
    },
    {
      "idShort": "InteractionMetadata",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
          }
        ]
      },
      "supplementalSemanticIds": [
        {
          "type": "ExternalReference",
          "keys": [
            {
              "type": "GlobalReference",
              "value": "https://www.w3.org/2019/wot/td#InteractionAffordance"
            }
          ]
        }
      ],
      "value": [
        {
          "idShort": "actions",
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://www.w3.org/2019/wot/td#ActionAffordance"
              }
            ]
          },
          "value": [
            {
              "idShort": "Start",
              "modelType": "SubmodelElementCollection",
              "value": [
                {
                  "idShort": "Key",
                  "modelType": "Property",
                  "value": "start",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "Title",
                  "modelType": "Property",
                  "value": "Start stoppering cycle",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "Synchronous",
                  "modelType": "Property",
                  "value": "true",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "Forms",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "opc_node_id",
                      "modelType": "Property",
                      "value": "ns=1;i=4010",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "opc_namespace",
                      "modelType": "Property",
                      "value": "1",
                      "valueType": "xs:string"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "idShort": "properties",
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://www.w3.org/2019/wot/td#PropertyAffordance"
              }
            ]
          },
          "value": [
            {
              "idShort": "State",
              "modelType": "SubmodelElementCollection",
              "value": [
                {
                  "idShort": "Key",
                  "modelType": "Property",
                  "value": "state",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "Title",
                  "modelType": "Property",
                  "value": "Operational state (IDLE/RUNNING/ERROR/HOMING)",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "Forms",
                  "modelType": "SubmodelElementCollection",
                  "value": [
                    {
                      "idShort": "opc_node_id",
                      "modelType": "Property",
                      "value": "ns=1;i=3010",
                      "valueType": "xs:string"
                    },
                    {
                      "idShort": "opc_namespace",
                      "modelType": "Property",
                      "value": "1",
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

- Pick the interface by the equipment's protocol; an asset may expose several.
- Add one action per Skill, and one property per value that OperationalData, Parameters or AIMC reads.
- For OPC UA, take `namespace_uri` from the NodeSet's `<NamespaceUris>` and node ids from
  `<UAMethod>` / `<UAVariable>`.
- The OPC UA endpoint fields and `opc_*` form fields are this pipeline's convention, not IDTA
  02017's `uav_*` terms.
