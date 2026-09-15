# Submodel Template: Skills (IDTA 02015 Control Component, flattened)

- **idShort**: `Skills`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Skills`
- **semanticId**: `https://admin-shell.io/idta/ControlComponentType/1/0` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Purpose

The executable operations this resource offers. Each skill wraps one AAS `Operation` that is
invoked through one AID action.

## Dependency Rules (Critical)

- Skills requires AID and Capabilities; Capabilities requires Skills.
- Every skill must be realized by at least one Capability.
- Every skill's `InterfaceReference` must point at an existing AID action.
- Skill semanticIds must start with `https://smartproductionlab.aau.dk/`.

## Structure

```
Skills (Submodel)
  ├─ Interfaces [SMC]          always present, empty
  ├─ Skills [SMC]
  │    └─ {SkillName} [SMC]
  │         ├─ SemanticId [Property, xs:string]      https://smartproductionlab.aau.dk/skills/{SkillName}
  │         ├─ {SkillName} [Operation]              semanticId = the same URI
  │         ├─ InterfaceReference [ReferenceElement] -> AID/{Interface}/InteractionMetadata/actions/{Action}
  │         └─ StateMachine [Property]              asynchronous skills only
  └─ Errors [SMC]              always present, empty
```

`Interfaces`, `Skills` and `Errors` are each mandatory, exactly once.

## Operation

- `qualifiers`:
  - `invocationDelegation` (`xs:string`): `{delegation_base_url}/operations/{systemId}/{SkillName}`
  - `Synchronous` (`xs:boolean`) for request/response actions, or `OneWay` (`xs:boolean`, `true`)
    when the AID action has neither an output schema nor a `response` topic
- `inputVariables` / `outputVariables` are derived from the AID action's `input` / `output` JSON
  Schema; omit them when the action has none.
- Asynchronous skills (`Synchronous` false) also get a `StateMachine` Property, polled for
  `IDLE` / `RUNNING` / `SUCCESS` / `FAILURE`.

## JSON Template

```json
{
  "idShort": "Skills",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Skills",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/ControlComponentType/1/0"}]
  },
  "submodelElements": [
    {"idShort": "Interfaces", "modelType": "SubmodelElementCollection"},
    {
      "idShort": "Skills",
      "modelType": "SubmodelElementCollection",
      "value": [
        {
          "idShort": "Start",
          "description": [{"language": "en", "text": "Skill: Start"}],
          "modelType": "SubmodelElementCollection",
          "value": [
            {
              "idShort": "SemanticId",
              "modelType": "Property",
              "value": "https://smartproductionlab.aau.dk/skills/Start",
              "valueType": "xs:string"
            },
            {
              "idShort": "Start",
              "description": [{"language": "en", "text": "Operation to invoke Start fill cycle action"}],
              "modelType": "Operation",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://smartproductionlab.aau.dk/skills/Start"
                  }
                ]
              },
              "qualifiers": [
                {
                  "value": "http://registration-service:8087/operations/{systemId}/Start",
                  "kind": "ConceptQualifier",
                  "valueType": "xs:string",
                  "type": "invocationDelegation"
                },
                {
                  "value": "true",
                  "kind": "ConceptQualifier",
                  "valueType": "xs:boolean",
                  "type": "Synchronous"
                }
              ]
            },
            {
              "idShort": "InterfaceReference",
              "description": [{"language": "en", "text": "Reference to Start action interface"}],
              "modelType": "ReferenceElement",
              "value": {
                "type": "ModelReference",
                "keys": [
                  {"type": "Submodel", "value": "{base_url}/submodels/instances/{systemId}/AID"},
                  {"type": "SubmodelElementCollection", "value": "InterfaceMQTT"},
                  {"type": "SubmodelElementCollection", "value": "InteractionMetadata"},
                  {"type": "SubmodelElementCollection", "value": "actions"},
                  {"type": "SubmodelElementCollection", "value": "Start"}
                ]
              }
            }
          ]
        }
      ]
    },
    {"idShort": "Errors", "modelType": "SubmodelElementCollection"}
  ]
}
```

## Notes

- Take skill names from the command list or the NodeSet's `<UAMethod>` BrowseNames, in
  PascalCase (`Start`, `Home`, `MoveToPosition`).
- Name each skill after its AID action; the `InterfaceReference` ends at that action's idShort.
