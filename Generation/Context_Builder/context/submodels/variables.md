# Submodel Template: OperationalData (Variables)

- **idShort**: `OperationalData` ← **CRITICAL: NOT "Variables"** (common mistake)
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/OperationalData`
- **semanticId**: `https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Declares the runtime operational variables (sensor readings, measurements, status values) that this
resource exposes. Each variable is a `Property` with `valueType: "xs:anyURI"` where the `value`
is the semantic URI for that variable.

## DEPENDENCY RULE

- OperationalData requires AID submodel to also be present.

## Per-Variable Structure

Each variable is a single `Property` at the top level:
- `idShort`: variable name (PascalCase, e.g. `Temperature`, `Pressure`, `FlowRate`)
- `modelType`: `Property`
- `valueType`: `xs:anyURI` — always this type
- `value`: semantic URI for the variable (e.g. `https://smartproductionlab.aau.dk/variables/Temperature`)
- `semanticId`: ExternalReference to the same URI

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/OperationalData",
  "idShort": "OperationalData",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Temperature",
      "valueType": "xs:anyURI",
      "value": "https://smartproductionlab.aau.dk/variables/Temperature",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/variables/Temperature"}]
      }
    },
    {
      "modelType": "Property",
      "idShort": "Pressure",
      "valueType": "xs:anyURI",
      "value": "https://smartproductionlab.aau.dk/variables/Pressure",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/variables/Pressure"}]
      }
    }
  ]
}
```

## Notes

- **The `idShort` of the submodel MUST be `"OperationalData"` not `"Variables"`** — this is a common naming trap.
- Extract variable names from the spec sheet's sensor list, measurement outputs, telemetry section, or I/O interface.
- Construct the semantic URI as: `https://smartproductionlab.aau.dk/variables/{variableName}`
- Typical variable names: `Temperature`, `Pressure`, `FlowRate`, `Weight`, `Speed`, `Torque`, `Position`, `Status`.
