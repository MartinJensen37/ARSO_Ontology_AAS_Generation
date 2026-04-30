"""AAS Builder for creating Asset Administration Shell instances."""

from typing import Dict, List
from basyx.aas import model


class AASBuilder:
    """
    Builder class for creating Asset Administration Shell (AAS) instances.

    This builder handles the creation of the top-level AAS structure including
    asset information, specific asset IDs, and submodel references.
    """

    def __init__(self, base_url: str):
        """
        Initialize the AAS builder.

        Args:
            base_url: Base URL for AAS identifiers
        """
        self.base_url = base_url

    def build(self, system_id: str, config: Dict) -> model.AssetAdministrationShell:
        """
        Create an Asset Administration Shell from configuration.

        Args:
            system_id: Unique identifier for the system
            config: Configuration dictionary containing AAS metadata

        Returns:
            AssetAdministrationShell instance
        """
        id_short = config.get('idShort', system_id)
        aas_id = config.get('id', f"{self.base_url}/aas/{system_id}")
        global_asset_id = config.get(
            'globalAssetId', f"{self.base_url}/assets/{system_id}")
        asset_type = config.get('assetType', '')
        serial_number = config.get('serialNumber', 'UNKNOWN')
        location = config.get('location', 'UNKNOWN')

        # Create asset information
        asset_information = self._create_asset_information(
            global_asset_id, asset_type, serial_number, location
        )

        # Determine which submodels to reference
        submodel_names = self._determine_submodels(config)

        # Create submodel references
        submodel_refs = self._create_submodel_references(
            system_id, submodel_names)

        # Create AAS with optional derivedFrom
        aas_kwargs = {
            'id_': aas_id,
            'asset_information': asset_information,
            'id_short': id_short,
            'submodel': submodel_refs
        }

        # Add derivedFrom if specified in config
        derived_from = config.get('derivedFrom')
        if derived_from:
            aas_kwargs['derived_from'] = model.ModelReference(
                (model.Key(
                    type_=model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
                    value=derived_from
                ),),
                model.AssetAdministrationShell
            )

        return model.AssetAdministrationShell(**aas_kwargs)

    def _create_asset_information(
        self,
        global_asset_id: str,
        asset_type: str,
        serial_number: str,
        location: str
    ) -> model.AssetInformation:
        """
        Create asset information with specific asset IDs.

        Args:
            global_asset_id: Global unique identifier for the asset
            asset_type: Type/category of the asset
            serial_number: Serial number of the asset
            location: Physical location of the asset

        Returns:
            AssetInformation instance with specific asset IDs
        """
        asset_information = model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=global_asset_id,
            asset_type=asset_type if asset_type else None
        )

        # Add specific asset IDs
        asset_information.specific_asset_id = {
            model.SpecificAssetId(
                name="serialNumber",
                value=serial_number,
                external_subject_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value="https://admin-shell.io/aas/3/0/SpecificAssetId/SerialNumber"
                    ),)
                )
            ),
            model.SpecificAssetId(
                name="location",
                value=location,
                external_subject_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value="https://admin-shell.io/aas/3/0/SpecificAssetId/Location"
                    ),)
                )
            )
        }

        return asset_information

    def _determine_submodels(self, config: Dict) -> List[str]:
        """
        Determine which submodels should be referenced based on configuration.

        Args:
            config: Configuration dictionary

        Returns:
            List of submodel names to include
        """
        submodel_names = []

        # DigitalNameplate is mandatory for ResourceAAS generation.
        submodel_names.append('Nameplate')

        # Add standard submodels if they exist in config
        if 'AID' in config or 'AssetInterfacesDescription' in config:
            submodel_names.append('AID')
        if 'Variables' in config:
            submodel_names.append('OperationalData')
        if 'Parameters' in config:
            submodel_names.append('Parameters')
        if 'HierarchicalStructures' in config:
            submodel_names.append('HierarchicalStructures')
        if 'Capabilities' in config and config.get('Capabilities'):
            submodel_names.append('Capabilities')

        # Add Skills submodel reference if:
        # 1. Skills are explicitly defined in config, OR
        # 2. There are actions in AssetInterfacesDescription (auto-generation)
        has_explicit_skills = 'Skills' in config and config.get('Skills')
        has_actions = self._has_interface_actions(config)

        if has_explicit_skills or has_actions:
            submodel_names.append('Skills')

        # Add Process AAS specific submodels if they exist in config
        if 'ProcessInformation' in config:
            submodel_names.append('ProcessInformation')
        if 'RequiredCapabilities' in config:
            submodel_names.append('RequiredCapabilities')
        if 'Policy' in config:
            submodel_names.append('Policy')

        return submodel_names

    def _has_interface_actions(self, config: Dict) -> bool:
        """
        Check if the configuration has interface actions defined.

        Args:
            config: Configuration dictionary

        Returns:
            True if actions are defined, False otherwise
        """
        interface_config = config.get('AID', {}) or config.get(
            'AssetInterfacesDescription', {}) or {}
        mqtt_config = interface_config.get('InterfaceMQTT', {}) or {}
        interaction_metadata = mqtt_config.get('InteractionMetadata', {}) or {}
        actions = interaction_metadata.get('actions', [])
        return bool(actions)

    def _create_submodel_references(
        self,
        system_id: str,
        submodel_names: List[str]
    ) -> List[model.ModelReference]:
        """
        Create model references for submodels.

        Args:
            system_id: System identifier
            submodel_names: List of submodel names to reference

        Returns:
            List of ModelReferences to submodels
        """
        return [
            model.ModelReference(
                (model.Key(
                    type_=model.KeyTypes.SUBMODEL,
                    value=f"{self.base_url}/submodels/instances/{system_id}/{sm_name}"
                ),),
                model.Submodel
            )
            for sm_name in submodel_names
        ]
