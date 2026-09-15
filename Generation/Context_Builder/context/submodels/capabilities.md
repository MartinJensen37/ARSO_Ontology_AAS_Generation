# Submodel Template: Capabilities (IDTA 02020)

- **idShort**: `Capabilities`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Capabilities`
- **semanticId**: `https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Purpose

What the resource can do, one level above Skills — e.g. Capability `Filling`, realized by
Skill `Start`.

## Dependency Rules (Critical)

- Capabilities requires Skills; Skills requires Capabilities.
- Every Skill must be realized by at least one Capability. One Capability may be realized by
  several Skills.
- Each Capability's semanticId must start with `https://smartproductionlab.aau.dk/`.
- Each `realizedBy` relationship's `second` reference must resolve to a Skill in this AAS.

## Structure

```
Capabilities (Submodel)
  └─ CapabilitySet [SMC]
       └─ {Name}Container [SMC]                        one per capability
            ├─ SemanticId [Property, xs:string]       capability URI
            ├─ {Name} [Capability]                    semanticId = capability URI
            └─ realizedBy [SML of RelationshipElement]
                 └─ (no idShort)  first -> this container, second -> [Skills submodel, {SkillName}]
```

| Element | semanticId |
|---|---|
| `CapabilitySet` | `https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0` |
| `{Name}Container` | `https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0` |
| `realizedBy` | `https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0` |

The ontology also accepts the IDTA 02020 ids
`https://admin-shell.io/idta/CapabilityDescription/CapabilitySet/1/0` and
`.../CapabilityContainer/1/0`. Elements inside a SubmodelElementList carry no idShort (AASd-120).

## JSON Template

```json
{
  "idShort": "Capabilities",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Capabilities",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [
      {
        "type": "GlobalReference",
        "value": "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0"
      }
    ]
  },
  "submodelElements": [
    {
      "idShort": "CapabilitySet",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0"
          }
        ]
      },
      "value": [
        {
          "idShort": "FillingContainer",
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [
              {
                "type": "GlobalReference",
                "value": "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0"
              }
            ]
          },
          "value": [
            {
              "idShort": "SemanticId",
              "modelType": "Property",
              "value": "https://smartproductionlab.aau.dk/Capability/Filling",
              "valueType": "xs:string"
            },
            {
              "idShort": "Filling",
              "modelType": "Capability",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://smartproductionlab.aau.dk/Capability/Filling"
                  }
                ]
              }
            },
            {
              "idShort": "realizedBy",
              "modelType": "SubmodelElementList",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"
                  }
                ]
              },
              "orderRelevant": true,
              "typeValueListElement": "RelationshipElement",
              "value": [
                {
                  "modelType": "RelationshipElement",
                  "first": {
                    "type": "ModelReference",
                    "keys": [
                      {
                        "type": "Submodel",
                        "value": "{base_url}/submodels/instances/{systemId}/Capabilities"
                      },
                      {"type": "SubmodelElementCollection", "value": "CapabilitySet"},
                      {"type": "SubmodelElementCollection", "value": "FillingContainer"}
                    ]
                  },
                  "second": {
                    "type": "ModelReference",
                    "keys": [
                      {
                        "type": "Submodel",
                        "value": "{base_url}/submodels/instances/{systemId}/Skills"
                      },
                      {"type": "SubmodelElementCollection", "value": "Start"}
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

- The container idShort is the capability name plus `Container`; the `Capability` element uses
  the bare name.
- Use the lab convention `https://smartproductionlab.aau.dk/Capability/{Name}` for the URI.
