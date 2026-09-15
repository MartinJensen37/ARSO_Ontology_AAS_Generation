# Submodel Template: DigitalNameplate (IDTA 02006-3-0)

- **idShort**: `DigitalNameplate`
- **Submodel ID pattern**: `{base_url}/submodels/instances/{systemId}/Nameplate`
- **semanticId**: `https://admin-shell.io/idta/nameplate/3/0/Nameplate` (ExternalReference)
- **kind**: `Instance`
- **administration**: `{"version": "1", "revision": "0"}`

## Mandatory elements (SHACL violation if missing)

| idShort | modelType | valueType | semanticId |
|---|---|---|---|
| `URIOfTheProduct` | `Property` | `xs:string` | `0112/2///61987#ABN590#002` |
| `ManufacturerName` | `MultiLanguageProperty` | — | `0112/2///61987#ABA565#009` |
| `ManufacturerProductDesignation` | `MultiLanguageProperty` | — | `0112/2///61987#ABA567#009` |
| `ContactInformation` | `SubmodelElementCollection` | — | `https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation` |
| `OrderCodeOfManufacturer` | `Property` | `xs:string` | `0112/2///61987#ABA950#008` |

`ContactInformation` must hold four MultiLanguageProperties, each mandatory:

| idShort | semanticId |
|---|---|
| `Street` | `0173-1#02-AAO128#002` |
| `ZipCode` | `0173-1#02-AAO129#002` |
| `CityTown` | `0173-1#02-AAO132#002` |
| `NationalCode` | `0173-1#02-AAO134#002` |

IDTA 02006-3-0 names this collection `AddressInformation`. The pipeline emits the idShort
`ContactInformation` with the IDTA semanticId, which is what the ontology checks; the profile
accepts either key.

## Optional elements — omit when the datasheet does not state them

Plain `Property` elements with `valueType: xs:string` and no semanticId. Never emit
`[VERIFY: ...]` on any of them.

| idShort | Format when present |
|---|---|
| `SerialNumber` | — |
| `ManufacturerProductFamily` | — |
| `ManufacturerArticleNumber` | — |
| `YearOfConstruction` | exactly 4 digits, `YYYY` |
| `DateOfManufacture` | `YYYY-MM-DD` |
| `HardwareVersion` | — |
| `SoftwareVersion` | — |
| `CountryOfOrigin` | ISO 3166-1 alpha-2, e.g. `DE` |

## JSON Template

```json
{
  "idShort": "DigitalNameplate",
  "modelType": "Submodel",
  "id": "{base_url}/submodels/instances/{systemId}/Nameplate",
  "administration": {"version": "1", "revision": "0"},
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{"type": "GlobalReference", "value": "https://admin-shell.io/idta/nameplate/3/0/Nameplate"}]
  },
  "submodelElements": [
    {
      "idShort": "URIOfTheProduct",
      "modelType": "Property",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0112/2///61987#ABN590#002"}]
      },
      "value": "{base_url}/products/ex-100",
      "valueType": "xs:string"
    },
    {
      "idShort": "ManufacturerName",
      "modelType": "MultiLanguageProperty",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0112/2///61987#ABA565#009"}]
      },
      "value": [{"language": "en", "text": "Example Automation GmbH"}]
    },
    {
      "idShort": "ManufacturerProductDesignation",
      "modelType": "MultiLanguageProperty",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0112/2///61987#ABA567#009"}]
      },
      "value": [{"language": "en", "text": "EX-100 Filling Station"}]
    },
    {
      "idShort": "ContactInformation",
      "modelType": "SubmodelElementCollection",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [
          {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation"
          }
        ]
      },
      "value": [
        {
          "idShort": "Street",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO128#002"}]
          },
          "value": [{"language": "en", "text": "Musterstrasse 1"}]
        },
        {
          "idShort": "ZipCode",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO129#002"}]
          },
          "value": [{"language": "en", "text": "70173"}]
        },
        {
          "idShort": "CityTown",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO132#002"}]
          },
          "value": [{"language": "en", "text": "Stuttgart"}]
        },
        {
          "idShort": "NationalCode",
          "modelType": "MultiLanguageProperty",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{"type": "GlobalReference", "value": "0173-1#02-AAO134#002"}]
          },
          "value": [{"language": "en", "text": "DE"}]
        }
      ]
    },
    {
      "idShort": "OrderCodeOfManufacturer",
      "modelType": "Property",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{"type": "GlobalReference", "value": "0112/2///61987#ABA950#008"}]
      },
      "value": "EX-100-EU",
      "valueType": "xs:string"
    },
    {
      "idShort": "SerialNumber",
      "modelType": "Property",
      "value": "EX-2024-001",
      "valueType": "xs:string"
    },
    {
      "idShort": "YearOfConstruction",
      "modelType": "Property",
      "value": "2024",
      "valueType": "xs:string"
    }
  ]
}
```

## Notes

- `URIOfTheProduct`: use the product URI from the datasheet, otherwise `{base_url}/assets/{systemId}`.
- If only a model number is given and no serial number, use the model number as `SerialNumber`.
- `NationalCode` is the ISO 3166-1 alpha-2 code of the manufacturer's address.
