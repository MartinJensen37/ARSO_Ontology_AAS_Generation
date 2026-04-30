# Submodel Template: HierarchicalStructures

- **idShort**: `HierarchicalStructures`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/HierarchicalStructures`
- **semanticId**: `https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`
- **displayName**: `[{"language": "en", "text": "{entryNodeName}"}]`

## Purpose

Describes the Bill of Materials (BoM) position of this resource within a larger system hierarchy.
The ArcheType determines the direction of relationships:
- `OneUp` → this resource IsPartOf another system (child knows parent)
- `OneDown` → this resource HasPart sub-resources (parent knows children)
- `OneUpAndOneDown` → both directions

## Structure

The submodel always contains exactly 2 top-level elements:
1. `ArcheType` Property — the hierarchy direction
2. `EntryNode` Entity — the root node representing THIS resource

## EntryNode (required)

The EntryNode entity represents this resource itself:
- `idShort`: use the asset name (same as `systemId` or `entryNodeName` from spec sheet)
- `entityType`: `SelfManagedEntity`
- `globalAssetId`: same as the shell's `globalAssetId`
- `semanticId`: `https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0`
- `statements`: array of child Node entities + RelationshipElements

## Child Node Entities (inside EntryNode.statements)

Each related resource is an Entity with:
- `idShort`: name of the related resource
- `entityType`: `SelfManagedEntity` (if globalAssetId known) or `CoManagedEntity`
- `globalAssetId`: REQUIRED (SHACL violation if missing)
- `semanticId`: `https://admin-shell.io/idta/HierarchicalStructures/Node/1/0`
- `statements`: array containing one `ReferenceElement` named `SameAs`

The `SameAs` ReferenceElement references the EntryNode of the related resource's own BoM submodel.

## RelationshipElements (inside EntryNode.statements)

For each child node, add a RelationshipElement:
- `idShort`: `IsPartOf_{nodeName}` or `HasPart_{nodeName}`
- `semanticId`: `https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0`
- `first`: ModelReference to this submodel's EntryNode
- `second`: ModelReference to this submodel's EntryNode → child entity

## JSON Template (OneUp — IsPartOf a parent system)

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures",
  "idShort": "HierarchicalStructures",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "displayName": [{"language": "en", "text": "{systemId}"}],
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "ArcheType",
      "valueType": "xs:string",
      "value": "OneUp",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0"}]
      }
    },
    {
      "modelType": "Entity",
      "idShort": "{systemId}",
      "entityType": "SelfManagedEntity",
      "globalAssetId": "{base_url}/assets/{systemId}",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"}]
      },
      "statements": [
        {
          "modelType": "Entity",
          "idShort": "ParentSystem",
          "entityType": "SelfManagedEntity",
          "globalAssetId": "{base_url}/assets/ParentSystem",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0"}]
          },
          "statements": [
            {
              "modelType": "ReferenceElement",
              "idShort": "SameAs",
              "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0"}]},
              "supplementalSemanticIds": [{"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"}]}],
              "value": {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "{base_url}/submodels/instances/ParentSystem/HierarchicalStructures"}, {"type": "Entity", "value": "{systemId}"}]}
            }
          ]
        },
        {
          "modelType": "RelationshipElement",
          "idShort": "IsPartOf_ParentSystem",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0"}]},
          "first": {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures"}, {"type": "Entity", "value": "{systemId}"}]},
          "second": {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/HierarchicalStructures"}, {"type": "Entity", "value": "{systemId}"}, {"type": "Entity", "value": "ParentSystem"}]}
        }
      ]
    }
  ]
}
```

## Notes

- If no parent/child system is described in the spec sheet, still create the EntryNode with empty
  statements (no child nodes) — this is valid.
- Infer the parent system name from context (e.g. "part of the filling line" → ParentSystem = "FillingLine").
- globalAssetId for child nodes can be constructed as `{base_url}/assets/{childSystemId}`.
