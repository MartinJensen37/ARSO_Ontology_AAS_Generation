"""Process AAS Submodel Builders.

This module provides builders for Process AAS specific submodels:
- ProcessInformation: General process metadata with product reference
- RequiredCapabilities: Capabilities required by the process with resource references
- Policy: Behavior tree policy reference
"""

from typing import Dict, List, Optional
from basyx.aas import model


class ProcessInformationSubmodelBuilder:
    """Builder for ProcessInformation submodel.

    Contains basic process metadata and a ReferenceElement to the product AAS.
    """

    SEMANTIC_ID = "https://smartproductionlab.aau.dk/submodels/ProcessInformation/1/0"

    def __init__(self, base_url: str, semantic_factory, element_factory):
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    def build(self, system_id: str, config: Dict) -> Optional[model.Submodel]:
        """Build ProcessInformation submodel from config.

        Expected config format:
            ProcessInformation:
                ProcessName: "Production of Human Growth Hormone"
                ProcessType: "AsepticFilling"
                CreatedAt: "2026-01-20T10:00:00Z"
                Status: "planned"
                ProductReference: "https://smartproductionlab.aau.dk/aas/HgHAAS"
        """
        process_info = config.get('ProcessInformation', {})
        if not process_info:
            return None

        elements = []

        # Simple string properties (excluding ProductReference - handled separately)
        string_props = ['ProcessName', 'ProcessType', 'CreatedAt', 'Status']
        for prop_name in string_props:
            value = process_info.get(prop_name)
            if value:
                elements.append(model.Property(
                    id_short=prop_name,
                    value_type=model.datatypes.String,
                    value=str(value)
                ))

        # ProductReference as ReferenceElement pointing to the Product AAS
        product_ref = process_info.get('ProductReference')
        if product_ref:
            elements.append(model.ReferenceElement(
                id_short="ProductReference",
                value=model.ModelReference(
                    key=(model.Key(
                        type_=model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                        value=product_ref
                    ),),
                    type_=model.AssetAdministrationShell
                ),
                description=model.MultiLanguageNameType(
                    {"en": "Reference to the product being produced"})
            ))

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/ProcessInformation",
            id_short="ProcessInformation",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                     value=self.SEMANTIC_ID),)
            ),
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=elements
        )


