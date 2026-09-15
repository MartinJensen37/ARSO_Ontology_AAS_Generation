# Submodel Template: Parameters

- **idShort**: `Parameters`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Parameters`
- **semanticId**: `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Purpose

Values an operator writes to the resource — setpoints, thresholds, recipe values. Each parameter
binds to the AID property it is written through.

## Dependency Rules

- Parameters requires AID.
- Every parameter's `InterfaceReference` must name an AID **property** — never an action or event.
- A parameter's semanticId, when set, must start with `https://smartproductionlab.aau.dk/`.

## Structure

```
Parameters (Submodel)
  └─ {ParameterName} [SMC]                      semanticId: https://smartproductionlab.aau.dk/parameters/{ParameterName}
       ├─ InterfaceReference [ReferenceElement] -> AID/{Interface}/InteractionMetadata/properties/{Property}
       └─ one Property per field of that property's input schema, when it has one
```

## JSON Template

```json
{
  "idShort": "Parameters",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Parameters",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "FillVolume",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://smartproductionlab.aau.dk/parameters/FillVolume"
          }
        ]
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
              {"type": "SubmodelElementCollection", "value": "FillVolume"}
            ]
          }
        }
      ]
    }
  ]
}
```

## Notes

- Take parameters from the configuration or command section, in PascalCase (`FillVolume`, `MaxSpeed`).
- Fixed ratings such as rated voltage or an operating temperature range belong in TechnicalData.
