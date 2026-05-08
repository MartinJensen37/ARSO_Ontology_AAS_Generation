"""
AAS Element Factory

Provides helper functions for creating common AAS elements.
"""

from basyx.aas import model
from typing import Any, Dict, List, Optional, Union




_REQUIRES_SEMANTIC_ID: set[str] = {
    "ManufacturerName",
    "ManufacturerProductDesignation",
    "ContactInformation",
    "OrderCodeOfManufacturer",
    "EndpointMetadata",
}


def _require_semantic_id(id_short, semantic_id):
    if id_short in _REQUIRES_SEMANTIC_ID and semantic_id is None:
        raise ValueError(
            f"AAS_generation: SME '{id_short}' requires a semanticId. "
            f"Pass semantic_id=SemanticIdFactory().<XXX>. See semantic_ids.py."
        )

class AASElementFactory:
    """Factory for creating AAS elements with consistent patterns."""

    @staticmethod
    def create_property(
        id_short: str,
        value: Any,
        value_type: type = None,
        semantic_id: Optional[model.ExternalReference] = None,
        description: Optional[str] = None
    ) -> model.Property:
        """
        Create a Property element.

        Args:
            id_short: Property identifier
            value: Property value
            value_type: AAS data type (auto-detected if None)
            semantic_id: Optional semantic ID
            description: Optional description

        Returns:
            Property element
        """
        _require_semantic_id(id_short, semantic_id)
        # Auto-detect value type if not provided
        if value_type is None:
            if isinstance(value, bool):
                value_type = model.datatypes.Boolean
            elif isinstance(value, int):
                value_type = model.datatypes.Int
            elif isinstance(value, float):
                value_type = model.datatypes.Double
            else:
                value_type = model.datatypes.String
                value = str(value)

        kwargs = {
            'id_short': id_short,
            'value_type': value_type,
            'value': value
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        if description:
            kwargs['description'] = model.MultiLanguageTextType(
                {"en": description})

        return model.Property(**kwargs)

    @staticmethod
    def create_file(
        id_short: str,
        value: str,
        content_type: str = "application/schema+json",
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.File:
        """
        Create a File element.

        Args:
            id_short: File identifier
            value: File path or URL
            content_type: MIME type
            semantic_id: Optional semantic ID

        Returns:
            File element
        """
        kwargs = {
            'id_short': id_short,
            'content_type': content_type,
            'value': value
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.File(**kwargs)

    @staticmethod
    def create_collection(
        id_short: str,
        elements: List[model.SubmodelElement],
        semantic_id: Optional[model.ExternalReference] = None,
        supplemental_semantic_ids: Optional[List[model.ExternalReference]] = None,
        description: Optional[str] = None
    ) -> model.SubmodelElementCollection:
        """
        Create a SubmodelElementCollection.

        Args:
            id_short: Collection identifier
            elements: Child elements
            semantic_id: Optional semantic ID
            supplemental_semantic_ids: Optional supplemental semantic IDs
            description: Optional description

        Returns:
            SubmodelElementCollection
        """
        _require_semantic_id(id_short, semantic_id)
        kwargs = {
            'id_short': id_short,
            'value': elements
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        if supplemental_semantic_ids:
            kwargs['supplemental_semantic_id'] = supplemental_semantic_ids

        if description:
            kwargs['description'] = model.MultiLanguageTextType(
                {"en": description})

        return model.SubmodelElementCollection(**kwargs)

    @staticmethod
    def create_multi_language_property(
        id_short: str,
        text: str,
        language: str = "en",
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.MultiLanguageProperty:
        """
        Create a MultiLanguageProperty element.

        Args:
            id_short: Property identifier
            text: Property text
            language: Language code
            semantic_id: Optional semantic ID

        Returns:
            MultiLanguageProperty element
        """
        _require_semantic_id(id_short, semantic_id)
        kwargs = {
            'id_short': id_short,
            'value': model.MultiLanguageTextType({language: text})
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.MultiLanguageProperty(**kwargs)

    @staticmethod
    def create_range(
        id_short: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
        value_type: type = None,
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.Range:
        """
        Create a Range element.

        Args:
            id_short: Range identifier
            min_value: Minimum value
            max_value: Maximum value
            value_type: AAS data type (auto-detected if None)
            semantic_id: Optional semantic ID

        Returns:
            Range element
        """
        if value_type is None:
            value_type = model.datatypes.Double

        kwargs = {
            'id_short': id_short,
            'value_type': value_type,
            'min': min_value,
            'max': max_value
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.Range(**kwargs)

    @staticmethod
    def create_reference_element(
        id_short: str,
        reference: model.ModelReference,
        semantic_id: Optional[model.ExternalReference] = None,
        supplemental_semantic_ids: Optional[List[model.ExternalReference]] = None,
        description: Optional[str] = None
    ) -> model.ReferenceElement:
        """
        Create a ReferenceElement.

        Args:
            id_short: Element identifier
            reference: Target reference
            semantic_id: Optional semantic ID
            supplemental_semantic_ids: Optional supplemental semantic IDs
            description: Optional description

        Returns:
            ReferenceElement
        """
        kwargs = {
            'id_short': id_short,
            'value': reference
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        if supplemental_semantic_ids:
            kwargs['supplemental_semantic_id'] = supplemental_semantic_ids

        if description:
            kwargs['description'] = model.MultiLanguageTextType(
                {"en": description})

        return model.ReferenceElement(**kwargs)

    @staticmethod
    def create_capability(
        id_short: str,
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.Capability:
        """
        Create a Capability element.

        Args:
            id_short: Capability identifier
            semantic_id: Optional semantic ID

        Returns:
            Capability element
        """
        kwargs = {'id_short': id_short}

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.Capability(**kwargs)

    @staticmethod
    def create_relationship(
        id_short: Optional[str],
        first: model.ModelReference,
        second: model.ModelReference,
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.RelationshipElement:
        """
        Create a RelationshipElement.

        Args:
            id_short: Element identifier (can be None for list items)
            first: First reference
            second: Second reference
            semantic_id: Optional semantic ID

        Returns:
            RelationshipElement
        """
        kwargs = {
            'id_short': id_short,
            'first': first,
            'second': second
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.RelationshipElement(**kwargs)

    @staticmethod
    def create_entity(
        id_short: str,
        entity_type: model.EntityType,
        global_asset_id: Optional[str] = None,
        statements: Optional[List[model.SubmodelElement]] = None,
        semantic_id: Optional[model.ExternalReference] = None
    ) -> model.Entity:
        """
        Create an Entity element.

        Args:
            id_short: Entity identifier
            entity_type: Type of entity (SELF_MANAGED or CO_MANAGED)
            global_asset_id: Optional global asset ID (required for SELF_MANAGED)
            statements: Optional child statements
            semantic_id: Optional semantic ID

        Returns:
            Entity element
        """
        kwargs = {
            'id_short': id_short,
            'entity_type': entity_type
        }

        if global_asset_id:
            kwargs['global_asset_id'] = global_asset_id

        if statements:
            kwargs['statement'] = statements

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        return model.Entity(**kwargs)

    @staticmethod
    def create_operation(
        id_short: str,
        input_vars: Optional[List[model.Property]] = None,
        output_vars: Optional[List[model.Property]] = None,
        inoutput_vars: Optional[List[model.Property]] = None,
        semantic_id: Optional[model.ExternalReference] = None,
        qualifiers: Optional[List[model.Qualifier]] = None,
        description: Optional[str] = None
    ) -> model.Operation:
        """
        Create an Operation element.

        Args:
            id_short: Operation identifier
            input_vars: Input variables
            output_vars: Output variables
            inoutput_vars: In-output variables
            semantic_id: Optional semantic ID
            qualifiers: Optional qualifiers
            description: Optional description

        Returns:
            Operation element
        """
        kwargs = {
            'id_short': id_short,
            'input_variable': tuple(input_vars) if input_vars else (),
            'output_variable': tuple(output_vars) if output_vars else (),
            'in_output_variable': tuple(inoutput_vars) if inoutput_vars else ()
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        if qualifiers:
            kwargs['qualifier'] = tuple(qualifiers)

        if description:
            kwargs['description'] = model.MultiLanguageTextType(
                {"en": description})

        return model.Operation(**kwargs)

    @staticmethod
    def create_submodel_element_list(
        id_short: str,
        type_value_list_element: type,
        value: Optional[List[model.SubmodelElement]] = None,
        semantic_id: Optional[model.ExternalReference] = None,
        supplemental_semantic_ids: Optional[List[model.ExternalReference]] = None
    ) -> model.SubmodelElementList:
        """
        Create a SubmodelElementList.

        Args:
            id_short: List identifier
            type_value_list_element: Type of elements in the list
            value: List of submodel elements
            semantic_id: Optional semantic ID
            supplemental_semantic_ids: Optional supplemental semantic IDs

        Returns:
            SubmodelElementList element
        """
        kwargs = {
            'id_short': id_short,
            'type_value_list_element': type_value_list_element,
            'value': value if value else []
        }

        if semantic_id:
            kwargs['semantic_id'] = semantic_id

        if supplemental_semantic_ids:
            kwargs['supplemental_semantic_id'] = supplemental_semantic_ids

        return model.SubmodelElementList(**kwargs)
