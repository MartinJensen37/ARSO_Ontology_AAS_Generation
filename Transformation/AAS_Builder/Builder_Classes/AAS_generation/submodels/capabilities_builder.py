"""Capabilities Submodel Builder for AAS generation."""

from typing import Dict, List, Any, Optional
from basyx.aas import model


class CapabilitiesSubmodelBuilder:
    """
    Builder class for creating Capabilities (OfferedCapabilityDescription) submodel.

    The Capabilities submodel describes what capabilities the asset offers
    and which skills realize those capabilities.
    """

    def __init__(self, base_url: str, semantic_factory, element_factory):
        """
        Initialize the Capabilities submodel builder.

        Args:
            base_url: Base URL for AAS identifiers
            semantic_factory: SemanticIdFactory instance for semantic IDs
            element_factory: AASElementFactory instance for element creation
        """
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        """
        Create the OfferedCapabilityDescription submodel.

        Args:
            system_id: Unique identifier for the system
            config: Configuration dictionary containing Capabilities section

        Returns:
            Capabilities submodel instance
        """
        capabilities = config.get('Capabilities', {}) or {}
        if isinstance(capabilities, list):
            capabilities = {item['name']: item for item in capabilities if isinstance(item, dict) and 'name' in item}
        capability_containers = []

        # Handle dict format: Capabilities: { CapName: {...}, ... }
        for cap_name, cap_config in capabilities.items():
            if not isinstance(cap_config, dict):
                cap_config = {"description": str(cap_config)} if cap_config else {}
            container = self._create_capability_container(
                system_id, cap_name, cap_config
            )
            if container:
                capability_containers.append(container)

        # Create CapabilitySet
        capability_set = self.element_factory.create_collection(
            id_short="CapabilitySet",
            elements=capability_containers,
            semantic_id=self.semantic_factory.CAPABILITY_SET
        )

        # Create submodel
        submodel = model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/Capabilities",
            id_short="Capabilities",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.CAPABILITIES_SUBMODEL,
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=[capability_set]
        )

        return submodel

    def _create_capability_container(self, system_id: str, cap_name: str,
                                     cap_config: Dict) -> model.SubmodelElementCollection:
        """
        Create a capability container with all its elements.

        Args:
            system_id: System identifier
            cap_name: Name of the capability
            cap_config: Configuration for the capability

        Returns:
            SubmodelElementCollection representing the capability container
        """
        container_elements = []

        # Add Capability element with semantic_id from config if specified
        # This enables capability matching based on semantic identifiers
        capability_semantic_id_value = cap_config.get(
            'semantic_id', f"{self.base_url}/Capability/{cap_name}")
        capability_semantic_id = capability_semantic_id_value
        if capability_semantic_id:
            # Convert string semantic_id from config to proper ExternalReference
            from ..core.semantic_ids import SemanticIdFactory
            capability_semantic_id = SemanticIdFactory.create_external_reference(
                capability_semantic_id)
        else:
            capability_semantic_id = self.semantic_factory.CAPABILITY

        # Converter compatibility: expose semantic trace as explicit Property in container
        container_elements.append(
            self.element_factory.create_property(
                id_short="SemanticId",
                value=capability_semantic_id_value,
                value_type=model.datatypes.String,
            )
        )

        container_elements.append(
            self.element_factory.create_capability(
                id_short=cap_name,
                semantic_id=capability_semantic_id
            )
        )

        # Add Comment if present
        if 'comment' in cap_config:
            container_elements.append(
                self.element_factory.create_multi_language_property(
                    id_short="Comment",
                    text=cap_config['comment']
                )
            )

        # Add CapabilityRelations only if there are relations defined
        # This avoids "empty collection" warnings in BaSyx UI
        capability_relations = cap_config.get('relations', [])
        if capability_relations:
            relation_elements = self._create_capability_relations(
                system_id, cap_name, cap_config, capability_relations
            )
            if relation_elements:
                container_elements.append(
                    self.element_factory.create_collection(
                        id_short="CapabilityRelations",
                        elements=relation_elements,
                        semantic_id=self.semantic_factory.CAPABILITY_RELATIONS
                    )
                )

        # Add realizedBy relationships to skills
        realized_by_list = self._create_realized_by_list(
            system_id, cap_name, cap_config
        )
        if realized_by_list:
            container_elements.append(realized_by_list)

        # Add PropertySet if present
        property_set = self._create_property_set(cap_config)
        if property_set:
            container_elements.append(property_set)

        # Create capability container
        return self.element_factory.create_collection(
            id_short=cap_config.get('id_short', cap_name + 'Container'),
            elements=container_elements,
            semantic_id=self.semantic_factory.CAPABILITY_CONTAINER,
            description=cap_config.get('description', '')
        )

    def _create_realized_by_list(self, system_id: str, cap_name: str,
                                 cap_config: Dict) -> Optional[model.SubmodelElementList]:
        """
        Create the realizedBy SubmodelElementList.

        Args:
            system_id: System identifier
            cap_name: Name of the capability
            cap_config: Configuration for the capability

        Returns:
            SubmodelElementList of relationships to skills, or None if no realizedBy
        """
        realized_by = cap_config.get('realizedBy')
        if not realized_by:
            return None

        # Handle both single string and list of strings
        if isinstance(realized_by, str):
            skill_names = [realized_by]
        else:
            skill_names = realized_by

        realized_by_elements = []
        for skill_name in skill_names:
            # Create relationship element pointing to skill
            # id_short=None for SubmodelElementList items (constraint AASd-120)
            rel_element = self.element_factory.create_relationship(
                id_short=None,
                first=model.ModelReference(
                    (model.Key(
                        type_=model.KeyTypes.SUBMODEL,
                        value=f"{self.base_url}/submodels/instances/{system_id}/Capabilities"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value="CapabilitySet"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value=cap_config.get(
                            'id_short', cap_name + 'Container')
                    )),
                    model.SubmodelElementCollection
                ),
                second=model.ModelReference(
                    (model.Key(
                        type_=model.KeyTypes.SUBMODEL,
                        value=f"{self.base_url}/submodels/instances/{system_id}/Skills"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value=skill_name
                    )),
                    model.SubmodelElementCollection
                )
            )
            realized_by_elements.append(rel_element)

        return self.element_factory.create_submodel_element_list(
            id_short="realizedBy",
            type_value_list_element=model.RelationshipElement,
            value=realized_by_elements,
            semantic_id=self.semantic_factory.CAPABILITY_REALIZED_BY
        )

    def _create_capability_relations(self, system_id: str, cap_name: str,
                                     cap_config: Dict,
                                     relations: List[Any]) -> List[model.SubmodelElement]:
        """
        Create capability relation elements.

        Capability relations describe relationships between capabilities,
        such as requires, isPartOf, isComposedOf, etc.

        Args:
            system_id: System identifier
            cap_name: Name of the capability
            cap_config: Configuration for the capability
            relations: List of relation configurations

        Returns:
            List of SubmodelElements representing the relations
        """
        relation_elements = []
        for idx, relation in enumerate(relations):
            if not isinstance(relation, dict):
                continue

            relation_type = relation.get('type', 'requires')
            target_capability = relation.get('target')

            if not target_capability:
                continue

            # Create a relationship element for each relation
            rel_element = self.element_factory.create_relationship(
                id_short=f"{relation_type}_{idx}",
                first=model.ModelReference(
                    (model.Key(
                        type_=model.KeyTypes.SUBMODEL,
                        value=f"{self.base_url}/submodels/instances/{system_id}/Capabilities"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value="CapabilitySet"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value=cap_config.get(
                            'id_short', cap_name + 'Container')
                    )),
                    model.SubmodelElementCollection
                ),
                second=model.ModelReference(
                    (model.Key(
                        type_=model.KeyTypes.SUBMODEL,
                        value=f"{self.base_url}/submodels/instances/{system_id}/Capabilities"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value="CapabilitySet"
                    ),
                        model.Key(
                        type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                        value=target_capability
                    )),
                    model.SubmodelElementCollection
                )
            )
            relation_elements.append(rel_element)

        return relation_elements

    def _create_property_set(self, cap_config: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create the PropertySet collection.

        Args:
            cap_config: Configuration for the capability

        Returns:
            SubmodelElementCollection for PropertySet, or None if no properties
        """
        if 'properties' not in cap_config or not cap_config['properties']:
            return None

        property_elements = []
        for prop in cap_config['properties']:
            prop_container = self._create_property_container(prop)
            if prop_container:
                property_elements.append(prop_container)

        if not property_elements:
            return None

        return self.element_factory.create_collection(
            id_short="PropertySet",
            elements=property_elements
        )

    def _create_property_container(self, prop: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create a property container for a capability property.

        Args:
            prop: Property configuration dictionary

        Returns:
            SubmodelElementCollection for the property, or None if invalid
        """
        prop_container_elements = []

        # Add Comment if description is present and not empty
        if 'description' in prop and prop['description']:
            prop_container_elements.append(
                self.element_factory.create_multi_language_property(
                    id_short="Comment",
                    text=prop['description']
                )
            )

        # Add Property value or range
        if 'min' in prop and 'max' in prop:
            prop_container_elements.append(
                self.element_factory.create_range(
                    id_short=prop['name'],
                    min_value=float(prop['min']),
                    max_value=float(prop['max']),
                    value_type=model.datatypes.Double
                )
            )
        elif 'value' in prop:
            prop_container_elements.append(
                self.element_factory.create_property(
                    id_short=prop['name'],
                    value=prop['value'],
                    value_type=model.datatypes.String
                )
            )

        if not prop_container_elements:
            return None

        return self.element_factory.create_collection(
            id_short=f"PropertyContainer_{prop['name']}",
            elements=prop_container_elements
        )
