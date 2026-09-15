# Submodel Template: OperationalData

- **idShort**: `OperationalData` — not `Variables` (the profile and UI key is `Variables`)
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/OperationalData`
- **semanticId**: `https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Purpose

Runtime values the resource reports while running — states, sensor readings, cycle times. Each
variable binds to the AID property it is read from.

## Dependency Rules

- OperationalData requires AID.
- Every variable's `InterfaceReference` must name an AID **property** — never an action or
  event, even for a one-shot value such as a cycle-completion reading.
- A variable's semanticId, when set, must start with `https://smartproductionlab.aau.dk/`.

## Structure

```
OperationalData (Submodel)
  └─ {VariableName} [SMC]                       semanticId: https://smartproductionlab.aau.dk/variables/{VariableName}
       ├─ InterfaceReference [ReferenceElement] -> AID/{Interface}/InteractionMetadata/properties/{Property}
       └─ one Property per field of that property's output schema, when it has one
```

`InterfaceReference` carries semanticId
`https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InterfaceReference`.

## JSON Template

```json
{
  "idShort": "OperationalData",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/OperationalData",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "State",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/variables/State"}]
      },
      "value": [
        {
          "idShort": "InterfaceReference",
          "modelType": "ReferenceElement",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InterfaceReference"
              }
            ]
          },
          "value": {
            "type": "ModelReference",
            "keys": [
              {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
              {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
              {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
              {"type": "SubmodelElementCollection", "value": "properties"},
              {"type": "SubmodelElementCollection", "value": "State"}
            ]
          }
        }
      ]
    }
  ]
}
```

## Notes

- Take variable names from the telemetry, measurement or status section, in PascalCase
  (`State`, `Weight`, `CycleTime`).
- Operator setpoints belong in Parameters and fixed datasheet ratings in TechnicalData.
