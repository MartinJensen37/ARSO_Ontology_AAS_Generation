#!/usr/bin/env python3
"""
AAS Generator

Generates Asset Administration Shell (AAS) descriptions programmatically
using the basyx-python-sdk from JSON/YAML configuration files.
Called by the API pipeline via Transformation.AAS_Builder.AAS_builder.
"""

import json
import yaml
import argparse
import os
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization
from .aas_builder import AASBuilder
from .element_factory import AASElementFactory
from .schema_handler import SchemaHandler
from .semantic_ids import SemanticIdFactory
from ..submodels import (
    DigitalNameplateSubmodelBuilder,
    AssetInterfacesBuilder,
    VariablesSubmodelBuilder,
    SkillsSubmodelBuilder,
    ParametersSubmodelBuilder,
    HierarchicalStructuresSubmodelBuilder,
    CapabilitiesSubmodelBuilder,
    # Process AAS specific builders
    ProcessInformationSubmodelBuilder,
    RequiredCapabilitiesSubmodelBuilder,
    PolicySubmodelBuilder,
)

try:
    from ..aas_validator import AASValidator
except Exception:
    class _NoOpValidationResult:
        warnings: list[str] = []

        @staticmethod
        def is_valid() -> bool:
            return True

        @staticmethod
        def summary() -> str:
            return "Validation not available"

    class AASValidator:
        def validate(self, obj_store):
            return _NoOpValidationResult()


def _as_named_dict(value: Any) -> Dict:
    """Coerce a profile section that should be {name: {...}} but may have
    arrived as a list (each item carrying its own name) or a bare
    "[VERIFY: ...]" placeholder string into the expected dict shape, instead
    of letting a downstream .get()/.items() call crash. Mirrors
    AssetInterfacesBuilder._as_named_dict (kept local here to avoid a
    cross-module dependency for a few lines of logic)."""
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


