# Submodel Template: Parameters

- **idShort**: `Parameters`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Parameters`
- **semanticId**: `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "1"}`

## Purpose

Declares the configuration parameters of this resource — static or semi-static values that control
its operating behavior (e.g. max speed, tolerance thresholds, calibration offsets).

## DEPENDENCY RULE

- Parameters requires AID submodel to also be present.

## Per-Parameter Structure

Each parameter is a `SubmodelElementCollection` at the top level containing:
- `ParameterValue` Property — the current or default value as a string
- `Unit` Property (optional) — the unit of measurement

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Parameters",
  "idShort": "Parameters",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel"}]
  },
  "administration": {"version": "1", "revision": "1"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "MaxSpeed",
      "value": [
        {"modelType": "Property", "idShort": "ParameterValue", "valueType": "xs:string", "value": "500"},
        {"modelType": "Property", "idShort": "Unit", "valueType": "xs:string", "value": "rpm"}
      ]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "PositionTolerance",
      "value": [
        {"modelType": "Property", "idShort": "ParameterValue", "valueType": "xs:string", "value": "0.1"},
        {"modelType": "Property", "idShort": "Unit", "valueType": "xs:string", "value": "mm"}
      ]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "OperatingTemperatureRange",
      "value": [
        {"modelType": "Property", "idShort": "ParameterValue", "valueType": "xs:string", "value": "0-50"},
        {"modelType": "Property", "idShort": "Unit", "valueType": "xs:string", "value": "°C"}
      ]
    }
  ]
}
```

## Notes

- Extract parameters from the spec sheet's technical specifications, operating conditions, or configuration section.
- Use PascalCase for parameter names: `MaxSpeed`, `MaxLoad`, `PositionTolerance`, `OperatingVoltage`.
- If a range is specified (e.g. 0–50°C), encode as `"0-50"` in `ParameterValue` with appropriate `Unit`.
- `ParameterValue` is always `xs:string` regardless of the actual value type.
- If no specific parameter values are in the spec sheet, use the spec sheet's nominal operating values.
