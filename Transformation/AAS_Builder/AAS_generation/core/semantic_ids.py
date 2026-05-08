"""
Semantic ID Factory

Centralizes creation of semantic IDs and references for AAS elements.
All IDs are aligned with ARSO_AAS.ttl and the imported ontology modules.
"""

from basyx.aas import model
from typing import List, Optional


class SemanticIdFactory:
    """Factory for creating semantic IDs and references."""

    # ── Submodel-level semantic IDs ───────────────────────────────────────────

    # IDTA 02006-3-0 (November 2024) — canonical for v3
    _DIGITAL_NAMEPLATE_SUBMODEL = "https://admin-shell.io/idta/nameplate/3/0/Nameplate"

    _VARIABLES_SUBMODEL  = "https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel"
    _PARAMETERS_SUBMODEL = "https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel"

    # IDTA 02011-1-1 — submodel is at /1/1/, individual SME types at /1/0/
    _HIERARCHICAL_STRUCTURES   = "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel"
    _HIERARCHICAL_ARCHETYPE    = "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0"
    _HIERARCHICAL_ENTRY_NODE   = "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
    _HIERARCHICAL_NODE         = "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0"
    _HIERARCHICAL_SAME_AS      = "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0"
    _HIERARCHICAL_HAS_PART     = "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0"
    _HIERARCHICAL_IS_PART_OF   = "https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0"
    _HIERARCHICAL_BULK_COUNT   = "https://admin-shell.io/idta/HierarchicalStructures/BulkCount/1/0"
    _HIERARCHICAL_RELATIONSHIP = "https://admin-shell.io/idta/HierarchicalStructures/Relationship/1/0"

    # IDTA 02017-1-1 (AID)
    _ASSET_INTERFACES          = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0"
    _ASSET_INTERFACES_SUBMODEL = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel"
    _ASSET_INTERFACES_INTERFACE    = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    _ASSET_INTERFACES_INTERACTION  = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
    _ASSET_INTERFACES_REFERENCE    = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InterfaceReference"
    _AID_ENDPOINT_METADATA         = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"

    # IDTA 02015-2-0 (Control Component Type — Skills)
    _SKILLS_SUBMODEL = "https://admin-shell.io/idta/ControlComponentType/1/0"

    # IDTA 02020-1-0 (Capability Description)
    _CAPABILITIES_SUBMODEL = "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0"
    # CapabilitySet/CapabilityContainer have no IDTA-canonical element semantic IDs;
    # these internal IDs keep backward-compat with existing generated files.
    _CAPABILITY_SET       = "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0"
    _CAPABILITY_CONTAINER = "https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0"
    # IDTA 02020 canonical for the Capability AAS element
    _CAPABILITY           = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"
    _CAPABILITY_RELATIONS = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRelations/1/0"
    _CAPABILITY_REALIZED_BY = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"

    # W3C Thing Description (informational)
    _WOT_TD          = "https://www.w3.org/2019/wot/td"
    _WOT_ACTION      = "https://www.w3.org/2019/wot/td#ActionAffordance"
    _WOT_PROPERTY    = "https://www.w3.org/2019/wot/td#PropertyAffordance"
    _WOT_INTERACTION = "https://www.w3.org/2019/wot/td#InteractionAffordance"

    _MQTT_PROTOCOL  = "https://www.w3.org/2019/wot/td/v1/binding/mqtt"
    _OPCUA_PROTOCOL = "http://opcfoundation.org/UA/WoT-Binding/"
    _HTTP_PROTOCOL  = "https://www.w3.org/2019/wot/td/v1/binding/http"

    # Specific Asset IDs
    _SERIAL_NUMBER = "https://admin-shell.io/aas/3/0/SpecificAssetId/SerialNumber"
    _LOCATION      = "https://admin-shell.io/aas/3/0/SpecificAssetId/Location"

    # ── Nameplate SME semantic IDs (IDTA 02006-3-0 / IEC 61987 IRDIs) ────────
    # Mandatory top-level elements
    _NP_MANUFACTURER_NAME                = "0112/2///61987#ABA565#009"
    _NP_MANUFACTURER_PRODUCT_DESIGNATION = "0112/2///61987#ABA567#009"
    _NP_ORDER_CODE_OF_MANUFACTURER       = "0112/2///61987#ABA950#008"
    _NP_URI_OF_THE_PRODUCT               = "0112/2///61987#ABN590#002"

    # AddressInformation SMC (drop-in from IDTA 02002; v3 renamed from ContactInformation)
    _NP_CONTACT_INFORMATION = "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation"

    # Mandatory AddressInformation child elements (ECLASS IRDIs per IDTA 02002)
    _NP_ADDRESS_STREET        = "0173-1#02-AAO128#002"
    _NP_ADDRESS_ZIPCODE       = "0173-1#02-AAO129#002"
    _NP_ADDRESS_CITY_TOWN     = "0173-1#02-AAO132#002"
    _NP_ADDRESS_NATIONAL_CODE = "0173-1#02-AAO134#002"

    # ── Properties (return ExternalReference objects) ─────────────────────────

    @property
    def DIGITAL_NAMEPLATE_SUBMODEL(self) -> model.ExternalReference:
        return self.create_external_reference(self._DIGITAL_NAMEPLATE_SUBMODEL)

    @property
    def ASSET_INTERFACES_DESCRIPTION(self) -> model.ExternalReference:
        return self.create_external_reference(self._ASSET_INTERFACES_SUBMODEL)

    @property
    def INTERFACE(self) -> model.ExternalReference:
        return self.create_external_reference(self._ASSET_INTERFACES_INTERFACE)

    @property
    def INTERACTION_METADATA(self) -> model.ExternalReference:
        return self.create_external_reference(self._ASSET_INTERFACES_INTERACTION)

    @property
    def INTERFACE_REFERENCE(self) -> model.ExternalReference:
        return self.create_external_reference(self._ASSET_INTERFACES_REFERENCE)

    @property
    def AID_ENDPOINT_METADATA(self) -> model.ExternalReference:
        return self.create_external_reference(self._AID_ENDPOINT_METADATA)

    @property
    def VARIABLES_SUBMODEL(self) -> model.ExternalReference:
        return self.create_external_reference(self._VARIABLES_SUBMODEL)

    @property
    def PARAMETERS_SUBMODEL(self) -> model.ExternalReference:
        return self.create_external_reference(self._PARAMETERS_SUBMODEL)

    @property
    def HIERARCHICAL_STRUCTURES(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_STRUCTURES)

    @property
    def HIERARCHICAL_ARCHETYPE(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_ARCHETYPE)

    @property
    def ENTRY_NODE(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_ENTRY_NODE)

    @property
    def HIERARCHICAL_NODE(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_NODE)

    @property
    def HIERARCHICAL_SAME_AS(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_SAME_AS)

    @property
    def HIERARCHICAL_HAS_PART(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_HAS_PART)

    @property
    def HIERARCHICAL_IS_PART_OF(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_IS_PART_OF)

    @property
    def HIERARCHICAL_BULK_COUNT(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_BULK_COUNT)

    @property
    def HIERARCHICAL_RELATIONSHIP(self) -> model.ExternalReference:
        return self.create_external_reference(self._HIERARCHICAL_RELATIONSHIP)

    @property
    def WOT_THING_DESCRIPTION(self) -> model.ExternalReference:
        return self.create_external_reference(self._WOT_TD)

    @property
    def WOT_ACTION_AFFORDANCE(self) -> model.ExternalReference:
        return self.create_external_reference(self._WOT_ACTION)

    @property
    def WOT_PROPERTY_AFFORDANCE(self) -> model.ExternalReference:
        return self.create_external_reference(self._WOT_PROPERTY)

    @property
    def WOT_INTERACTION_AFFORDANCE(self) -> model.ExternalReference:
        return self.create_external_reference(self._WOT_INTERACTION)

    @property
    def MQTT_PROTOCOL(self) -> model.ExternalReference:
        return self.create_external_reference(self._MQTT_PROTOCOL)

    @property
    def OPCUA_PROTOCOL(self) -> model.ExternalReference:
        return self.create_external_reference(self._OPCUA_PROTOCOL)

    @property
    def HTTP_PROTOCOL(self) -> model.ExternalReference:
        return self.create_external_reference(self._HTTP_PROTOCOL)

    @property
    def SKILLS_SUBMODEL(self) -> model.ExternalReference:
        return self.create_external_reference(self._SKILLS_SUBMODEL)

    @property
    def CAPABILITIES_SUBMODEL(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITIES_SUBMODEL)

    @property
    def CAPABILITY_SET(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITY_SET)

    @property
    def CAPABILITY_CONTAINER(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITY_CONTAINER)

    @property
    def CAPABILITY(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITY)

    @property
    def CAPABILITY_RELATIONS(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITY_RELATIONS)

    @property
    def CAPABILITY_REALIZED_BY(self) -> model.ExternalReference:
        return self.create_external_reference(self._CAPABILITY_REALIZED_BY)

    # Nameplate elements

    @property
    def NP_MANUFACTURER_NAME(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_MANUFACTURER_NAME)

    @property
    def NP_MANUFACTURER_PRODUCT_DESIGNATION(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_MANUFACTURER_PRODUCT_DESIGNATION)

    @property
    def NP_CONTACT_INFORMATION(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_CONTACT_INFORMATION)

    @property
    def NP_ORDER_CODE_OF_MANUFACTURER(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_ORDER_CODE_OF_MANUFACTURER)

    @property
    def NP_URI_OF_THE_PRODUCT(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_URI_OF_THE_PRODUCT)

    @property
    def NP_ADDRESS_STREET(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_ADDRESS_STREET)

    @property
    def NP_ADDRESS_ZIPCODE(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_ADDRESS_ZIPCODE)

    @property
    def NP_ADDRESS_CITY_TOWN(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_ADDRESS_CITY_TOWN)

    @property
    def NP_ADDRESS_NATIONAL_CODE(self) -> model.ExternalReference:
        return self.create_external_reference(self._NP_ADDRESS_NATIONAL_CODE)

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def create_external_reference(semantic_id: str) -> model.ExternalReference:
        return model.ExternalReference(
            (model.Key(
                type_=model.KeyTypes.GLOBAL_REFERENCE,
                value=semantic_id
            ),)
        )

    @staticmethod
    def create_model_reference(
        reference_chain: List[tuple],
        referred_type: type
    ) -> model.ModelReference:
        keys = tuple(
            model.Key(type_=key_type, value=value)
            for key_type, value in reference_chain
        )
        return model.ModelReference(keys, referred_type)

    @staticmethod
    def create_submodel_reference(submodel_id: str) -> model.ModelReference:
        return model.ModelReference(
            (model.Key(
                type_=model.KeyTypes.SUBMODEL,
                value=submodel_id
            ),),
            model.Submodel
        )

    @staticmethod
    def create_skill_semantic_id(skill_name: str, base_url: str = "https://smartproductionlab.aau.dk") -> model.ExternalReference:
        return SemanticIdFactory.create_external_reference(
            f"{base_url}/skills/{skill_name}"
        )


