# Submodel Template: Capabilities

- **idShort**: `Capabilities`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Capabilities`
- **semanticId**: `https://admin-shell.io/idta/CapabilityDescription/1/0` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Declares the semantic capabilities of this resource — what it CAN do (at a higher abstraction level
than Skills). Each Capability is a formal declaration that MUST be realized by a Skill.

## DEPENDENCY RULES (Critical)

- Capabilities MUST be accompanied by Skills submodel (mutually required).
- Each Capability's `SemanticId` Property value MUST start with `https://smartproductionlab.aau.dk/`.
- Each Capability MUST have a `realizedBy` SubmodelElementList pointing to a Skill (SHACL violation otherwise).
- One Capability can reference one or more Skills via the `realizedBy` list.

## Structure

The submodel has ONE top-level element: `CapabilitySet` SubmodelElementCollection.
Inside `CapabilitySet`, each capability is its own SubmodelElementCollection.

Each capability SubmodelElementCollection contains:
1. `SemanticId` Property — URI starting with `https://smartproductionlab.aau.dk/capabilities/...`
2. `Capability` element — formal AAS Capability model type
3. `realizedBy` SubmodelElementList — list of RelationshipElements pointing to Skills

## realizedBy Structure

```json
{
  "modelType": "SubmodelElementList",
  "idShort": "realizedBy",
  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"}]},
  "orderRelevant": true,
  "typeValueListElement": "RelationshipElement",
  "value": [
    {
      "modelType": "RelationshipElement",
      "idShort": "{skillName}",
      "first": {
        "type": "ModelReference",
        "keys": [
          {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/Capabilities"},
          {"type": "SubmodelElementCollection", "value": "CapabilitySet"},
          {"type": "SubmodelElementCollection", "value": "{capabilityName}"}
        ]
      },
      "second": {
        "type": "ModelReference",
        "keys": [
          {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/Skills"},
          {"type": "SubmodelElementCollection", "value": "{skillName}"}
        ]
      }
    }
  ]
}
```

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Capabilities",
  "idShort": "Capabilities",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/CapabilityDescription/1/0"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "CapabilitySet",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0"}]
      },
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "idShort": "Dispensing",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0"}]
          },
          "value": [
            {
              "modelType": "Property",
              "idShort": "SemanticId",
              "valueType": "xs:string",
              "value": "https://smartproductionlab.aau.dk/capabilities/Dispensing"
            },
            {
              "modelType": "Capability",
              "idShort": "Dispensing",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/capabilities/Dispensing"}]
              }
            },
            {
              "modelType": "SubmodelElementList",
              "idShort": "realizedBy",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"}]
              },
              "orderRelevant": true,
              "typeValueListElement": "RelationshipElement",
              "value": [
                {
                  "modelType": "RelationshipElement",
                  "idShort": "Dispense",
                  "first": {
                    "type": "ModelReference",
                    "keys": [
                      {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/Capabilities"},
                      {"type": "SubmodelElementCollection", "value": "CapabilitySet"},
                      {"type": "SubmodelElementCollection", "value": "Dispensing"}
                    ]
                  },
                  "second": {
                    "type": "ModelReference",
                    "keys": [
                      {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/Skills"},
                      {"type": "SubmodelElementCollection", "value": "Dispense"}
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

- Capabilities are higher-level than Skills: e.g. Capability = "Dispensing", Skill = "Dispense".
- The number of Capabilities can equal the number of Skills, or one Capability can cover multiple Skills.
- Each Capability's `realizedBy` RelationshipElement `idShort` must match the Skill's `idShort` in the Skills submodel.
- The `second` key path in the RelationshipElement must point to the EXACT path in the Skills submodel.
