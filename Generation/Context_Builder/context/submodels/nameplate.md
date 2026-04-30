# Submodel Template: DigitalNameplate (v2 — IDTA 02006-3)

- **idShort**: `DigitalNameplate`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Nameplate`
- **semanticId**: `https://admin-shell.io/zvei/nameplate/2/0/Nameplate` (ExternalReference) — **IDTA-aligned, MUST match exactly**
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Required semanticIds for mandatory child SMEs

| idShort                          | semanticId IRI |
|---|---|
| `ManufacturerName`               | `https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerName` |
| `ManufacturerProductDesignation` | `https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerProductDesignation` |
| `ContactInformation`             | `https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ContactInformation` |
| `OrderCodeOfManufacturer`        | `https://admin-shell.io/zvei/nameplate/1/0/Nameplate/OrderCodeOfManufacturer` |

## Required Fields (SHACL violations if missing)

| idShort | modelType | valueType | Notes |
|---|---|---|---|
| `ManufacturerName` | `MultiLanguageProperty` | — | value: `[{"language": "en", "text": "..."}]` — MANDATORY |
| `ManufacturerProductDesignation` | `MultiLanguageProperty` | — | MANDATORY |
| `ContactInformation` | `SubmodelElementCollection` | — | MANDATORY — MUST contain Street, ZipCode, CityTown, NationalCode (all MultiLanguageProperty with ECLASS semanticIds — see template) |
| `OrderCodeOfManufacturer` | `Property` | `xs:string` | MANDATORY |
| `SerialNumber` | `Property` | `xs:string` | Recommended |

## Optional Fields — OMIT if not in spec sheet (do NOT use [VERIFY: ...])

| idShort | modelType | valueType | Format constraint when present |
|---|---|---|---|
| `ManufacturerProductFamily` | `MultiLanguageProperty` | — | Multi-language |
| `URIOfTheProduct` | `Property` | `xs:string` | Product URI |
| `ManufacturerArticleNumber` | `Property` | `xs:string` | — |
| `BatchNumber` | `Property` | `xs:string` | — |
| `YearOfConstruction` | `Property` | `xs:string` | **Exactly 4 digits: `YYYY`**, omit if unknown |
| `DateOfManufacture` | `Property` | `xs:string` | **Format: `YYYY-MM-DD`**, omit if unknown |
| `HardwareVersion` | `Property` | `xs:string` | — |
| `SoftwareVersion` | `Property` | `xs:string` | — |
| `CountryOfOrigin` | `Property` | `xs:string` | ISO 3166-1 alpha-2 |

**Rule:** if the value is not stated in the spec sheet, **omit the field** entirely. Do not
emit `"value": "[VERIFY: ...]"` on optional fields — the validator treats that as a
generation defect.

## JSON Template

```json
{
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Nameplate",
  "idShort": "DigitalNameplate",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/zvei/nameplate/2/0/Nameplate"}]
  },
  "administration": {"version": "1", "revision": "0"},
  "submodelElements": [
    {
      "modelType": "MultiLanguageProperty",
      "idShort": "ManufacturerName",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerName"}]
      },
      "value": [{"language": "en", "text": "<manufacturer name from spec sheet>"}]
    },
    {
      "modelType": "MultiLanguageProperty",
      "idShort": "ManufacturerProductDesignation",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ManufacturerProductDesignation"}]
      },
      "value": [{"language": "en", "text": "<product designation>"}]
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "ContactInformation",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/ContactInformation"}]
      },
      "value": [
        {
          "modelType": "MultiLanguageProperty",
          "idShort": "Street",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO128#002"}]},
          "value": [{"language": "en", "text": "<street and number>"}]
        },
        {
          "modelType": "MultiLanguageProperty",
          "idShort": "ZipCode",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO129#002"}]},
          "value": [{"language": "en", "text": "<postal code>"}]
        },
        {
          "modelType": "MultiLanguageProperty",
          "idShort": "CityTown",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO132#002"}]},
          "value": [{"language": "en", "text": "<city>"}]
        },
        {
          "modelType": "MultiLanguageProperty",
          "idShort": "NationalCode",
          "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO134#002"}]},
          "value": [{"language": "en", "text": "<ISO 3166-1 alpha-2 country code, e.g. DE>"}]
        }
      ]
    },
    {
      "modelType": "Property",
      "idShort": "OrderCodeOfManufacturer",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate/OrderCodeOfManufacturer"}]
      },
      "valueType": "xs:string",
      "value": "<order code>"
    },
    {
      "modelType": "Property",
      "idShort": "SerialNumber",
      "valueType": "xs:string",
      "value": "<serial number>"
    },
    {
      "modelType": "Property",
      "idShort": "YearOfConstruction",
      "valueType": "xs:string",
      "value": "2024"
    }
    /* Omit DateOfManufacture, HardwareVersion, etc. when the spec sheet
       doesn't state a value. Don't fill them with [VERIFY: ...] markers. */
  ]
}
```

## Notes

- All four mandatory child SMEs (`ManufacturerName`, `ManufacturerProductDesignation`,
  `ContactInformation`, `OrderCodeOfManufacturer`) MUST carry the IDTA semanticId shown above.
- Extract manufacturer name, serial/part numbers, product family, version strings from the spec sheet.
- If only a model number is available and no explicit serial number, use the model number as `SerialNumber`.
- `YearOfConstruction` must be exactly 4 digits — never include month or day.
- `DateOfManufacture` must be `YYYY-MM-DD` — only include if a full date is known.
