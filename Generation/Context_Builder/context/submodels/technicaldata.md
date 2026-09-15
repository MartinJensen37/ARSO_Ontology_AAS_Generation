# Submodel Template: TechnicalData (IDTA 02003)

- **idShort**: `TechnicalData`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/TechnicalData`
- **semanticId**: `0173-1#01-AHX837#002` (ExternalReference, ECLASS IRDI)
- **kind**: `Instance`
- **administration**: `{"version": "2", "revision": "0"}`

## Purpose

Manufacturer-declared technical data: who made the asset, how it is classified, and the values
from its datasheet specification table — dimensions, ratings, tolerances. Runtime values belong
in OperationalData and operator settings in Parameters.

## Structure

```
TechnicalData (Submodel)
  ├─ GeneralInformation [SMC, 1]
  ├─ ProductClassifications [SML, 0..1]
  │    └─ (no idShort) [SMC]          one per classification
  ├─ TechnicalPropertyAreas [SML, 0..1]
  │    └─ (no idShort) [SMC]
  │         └─ {Section} [SMC]         one per datasheet group, holding its values
  └─ FurtherInformation [SMC, 0..1]
```

## GeneralInformation (mandatory)

semanticId `0173-1#02-ABK161#002/0173-1#01-AHX838#002`. All four children are mandatory; any
the datasheet omits falls back to the DigitalNameplate value.

| idShort | modelType | valueType | semanticId |
|---|---|---|---|
| `ManufacturerName` | `Property` | `xs:string` | `0173-1#02-AAO677#004` |
| `ManufacturerProductDesignation` | `MultiLanguageProperty` | — | `0173-1#02-AAW338#003` |
| `ManufacturerArticleNumber` | `Property` | `xs:string` | `0173-1#02-AAO676#005` |
| `ManufacturerOrderCode` | `Property` | `xs:string` | `0173-1#02-AAO227#004` |

`ManufacturerName` is a plain `Property` here, unlike DigitalNameplate where it is an MLP.

## ProductClassifications (optional)

A SubmodelElementList `0173-1#02-ABK162#002` of collections
`0173-1#02-ABK162#002/0173-1#01-AHX839#002`. Emit only a class the datasheet actually states.

| idShort | Cardinality | semanticId |
|---|---|---|
| `ClassificationSystem` | 1 | `0173-1#02-ABL424#001` |
| `ClassificationSystemVersion` | 0..1 | `0173-1#02-AAR710#003` |
| `ProductClassId` | 1 | `0173-1#02-ABG776#003` |
| `ProductClassCodedName` | 1 | `0173-1#02-ABK128#002` |

## TechnicalPropertyAreas (optional)

A SubmodelElementList `0173-1#02-ABK163#002` holding one area collection
`0173-1#02-ABL358#002/0173-1#01-AHX773#002`. Inside it, each datasheet group is a `{Section}`
collection named after the group; loose values go into a `General` section.

- A single value is a `Property` (`xs:string`) with its unit in the value, e.g. `"230 V AC"`.
- A min/max pair is a `Range` (`xs:string`).
- Sections and values carry the generic marker `https://admin-shell.io/SMT/General/Arbitrary`.

IDTA's own sample gives the area collections idShorts such as `ECLASS`, but AASd-120 forbids an
idShort inside a list, so the pipeline nests named sections one level down instead.

## FurtherInformation (optional)

Collection `0173-1#02-ABK164#002` with free-text statements and a validity date:

| idShort | modelType | Cardinality | semanticId |
|---|---|---|---|
| `TextStatement` | `MultiLanguageProperty` | 0..* | `0173-1#02-ABK134#002` |
| `ValidDate` | `Property` (`xs:date`) | 1 | `0173-1#02-ABL775#001` |

Omit the whole collection when there is no `ValidDate`.

## JSON Template

