"""DigitalNameplate submodel builder, IDTA 02006 aligned.

Threads IDTA semanticIds onto the mandatory child SMEs (ManufacturerName,
ManufacturerProductDesignation, ContactInformation, OrderCodeOfManufacturer).
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

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        nameplate_config = (
            config.get("DigitalNameplate", {}) or config.get("Nameplate", {}) or {}
        )
        if not isinstance(nameplate_config, dict):
            # LLM sometimes emits a bare "[VERIFY: ...]" string; treat as absent.
            nameplate_config = {}
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

        # Mandatory per IDTA 02006. No fallback: a fabricated value would pass
        # SHACL's structural check while hiding that nothing was supplied.
        manufacturer_name = nameplate_config.get("ManufacturerName") or config.get("manufacturerName")
        if manufacturer_name:
            elements.append(
                self.element_factory.create_multi_language_property(
                    id_short="ManufacturerName",
                    text=manufacturer_name,
                    semantic_id=self.semantic_factory.NP_MANUFACTURER_NAME,
                )
            )

        # Mandatory; no fallback -- a defaulted designation would be fabricated.
        product_designation = (
            nameplate_config.get("ManufacturerProductDesignation")
            or config.get("manufacturerProductDesignation")
        )
        if product_designation:
            elements.append(
                self.element_factory.create_multi_language_property(
                    id_short="ManufacturerProductDesignation",
                    text=str(product_designation),
                    semantic_id=self.semantic_factory.NP_MANUFACTURER_PRODUCT_DESIGNATION,
                )
            )

        # Mandatory; a minimal typed SMC satisfying the ontology's
        # someValuesFrom arso:ContactInformationSMC restriction.
        # "ContactInformation" is legacy; "AddressInformation" is v3 canonical.
        contact_config = (
            nameplate_config.get("AddressInformation")
            or nameplate_config.get("ContactInformation")
            or {}
        )
        if not isinstance(contact_config, dict):
            # Placeholder string instead of an object; treat as absent.
            contact_config = {}
        _address_sids = {
            "Street":       self.semantic_factory.NP_ADDRESS_STREET,
            "ZipCode":      self.semantic_factory.NP_ADDRESS_ZIPCODE,
            "CityTown":     self.semantic_factory.NP_ADDRESS_CITY_TOWN,
            "NationalCode": self.semantic_factory.NP_ADDRESS_NATIONAL_CODE,
        }
        # Each individually mandatory (minCount 1) per IDTA 02006-3-0.
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

        # Mandatory; omitted when missing so the SHACL shape flags it.
        order_code = (
            nameplate_config.get("OrderCodeOfManufacturer")
            or nameplate_config.get("ManufacturerArticleNumber")
            or config.get("manufacturerArticleNumber")
        )
        if order_code:
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

