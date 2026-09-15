# Submodel Template: TechnicalData (IDTA 02003)

- **idShort**: `TechnicalData`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/TechnicalData`
- **semanticId**: `0173-1#01-AHX837#002` (ExternalReference, ECLASS IRDI)
- **kind**: `Instance`
- **administration**: `{"version": "2", "revision": "0"}`

## Purpose

Carries the manufacturer-declared technical properties of the asset: who made it,
how it is classified, and its measured characteristics. Use it for values read off
a datasheet's specification table — dimensions, ratings, throughput, tolerances.

Do **not** put runtime values here. Anything the asset reports while running
belongs in OperationalData; anything an operator sets belongs in Parameters.

## Structure

```
TechnicalData (Submodel)
  ├─ GeneralInformation [SMC, 1]
  ├─ ProductClassifications [SML, 0..*]
  ├─ TechnicalProperties [SMC, 1]      ← free-form, see below
  └─ FurtherInformation [SMC, 0..1]
```

## GeneralInformation (mandatory)

| idShort | modelType | valueType | Cardinality | semanticId |
|---|---|---|---|---|
| `ManufacturerName` | `Property` | `xs:string` | 1 | `0173-1#02-AAO677#004` |
| `ManufacturerProductDesignation` | `MultiLanguageProperty` | — | 1 | `0173-1#02-AAW338#003` |
| `ManufacturerArticleNumber` | `Property` | `xs:string` | 1 | `0173-1#02-AAO676#005` |
| `ManufacturerOrderCode` | `Property` | `xs:string` | 1 | `0173-1#02-AAO227#004` |
| `ProductImage` | `File` | — | 0..* | `0173-1#02-ABK291#002` |

`GeneralInformation` itself carries `0173-1#02-ABK161#002/0173-1#01-AHX838#002`.

Note `ManufacturerName` here is a plain `Property`, **not** a MultiLanguageProperty —
this differs from DigitalNameplate, where the same concept is an MLP.

## ProductClassifications (optional)

An SML (`0173-1#02-ABK162#002`) of classification SMCs
(`0173-1#02-ABK162#002/0173-1#01-AHX839#002`), each:

| idShort | modelType | valueType | Cardinality | semanticId |
|---|---|---|---|---|
| `ClassificationSystem` | `Property` | `xs:string` | 1 | `0173-1#02-ABL424#001` |
| `ClassificationSystemVersion` | `Property` | `xs:string` | 0..1 | `0173-1#02-AAR710#003` |
| `ProductClassId` | `Property` | `xs:string` | 1 | `0173-1#02-ABG776#003` |
| `ProductClassCodedName` | `Property` | `xs:string` | 1 | `0173-1#02-ABK128#002` |
| `ProductClassName` | `MultiLanguageProperty` | — | 0..1 | `0173-1#02-ABK273#002` |

Emit this only when the datasheet states an ECLASS or IEC CDD class. Do not invent
a classification.

## TechnicalProperties (mandatory, free-form)

This is the one deliberately open section of the template. Its children are
"arbitrary" elements — the datasheet's own property names, each carrying
`https://admin-shell.io/SMT/General/Arbitrary` as semanticId when no ECLASS IRDI
is known. Group related properties into `Section` SMCs.

Use `Property` for a single value, `Range` for a min/max pair, and
`MultiLanguageProperty` for prose. Always put the unit in the value string
(`"400 V"`) or in a sibling property — never guess an IRDI.

```json
{
  "modelType": "SubmodelElementCollection",
  "idShort": "TechnicalProperties",
  "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#01-AHD205#001"}]},
  "value": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "ElectricalRatings",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/SMT/General/Arbitrary"}]},
      "value": [
        {"modelType": "Property", "idShort": "RatedVoltage", "valueType": "xs:string", "value": "230 V AC",
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/SMT/General/Arbitrary"}]}},
        {"modelType": "Range", "idShort": "OperatingTemperature", "valueType": "xs:string", "min": "5", "max": "40",
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/SMT/General/Arbitrary"}]}}
      ]
    }
  ]
}
```

## FurtherInformation (optional)

SMC `0173-1#02-ABK164#002`, holding free-text statements plus a validity date:

| idShort | modelType | valueType | Cardinality | semanticId |
|---|---|---|---|---|
| `TextStatement` | `MultiLanguageProperty` | — | 0..* | `0173-1#02-ABK134#002` |
| `ValidDate` | `Property` | `xs:date` | 1 | `0173-1#02-ABL775#001` |

`ValidDate` is mandatory **once FurtherInformation exists** — omit the whole SMC
rather than emitting it without a date.

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/TechnicalData",
  "idShort": "TechnicalData",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "0173-1#01-AHX837#002"}]
  },
  "administration": {"version": "2", "revision": "0"},
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "GeneralInformation",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-ABK161#002/0173-1#01-AHX838#002"}]},
      "value": [
        {"modelType": "Property", "idShort": "ManufacturerName", "valueType": "xs:string", "value": "<manufacturer>",
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO677#004"}]}},
        {"modelType": "MultiLanguageProperty", "idShort": "ManufacturerProductDesignation",
         "value": [{"language": "en", "text": "<product designation>"}],
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAW338#003"}]}},
        {"modelType": "Property", "idShort": "ManufacturerArticleNumber", "valueType": "xs:string", "value": "<article number>",
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO676#005"}]}},
        {"modelType": "Property", "idShort": "ManufacturerOrderCode", "valueType": "xs:string", "value": "<order code>",
         "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO227#004"}]}}
      ]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "TechnicalProperties",
      "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#01-AHD205#001"}]},
      "value": []
    }
  ]
}
```

## Notes

- All four `GeneralInformation` fields are mandatory. If the datasheet gives no
  article number or order code, reuse the model/type designation rather than
  omitting the element — SHACL requires all four.
- Take every `TechnicalProperties` value verbatim from the datasheet's
  specification table. Do not derive, convert or round.
- `ManufacturerName` and `ManufacturerProductDesignation` usually duplicate the
  DigitalNameplate values. Keep them consistent between the two submodels.
- Use `https://admin-shell.io/SMT/General/Arbitrary` for any property whose ECLASS
  IRDI you do not know. Never invent an IRDI — a wrong one is worse than the
  generic marker.