class RequiredCapabilitiesSubmodelBuilder:
    """Builder for the RequiredCapabilities submodel.

    Groups capabilities by type; each type is an SMC holding a Description and a
    References SMC of ReferenceElements to asset capabilities, so several assets
    can provide the same capability type.

    Accepts either the simplified `resources: {name: aas_id}` form or the legacy
    explicit `references: {name: {submodel_id, capability_path}}` form.
    """

    SEMANTIC_ID = "https://smartproductionlab.aau.dk/submodels/RequiredCapabilities/1/0"

    def __init__(self, base_url: str, semantic_factory, element_factory):
        """
        Initialize the builder.

        Args:
            base_url: Base URL for AAS identifiers
            semantic_factory: Factory for semantic IDs
            element_factory: Factory for AAS elements
        """
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    def build(self, system_id: str, config: Dict) -> Optional[model.Submodel]:
        """Build the RequiredCapabilities submodel from config.

        Args:
            system_id: Unique identifier for the system.
            config: Config dict; reads the 'RequiredCapabilities' section, mapping
                each capability name to {semantic_id, description, resources}.

        Returns:
            RequiredCapabilities submodel, or None if no capabilities are configured.
        """
        capabilities = config.get('RequiredCapabilities', {})
        if not capabilities:
            return None

        cap_collections = []

        for cap_name, cap_config in capabilities.items():
            if isinstance(cap_config, dict):
                cap_coll = self._build_capability_type(cap_name, cap_config)
                cap_collections.append(cap_coll)

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/RequiredCapabilities",
            id_short="RequiredCapabilities",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                     value=self.SEMANTIC_ID),)
            ),
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=cap_collections
        )

    def _build_capability_type(self, cap_name: str, cap_config: Dict) -> model.SubmodelElementCollection:
        """Build a capability type collection with description and references collection."""
        elements = []

        # Description property
        description = cap_config.get('description', '')
        if description:
            elements.append(model.Property(
                id_short="Description",
                value_type=model.datatypes.String,
                value=description
            ))

        # Check for new format (resources with AAS ID) or legacy format (references)
        resources = cap_config.get('resources', {})
        references = cap_config.get('references', {})

        ref_elements = []

        if resources:
            # New simplified format: derive capability reference from AAS ID
            for resource_name, aas_id in resources.items():
                ref_element = self._build_capability_reference_from_aas_id(
                    resource_name, aas_id, cap_name
                )
                if ref_element:
                    ref_elements.append(ref_element)
        elif references:
            # Legacy explicit format
            for resource_name, ref_config in references.items():
                ref_element = self._build_capability_reference(
                    resource_name, ref_config)
                if ref_element:
                    ref_elements.append(ref_element)

        if ref_elements:
            elements.append(model.SubmodelElementCollection(
                id_short="References",
                value=ref_elements
            ))

        # Semantic ID from capability type (decorates the collection)
        semantic_id = cap_config.get('semantic_id', '')
        semantic_ref = None
        if semantic_id:
            semantic_ref = model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value=semantic_id),)
            )

        return model.SubmodelElementCollection(
            id_short=cap_name,
            value=elements,
            semantic_id=semantic_ref
        )

    def _build_capability_reference_from_aas_id(
        self,
        resource_name: str,
        aas_id: str,
        capability_name: str
    ) -> Optional[model.ReferenceElement]:
        """Build a ReferenceElement by deriving the capability path from an AAS ID.

        Args:
            resource_name: Resource name, used as id_short.
            aas_id: AAS ID URL, e.g. https://.../aas/imaLoadingSystemAAS
            capability_name: Capability name, e.g. "Loading".

        Returns:
            ReferenceElement pointing at the capability, or None if parsing fails.
        """
        # Extract idShort from AAS ID (last segment after /aas/)
        id_short = self._extract_id_short_from_aas_id(aas_id)
        if not id_short:
            import logging
            logging.getLogger(__name__).warning(
                f"Could not extract idShort from AAS ID: {aas_id}"
            )
            return None

        # Construct submodel ID and capability path
        submodel_id = f"{self.base_url}/submodels/instances/{id_short}/Capabilities"
        capability_path = ["CapabilitySet",
                           f"{capability_name}Container", capability_name]

        return self._build_reference_element(resource_name, submodel_id, capability_path)

    def _extract_id_short_from_aas_id(self, aas_id: str) -> Optional[str]:
        """Extract idShort from an AAS ID URL.

        Args:
            aas_id: AAS ID URL, e.g. https://.../aas/imaLoadingSystem

        Returns:
            idShort with the conventional 'AAS' suffix, or None if parsing fails.
        """
        if not aas_id:
            return None

        # Try to extract from /aas/ pattern
        if '/aas/' in aas_id:
            extracted = aas_id.split('/aas/')[-1].rstrip('/')
        else:
            # Fallback: use last path segment
            extracted = aas_id.rstrip('/').split('/')[-1]

        # Ensure AAS suffix is present (convention: idShort = systemName + "AAS")
        if extracted and not extracted.endswith('AAS'):
            extracted = extracted + 'AAS'

        return extracted

    def _build_capability_reference(self, resource_name: str, cap_ref_config: Dict) -> Optional[model.ReferenceElement]:
        """Build ReferenceElement from explicit config (legacy format).

        Args:
            resource_name: Name of the resource (used as id_short)
            cap_ref_config: Dictionary with:
                - submodel_id: Full ID of the OfferedCapabilityDescription submodel
                - capability_path: List of idShorts to reach the capability 
                                   e.g., ["CapabilitySet", "DispensingContainer", "Dispensing"]
        """
        submodel_id = cap_ref_config.get('submodel_id')
        capability_path = cap_ref_config.get('capability_path', [])

        if not submodel_id:
            return None

        return self._build_reference_element(resource_name, submodel_id, capability_path)

    def _build_reference_element(
        self,
        resource_name: str,
        submodel_id: str,
        capability_path: List[str]
    ) -> model.ReferenceElement:
        """Build ReferenceElement with key chain to capability.

        Args:
            resource_name: Name of the resource (used as id_short)
            submodel_id: Full ID of the OfferedCapabilityDescription submodel
            capability_path: List of idShorts to reach the capability

        Returns:
            ReferenceElement pointing to the capability
        """
        # Build the key chain
        keys = [
            model.Key(
                type_=model.KeyTypes.SUBMODEL,
                value=submodel_id
            )
        ]

        # Add keys for the path to the capability element
        for i, path_element in enumerate(capability_path):
            # Last element is the Capability, others are SubmodelElementCollections
            if i == len(capability_path) - 1:
                key_type = model.KeyTypes.CAPABILITY
            else:
                key_type = model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION

            keys.append(model.Key(
                type_=key_type,
                value=path_element
            ))

        return model.ReferenceElement(
            id_short=resource_name,
            value=model.ModelReference(
                key=tuple(keys),
                type_=model.Capability
            )
        )


class PolicySubmodelBuilder:
    """Builder for Policy submodel (Behavior Tree reference)."""

    SEMANTIC_ID = "https://smartproductionlab.aau.dk/submodels/Policy/1/0"

    def __init__(self, base_url: str, semantic_factory, element_factory):
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    def build(self, system_id: str, config: Dict) -> Optional[model.Submodel]:
        """Build Policy submodel from config.

        Expected config format:
            Policy:
                semantic_id: "https://smartproductionlab.aau.dk/submodels/Policy/1/0"
                BehaviorTree:
                    File: "https://example.com/policy/production.xml"
                    contentType: "application/xml"
                    description: "Production behavior tree policy"
        """
        policy = config.get('Policy', {})
        if not policy:
            return None

        elements = []

        # Behavior Tree reference
        policy_config = policy.get('Policy', {})
        if policy_config:
            policy_file = policy_config.get('File', '')
            content_type = policy_config.get('contentType', 'application/xml')
            description = policy_config.get('description', '')

            # Use File element for the policy reference
            elements.append(model.File(
                id_short="Policy",
                content_type=content_type,
                semantic_id=policy_config.get('semanticId', ''),
                value=policy_file,
                description=model.MultiLanguageNameType(
                    {"en": description}) if description else None
            ))

        # Policy semantic ID
        policy_semantic = policy.get('semantic_id', self.SEMANTIC_ID)

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/Policy",
            id_short="Policy",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=model.ExternalReference(
                key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE,
                     value=policy_semantic),)
            ),
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=elements
        )
