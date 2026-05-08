"""Skills Submodel Builder for AAS generation."""

from typing import Dict, List, Optional
from basyx.aas import model


class SkillsSubmodelBuilder:
    """
    Builder class for creating Skills submodel.

    The Skills submodel contains Operations derived from action interfaces,
    each wrapped in a SubmodelElementCollection with interface references.
    """

    def __init__(self, base_url: str, delegation_base_url: Optional[str],
                 semantic_factory, element_factory, schema_handler):
        """
        Initialize the Skills submodel builder.

        Args:
            base_url: Base URL for AAS identifiers
            delegation_base_url: Base URL for operation delegation service
            semantic_factory: SemanticIdFactory instance for semantic IDs
            element_factory: AASElementFactory instance for element creation
            schema_handler: SchemaHandler instance for schema processing
        """
        self.base_url = base_url
        self.delegation_base_url = delegation_base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory
        self.schema_handler = schema_handler

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        """
        Create the Skills submodel with Operations derived from action interfaces.

        Each operation is wrapped in a SubmodelElementCollection that also contains
        a reference to its corresponding action interface.

        The operations are generated from:
        - Explicit Skills configuration in YAML (if provided)
        - OR automatically from action interfaces in AssetInterfacesDescription

        Args:
            system_id: Unique identifier for the system
            config: Configuration dictionary

        Returns:
            Skills submodel with Operations wrapped in SubmodelElementCollections
        """
        skills_config = config.get('Skills', {}) or {}
        if isinstance(skills_config, list):
            skills_config = {item['name']: item for item in skills_config if isinstance(item, dict) and 'name' in item}
        skill_elements = []

        # Get action interfaces from AID — detect interface type automatically
        interface_config = config.get('AID', {}) or config.get(
            'AssetInterfacesDescription', {}) or {}
        _iface_keys = ('InterfaceMQTT', 'InterfaceOPCUA', 'InterfaceHTTP')
        iface_id_short = next((k for k in _iface_keys if k in interface_config), 'InterfaceMQTT')
        iface_config = interface_config.get(iface_id_short, {}) or {}
        interaction_metadata = iface_config.get('InteractionMetadata', {}) or {}
        actions = interaction_metadata.get('actions', {}) or {}

        # Actions is already a dict with action names as keys
        action_map = actions

        # If explicit Skills are configured, use them
        if skills_config:
            for skill_name, skill_data in skills_config.items():
                if not isinstance(skill_data, dict):
                    skill_data = {"description": str(skill_data)}
                skill_collection = self._create_skill_collection(
                    skill_name, skill_data, action_map, system_id, iface_id_short
                )
                if skill_collection:
                    skill_elements.append(skill_collection)

        # CCType requires exactly one Interfaces, Skills, and Errors container
        # at the submodel level (cardinality 1 each, may be empty).
        interfaces_smc = self.element_factory.create_collection(
            id_short="Interfaces", elements=[]
        )
        skills_smc = self.element_factory.create_collection(
            id_short="Skills", elements=skill_elements
        )
        errors_smc = self.element_factory.create_collection(
            id_short="Errors", elements=[]
        )

        # Create submodel
        submodel = model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/Skills",
            id_short="Skills",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.SKILLS_SUBMODEL,
            administration=model.AdministrativeInformation(
                version="1", revision="0"),
            submodel_element=[interfaces_smc, skills_smc, errors_smc]
        )

        return submodel

    def _create_skill_collection(self, skill_name: str, skill_data: Dict,
                                 action_map: Dict, system_id: str,
                                 iface_id_short: str = 'InterfaceMQTT') -> Optional[model.SubmodelElementCollection]:
        """
        Create a skill collection with operation and interface reference.

        Args:
            skill_name: Name of the skill
            skill_data: Configuration for the skill
            action_map: Map of action names to action configs
            system_id: System identifier

        Returns:
            SubmodelElementCollection containing the skill operation
        """
        # Get the interface name for this skill
        interface_name = skill_data.get('interface', skill_name)
        elements = []
        is_async = False

        skill_semantic_id = skill_data.get(
            'semantic_id', f"{self.base_url}/skills/{skill_name}")
        elements.append(
            self.element_factory.create_property(
                id_short="SemanticId",
                value=skill_semantic_id,
                value_type=model.datatypes.String,
            )
        )

        # Create the Operation from the linked action interface
        if interface_name and interface_name in action_map:
            action_config = action_map[interface_name]
            operation = self._create_operation_from_action(
                skill_name, action_config, system_id
            )
            elements.append(operation)

            # Determine if this is an asynchronous operation
            is_async = self._is_async_operation(action_config)

            # Create reference to the action interface
            interface_reference = self._create_interface_reference(
                interface_name, system_id, iface_id_short)
            elements.append(interface_reference)

        elif 'input_variable' in skill_data or 'output_variable' in skill_data:
            # Fallback: create operation from explicit skill config
            operation = self._create_operation_from_config(
                skill_name, skill_data, system_id)
            elements.append(operation)

        if not elements:
            return None

        # For asynchronous operations, add an StateMachine property
        # This property can be polled by clients for intermediate state updates
        if is_async:
            state_property = self._create_state_machine_property()
            elements.append(state_property)

        # Wrap operation and reference in a SubmodelElementCollection
        return self.element_factory.create_collection(
            id_short=skill_name,
            elements=elements,
            description=skill_data.get('description', f'Skill: {skill_name}')
        )

    def _create_operation_from_action(self, action_name: str, action_config: Dict,
                                      system_id: str) -> model.Operation:
        """
        Create an operation from an action interface configuration.

        Args:
            action_name: Name of the action
            action_config: Action configuration from AssetInterfacesDescription
            system_id: System identifier

        Returns:
            Operation element
        """
        input_variables = []
        output_variables = []
        inoutput_variables = []

        # Track property names to avoid duplicates between input and output
        input_prop_names = set()

        # Parse input schema if present - expand arrays into individual variables
        input_schema_url = action_config.get('input')
        if input_schema_url:
            schema = self.schema_handler.load_schema(input_schema_url)
            if schema:
                # Use extract_operation_variables to expand arrays (e.g., Position -> X, Y, Theta)
                vars = self.schema_handler.extract_operation_variables(schema)
                for var_name, var_info in vars.items():
                    var_type = var_info.get('type', 'string')
                    var_desc = var_info.get('description', '')

                    input_variables.append(
                        self._create_operation_variable(
                            var_name, var_type, var_desc)
                    )
                    input_prop_names.add(var_name)

        # Parse output schema if present - expand arrays into individual variables
        output_schema_url = action_config.get('output')
        if output_schema_url:
            schema = self.schema_handler.load_schema(output_schema_url)
            if schema:
                # Use extract_operation_variables to expand arrays
                vars = self.schema_handler.extract_operation_variables(schema)
                for var_name, var_info in vars.items():
                    var_type = var_info.get('type', 'string')
                    var_desc = var_info.get('description', '')

                    # If property exists in both input and output, it becomes in-output
                    if var_name in input_prop_names:
                        # Move from input to in-output
                        inoutput_variables.append(
                            self._create_operation_variable(
                                var_name, var_type, var_desc)
                        )
                        # Remove from input_variables
                        input_variables = [
                            v for v in input_variables if v.id_short != var_name]
                    else:
                        output_variables.append(
                            self._create_operation_variable(
                                var_name, var_type, var_desc)
                        )

        # Get description from action title or key
        description = action_config.get('title', action_name)

        # Create semantic ID from action name
        semantic_id = self.semantic_factory.create_skill_semantic_id(
            action_name)

        # Build the qualifiers for the operation
        qualifiers = self._create_operation_qualifiers(
            action_config, system_id, action_name)

        # Use element factory to create the operation
        return self.element_factory.create_operation(
            id_short=action_name,
            input_vars=input_variables if input_variables else None,
            output_vars=output_variables if output_variables else None,
            inoutput_vars=inoutput_variables if inoutput_variables else None,
            semantic_id=semantic_id,
            qualifiers=qualifiers if qualifiers else None,
            description=f"Operation to invoke {description} action"
        )

    def _create_operation_from_config(self, skill_name: str, skill_data: Dict,
                                      system_id: str) -> model.Operation:
        """
        Create operation from explicit skill configuration (fallback method).

        Args:
            skill_name: Name of the skill
            skill_data: Skill configuration
            system_id: System identifier

        Returns:
            Operation element
        """
        input_variables = []
        output_variables = []

        if 'input_variable' in skill_data and skill_data['input_variable']:
            for var_name, var_type in skill_data['input_variable'].items():
                input_variables.append(
                    self._create_operation_variable(var_name, var_type)
                )

        if 'output_variable' in skill_data and skill_data['output_variable']:
            for var_name, var_type in skill_data['output_variable'].items():
                output_variables.append(
                    self._create_operation_variable(var_name, var_type)
                )

        # Build qualifiers for delegation
        qualifiers = []
        if self.delegation_base_url:
            qualifiers.extend([
                model.Qualifier(
                    type_="invocationDelegation",
                    value_type=model.datatypes.String,
                    value=f"{self.delegation_base_url}/operations/{system_id}/{skill_name}",
                    kind=model.QualifierKind.CONCEPT_QUALIFIER
                ),
                model.Qualifier(
                    type_="Synchronous",
                    value_type=model.datatypes.Boolean,
                    value="true",
                    kind=model.QualifierKind.CONCEPT_QUALIFIER
                )
            ])

        return model.Operation(
            id_short=skill_name,
            input_variable=input_variables if input_variables else (),
            output_variable=output_variables if output_variables else (),
            description=model.MultiLanguageTextType(
                {"en": skill_data.get('description', f'Operation for {skill_name}')}),
            qualifier=qualifiers if qualifiers else ()
        )

    def _create_operation_variable(self, var_name: str, var_type: str,
                                   description: str = "") -> model.Property:
        """
        Create an operation variable (input/output parameter) as a Property.

        Args:
            var_name: Name of the variable
            var_type: Type of the variable (JSON schema type)
            description: Optional description

        Returns:
            Property element for use in Operation
        """
        aas_type = self.schema_handler.get_aas_type(var_type)

        # For operation variables, we need a Property without a value
        # display_name must be MultiLanguageNameType (array of {language, text})
        prop = model.Property(
            id_short=var_name,
            value_type=aas_type,
            display_name=model.MultiLanguageNameType({"en": var_name}),
            description=model.MultiLanguageTextType(
                {"en": description}) if description else None
        )
        return prop

    def _create_operation_qualifiers(self, action_config: Dict, system_id: str,
                                     action_name: str) -> List[model.Qualifier]:
        """
        Create qualifiers for an operation.

        Args:
            action_config: Action configuration
            system_id: System identifier
            action_name: Name of the action

        Returns:
            List of qualifiers
        """
        qualifiers = []

        # Determine operation type from config structure
        # One-way: no output schema AND no response in forms
        forms = action_config.get('forms', {})
        has_output = 'output' in action_config
        has_response = 'response' in forms
        is_one_way = not has_output and not has_response
        is_synchronous = str(action_config.get(
            'synchronous', 'true')).lower() == 'true'

        # Add invocationDelegation qualifier for BaSyx Operation Delegation
        # Operation type (oneWay, synchronous) is read from topics.json by the delegation service
        if self.delegation_base_url:
            delegation_url = f"{self.delegation_base_url}/operations/{system_id}/{action_name}"
            qualifiers.append(
                model.Qualifier(
                    type_="invocationDelegation",
                    value_type=model.datatypes.String,
                    value=delegation_url
                )
            )

        # Add operation type qualifier
        if is_one_way:
            # OneWay operations: no response expected, synchronous flag is not applicable
            qualifiers.append(
                model.Qualifier(
                    type_="OneWay",
                    value_type=model.datatypes.Boolean,
                    value=True
                )
            )
        else:
            # Two-way operations: add synchronous flag (default: true)
            qualifiers.append(
                model.Qualifier(
                    type_="Synchronous",
                    value_type=model.datatypes.Boolean,
                    value=is_synchronous
                )
            )

        return qualifiers

    def _is_async_operation(self, action_config: Dict) -> bool:
        """
        Determine if an operation is asynchronous based on action configuration.

        Args:
            action_config: Action configuration dictionary

        Returns:
            True if the operation is asynchronous (synchronous=false), False otherwise
        """
        # Check synchronous flag (default is true = synchronous)
        # If synchronous is false, the operation is asynchronous
        return str(action_config.get('synchronous', 'true')).lower() == 'false'

    def _create_state_machine_property(self) -> model.Property:
        """
        Create an StateMachine property for asynchronous operations.

        This property is updated by the Operation Delegation Service with
        intermediate states (IDLE, RUNNING, SUCCESS, FAILURE) during execution.
        Clients can poll this property to monitor operation progress.

        Returns:
            Property element for operation state
        """
        return model.Property(
            id_short="StateMachine",
            value_type=model.datatypes.String,
            value="IDLE",
            description=model.MultiLanguageTextType({
                "en": "Current state of the asynchronous operation. "
                      "Values: IDLE, RUNNING, SUCCESS, FAILURE. "
                      "Poll this property to monitor operation progress."
            })
        )

    def _create_interface_reference(self, interface_name: str, system_id: str,
                                    iface_id_short: str = 'InterfaceMQTT') -> model.ReferenceElement:
        """
        Create a reference to an action interface.

        Args:
            interface_name: Name of the interface
            system_id: System identifier

        Returns:
            ReferenceElement pointing to the interface
        """
        return model.ReferenceElement(
            id_short="InterfaceReference",
            value=model.ModelReference(
                (model.Key(
                    type_=model.KeyTypes.SUBMODEL,
                    value=f"{self.base_url}/submodels/instances/{system_id}/AID"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value=iface_id_short
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value="InteractionMetadata"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value="actions"
                ),
                    model.Key(
                    type_=model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
                    value=interface_name
                ),),
                model.SubmodelElementCollection
            ),
            description=model.MultiLanguageTextType(
                {"en": f"Reference to {interface_name} action interface"})
        )
