# Submodel Template: HierarchicalStructures (IDTA 02011-1-1)

- **idShort**: `HierarchicalStructures`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/HierarchicalStructures`
- **semanticId**: `https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`
- **displayName**: the BoM name, e.g. `[{"language": "en", "text": "BillOfMaterials"}]`

## Purpose

This resource's position in a Bill of Materials. `ArcheType` sets which relations it declares:

- `OneUp` — its parent only (`IsPartOf`)
- `OneDown` — its children only (`HasPart`)
- `Full` — both

No other value is valid; SHACL rejects anything else.

## Structure

```
HierarchicalStructures (Submodel)
  ├─ ArcheType [Property, xs:string]           "OneUp" | "OneDown" | "Full"
  └─ EntryNode [Entity, SelfManagedEntity]     this resource
       ├─ HasPart_{Name} | IsPartOf_{Name} [RelationshipElement]   one per related system
       └─ {Name} [Entity]                                         one per related system
            └─ SameAs [ReferenceElement]  -> that system's own HierarchicalStructures EntryNode
```

| Element | semanticId |
|---|---|
| `ArcheType` | `https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0` |
| `EntryNode` | `https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0` |
| Child `Entity` | `https://admin-shell.io/idta/HierarchicalStructures/Node/1/0` |
| `HasPart_{Name}` | `https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0` |
| `IsPartOf_{Name}` | `https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0` |
| `SameAs` | `https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0`, supplementalSemanticId `.../EntryNode/1/0` |

- `EntryNode`: the idShort is literally `EntryNode`; its `globalAssetId` is the shell's.
- Child entity: `SelfManagedEntity` with a `globalAssetId` when one is known, else `CoManagedEntity`.
- RelationshipElement: `first` → `[this submodel, EntryNode]`, `second` → `[this submodel, EntryNode, {Name}]`.
- `SameAs` → `[{base_url}/submodels/instances/{Name}AAS/HierarchicalStructures, EntryNode]`, unless the entry sets its own `systemId`.

## JSON Template (OneDown, one child)

```json
{
  "idShort": "HierarchicalStructures",
  "displayName": [{"language": "en", "text": "BillOfMaterials"}],
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures",
  "administration": {"version": "1", "revision": "1"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "ArcheType",
      "modelType": "Property",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0"
          }
        ]
      },
      "value": "OneDown",
      "valueType": "xs:string"
    },
    {
      "idShort": "EntryNode",
      "modelType": "Entity",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
          }
        ]
      },
      "statements": [
        {
          "idShort": "HasPart_ControllerModule",
          "modelType": "RelationshipElement",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0"
              }
            ]
          },
          "first": {
            "type": "ModelReference",
            "keys": [
              {
                "type": "Submodel",
                "value": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures"
              },
              {"type": "Entity", "value": "EntryNode"}
            ]
          },
          "second": {
            "type": "ModelReference",
            "keys": [
              {
                "type": "Submodel",
                "value": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures"
              },
              {"type": "Entity", "value": "EntryNode"},
              {"type": "Entity", "value": "ControllerModule"}
            ]
          }
        },
        {
          "idShort": "ControllerModule",
          "modelType": "Entity",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0"
              }
            ]
          },
          "statements": [
            {
              "idShort": "SameAs",
              "modelType": "ReferenceElement",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0"
                  }
                ]
              },
              "supplementalSemanticIds": [
                {
                  "type": "ExternalReference",
                  "keys": [
                    {
                      "type": "GlobalReference",
                      "value": "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
                    }
                  ]
                }
              ],
              "value": {
                "type": "ModelReference",
                "keys": [
                  {
                    "type": "Submodel",
                    "value": "{base_url}/submodels/instances/ControllerModuleAAS/HierarchicalStructures"
                  },
                  {"type": "Entity", "value": "EntryNode"}
                ]
              }
            }
          ],
          "entityType": "SelfManagedEntity",
          "globalAssetId": "{base_url}/assets/ControllerModule"
        }
      ],
      "entityType": "SelfManagedEntity",
      "globalAssetId": "{base_url}/assets/ExampleAsset"
    }
  ]
}
```

## Notes

- Declare at least one related system; an `EntryNode` without statements is flagged.
- Infer the parent from context, e.g. "station 1 of the filling line" → `IsPartOf_FillingLine`.
- Build a child's `globalAssetId` as `{base_url}/assets/{Name}` when the source gives none.
