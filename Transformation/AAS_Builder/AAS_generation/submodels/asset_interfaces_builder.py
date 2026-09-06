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

    # Legacy fixed key names -> protocol, for profiles/LLM output that don't
    # set an explicit 'protocol' field on the interface (see _infer_protocol).
    _LEGACY_KEY_PROTOCOL = {
        'InterfaceMQTT':  'MQTT',
        'InterfaceOPCUA': 'OPCUA',
        'InterfaceHTTP':  'HTTP',
        'InterfaceMODBUS': 'MODBUS',
    }

    # protocol -> semantic_factory property name for its WoT binding supplementalSemanticId
    _PROTOCOL_SEMANTIC_PROP = {
        'MQTT':   'MQTT_PROTOCOL',
        'OPCUA':  'OPCUA_PROTOCOL',
        'HTTP':   'HTTP_PROTOCOL',
        'MODBUS': 'MODBUS_PROTOCOL',
    }

    @staticmethod
    def _as_named_dict(value) -> Dict:
        """Coerce InteractionMetadata / actions / properties / events into the
        {name: {...}} shape these builders expect.

        An LLM will sometimes emit a list of entries instead (a plausible
        alternate encoding, each item carrying its own name), or occasionally
        a bare "[VERIFY: ...]" placeholder string for a whole section. Rather
        than crash on the first .get()/.items() call downstream, reinterpret
        a list using each item's own 'name' or 'key' field as the dict key
        (dropping only entries with neither), and treat anything else
        unrecognized as absent.
        """
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            result: Dict = {}
            for idx, item in enumerate(value):
                if not isinstance(item, dict):
                    continue
                name = item.get('name') or item.get('key') or f"Item{idx + 1}"
                result[name] = item
            return result
        return {}

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        """
        Create the AssetInterfacesDescription submodel.

        arso:InterfaceSMC (aid.ttl) is identified by semanticId, not a fixed
        idShort -- "one per communication interface" is explicitly anticipated,
        and idShort is user-defined. So every entry under AID in the profile
        becomes its own Interface SMC here (not just the first one matched
        against a hardcoded key), keyed by whatever name the caller gave it.
        """
        interface_config = config.get('AID', {}) or config.get(
            'AssetInterfacesDescription', {}) or {}
        if not isinstance(interface_config, dict):
            # An LLM occasionally emits the whole section as a bare
            # "[VERIFY: ...]" string instead of an object; treat as absent.
            interface_config = {}

        entries = {
            k: v for k, v in interface_config.items() if isinstance(v, dict)
        }
        if not entries:
            # Preserve the old scaffold behavior: an AID submodel with one
            # empty default interface rather than no interfaces at all.
            entries = {'InterfaceMQTT': {}}

        interface_smcs = [
            self._build_one_interface(iface_key, iface_config, system_id)
            for iface_key, iface_config in entries.items()
        ]

        submodel = model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/AID",
            id_short="AID",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.ASSET_INTERFACES_DESCRIPTION,
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=interface_smcs
        )

        return submodel

    def _infer_protocol(self, iface_key: str, iface_config: Dict) -> str:
        """Prefer an explicit 'protocol' field (set by the canvas UI); fall
        back to sniffing legacy fixed key names (set by LLM-generated
        profiles that predate the per-interface 'protocol' field)."""
        explicit = iface_config.get('protocol')
        if explicit in self._PROTOCOL_SEMANTIC_PROP:
            return explicit
        return self._LEGACY_KEY_PROTOCOL.get(iface_key, 'MQTT')

    def _build_one_interface(self, iface_key: str, iface_config: Dict, system_id: str) -> model.SubmodelElementCollection:
        protocol = self._infer_protocol(iface_key, iface_config)
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

        # EndpointMetadata — OPC-UA has a different field set than MQTT/HTTP/MODBUS
        if protocol == 'OPCUA':
            endpoint_metadata = self._create_opcua_endpoint_metadata(iface_config)
        else:
            endpoint_metadata = self._create_mqtt_endpoint_metadata(iface_config)
        if endpoint_metadata:
            interface_elements.append(endpoint_metadata)

        # InteractionMetadata (shared structure for all protocols)
        interaction_metadata = self._as_named_dict(iface_config.get('InteractionMetadata', {}))
        interaction_elements = []

        actions = self._as_named_dict(interaction_metadata.get('actions', {}))
        if actions:
            actions_collection = self._create_actions_from_interaction_metadata(actions)
            if actions_collection:
                interaction_elements.append(actions_collection)

        properties = self._as_named_dict(interaction_metadata.get('properties', {}))
        if properties:
            properties_collection = self._create_properties_from_interaction_metadata(properties)
            if properties_collection:
                interaction_elements.append(properties_collection)

        events = self._as_named_dict(interaction_metadata.get('events', {}))
        if events:
            events_collection = self._create_events_from_interaction_metadata(events)
            if events_collection:
                interaction_elements.append(events_collection)

        if interaction_elements:
            interface_elements.append(self.element_factory.create_collection(
                id_short="InteractionMetadata",
                elements=interaction_elements,
                semantic_id=self.semantic_factory.INTERACTION_METADATA,
                supplemental_semantic_ids=[self.semantic_factory.WOT_INTERACTION_AFFORDANCE]
            ))

        protocol_sem_prop = self._PROTOCOL_SEMANTIC_PROP[protocol]
        protocol_sem_id = getattr(self.semantic_factory, protocol_sem_prop)
        return self.element_factory.create_collection(
            id_short=iface_key,
            elements=interface_elements,
            semantic_id=self.semantic_factory.INTERFACE,
            supplemental_semantic_ids=[
                protocol_sem_id,
                self.semantic_factory.WOT_THING_DESCRIPTION
            ]
        )

    def _create_mqtt_endpoint_metadata(self, mqtt_config: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create the EndpointMetadata collection for MQTT/HTTP/MODBUS interfaces.

        Args:
            mqtt_config: interface configuration dictionary

        Returns:
            EndpointMetadata SubmodelElementCollection or None
        """
        endpoint_config = mqtt_config.get('EndpointMetadata', {})
        if not isinstance(endpoint_config, dict) or not endpoint_config:
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

        # MODBUS byte/word order — set once per interface (not per-form,
        # since it describes the device's register layout, not one operation).
        for field in ('modv_mostSignificantByte', 'modv_mostSignificantWord'):
            if field in endpoint_config:
                endpoint_elements.append(
                    self.element_factory.create_property(
                        id_short=field,
                        value=str(endpoint_config[field]),
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
        if not isinstance(endpoint_config, dict) or not endpoint_config:
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
        actions = self._as_named_dict(actions)
        if not actions:
            return None

        action_elements = []

        # Actions is a dict with action names as keys
        for action_name, action_config in actions.items():
            if not isinstance(action_config, dict):
                action_config = {}

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
            if isinstance(action_config.get('forms'), dict):
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
        properties = self._as_named_dict(properties)
        if not properties:
            return None

        property_elements = []

        # Properties is a dict with property names as keys
        for prop_name, prop_config in properties.items():
            if not isinstance(prop_config, dict):
                prop_config = {}

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
            if isinstance(prop_config.get('forms'), dict):
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

    def _create_events_from_interaction_metadata(self, events: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create Events collection from interaction metadata (arso:EventsSMC,
        WoT EventAffordances — subscribable notifications; key/title/forms
        only, no input/output schema like actions/properties have).

        Args:
            events: Dictionary of event name -> event config

        Returns:
            Events SubmodelElementCollection or None
        """
        events = self._as_named_dict(events)
        if not events:
            return None

        event_elements = []

        for event_name, event_config in events.items():
            if not isinstance(event_config, dict):
                event_config = {}
            elements = []

            if 'key' in event_config:
                elements.append(
                    self.element_factory.create_property(
                        id_short="Key",
                        value=event_config['key'],
                        value_type=model.datatypes.String
                    )
                )

            if 'title' in event_config:
                elements.append(
                    self.element_factory.create_property(
                        id_short="Title",
                        value=event_config['title'],
                        value_type=model.datatypes.String
                    )
                )

            if isinstance(event_config.get('forms'), dict):
                forms_config = event_config['forms']
                form_elements = [
                    self.element_factory.create_property(
                        id_short=key,
                        value=str(value),
                        value_type=model.datatypes.String
                    )
                    for key, value in forms_config.items()
                ]
                if form_elements:
                    elements.append(
                        self.element_factory.create_collection(
                            id_short="Forms",
                            elements=form_elements
                        )
                    )

            event_elements.append(
                self.element_factory.create_collection(
                    id_short=event_name,
                    elements=elements
                )
            )

        if not event_elements:
            return None

        return self.element_factory.create_collection(
            id_short="events",
            elements=event_elements,
            semantic_id=self.semantic_factory.WOT_EVENT_AFFORDANCE
        )