```json
{
  "idShort": "TechnicalData",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/TechnicalData",
  "administration": {"version": "2", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "0173-1#01-AHX837#002"}]
  },
  "submodelElements": [
    {
      "idShort": "GeneralInformation",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK161#002/0173-1#01-AHX838#002"}]
      },
      "value": [
        {
          "idShort": "ManufacturerName",
          "modelType": "Property",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO677#004"}]
          },
          "value": "Example Automation GmbH",
          "valueType": "xs:string"
        },
        {
          "idShort": "ManufacturerProductDesignation",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAW338#003"}]
          },
          "value": [{"language": "en", "text": "EX-100 Filling Station"}]
        },
        {
          "idShort": "ManufacturerArticleNumber",
          "modelType": "Property",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO676#005"}]
          },
          "value": "EX-100",
          "valueType": "xs:string"
        },
        {
          "idShort": "ManufacturerOrderCode",
          "modelType": "Property",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO227#004"}]
          },
          "value": "EX-100-EU",
          "valueType": "xs:string"
        }
      ]
    },
    {
      "idShort": "ProductClassifications",
      "modelType": "SubmodelElementList",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK162#002"}]
      },
      "orderRelevant": true,
      "typeValueListElement": "SubmodelElementCollection",
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK162#002/0173-1#01-AHX839#002"}]
          },
          "value": [
            {
              "idShort": "ClassificationSystem",
              "modelType": "Property",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABL424#001"}]
              },
              "value": "ECLASS",
              "valueType": "xs:string"
            },
            {
              "idShort": "ClassificationSystemVersion",
              "modelType": "Property",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAR710#003"}]
              },
              "value": "12.0",
              "valueType": "xs:string"
            },
            {
              "idShort": "ProductClassId",
              "modelType": "Property",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABG776#003"}]
              },
              "value": "0173-1#01-AKJ975#017",
              "valueType": "xs:string"
            },
            {
              "idShort": "ProductClassCodedName",
              "modelType": "Property",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK128#002"}]
              },
              "value": "27-27-03-01",
              "valueType": "xs:string"
            }
          ]
        }
      ]
    },
    {
      "idShort": "TechnicalPropertyAreas",
      "modelType": "SubmodelElementList",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK163#002"}]
      },
      "orderRelevant": true,
      "typeValueListElement": "SubmodelElementCollection",
      "value": [
        {
          "modelType": "SubmodelElementCollection",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABL358#002/0173-1#01-AHX773#002"}]
          },
          "value": [
            {
              "idShort": "ElectricalRatings",
              "modelType": "SubmodelElementCollection",
              "semanticId": {
                "type": "ExternalReference",
                "keys": [
                  {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/SMT/General/Arbitrary"
                  }
                ]
              },
              "value": [
                {
                  "idShort": "RatedVoltage",
                  "modelType": "Property",
                  "semanticId": {
                    "type": "ExternalReference",
                    "keys": [
                      {
                        "type": "GlobalReference",
                        "value": "https://admin-shell.io/SMT/General/Arbitrary"
                      }
                    ]
                  },
                  "value": "230 V AC",
                  "valueType": "xs:string"
                },
                {
                  "idShort": "OperatingTemperature",
                  "modelType": "Range",
                  "semanticId": {
                    "type": "ExternalReference",
                    "keys": [
                      {
                        "type": "GlobalReference",
                        "value": "https://admin-shell.io/SMT/General/Arbitrary"
                      }
                    ]
                  },
                  "valueType": "xs:string",
                  "min": "5",
                  "max": "40"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "idShort": "FurtherInformation",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK164#002"}]
      },
      "value": [
        {
          "idShort": "TextStatement",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK134#002"}]
          },
          "value": [{"language": "en", "text": "Values at nominal load."}]
        },
        {
          "idShort": "ValidDate",
          "modelType": "Property",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABL775#001"}]
          },
          "value": "2024-06-01",
          "valueType": "xs:date"
        }
      ]
    }
  ]
}
```

## Notes

- Copy values verbatim from the specification table, including units. Do not convert or round.
- Never invent an ECLASS IRDI; the generic Arbitrary marker is correct when none is known.
- Keep `ManufacturerName` and `ManufacturerProductDesignation` consistent with DigitalNameplate.