# ── Module-level constants (importable without instantiating the factory) ─────

SM_NAMEPLATE               = SemanticIdFactory._DIGITAL_NAMEPLATE_SUBMODEL
SM_HIERARCHICAL_STRUCTURES = SemanticIdFactory._HIERARCHICAL_STRUCTURES
SM_ASSET_INTERFACES        = SemanticIdFactory._ASSET_INTERFACES_SUBMODEL
SM_CAPABILITIES            = SemanticIdFactory._CAPABILITIES_SUBMODEL
SM_SKILLS                  = SemanticIdFactory._SKILLS_SUBMODEL
SM_OPERATIONAL_DATA        = SemanticIdFactory._VARIABLES_SUBMODEL
SM_PARAMETERS              = SemanticIdFactory._PARAMETERS_SUBMODEL

NP_MANUFACTURER_NAME                = SemanticIdFactory._NP_MANUFACTURER_NAME
NP_MANUFACTURER_PRODUCT_DESIGNATION = SemanticIdFactory._NP_MANUFACTURER_PRODUCT_DESIGNATION
NP_CONTACT_INFORMATION              = SemanticIdFactory._NP_CONTACT_INFORMATION
NP_ORDER_CODE_OF_MANUFACTURER       = SemanticIdFactory._NP_ORDER_CODE_OF_MANUFACTURER
NP_URI_OF_THE_PRODUCT               = SemanticIdFactory._NP_URI_OF_THE_PRODUCT
NP_ADDRESS_STREET                   = SemanticIdFactory._NP_ADDRESS_STREET
NP_ADDRESS_ZIPCODE                  = SemanticIdFactory._NP_ADDRESS_ZIPCODE
NP_ADDRESS_CITY_TOWN                = SemanticIdFactory._NP_ADDRESS_CITY_TOWN
NP_ADDRESS_NATIONAL_CODE            = SemanticIdFactory._NP_ADDRESS_NATIONAL_CODE

HS_ARCHETYPE   = SemanticIdFactory._HIERARCHICAL_ARCHETYPE
HS_ENTRY_NODE  = SemanticIdFactory._HIERARCHICAL_ENTRY_NODE
HS_NODE        = SemanticIdFactory._HIERARCHICAL_NODE
HS_HAS_PART    = SemanticIdFactory._HIERARCHICAL_HAS_PART
HS_IS_PART_OF  = SemanticIdFactory._HIERARCHICAL_IS_PART_OF
HS_SAME_AS     = SemanticIdFactory._HIERARCHICAL_SAME_AS
HS_BULK_COUNT  = SemanticIdFactory._HIERARCHICAL_BULK_COUNT

AID_INTERFACE            = SemanticIdFactory._ASSET_INTERFACES_INTERFACE
AID_ENDPOINT_METADATA    = SemanticIdFactory._AID_ENDPOINT_METADATA
AID_INTERACTION_METADATA = SemanticIdFactory._ASSET_INTERFACES_INTERACTION
