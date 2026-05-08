"""
Schema Handler

Handles loading and parsing JSON schemas for AAS generation.
"""

import json
import urllib.request
from pathlib import Path
from typing import Dict, Optional
from basyx.aas import model


# JSON Schema to AAS datatypes mapping
SCHEMA_TYPE_TO_AAS_TYPE = {
    'string': model.datatypes.String,
    'integer': model.datatypes.Int,
    'number': model.datatypes.Double,
    'boolean': model.datatypes.Boolean,
    'array': model.datatypes.String,  # Arrays serialized as JSON strings
    'object': model.datatypes.String,  # Objects serialized as JSON strings
}


class SchemaHandler:
    """Handles loading and parsing JSON schemas."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize schema handler.

        Args:
            project_root: Root directory of the project (for locating schema files)
        """
        # Default to the workspace root (parent of Registration_Service)
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root
        self._schema_cache: Dict[str, Dict] = {}

    def load_schema(self, schema_url: str) -> Optional[Dict]:
        """
        Load a JSON schema from URL or local path.

        Args:
            schema_url: URL or local path to the schema

        Returns:
            Parsed schema dictionary or None if not found
        """
        # Check cache first
        if schema_url in self._schema_cache:
            return self._schema_cache[schema_url]

        schema = None

        # Try to resolve from local MQTTSchemas folder first
        if 'MQTTSchemas/' in schema_url or 'schemas/' in schema_url:
            schema = self._load_local_schema(schema_url)

        # If no local file found, try to fetch from URL
        if schema is None and schema_url.startswith('http'):
            schema = self._load_remote_schema(schema_url)

        if schema:
            self._schema_cache[schema_url] = schema

        return schema

    def _load_local_schema(self, schema_url: str) -> Optional[Dict]:
        """
        Load schema from local file system.

        Args:
            schema_url: Schema URL (used to extract filename)

        Returns:
            Parsed schema or None
        """
        # Extract filename from URL
        filename = schema_url.split('/')[-1]

        # Look in common schema locations
        local_paths = [
            self.project_root / 'MQTTSchemas' / filename,
        ]

        for local_path in local_paths:
            if local_path.exists():
                try:
                    with open(local_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(
                        f"Warning: Could not load schema from {local_path}: {e}")

        return None

    def _load_remote_schema(self, schema_url: str) -> Optional[Dict]:
        """
        Load schema from remote URL.

        Args:
            schema_url: Schema URL

        Returns:
            Parsed schema or None
        """
        try:
            with urllib.request.urlopen(schema_url, timeout=5) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Warning: Could not fetch schema from {schema_url}: {e}")
            return None

    def extract_properties(self, schema: Dict, include_inherited: bool = True) -> Dict[str, Dict]:
        """
        Extract properties from a JSON schema, including from allOf references.

        Args:
            schema: The JSON schema dictionary
            include_inherited: Whether to include properties from referenced schemas

        Returns:
            Dictionary of property name -> property definition
        """
        properties = {}

        # Direct properties
        if 'properties' in schema:
            for prop_name, prop_def in schema['properties'].items():
                properties[prop_name] = prop_def

        # Handle allOf (schema composition)
        if include_inherited and 'allOf' in schema:
            for sub_schema in schema['allOf']:
                if '$ref' in sub_schema:
                    # Try to load referenced schema
                    ref_schema = self.load_schema(sub_schema['$ref'])
                    if ref_schema:
                        ref_props = self.extract_properties(
                            ref_schema, include_inherited=True)
                        properties.update(ref_props)
                elif 'properties' in sub_schema:
                    for prop_name, prop_def in sub_schema['properties'].items():
                        properties[prop_name] = prop_def

        return properties

    def extract_operation_variables(self, schema: Dict, include_inherited: bool = True) -> Dict[str, Dict]:
        """
        Extract operation variables from a JSON schema.

        Recursively unpacks arrays with prefixItems (tuples) into individual named fields.
        For example: Position[x, y, theta] → X, Y, Theta
        Uses 'title' property from prefixItems for field names (without parent prefix).

        Args:
            schema: The JSON schema dictionary
            include_inherited: Whether to include properties from referenced schemas

        Returns:
            Dictionary of variable name -> {type, description, array_info}
            array_info contains: {parent_field, item_field, is_array_item, index}
        """
        # Get all properties
        properties = self.extract_properties(schema, include_inherited)

        variables = {}

        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get('type', 'string')

            if prop_type == 'array':
                # Check for prefixItems (tuple-like arrays)
                prefix_items = prop_def.get('prefixItems')
                if prefix_items:
                    # Unpack tuple array into individual fields using titles
                    # Use the item title directly (e.g., "X") not prefixed (e.g., "Position_X")
                    # This matches the MQTT schema field names for automatic mapping
                    for idx, item_def in enumerate(prefix_items):
                        item_title = item_def.get('title', f'Item{idx}')
                        var_name = item_title  # Use title directly, no prefix
                        variables[var_name] = {
                            'type': item_def.get('type', 'string'),
                            'description': item_def.get('description', ''),
                            'array_info': {
                                'parent_field': prop_name,
                                'item_field': item_title,
                                'is_array_item': True,
                                'index': idx
                            }
                        }
                else:
                    # Array without prefixItems - keep as string
                    variables[prop_name] = {
                        'type': prop_type,
                        'description': prop_def.get('description', ''),
                        'array_info': None
                    }
            else:
                # Regular property
                variables[prop_name] = {
                    'type': prop_type,
                    'description': prop_def.get('description', ''),
                    'array_info': None
                }

        return variables

    def get_aas_type(self, json_type: str) -> type:
        """
        Convert JSON schema type to AAS datatype.

        Args:
            json_type: JSON schema type string

        Returns:
            AAS datatype class
        """
        return SCHEMA_TYPE_TO_AAS_TYPE.get(json_type, model.datatypes.String)

    def extract_data_fields(self, schema_url: str) -> Dict[str, Dict]:
        """
        Extract the data fields from a schema for DataBridge configuration.

        This extracts the meaningful data fields from the schema, excluding
        common base fields like TimeStamp that are present in all messages.

        Args:
            schema_url: URL of the schema to extract fields from

        Returns:
            Dictionary of field_name -> {type, description, default_value}
        """
        schema = self.load_schema(schema_url)
        if not schema:
            return {}

        # Get all properties including from allOf
        all_properties = self.extract_properties(
            schema, include_inherited=True)

        # Get required fields from the main schema (not inherited)
        required_fields = set()
        if 'required' in schema:
            required_fields.update(schema['required'])

        # Also check allOf for required fields (but not from base refs)
        if 'allOf' in schema:
            for sub_schema in schema['allOf']:
                if '$ref' not in sub_schema and 'required' in sub_schema:
                    required_fields.update(sub_schema['required'])

        # Base fields to exclude (from data.schema.json)
        base_fields = {'TimeStamp'}

        # Extract data fields (required fields minus base fields)
        data_fields = {}
        for field_name in required_fields:
            if field_name in base_fields:
                continue

            prop_def = all_properties.get(field_name, {})
            json_type = prop_def.get('type', 'string')

            # Determine default value based on type
            if json_type == 'array':
                default_value = '[]'
            elif json_type == 'integer':
                default_value = 0
            elif json_type == 'number':
                default_value = 0.0
            elif json_type == 'boolean':
                default_value = False
            else:
                default_value = ''

            data_fields[field_name] = {
                'type': json_type,
                'aas_type': self.get_aas_type(json_type),
                'description': prop_def.get('description', ''),
                'default_value': default_value
            }

        return data_fields

    def clear_cache(self):
        """Clear the schema cache."""
        self._schema_cache.clear()
