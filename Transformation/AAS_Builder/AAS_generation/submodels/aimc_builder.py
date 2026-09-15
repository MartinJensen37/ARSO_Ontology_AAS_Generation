"""AIMC Submodel Builder (IDTA 02027, Asset Interfaces Mapping Configuration)."""

from typing import Any, Dict, List, Optional
from basyx.aas import model

_SMC = model.KeyTypes.SUBMODEL_ELEMENT_COLLECTION
_SM = model.KeyTypes.SUBMODEL


class AIMCSubmodelBuilder:
    """Builds the AssetInterfacesMappingConfiguration submodel.

    One MappingConfiguration per AID interface, each pairing Sources (AID
    properties) with Sinks (the elements receiving those values).
    """

    DEFAULT_SINK_SUBMODEL = "OperationalData"

    def __init__(self, base_url: str, semantic_factory, element_factory=None):
        """
        Args:
            base_url: Base URL for AAS identifiers.
            semantic_factory: SemanticIdFactory instance.
            element_factory: AASElementFactory instance.
        """
        self.base_url = base_url
        self.semantic_factory = semantic_factory
        self.element_factory = element_factory

    def build(self, system_id: str, config: Dict) -> Optional[model.Submodel]:
        """Create the AIMC submodel.

        Args:
            system_id: Unique identifier for the system.
            config: Config dict; reads the 'AIMC' section, mapping each AID
                interface name to {DefaultPollingInterval, Mappings}.

        Returns:
            AIMC submodel, or None when no interface yields a usable mapping.
        """
        cfg = config.get("AIMC") or config.get("AssetInterfacesMappingConfiguration") or {}
        if not isinstance(cfg, dict):
            # LLM sometimes emits a bare "[VERIFY: ...]" string; treat as absent.
            cfg = {}

        configurations = [
            smc for iface_name, iface_cfg in cfg.items()
            if (smc := self._mapping_configuration(system_id, iface_name, iface_cfg)) is not None
        ]
        if not configurations:
            return None

        mapping_list = model.SubmodelElementList(
            id_short="MappingConfigurations",
            type_value_list_element=model.SubmodelElementCollection,
            order_relevant=False,
            semantic_id=self.semantic_factory.AIMC_CONFIGURATIONS,
            value=configurations,
        )

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/AssetInterfacesMappingConfiguration",
            id_short="AssetInterfacesMappingConfiguration",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.AIMC_SUBMODEL,
            administration=model.AdministrativeInformation(version="2", revision="0"),
            submodel_element=[mapping_list],
        )

    def _mapping_configuration(self, system_id: str, iface_name: str,
                               iface_cfg: Any) -> Optional[model.SubmodelElementCollection]:
        """Build one MappingConfiguration for a single AID interface.

        Args:
            system_id: System identifier.
            iface_name: AID interface idShort, e.g. "InterfaceMQTT".
            iface_cfg: Config for that interface.

        Returns:
            MappingConfiguration SMC, or None when it has no valid mappings.
        """
        mappings = self._normalize_mappings(iface_cfg)
        if not mappings:
            return None

        children: List[model.SubmodelElement] = [
            model.ReferenceElement(
                id_short="InterfaceReference",
                value=self._reference(system_id, "AID", [iface_name]),
            )
        ]

        polling = iface_cfg.get("DefaultPollingInterval") if isinstance(iface_cfg, dict) else None
        if polling is not None:
            children.append(self.element_factory.create_property(
                id_short="DefaultPollingInterval", value=float(polling),
                value_type=model.datatypes.Double,
                semantic_id=self.semantic_factory.AIMC_DEFAULT_POLLING))

        sources, sinks = [], []
        for entry in mappings:
            sources.append(self._source(system_id, iface_name, entry))
            sinks.append(self._sink(system_id, entry))

        children.append(model.SubmodelElementList(
            id_short="Sources", type_value_list_element=model.SubmodelElementCollection,
            semantic_id=self.semantic_factory.AIMC_SOURCES, value=sources))
        children.append(model.SubmodelElementList(
            id_short="Sinks", type_value_list_element=model.SubmodelElementCollection,
            semantic_id=self.semantic_factory.AIMC_SINKS, value=sinks))

        return self.element_factory.create_collection(
            id_short=None, elements=children,
            semantic_id=self.semantic_factory.AIMC_CONFIGURATION)

    @staticmethod
    def _normalize_mappings(iface_cfg: Any) -> List[Dict[str, Any]]:
        """Coerce the Mappings config into a list of {source, sink, ...} dicts.

        Accepts a list of dicts, or the compact {source: sink} dict form.

        Args:
            iface_cfg: One interface's config.

        Returns:
            List of mapping dicts, each with at least 'source' and 'sink'.
        """
        if not isinstance(iface_cfg, dict):
            return []
        raw = iface_cfg.get("Mappings") or iface_cfg.get("mappings") or []
        out: List[Dict[str, Any]] = []
        if isinstance(raw, dict):
            raw = [{"source": k, "sink": v} for k, v in raw.items()]
        if not isinstance(raw, list):
            return []
        for item in raw:
            if not isinstance(item, dict):
                continue
            source = item.get("source") or item.get("Source")
            sink = item.get("sink") or item.get("Sink") or source
            if not source:
                continue
            out.append({
                "source": str(source),
                "sink": str(sink),
                "sinkSubmodel": item.get("sinkSubmodel") or item.get("SinkSubmodel"),
                "pollingInterval": item.get("pollingInterval") or item.get("PollingInterval"),
            })
        return out

    def _source(self, system_id: str, iface_name: str,
                entry: Dict[str, Any]) -> model.SubmodelElementCollection:
        """Build one Source SMC pointing at an AID property."""
        children: List[model.SubmodelElement] = [
            model.ReferenceElement(
                id_short="Source",
                semantic_id=self.semantic_factory.AIMC_SOURCE_REF,
                value=self._reference(system_id, "AID", [
                    iface_name, "InteractionMetadata", "properties", entry["source"]]),
            ),
            self.element_factory.create_property(
                id_short="SourceId", value=entry["source"],
                value_type=model.datatypes.String,
                semantic_id=self.semantic_factory.AIMC_SOURCE_ID),
        ]
        if entry.get("pollingInterval") is not None:
            children.append(self.element_factory.create_property(
                id_short="PollingInterval", value=float(entry["pollingInterval"]),
                value_type=model.datatypes.Double,
                semantic_id=self.semantic_factory.AIMC_SOURCE_POLLING))
        return self.element_factory.create_collection(
            id_short=None, elements=children,
            semantic_id=self.semantic_factory.AIMC_SOURCE)

    def _sink(self, system_id: str, entry: Dict[str, Any]) -> model.SubmodelElementCollection:
        """Build one Sink SMC pointing at the element receiving the value."""
        target_sm = entry.get("sinkSubmodel") or self.DEFAULT_SINK_SUBMODEL
        children: List[model.SubmodelElement] = [
            model.ReferenceElement(
                id_short="Sink",
                semantic_id=self.semantic_factory.AIMC_SINK_REF,
                value=self._reference(system_id, target_sm, [entry["sink"]]),
            ),
            self.element_factory.create_property(
                id_short="SinkId", value=entry["sink"],
                value_type=model.datatypes.String,
                semantic_id=self.semantic_factory.AIMC_SINK_ID),
        ]
        return self.element_factory.create_collection(
            id_short=None, elements=children,
            semantic_id=self.semantic_factory.AIMC_SINK)

    def _reference(self, system_id: str, submodel_name: str,
                   path: List[str]) -> model.ModelReference:
        """Build a ModelReference into a submodel of this AAS.

        Args:
            system_id: System identifier.
            submodel_name: Last segment of the target submodel id.
            path: idShorts walked from the submodel down to the target element.

        Returns:
            ModelReference whose first key is the submodel (AASd-125).
        """
        keys = [model.Key(
            type_=_SM,
            value=f"{self.base_url}/submodels/instances/{system_id}/{submodel_name}")]
        keys += [model.Key(type_=_SMC, value=segment) for segment in path]
        return model.ModelReference(tuple(keys), model.SubmodelElementCollection)
