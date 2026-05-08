"""DigitalNameplateSubmodelBuilderV2 — overrides v1 to thread IDTA semanticIds
into mandatory child SMEs (ManufacturerName, ProductDesignation,
ContactInformation, OrderCodeOfManufacturer).

The submodel-level semanticId is corrected automatically by passing a
SemanticIdFactoryV2 instance to the constructor (it overrides the broken
"https://admin-shell.io/IDTA 02006-3-0" via the inherited property).
"""
from __future__ import annotations

from typing import Dict

from basyx.aas import model



class DigitalNameplateSubmodelBuilder:
    """DigitalNameplate submodel builder — IDTA 02006 aligned, basyx SDK based."""

    def __init__(self, base_url: str, semantic_factory, element_factory):
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    """Inherits everything; overrides build() to attach mandatory SME semanticIds."""

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        nameplate_config = (
            config.get("DigitalNameplate", {}) or config.get("Nameplate", {}) or {}
        )
        elements = []

        uri_of_product = nameplate_config.get(
            "URIOfTheProduct", f"{self.base_url}/assets/{system_id}"
        )
        elements.append(
            self.element_factory.create_property(
                id_short="URIOfTheProduct",
                value=uri_of_product,
                value_type=model.datatypes.String,
                semantic_id=self.semantic_factory.NP_URI_OF_THE_PRODUCT,
            )
        )

        # ManufacturerName — IDTA-aligned semanticId (mandatory per IDTA 02006)
        manufacturer_name = nameplate_config.get(
            "ManufacturerName",
            config.get("manufacturerName", "Unknown Manufacturer"),
        )
        elements.append(
            self.element_factory.create_multi_language_property(
                id_short="ManufacturerName",
                text=manufacturer_name,
                semantic_id=self.semantic_factory.NP_MANUFACTURER_NAME,
            )
        )

        # ManufacturerProductDesignation — IDTA-aligned (mandatory)
        product_designation = nameplate_config.get(
            "ManufacturerProductDesignation",
            config.get("manufacturerProductDesignation", config.get("idShort", system_id)),
        )
        elements.append(
            self.element_factory.create_multi_language_property(
                id_short="ManufacturerProductDesignation",
                text=str(product_designation),
                semantic_id=self.semantic_factory.NP_MANUFACTURER_PRODUCT_DESIGNATION,
            )
        )

        # ContactInformation — IDTA-aligned (mandatory). IDTA 02006 expects an SMC
        # holding an IDTA 02002 ContactInformation; we emit a minimal-yet-typed SMC
        # so the ontology's `someValuesFrom arso:ContactInformationSMC` restriction
        # is satisfied. Inner SMEs can be filled by callers via config.
        # "ContactInformation" is the legacy key; "AddressInformation" is v3 canonical
        contact_config = (
            nameplate_config.get("AddressInformation")
            or nameplate_config.get("ContactInformation")
            or {}
        )
        _address_sids = {
            "Street":       self.semantic_factory.NP_ADDRESS_STREET,
            "ZipCode":      self.semantic_factory.NP_ADDRESS_ZIPCODE,
            "CityTown":     self.semantic_factory.NP_ADDRESS_CITY_TOWN,
            "NationalCode": self.semantic_factory.NP_ADDRESS_NATIONAL_CODE,
        }
        contact_inner: list[model.SubmodelElement] = []
        for field, idshort in (
            ("Street", "Street"),
            ("ZipCode", "ZipCode"),
            ("CityTown", "CityTown"),
            ("NationalCode", "NationalCode"),
        ):
            value = contact_config.get(field)
            if value:
                contact_inner.append(
                    self.element_factory.create_multi_language_property(
                        id_short=idshort,
                        text=str(value),
                        semantic_id=_address_sids[field],
                    )
                )
        elements.append(
            self.element_factory.create_collection(
                id_short="ContactInformation",
                elements=contact_inner,
                semantic_id=self.semantic_factory.NP_CONTACT_INFORMATION,
            )
        )

        # OrderCodeOfManufacturer — IDTA-aligned (mandatory)
        order_code = (
            nameplate_config.get("OrderCodeOfManufacturer")
            or nameplate_config.get("ManufacturerArticleNumber")
            or config.get("manufacturerArticleNumber")
            or "[VERIFY: order code]"
        )
        elements.append(
            self.element_factory.create_property(
                id_short="OrderCodeOfManufacturer",
                value=str(order_code),
                value_type=model.datatypes.String,
                semantic_id=self.semantic_factory.NP_ORDER_CODE_OF_MANUFACTURER,
            )
        )

        # Optional string fields (no IDTA-mandatory semanticId in our ontology)
        optional_string_fields = {
            "ManufacturerProductFamily": nameplate_config.get(
                "ManufacturerProductFamily", config.get("manufacturerProductFamily")
            ),
            "ManufacturerArticleNumber": nameplate_config.get(
                "ManufacturerArticleNumber", config.get("manufacturerArticleNumber")
            ),
            "SerialNumber": nameplate_config.get(
                "SerialNumber", config.get("serialNumber")
            ),
            "YearOfConstruction": nameplate_config.get(
                "YearOfConstruction", config.get("yearOfConstruction")
            ),
            "DateOfManufacture": nameplate_config.get(
                "DateOfManufacture", config.get("dateOfManufacture")
            ),
            "HardwareVersion": nameplate_config.get(
                "HardwareVersion", config.get("hardwareVersion")
            ),
            "SoftwareVersion": nameplate_config.get(
                "SoftwareVersion", config.get("softwareVersion")
            ),
            "CountryOfOrigin": nameplate_config.get(
                "CountryOfOrigin", config.get("countryOfOrigin")
            ),
        }
        for field_name, field_value in optional_string_fields.items():
            if field_value in (None, ""):
                continue
            elements.append(
                self.element_factory.create_property(
                    id_short=field_name,
                    value=str(field_value),
                    value_type=model.datatypes.String,
                )
            )

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/Nameplate",
            id_short="DigitalNameplate",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.DIGITAL_NAMEPLATE_SUBMODEL,
            administration=model.AdministrativeInformation(version="1", revision="0"),
            submodel_element=elements,
        )

