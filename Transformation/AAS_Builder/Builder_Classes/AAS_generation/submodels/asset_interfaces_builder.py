"""Asset Interfaces Description Submodel Builder for AAS generation."""

from typing import Dict, List, Optional
from basyx.aas import model


class AssetInterfacesBuilder:
    """
    Builder class for creating AssetInterfacesDescription submodel.

    This submodel describes the communication interfaces of an asset,
    primarily MQTT-based interfaces following W3C Thing Description patterns.
    """

    def __init__(self, base_url: str, semantic_factory, element_factory):
        """
        Initialize the AssetInterfacesDescription submodel builder.

        Args:
            base_url: Base URL for AAS identifiers
            semantic_factory: SemanticIdFactory instance for semantic IDs
            element_factory: AASElementFactory instance for element creation
        """
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    # Maps profile key → (AAS idShort, protocol semantic ID property name)
    _INTERFACE_TYPES = {
        'InterfaceMQTT':   ('InterfaceMQTT',   'MQTT_PROTOCOL'),
        'InterfaceOPCUA':  ('InterfaceOPCUA',  'OPCUA_PROTOCOL'),
        'InterfaceHTTP':   ('InterfaceHTTP',   'HTTP_PROTOCOL'),
    }

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        """
        Create the AssetInterfacesDescription submodel.

        Detects the interface type (MQTT, OPC UA, HTTP) from the profile config
        and builds the appropriate interface SMC.
        """
        interface_config = config.get('AID', {}) or config.get(
            'AssetInterfacesDescription', {}) or {}

        # Detect which interface type is present; fall back to MQTT if none found.
        iface_key = next(
            (k for k in self._INTERFACE_TYPES if k in interface_config),
            'InterfaceMQTT'
        )
        iface_id_short, protocol_sem_prop = self._INTERFACE_TYPES[iface_key]
        iface_config = interface_config.get(iface_key, {}) or {}

        interface_elements = []

        # title property
        title = iface_config.get('Title', system_id)
        interface_elements.append(
            self.element_factory.create_property(
                id_short="title",
                value=title,
                value_type=model.datatypes.String
            )
        )

        # EndpointMetadata — OPC-UA has different fields than MQTT/HTTP
        if iface_key == 'InterfaceOPCUA':
            endpoint_metadata = self._create_opcua_endpoint_metadata(iface_config)
        else:
            endpoint_metadata = self._create_mqtt_endpoint_metadata(iface_config)
        if endpoint_metadata:
            interface_elements.append(endpoint_metadata)

        # InteractionMetadata (shared structure for all protocols)
        interaction_metadata = iface_config.get('InteractionMetadata', {})
        interaction_elements = []

        actions = interaction_metadata.get('actions', [])
        if actions:
            actions_collection = self._create_actions_from_interaction_metadata(actions)
            if actions_collection:
                interaction_elements.append(actions_collection)

        properties = interaction_metadata.get('properties', [])
        if properties:
            properties_collection = self._create_properties_from_interaction_metadata(properties)
            if properties_collection:
                interaction_elements.append(properties_collection)

        if interaction_elements:
            interface_elements.append(self.element_factory.create_collection(
                id_short="InteractionMetadata",
                elements=interaction_elements,
                semantic_id=self.semantic_factory.INTERACTION_METADATA,
                supplemental_semantic_ids=[self.semantic_factory.WOT_INTERACTION_AFFORDANCE]
            ))

        protocol_sem_id = getattr(self.semantic_factory, protocol_sem_prop)
        interface_smc = self.element_factory.create_collection(
            id_short=iface_id_short,
            elements=interface_elements,
            semantic_id=self.semantic_factory.INTERFACE,
            supplemental_semantic_ids=[
                protocol_sem_id,
                self.semantic_factory.WOT_THING_DESCRIPTION
            ]
        )

        submodel = model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/AID",
            id_short="AID",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.ASSET_INTERFACES_DESCRIPTION,
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=[interface_smc]
        )

        return submodel

    def _create_mqtt_endpoint_metadata(self, mqtt_config: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create the EndpointMetadata collection for MQTT topics.

        Args:
            mqtt_config: MQTT configuration dictionary

        Returns:
            EndpointMetadata SubmodelElementCollection or None
        """
        endpoint_config = mqtt_config.get('EndpointMetadata', {})
        if not endpoint_config:
            return None

        endpoint_elements = []

        # Base endpoint
        if 'base' in endpoint_config:
            endpoint_elements.append(
                self.element_factory.create_property(
                    id_short="base",
                    value=endpoint_config['base'],
                    value_type=model.datatypes.String
                )
            )

        # Content type
        if 'contentType' in endpoint_config:
            endpoint_elements.append(
                self.element_factory.create_property(
                    id_short="contentType",
                    value=endpoint_config['contentType'],
                    value_type=model.datatypes.String
                )
            )

        # WoT TD requires security definitions and a security reference.
        # Add a minimal nosec scheme so the AID is structurally valid.
        nosec_smc = self.element_factory.create_collection(
            id_short="nosec_sc",
            elements=[
                self.element_factory.create_property(
                    id_short="scheme",
                    value="nosec",
                    value_type=model.datatypes.String,
                )
            ],
        )
        endpoint_elements.append(
            self.element_factory.create_collection(
                id_short="securityDefinitions",
                elements=[nosec_smc],
            )
        )
        endpoint_elements.append(
            model.SubmodelElementList(
                id_short="security",
                type_value_list_element=model.Property,
                value_type_list_element=model.datatypes.String,
                value=[
                    model.Property(
                        id_short=None,
                        value="nosec_sc",
                        value_type=model.datatypes.String,
                    )
                ],
            )
        )

        return self.element_factory.create_collection(
            id_short="EndpointMetadata",
            elements=endpoint_elements,
            semantic_id=self.semantic_factory.AID_ENDPOINT_METADATA,
        )

    def _create_opcua_endpoint_metadata(self, opcua_config: Dict) -> Optional[model.SubmodelElementCollection]:
        """Create EndpointMetadata for an OPC UA interface (IDTA 02017-1-1 §6.3)."""
        endpoint_config = opcua_config.get('EndpointMetadata', {})
        if not endpoint_config:
            return None

        endpoint_elements = []

        # OPC UA specific fields
        for field in ('protocol', 'encoding', 'base', 'port',
                      'security_mode', 'security_policy',
                      'namespace_uri', 'namespace_index'):
            if field in endpoint_config:
                endpoint_elements.append(
                    self.element_factory.create_property(
                        id_short=field,
                        value=str(endpoint_config[field]),
                        value_type=model.datatypes.String
                    )
                )

        # Minimal nosec security definitions (required by SHACL)
        nosec_smc = self.element_factory.create_collection(
            id_short="nosec_sc",
            elements=[
                self.element_factory.create_property(
                    id_short="scheme",
                    value="nosec",
                    value_type=model.datatypes.String,
                )
            ],
        )
        endpoint_elements.append(
            self.element_factory.create_collection(
                id_short="securityDefinitions",
                elements=[nosec_smc],
            )
        )
        endpoint_elements.append(
            model.SubmodelElementList(
                id_short="security",
                type_value_list_element=model.Property,
                value_type_list_element=model.datatypes.String,
                value=[
                    model.Property(
                        id_short=None,
                        value="nosec_sc",
                        value_type=model.datatypes.String,
                    )
                ],
            )
        )

        return self.element_factory.create_collection(
            id_short="EndpointMetadata",
            elements=endpoint_elements,
            semantic_id=self.semantic_factory.AID_ENDPOINT_METADATA,
        )

    def _create_actions_from_interaction_metadata(self, actions: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create Actions collection from interaction metadata.

        Args:
            actions: Dictionary of action name -> action config

        Returns:
            Actions SubmodelElementCollection or None
        """
        if not actions:
            return None

        action_elements = []

        # Actions is a dict with action names as keys
        for action_name, action_config in actions.items():

            action_props = []

            # Key/Title
            if 'key' in action_config:
                action_props.append(
                    self.element_factory.create_property(
                        id_short="Key",
                        value=action_config['key'],
                        value_type=model.datatypes.String
                    )
                )

            if 'title' in action_config:
                action_props.append(
                    self.element_factory.create_property(
                        id_short="Title",
                        value=action_config['title'],
                        value_type=model.datatypes.String
                    )
                )

            # Synchronous flag — AAS schema expects xsd:string, not boolean
            if 'synchronous' in action_config:
                action_props.append(
                    self.element_factory.create_property(
                        id_short="Synchronous",
                        value=str(action_config['synchronous']).lower(),
                        value_type=model.datatypes.String
                    )
                )

            # Input/Output schemas
            if 'input' in action_config:
                action_props.append(
                    self.element_factory.create_file(
                        id_short="input",
                        value=action_config['input'],
                        content_type="application/schema+json"
                    )
                )

            if 'output' in action_config:
                action_props.append(
                    self.element_factory.create_file(
                        id_short="output",
                        value=action_config['output'],
                        content_type="application/schema+json"
                    )
                )

            # Forms
            if 'forms' in action_config:
                forms_config = action_config['forms']
                form_elements = []

                for key, value in forms_config.items():
                    if key == 'response' and isinstance(value, dict):
                        # Response is a nested structure
                        response_elements = []
                        for resp_key, resp_value in value.items():
                            response_elements.append(
                                self.element_factory.create_property(
                                    id_short=resp_key,
                                    value=str(resp_value),
                                    value_type=model.datatypes.String
                                )
                            )
                        form_elements.append(
                            self.element_factory.create_collection(
                                id_short="response",
                                elements=response_elements
                            )
                        )
                    else:
                        form_elements.append(
                            self.element_factory.create_property(
                                id_short=key,
                                value=str(value),
                                value_type=model.datatypes.String
                            )
                        )

                if form_elements:
                    action_props.append(
                        self.element_factory.create_collection(
                            id_short="Forms",
                            elements=form_elements
                        )
                    )

            action_element = self.element_factory.create_collection(
                id_short=action_name,
                elements=action_props
            )
            action_elements.append(action_element)

        if not action_elements:
            return None

        return self.element_factory.create_collection(
            id_short="actions",
            elements=action_elements,
            semantic_id=self.semantic_factory.WOT_ACTION_AFFORDANCE
        )

    def _create_properties_from_interaction_metadata(self, properties: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create Properties collection from interaction metadata.

        Args:
            properties: Dictionary of property name -> property config

        Returns:
            Properties SubmodelElementCollection or None
        """
        if not properties:
            return None

        property_elements = []

        # Properties is a dict with property names as keys
        for prop_name, prop_config in properties.items():

            prop_elements = []

            # Key/Title
            if 'key' in prop_config:
                prop_elements.append(
                    self.element_factory.create_property(
                        id_short="Key",
                        value=prop_config['key'],
                        value_type=model.datatypes.String
                    )
                )

            if 'title' in prop_config:
                prop_elements.append(
                    self.element_factory.create_property(
                        id_short="Title",
                        value=prop_config['title'],
                        value_type=model.datatypes.String
                    )
                )

            # Output schema
            if 'output' in prop_config:
                prop_elements.append(
                    self.element_factory.create_file(
                        id_short="output",
                        value=prop_config['output'],
                        content_type="application/schema+json"
                    )
                )

            # Forms
            if 'forms' in prop_config:
                forms_config = prop_config['forms']
                form_elements = []

                for key, value in forms_config.items():
                    form_elements.append(
                        self.element_factory.create_property(
                            id_short=key,
                            value=str(value),
                            value_type=model.datatypes.String
                        )
                    )

                if form_elements:
                    prop_elements.append(
                        self.element_factory.create_collection(
                            id_short="Forms",
                            elements=form_elements
                        )
                    )

            property_element = self.element_factory.create_collection(
                id_short=prop_name,
                elements=prop_elements
            )
            property_elements.append(property_element)

        if not property_elements:
            return None

        return self.element_factory.create_collection(
            id_short="properties",
            elements=property_elements,
            semantic_id=self.semantic_factory.WOT_PROPERTY_AFFORDANCE
        )
