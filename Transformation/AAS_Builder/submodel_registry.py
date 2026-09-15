"""Single registry describing every submodel the framework can build.

One entry per submodel replaces the parallel if-chains that used to live in
generate_aas.py (`_build_object_store`), aas_builder.py (`_determine_submodels`)
and aas_to_profile.py (`_SUBMODEL_IDSHORT_TO_KEY`). Adding a submodel means
adding a spec here plus its builder and its ontology module.

Deliberately free of heavy imports so the inverse parser and the API can import
it without pulling in basyx; builder classes are resolved lazily by name.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubmodelSpec:
    """One buildable submodel.

    Args:
        key: UI-facing SubmodelKey, also the profile key the editor writes.
        ref_name: Submodel-reference name and the last segment of the submodel id.
        id_short: idShort of the built submodel, used to invert an AAS.
        profile_keys: Profile sections that activate this submodel; the first is
            canonical, the rest are accepted aliases.
        builder: Attribute name the builder instance gets on AASGenerator.
        builder_cls: Class name exported by AAS_generation.submodels.
        ctor: Constructor shape - "basic", "schema" or "skills".
        build_arg: Extra argument build() takes, if any.
        build_when_empty: Build even when the section is present but empty.
        label: Human-readable name for the UI catalog.
        description: One-line UI catalog description.
        required: Always present on an AAS, regardless of config.
    """
    key: str
    ref_name: str
    id_short: str
    profile_keys: tuple[str, ...]
    builder: str
    builder_cls: str
    ctor: str = "basic"
    build_arg: str | None = None
    build_when_empty: bool = False
    label: str = ""
    description: str = ""
    required: bool = False

    def active_in(self, config: dict) -> bool:
        """Whether this submodel should be built for the given profile config."""
        for pk in self.profile_keys:
            value = config.get(pk)
            if self.build_when_empty:
                if value is not None:
                    return True
            elif value:
                return True
        return False


SUBMODEL_SPECS: tuple[SubmodelSpec, ...] = (
    SubmodelSpec(
        key="Nameplate", ref_name="Nameplate", id_short="DigitalNameplate",
        profile_keys=("DigitalNameplate", "Nameplate"),
        builder="nameplate_builder", builder_cls="DigitalNameplateSubmodelBuilder",
        build_when_empty=True, required=True,
        label="DigitalNameplate",
        description="Manufacturer, serial number, product URI",
    ),
    SubmodelSpec(
        key="HierarchicalStructures", ref_name="HierarchicalStructures",
        id_short="HierarchicalStructures",
        profile_keys=("HierarchicalStructures",),
        builder="hierarchical_structures_builder",
        builder_cls="HierarchicalStructuresSubmodelBuilder",
        build_when_empty=True, required=True,
        label="BillOfMaterials",
        description="BOM - IsPartOf / HasPart relationships",
    ),
    SubmodelSpec(
        key="AID", ref_name="AID", id_short="AID",
        profile_keys=("AID", "AssetInterfacesDescription"),
        builder="asset_interfaces_builder", builder_cls="AssetInterfacesBuilder",
        label="AssetInterfaceDescription",
        description="MQTT/HTTP/OPC UA endpoint + interaction metadata",
    ),
    SubmodelSpec(
        key="Skills", ref_name="Skills", id_short="Skills",
        profile_keys=("Skills",),
        builder="skills_builder", builder_cls="SkillsSubmodelBuilder",
        ctor="skills",
        label="Skills",
        description="Invocable operations bound to AID actions",
    ),
    SubmodelSpec(
        key="Capabilities", ref_name="Capabilities", id_short="Capabilities",
        profile_keys=("Capabilities",),
        builder="capabilities_builder", builder_cls="CapabilitiesSubmodelBuilder",
        label="Capabilities",
        description="What the asset can do, realized by skills",
    ),
    SubmodelSpec(
        key="Variables", ref_name="OperationalData", id_short="OperationalData",
        profile_keys=("OperationalData", "Variables"),
        builder="variables_builder", builder_cls="VariablesSubmodelBuilder",
        ctor="schema", build_arg="interface_properties",
        label="OperationalData",
        description="Runtime values read from AID properties",
    ),
    SubmodelSpec(
        key="Parameters", ref_name="Parameters", id_short="Parameters",
        profile_keys=("Parameters",),
        builder="parameters_builder", builder_cls="ParametersSubmodelBuilder",
        ctor="schema", build_arg="interface_input_properties",
        label="Parameters",
        description="Operator-set configuration values",
    ),
    SubmodelSpec(
        key="TechnicalData", ref_name="TechnicalData", id_short="TechnicalData",
        profile_keys=("TechnicalData",),
        builder="technical_data_builder", builder_cls="TechnicalDataSubmodelBuilder",
        label="TechnicalData",
        description="Datasheet properties and product classification",
    ),
    SubmodelSpec(
        key="AIMC", ref_name="AssetInterfacesMappingConfiguration",
        id_short="AssetInterfacesMappingConfiguration",
        profile_keys=("AIMC", "AssetInterfacesMappingConfiguration"),
        builder="aimc_builder", builder_cls="AIMCSubmodelBuilder",
        label="InterfaceMapping",
        description="Maps AID affordances onto other submodel elements",
    ),
)

SPEC_BY_KEY: dict[str, SubmodelSpec] = {s.key: s for s in SUBMODEL_SPECS}
SPEC_BY_ID_SHORT: dict[str, SubmodelSpec] = {s.id_short: s for s in SUBMODEL_SPECS}

# idShort -> UI key, for inverting a generated AAS back into a profile.
SUBMODEL_IDSHORT_TO_KEY: dict[str, str] = {s.id_short: s.key for s in SUBMODEL_SPECS}

# UI key -> canonical profile section name.
SUBMODEL_PROFILE_KEYS: dict[str, str] = {s.key: s.profile_keys[0] for s in SUBMODEL_SPECS}

REQUIRED_SUBMODEL_KEYS: tuple[str, ...] = tuple(s.key for s in SUBMODEL_SPECS if s.required)


def ui_catalog() -> list[dict]:
    """Serializable submodel catalog for the UI (served by /api/generation-config)."""
    return [
        {
            "key": s.key,
            "idShort": s.id_short,
            "profileKey": s.profile_keys[0],
            "label": s.label or s.key,
            "description": s.description,
            "required": s.required,
        }
        for s in SUBMODEL_SPECS
    ]
