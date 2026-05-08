"""Parameters Submodel Builder for AAS generation."""

from typing import Dict, List, Optional
from basyx.aas import model

from ..core.schema_handler import SchemaHandler


class ParametersSubmodelBuilder:
    """
    Builder class for creating Parameters submodel.

    The Parameters submodel contains collections of parameter definitions
    with their properties and optional interface references.

    Parameters are similar to Variables but represent writable values
    that can be set via MQTT interfaces (using input schemas).
    """

    def __init__(self, base_url: str, semantic_factory, element_factory=None,
                 schema_handler: SchemaHandler = None):
        """
        Initialize the Parameters submodel builder.

        Args:
            base_url: Base URL for AAS identifiers
            semantic_factory: SemanticIdFactory instance for semantic IDs
            element_factory: AASElementFactory instance for element creation
            schema_handler: Optional SchemaHandler for schema-driven field extraction
        """
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory
        self.schema_handler = schema_handler or SchemaHandler()
        self.current_system_id = None
        self._properties_cache = None

    def build(self, system_id: str, config: Dict, properties: List[Dict] = None) -> model.Submodel:
        """
        Create the Parameters submodel.

        Args:
            system_id: Unique identifier for the system
            config: Configuration dictionary containing Parameters section
            properties: Optional list of interface property dicts with schema URLs

        Returns:
            Parameters submodel instance
        """
        self.current_system_id = system_id
        parameters_config = config.get('Parameters', {}) or {}
        parameter_elements = []

        # Build property lookup for schema-driven field extraction
        self._properties_cache = {}
        if properties:
            self._properties_cache = {p['name']: p for p in properties}

        # Handle dict format: Parameters: { ParamName: {...}, ... }
        for param_name, param_config in parameters_config.items():
            param_collection = self._create_parameter_collection(
                param_name, param_config or {})
            if param_collection:
                parameter_elements.append(param_collection)

        submodel = model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/Parameters",
            id_short="Parameters",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.PARAMETERS_SUBMODEL,
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=parameter_elements
        )

        return submodel

    def _create_parameter_collection(self, param_name: str,
                                     param_config: Dict) -> Optional[model.SubmodelElementCollection]:
        """
        Create a parameter collection from config format.

        Field names and types are derived from the MQTT schema if an
        InterfaceReference is present and the referenced property has an input schema.

        If a 'Field' is specified in the config, only that field from the schema
        is included.

        Args:
            param_name: Name of the parameter
            param_config: Configuration dictionary for the parameter

        Returns:
            SubmodelElementCollection for the parameter or None if no elements
        """
        elements = []

        # Add semantic ID if present
        semantic_id = param_config.get('semanticId')
        interface_ref = param_config.get('InterfaceReference')
        # Optional: extract only this field
        specific_field = param_config.get('Field')

        # Try to get fields from schema if interface reference exists
        # Parameters use 'input' schema (for setting values)
        schema_fields = {}
        if interface_ref and self._properties_cache:
            prop = self._properties_cache.get(interface_ref)
            if prop and prop.get('schema'):
                all_schema_fields = self.schema_handler.extract_data_fields(
                    prop['schema'])

                # If a specific field is requested, filter to just that field
                if specific_field and specific_field in all_schema_fields:
                    schema_fields = {
                        specific_field: all_schema_fields[specific_field]}
                else:
                    schema_fields = all_schema_fields

        # Use schema-derived fields if available, otherwise fall back to config
        if schema_fields and self.element_factory:
            for field_name, field_def in schema_fields.items():
                # Get default value from config if provided, otherwise use schema default
                config_value = None
                for key, value in param_config.items():
                    if key not in ['semanticId', 'InterfaceReference', 'Field'] and key == field_name:
                        config_value = value
                        break

                value = config_value if config_value is not None else field_def['default_value']
                value_type = field_def['aas_type']

                elements.append(
                    self.element_factory.create_property(
                        id_short=field_name,
                        value_type=value_type,
                        value=value
                    )
                )
        elif self.element_factory:
            # Fallback: use fields defined directly in config
            for key, value in param_config.items():
                if key in ['semanticId', 'InterfaceReference', 'Field']:
                    continue

                # Determine value type
                if isinstance(value, bool):
                    value_type = model.datatypes.Boolean
                elif isinstance(value, int):
                    value_type = model.datatypes.Int
                elif isinstance(value, float):
                    value_type = model.datatypes.Double
                else:
                    value_type = model.datatypes.String
                    value = str(value)

                elements.append(
                    self.element_factory.create_property(
                        id_short=key,
                        value_type=value_type,
                        value=value
                    )
                )

        # Add InterfaceReference as ReferenceElement if present
        if interface_ref:
            ref_element = self._create_interface_reference(interface_ref)
            if ref_element:
                elements.append(ref_element)

        if not elements:
            return None

        # Build semantic ID for collection if provided
        collection_semantic_id = None
        if semantic_id:
            collection_semantic_id = self.semantic_factory.create_external_reference(
                semantic_id)

        return self.element_factory.create_collection(
            id_short=param_name,
            elements=elements,
            semantic_id=collection_semantic_id
        )

    def _create_interface_reference(self, interface_ref_name: str) -> Optional[model.ReferenceElement]:
        """
        Create an interface reference element.

        Args:
            interface_ref_name: Name of the interface property to reference

        Returns:
            ReferenceElement pointing to the interface property
        """
        if not self.element_factory:
            return None

        return self.element_factory.create_reference_element(
            id_short="InterfaceReference",
            reference=model.ModelReference(
                (model.Key(
                    type_=model.KeyTypes.SUBMODEL,
                    value=f"{self.base_url}/submodels/instances/{self.current_system_id}/AID"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value="InterfaceMQTT"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value="InteractionMetadata"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value="properties"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value=interface_ref_name
                )),
                model.SubmodelElementCollection
            ),
            semantic_id=self.semantic_factory.INTERFACE_REFERENCE
        )
