# Submodel Template: Skills

- **idShort**: `Skills`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Skills`
- **semanticId**: `https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Describes the executable skills (functions/operations) that this resource can perform.
Each skill is a `SubmodelElementCollection` containing a `SemanticId` Property and an `Operation` element.

## DEPENDENCY RULES (Critical)

- Skills MUST be accompanied by Capabilities submodel (mutually required).
- Skills MUST be accompanied by AID submodel (required for interface linkage).
- Each Skill's `SemanticId` Property value MUST start with `https://smartproductionlab.aau.dk/`.

## Per-Skill Structure

Each skill is a `SubmodelElementCollection` at the top level with:
- `idShort`: the skill name (e.g. `"Dispense"`, `"PickItem"`)
- `value`: array containing:
  1. `SemanticId` Property — URI starting with `https://smartproductionlab.aau.dk/skills/...`
  2. `Operation` element — the executable AAS operation

## Operation Element

The `Operation` has:
- `idShort`: same as the skill name
- `semanticId`: ExternalReference to the same URI as the SemanticId Property
- `qualifiers`: optional array for invocation delegation and call type
- `inputVariables`: optional array of `{value: Property}` objects
- `outputVariables`: optional array of `{value: Property}` objects
- `inoutputVariables`: optional array of `{value: Property}` objects

## Qualifier Types

```json
{"type": "invocationDelegation", "valueType": "xs:string", "value": "<mqtt-topic-or-http-endpoint>", "kind": "ConceptQualifier"}
{"type": "synchronous", "valueType": "xs:boolean", "value": "true", "kind": "ConceptQualifier"}
{"type": "asynchronous", "valueType": "xs:boolean", "value": "true", "kind": "ConceptQualifier"}
```

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Skills",
  "idShort": "Skills",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "Dispense",
      "value": [
        {
          "modelType": "Property",
          "idShort": "SemanticId",
          "valueType": "xs:string",
          "value": "https://smartproductionlab.aau.dk/skills/Dispense"
        },
        {
          "modelType": "Operation",
          "idShort": "Dispense",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/skills/Dispense"}]
          },
          "qualifiers": [
            {"type": "invocationDelegation", "valueType": "xs:string", "value": "mqtt://broker.example.com/device/skills/dispense", "kind": "ConceptQualifier"},
            {"type": "synchronous", "valueType": "xs:boolean", "value": "true", "kind": "ConceptQualifier"}
          ],
          "inputVariables": [
            {"value": {"modelType": "Property", "idShort": "volume", "valueType": "xs:double", "description": [{"language": "en", "text": "Volume in mL"}]}},
            {"value": {"modelType": "Property", "idShort": "targetContainer", "valueType": "xs:string"}}
          ],
          "outputVariables": [
            {"value": {"modelType": "Property", "idShort": "dispensedVolume", "valueType": "xs:double"}},
            {"value": {"modelType": "Property", "idShort": "success", "valueType": "xs:boolean"}}
          ]
        }
      ]
    }
  ]
}
```

## Notes

- Extract skill names from the spec sheet's function list, operation modes, or capabilities section.
- Use descriptive PascalCase names: `PickItem`, `Dispense`, `MoveToPosition`, `SetParameter`.
- The `invocationDelegation` qualifier value should be the MQTT topic or HTTP endpoint if known from the spec sheet, otherwise leave it empty or omit the qualifier.
- Each skill here MUST have a corresponding Capability in the Capabilities submodel with a `realizedBy` link.
- Each skill here MUST have a corresponding action entry in the AID submodel's InteractionMetadata.actions.