class AASGenerator:
    """Generates AAS descriptions from configuration files."""

    _URL_FIELDS = {"id", "globalAssetId", "derivedFrom", "assetType"}

    @staticmethod
    def _load_config_file(config_path: str) -> Dict[str, Any]:
        """
        Load generator config from JSON or YAML.

        Supported extensions: .json, .yaml, .yml
        """
        path = Path(config_path)
        suffix = path.suffix.lower()

        if suffix not in {".json", ".yaml", ".yml"}:
            raise ValueError(
                f"Unsupported config file extension '{suffix}'. "
                "Use .json, .yaml or .yml"
            )

        with path.open("r", encoding="utf-8") as f:
            if suffix == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

        if not isinstance(data, dict) or not data:
            raise ValueError("Configuration must be a non-empty object/mapping.")

        first_value = next(iter(data.values()))
        if not isinstance(first_value, dict):
            raise ValueError(
                "Configuration root must be {'<system_id>': {...}} with system config as object."
            )

        return data

    def __init__(self, config_path: str, delegation_base_url: str = None, base_url_override: str = None):
        """
        Initialize the AAS Generator.

        Args:
            config_path: Path to the YAML configuration file
            delegation_base_url: Base URL for Operation Delegation Service
                                 (e.g., 'http://registration-service:8087')
            base_url_override: Optional explicit base URL to use for relative URI expansion
        """
        # Load configuration (JSON or YAML)
        self.config = self._load_config_file(config_path)

        # Extract system info from config
        self.system_id = list(self.config.keys())[0]
        self.system_config = self.config[self.system_id]

        # Set base URL from system configuration
        extracted_base_url = self._extract_base_url(self.system_config)
        self.base_url = (base_url_override or extracted_base_url).rstrip("/")
        self._normalize_config_urls(self.system_config)

        # Operation Delegation Service URL for BaSyx invocationDelegation
        self.delegation_base_url = delegation_base_url or os.environ.get(
            'DELEGATION_SERVICE_URL',
            'http://registration-service:8087'
        )

        # Initialize all helper services and builders
        self._initialize_builders()
        self._guidance_applied = False

    def _to_absolute_url(self, value: str) -> str:
        text = value.strip()
        if not text:
            return text
        if text.startswith("http://") or text.startswith("https://"):
            return text
        if text.startswith("/"):
            return f"{self.base_url.rstrip('/')}{text}"
        return f"{self.base_url.rstrip('/')}/{text}"

    def _normalize_config_urls(self, node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in self._URL_FIELDS and isinstance(value, str):
                    node[key] = self._to_absolute_url(value)
                else:
                    self._normalize_config_urls(value)
        elif isinstance(node, list):
            for item in node:
                self._normalize_config_urls(item)

    def _normalize_submodel_references(self, aas_dict: Dict[str, Any]) -> Dict[str, Any]:
        submodels = aas_dict.get("submodels")
        if not isinstance(submodels, list):
            return aas_dict

        idshort_to_id: Dict[str, str] = {}
        for submodel in submodels:
            if not isinstance(submodel, dict):
                continue
            id_short = submodel.get("idShort")
            submodel_id = submodel.get("id")
            if isinstance(id_short, str) and isinstance(submodel_id, str):
                idshort_to_id[id_short] = submodel_id

        shells = aas_dict.get("assetAdministrationShells")
        if not isinstance(shells, list):
            return aas_dict

        for shell in shells:
            if not isinstance(shell, dict):
                continue
            refs = shell.get("submodels")
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if not isinstance(ref, dict):
                    continue
                keys = ref.get("keys")
                if not isinstance(keys, list):
                    continue
                for key in keys:
                    if not isinstance(key, dict):
                        continue
                    if str(key.get("type", "")).lower() != "submodel":
                        continue
                    value = key.get("value")
                    if not isinstance(value, str) or not value.strip():
                        continue
                    ref_name = value.rstrip("/").split("/")[-1]
                    canonical = idshort_to_id.get(ref_name)
                    if canonical:
                        key["value"] = canonical

        return aas_dict

    # ==================== Initialization Methods ====================

    def _extract_base_url(self, config: Dict) -> str:
        """
        Extract base URL from system configuration.

        Args:
            config: System configuration dictionary

        Returns:
            Base URL for the system
        """
        aas_id = config.get('id', '')
        if aas_id:
            if isinstance(aas_id, str) and (aas_id.startswith("http://") or aas_id.startswith("https://")):
                parts = aas_id.rsplit('/aas/', 1)
                if len(parts) == 2 and parts[0]:
                    return parts[0]
                return aas_id.rsplit('/', 1)[0]

            # Extract base URL from ID (e.g., https://smartproductionlab.aau.dk/aas/...)
            if isinstance(aas_id, str) and aas_id.startswith('/'):
                return 'https://smartproductionlab.aau.dk'

        return 'https://smartproductionlab.aau.dk'

    def _initialize_builders(self):
        """Initialize all factory and builder instances."""
        # Core helper services
        self.schema_handler = SchemaHandler()
        self.element_factory = AASElementFactory()
        self.semantic_factory = SemanticIdFactory()

        # AAS builder
        self.aas_builder = AASBuilder(self.base_url)

        # Submodel builders
        self.nameplate_builder = DigitalNameplateSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )
        self.asset_interfaces_builder = AssetInterfacesBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )
        self.variables_builder = VariablesSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory,
            self.schema_handler
        )
        self.skills_builder = SkillsSubmodelBuilder(
            self.base_url, self.delegation_base_url,
            self.semantic_factory, self.element_factory, self.schema_handler
        )
        self.parameters_builder = ParametersSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory,
            self.schema_handler
        )
        self.hierarchical_structures_builder = HierarchicalStructuresSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )
        self.capabilities_builder = CapabilitiesSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )

        # Process AAS specific builders
        self.process_info_builder = ProcessInformationSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )
        self.required_capabilities_builder = RequiredCapabilitiesSubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )
        self.policy_builder = PolicySubmodelBuilder(
            self.base_url, self.semantic_factory, self.element_factory
        )

    # ==================== Main Generation Methods ====================

    def generate_all(self, output_dir: str, validate: bool = True) -> bool:
        """
        Generate and save AAS file from the configuration.

        Args:
            output_dir: Directory to save the generated JSON file
            validate: If True, validate the generated AAS

        Returns:
            True if generation succeeded, False otherwise
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Generating AAS for {self.system_id}...")

        self._ensure_ontology_guidance()

        # Generate AAS
        obj_store = self._build_object_store()

        # Validate if requested
        if validate and not self._validate_object_store(obj_store):
            print(f"\n❌ Validation failed for {self.system_id}")
            return False

        # Serialize and save
        aas_dict = self._serialize_to_dict(obj_store)
        output_file = output_path / f"{self.system_id}.json"

        with open(output_file, 'w') as f:
            json.dump(aas_dict, f, indent=2)

        print(f"Saved to {output_file}")
        return True

    def generate_system(self, system_id: str, config: Dict, return_store: bool = False):
        """
        Legacy compatibility method for generating AAS.

        Note: This method exists for backward compatibility with existing code.
        New code should use generate_all() instead.

        Args:
            system_id: Unique identifier for the system (ignored, uses config system_id)
            config: Configuration dictionary for this system (ignored, uses loaded config)
            return_store: If True, returns (obj_store, dict), otherwise just dict

        Returns:
            Dictionary representation of the AAS, or tuple of (obj_store, dict) if return_store=True
        """
        self._ensure_ontology_guidance()
        obj_store = self._build_object_store()
        aas_dict = self._serialize_to_dict(obj_store)

        if return_store:
            return obj_store, aas_dict
        return aas_dict

    def validate_generated_aas(self, obj_store: model.DictObjectStore, context: str = "") -> bool:
        """
        Legacy compatibility method for validation.

        Note: This method exists for backward compatibility with existing code.
        New code should use _validate_object_store() or generate_all(validate=True).

        Args:
            obj_store: The DictObjectStore containing generated AAS objects
            context: Context string for error messages (e.g., system name)

        Returns:
            True if validation passed (no errors), False otherwise
        """
        return self._validate_object_store(obj_store)

    # ==================== Core Building Methods ====================

    def _ensure_ontology_guidance(self) -> None:
        """Apply ontology-guided config enrichment once per generator instance."""
        if self._guidance_applied:
            return

        suggestions = self._apply_ontology_guidance(self.system_config)
        actionable = [s for s in suggestions if s["action"] != "hint"]
        if actionable:
            print("Ontology guidance:")
            for s in actionable:
                print(f"  • {s['description']}")

        self._guidance_applied = True

    def _apply_ontology_guidance(self, config: Dict) -> List[Dict[str, Any]]:
        """Apply ontology-aligned dependency and semantic guidance before building.

        Returns a list of structured suggestion dicts, each with:
          field (str): dot-path of the affected config field
          action (str): "auto-create" | "fill" | "add" | "hint"
          description (str): human-readable explanation
          proposed_value (Any): the value that will be / was applied (None for hints)

        Also mutates ``config`` in-place for auto-create/fill actions so the
        caller gets the enriched config for free.

        Auto-fix suggestions (fill / auto-create) are generated here for imperative
        repairs that can be applied with a single click.

        Hint suggestions are derived directly from the project SHACL shapes via
        Guidance.ontology_guidance_engine, which validates a real (best-effort)
        AAS RDF projection of this config — no constraint logic is duplicated in
        Python.  When the SHACL files change, hints update automatically.
        """
        suggestions: List[Dict[str, Any]] = []
        base = self.base_url.rstrip("/")

        def _suggest(field: str, action: str, description: str, proposed_value: Any = None) -> None:
            suggestions.append({
                "field": field,
                "action": action,
                "description": description,
                "proposed_value": proposed_value,
            })

        # ── Canonicalize AID key (legacy → canonical) ────────────────────────
        aid_config = config.get('AID') or config.get('AssetInterfacesDescription')
        if aid_config and 'AID' not in config:
            config['AID'] = copy.deepcopy(aid_config)
            _suggest("AID", "add", "Mapped legacy 'AssetInterfacesDescription' to canonical 'AID'.")

        skills_cfg = config.get('Skills') or {}
        variables_cfg = config.get('Variables') or {}
        parameters_cfg = config.get('Parameters') or {}
        # An LLM occasionally emits a whole section as a bare "[VERIFY: ...]"
        # string instead of an object; treat each as absent rather than crash.
        if not isinstance(skills_cfg, dict):
            skills_cfg = {}
        if not isinstance(variables_cfg, dict):
            variables_cfg = {}
        if not isinstance(parameters_cfg, dict):
            parameters_cfg = {}

        # ── Auto-fix: Skills / Variables / Parameters require an AID interface ─
        if not config.get('AID') and (skills_cfg or variables_cfg or parameters_cfg):
            scaffold: Dict[str, Any] = {
                'InterfaceMQTT': {
                    'Title': config.get('idShort', self.system_id),
                    'InteractionMetadata': {'actions': {}, 'properties': {}},
                }
            }
            config['AID'] = scaffold
            _suggest(
                "AID", "auto-create",
                "Created minimal 'AID' scaffold because Skills/Variables/Parameters are present "
                "(the ARSO ontology requires an AID submodel whenever any of these are present).",
                scaffold,
            )

        # Actions across ALL configured interfaces, not just a hardcoded one —
        # an asset can expose actions on several interfaces at once.
        aid_cfg = config.get('AID') or {}
        if not isinstance(aid_cfg, dict):
            # An LLM occasionally emits the whole section as a bare
            # "[VERIFY: ...]" string instead of an object; treat as absent.
            aid_cfg = {}
        actions_by_interface: Dict[str, Dict[str, Any]] = {}
        for iface_key, iface_cfg in aid_cfg.items():
            if not isinstance(iface_cfg, dict):
                continue
            iface_interaction = iface_cfg.get('InteractionMetadata', {})
            iface_actions = iface_interaction.get('actions', {}) if isinstance(iface_interaction, dict) else {}
            if isinstance(iface_actions, dict):
                for action_name in iface_actions:
                    actions_by_interface[action_name] = iface_key
            elif isinstance(iface_actions, list):
                for action_item in iface_actions:
                    if isinstance(action_item, dict):
                        name = action_item.get('name') or action_item.get('key')
                        if name:
                            actions_by_interface[name] = iface_key

        # ── Auto-fix: derive Skills from AID actions when absent ─────────────
        if not skills_cfg and actions_by_interface:
            generated_skills: Dict[str, Dict[str, Any]] = {}
            for action_name, iface_key in actions_by_interface.items():
                generated_skills[action_name] = {
                    'description': f"Auto-generated skill for action {action_name}",
                    'semantic_id': f"{base}/skills/{action_name}",
                    'interface': action_name,
                    'interfaceKey': iface_key,
                }
            config['Skills'] = generated_skills
            skills_cfg = generated_skills
            _suggest("Skills", "auto-create",
                     "Generated Skills entries from AID action definitions.",
                     generated_skills)
        elif skills_cfg:
            for skill_name, skill_data in list(skills_cfg.items()):
                if not isinstance(skill_data, dict):
                    skill_data = {}
                    skills_cfg[skill_name] = skill_data
                if 'interface' not in skill_data:
                    skill_data['interface'] = skill_name
                    _suggest(
                        f"Skills.{skill_name}.interface", "fill",
                        f"Skill '{skill_name}' missing interface; defaulted to '{skill_name}'.",
                        skill_name,
                    )
                if 'semantic_id' not in skill_data:
                    val = f"{base}/skills/{skill_name}"
                    skill_data['semantic_id'] = val
                    _suggest(
                        f"Skills.{skill_name}.semantic_id", "fill",
                        f"Skill '{skill_name}' missing semantic_id; applied default URI "
                        f"(the Skill's semanticId must use the lab's URI namespace).",
                        val,
                    )

        capabilities_cfg = config.get('Capabilities') or {}
        if not isinstance(capabilities_cfg, dict):
            # An LLM occasionally emits the whole section as a bare
            # "[VERIFY: ...]" string instead of an object; treat as absent.
            capabilities_cfg = {}

        # ── Auto-fix: every Skill must be realized by at least one Capability ─
        # Fill in missing semantic_id/realizedBy on whatever capabilities are
        # already present first, so "which skills are still uncovered" below
        # is computed after any LLM-authored capability's realizedBy is known.
        for cap_name, cap_data in list(capabilities_cfg.items()):
            if not isinstance(cap_data, dict):
                cap_data = {}
                capabilities_cfg[cap_name] = cap_data
            if 'semantic_id' not in cap_data:
                val = f"{base}/Capability/{cap_name}"
                cap_data['semantic_id'] = val
                _suggest(
                    f"Capabilities.{cap_name}.semantic_id", "fill",
                    f"Capability '{cap_name}' missing semantic_id; applied default URI "
                    f"(the Capability's semanticId must use the lab's URI namespace).",
                    val,
                )
            if 'realizedBy' not in cap_data:
                target = cap_name if cap_name in skills_cfg else (
                    next(iter(skills_cfg)) if skills_cfg else None
                )
                if target:
                    cap_data['realizedBy'] = target
                    _suggest(
                        f"Capabilities.{cap_name}.realizedBy", "fill",
                        f"Capability '{cap_name}' missing realizedBy; linked to '{target}' "
                        f"(the ARSO ontology requires each Capability's realizedBy to "
                        f"reference an existing Skill).",
                        target,
                    )

        # A profile can legitimately define capabilities for only SOME of its
        # skills (an LLM providing one thoughtful capability is not "wrong"),
        # but every skill still needs at least one - generate one for any
        # skill no existing capability's realizedBy already targets, instead
        # of only doing this when Capabilities was completely absent.
        realized_skills = {
            cap_data.get('realizedBy')
            for cap_data in capabilities_cfg.values()
            if isinstance(cap_data, dict) and cap_data.get('realizedBy')
        }
        missing_skills = [s for s in skills_cfg if s not in realized_skills]
        if missing_skills:
            generated_caps = {}
            for skill_name in missing_skills:
                # A capability keyed by this skill name may already exist but
                # legitimately realize a *different* skill - don't clobber it.
                cap_name = skill_name if skill_name not in capabilities_cfg else f"{skill_name}Capability"
                generated_caps[cap_name] = {
                    'realizedBy': skill_name,
                    'semantic_id': f"{base}/Capability/{skill_name}",
                }
            capabilities_cfg.update(generated_caps)
            config['Capabilities'] = capabilities_cfg
            _suggest(
                "Capabilities", "auto-create",
                f"Generated Capabilities for skill(s) with none: {', '.join(missing_skills)} "
                "(the ARSO ontology requires that any AAS providing Skills also provides "
                "Capabilities for them).",
                generated_caps,
            )

        # ── Ontology-driven hints: run SHACL on the post-fix config ───────────
        # All hint-type suggestions come from the actual SHACL shapes, evaluated
        # against a real (best-effort) AAS RDF projection of this config -- the
        # same projection final validation uses -- so hints can never disagree
        # with what generation will ultimately enforce. No constraint logic is
        # duplicated here.
        try:
            from Guidance.ontology_guidance_engine import check_aas_dict
            preview_store = self._build_object_store()
            preview_dict = self._serialize_to_dict(preview_store)
            shacl_hints = check_aas_dict(preview_dict)
            suggestions.extend(shacl_hints)
        except ImportError:
            pass  # rdflib/pyshacl not installed — hints unavailable
        except Exception:
            pass  # config too incomplete to build a preview yet — no hints this round

        return suggestions

    def _extract_interface_properties(self) -> List[Dict]:
        """
        Extract interface properties with output schema URLs from config.

        These are used for schema-driven field extraction in Variables submodel.
        Scans every configured interface (not just one hardcoded interface) so
        an asset can expose properties across several interfaces at once; each
        property dict is tagged with the interface it came from so downstream
        InterfaceReference elements can point at the right one.

        Returns:
            List of property dicts with name, schema URL (from output field),
            and the owning interface key
        """
        interface_config = self.system_config.get('AID', {}) or self.system_config.get(
            'AssetInterfacesDescription', {}) or {}
        if not isinstance(interface_config, dict):
            # An LLM occasionally emits the whole section as a bare
            # "[VERIFY: ...]" string instead of an object; treat as absent.
            interface_config = {}

        properties = []
        for iface_key, iface_cfg in interface_config.items():
            if not isinstance(iface_cfg, dict):
                continue
            interaction_config = _as_named_dict(iface_cfg.get('InteractionMetadata', {}))
            properties_dict = _as_named_dict(interaction_config.get('properties', {}))
            for prop_name, prop_config in properties_dict.items():
                if isinstance(prop_config, dict):
                    properties.append({
                        'name': prop_name,
                        'schema': prop_config.get('output'),
                        'interface': iface_key,
                    })

        return properties

    def _extract_interface_input_properties(self) -> List[Dict]:
        """
        Extract interface properties with input schema URLs from config.

        These are used for schema-driven field extraction in Parameters submodel.
        Parameters use 'input' schemas (for writable values). Scans every
        configured interface, tagging each property with its owning interface
        key (see _extract_interface_properties).

        Returns:
            List of property dicts with name, schema URL (from input field),
            and the owning interface key
        """
        interface_config = self.system_config.get('AID', {}) or self.system_config.get(
            'AssetInterfacesDescription', {}) or {}
        if not isinstance(interface_config, dict):
            # An LLM occasionally emits the whole section as a bare
            # "[VERIFY: ...]" string instead of an object; treat as absent.
            interface_config = {}

        properties = []
        for iface_key, iface_cfg in interface_config.items():
            if not isinstance(iface_cfg, dict):
                continue
            interaction_config = _as_named_dict(iface_cfg.get('InteractionMetadata', {}))
            properties_dict = _as_named_dict(interaction_config.get('properties', {}))
            for prop_name, prop_config in properties_dict.items():
                if isinstance(prop_config, dict):
                    properties.append({
                        'name': prop_name,
                        'schema': prop_config.get('input'),
                        'interface': iface_key,
                    })

        return properties

    def _build_object_store(self) -> model.DictObjectStore:
        """
        Build the complete AAS object store with all submodels.

        Returns:
            DictObjectStore containing AAS and all submodels
        """
        obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore(
        )

        # Generate main AAS shell
        aas = self.aas_builder.build(self.system_id, self.system_config)
        obj_store.add(aas)

        # Extract interface properties for schema-driven field extraction
        interface_properties = self._extract_interface_properties()
        # Extract input properties for Parameters submodel
        interface_input_properties = self._extract_interface_input_properties()

        # Generate standard submodels — only include sections present in config
        cfg = self.system_config

        if cfg.get('DigitalNameplate') is not None:
            obj_store.add(self.nameplate_builder.build(self.system_id, cfg))

        if cfg.get('AID') or cfg.get('AssetInterfacesDescription'):
            obj_store.add(self.asset_interfaces_builder.build(self.system_id, cfg))

        if cfg.get('OperationalData') or cfg.get('Variables'):
            obj_store.add(self.variables_builder.build(self.system_id, cfg, interface_properties))

        if cfg.get('Parameters'):
            obj_store.add(self.parameters_builder.build(self.system_id, cfg, interface_input_properties))

        if cfg.get('HierarchicalStructures') is not None:
            obj_store.add(self.hierarchical_structures_builder.build(self.system_id, cfg))

        if cfg.get('Capabilities'):
            obj_store.add(self.capabilities_builder.build(self.system_id, cfg))

        if cfg.get('Skills'):
            obj_store.add(self.skills_builder.build(self.system_id, cfg))

        # Generate Process AAS specific submodels (if config contains them)
        process_submodels = self._build_process_submodels()
        for submodel in process_submodels:
            if submodel is not None:
                obj_store.add(submodel)

        return obj_store

    def _build_process_submodels(self) -> list:
        """
        Build Process AAS specific submodels if the config contains them.

        Returns:
            List of Process-specific submodels (may contain None values)
        """
        submodels = []

        # Check if this is a Process AAS by looking for Process-specific sections
        has_process_info = 'ProcessInformation' in self.system_config
        has_required_caps = 'RequiredCapabilities' in self.system_config
        has_policy = 'Policy' in self.system_config

        if has_process_info:
            submodels.append(self.process_info_builder.build(
                self.system_id, self.system_config))

        if has_required_caps:
            submodels.append(self.required_capabilities_builder.build(
                self.system_id, self.system_config))

        if has_policy:
            submodels.append(self.policy_builder.build(
                self.system_id, self.system_config))

        return submodels

    # ==================== Serialization Methods ====================

    def _serialize_to_dict(self, obj_store: model.DictObjectStore) -> Dict:
        """
        Serialize object store to dictionary format.

        Args:
            obj_store: DictObjectStore to serialize

        Returns:
            Dictionary representation of the object store
        """
        json_data = json_serialization.object_store_to_json(obj_store)
        aas_dict = json.loads(json_data)
        return self._normalize_submodel_references(aas_dict)

    # ==================== Validation Methods ====================

    def _validate_object_store(self, obj_store: model.DictObjectStore) -> bool:
        """
        Validate the generated AAS object store.

        Args:
            obj_store: The DictObjectStore containing generated AAS objects

        Returns:
            True if validation passed (no errors), False otherwise
        """
        print(f"Validating {self.system_id}...")

        validator = AASValidator()
        result = validator.validate(obj_store)

        if not result.is_valid():
            print(f"\n⚠️  Validation errors found:")
            print(result.summary())
            return False

        if result.warnings:
            print(
                f"\n✓ Validation passed (with {len(result.warnings)} warning(s))")
            print("Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        else:
            print(f"✓ Validation passed")

        return True


def main():
    """Main entry point for the script."""

    parser = argparse.ArgumentParser(
        description='Generate AAS descriptions from configuration file'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='output_test/resource_config.yaml',
        help='Path to the JSON/YAML configuration file (default: output_test/resource_config.yaml)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='Resource/',
        help='Output directory for generated JSON file (default: output_test/Resource/)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate generated AAS (default: enabled)'
    )
    parser.add_argument(
        '--no-validate',
        dest='validate',
        action='store_false',
        help='Disable AAS validation'
    )
    parser.add_argument(
        '--delegation-url',
        type=str,
        default=None,
        help='Base URL for Operation Delegation Service (e.g., http://registration-service:8087). '
             'If not specified, uses DELEGATION_SERVICE_URL env var or default.'
    )

    args = parser.parse_args()

    # Create generator
    generator = AASGenerator(
        args.config, delegation_base_url=args.delegation_url)

    # Generate the system
    success = generator.generate_all(args.output, validate=args.validate)

    print("\nGeneration complete!")
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
