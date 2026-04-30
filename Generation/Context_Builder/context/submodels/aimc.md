# Submodel Template: AIMC (Asset Interfaces Mapping Configuration)

- **idShort**: `AssetInterfacesMappingConfiguration`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration`
- **semanticId**: `https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Maps the AID interface affordances (properties/actions/events) to the corresponding submodel
elements in Variables, Skills, and Parameters. This creates the semantic bridge between the
communication interface and the operational data.

## Structure

The AIMC submodel contains `MappingConfigurations` as the top-level element — a
SubmodelElementCollection where each child maps one interface.

Each mapping configuration:
- `idShort`: interface name (matching the AID interface idShort)
- Contains a `MappingSourceSinkRelation` SubmodelElementList

Each `MappingSourceSinkRelation` entry is a `RelationshipElement`:
- `first`: points to the AID affordance (source interface)
- `second`: points to the submodel element it maps to (sink: Variables, Skills, or Parameters)

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/AssetInterfacesMappingConfiguration",
  "idShort": "AssetInterfacesMappingConfiguration",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "MappingConfigurations",
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "InterfaceMQTT",
          "value": [
            {
              "modelType": "SubmodelElementList",
              "idShort": "MappingSourceSinkRelations",
              "typeValueListElement": "RelationshipElement",
              "value": [
                {
                  "modelType": "RelationshipElement",
                  "idShort": "Temperature_to_OperationalData",
                  "first": {
                    "type": "ModelReference",
                    "keys": [
                      {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
                      {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
                      {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
                      {"type": "SubmodelElementCollection", "value": "properties"},
                      {"type": "SubmodelElementCollection", "value": "Temperature"}
                    ]
                  },
                  "second": {
                    "type": "ModelReference",
                    "keys": [
                      {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/OperationalData"},
                      {"type": "Property", "value": "Temperature"}
                    ]
                  }
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

- AIMC is optional — only include if explicitly requested.
- Each `first` reference must match an existing affordance path in the AID submodel.
- Each `second` reference must match an existing element in OperationalData, Skills, or Parameters.
- The naming pattern for RelationshipElement idShort: `{affordanceName}_to_{targetSubmodel}`.
