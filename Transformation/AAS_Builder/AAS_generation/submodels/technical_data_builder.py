"""TechnicalData Submodel Builder (IDTA 02003)."""

import datetime
from typing import Any, Dict, List, Optional
from basyx.aas import model


class TechnicalDataSubmodelBuilder:
    """Builds the TechnicalData submodel.

    Carries manufacturer-declared technical properties: GeneralInformation,
    optional ProductClassifications, a free-form TechnicalProperties tree, and
    optional FurtherInformation.
    """

    # GeneralInformation children, in template order.
    _GENERAL_FIELDS = (
        ("ManufacturerName", "TD_MANUFACTURER_NAME", "property"),
        ("ManufacturerProductDesignation", "TD_PRODUCT_DESIGNATION", "mlp"),
        ("ManufacturerArticleNumber", "TD_ARTICLE_NUMBER", "property"),
        ("ManufacturerOrderCode", "TD_ORDER_CODE", "property"),
    )

    _CLASSIFICATION_FIELDS = (
        ("ClassificationSystem", "TD_CLASSIFICATION_SYSTEM"),
        ("ClassificationSystemVersion", "TD_CLASSIFICATION_VERSION"),
        ("ProductClassId", "TD_PRODUCT_CLASS_ID"),
        ("ProductClassCodedName", "TD_PRODUCT_CLASS_CODED"),
    )

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

    def build(self, system_id: str, config: Dict) -> model.Submodel:
        """Create the TechnicalData submodel.

        Args:
            system_id: Unique identifier for the system.
            config: Config dict; reads the 'TechnicalData' section, with optional
                GeneralInformation / ProductClassifications / TechnicalProperties /
                FurtherInformation subsections.

        Returns:
            TechnicalData submodel instance.
        """
        cfg = config.get("TechnicalData") or {}
        if not isinstance(cfg, dict):
            # LLM sometimes emits a bare "[VERIFY: ...]" string; treat as absent.
            cfg = {}

        elements: List[model.SubmodelElement] = [
            self._general_information(cfg.get("GeneralInformation"), config)
        ]

        classifications = self._product_classifications(cfg.get("ProductClassifications"))
        if classifications is not None:
            elements.append(classifications)

        areas = self._property_areas(
            cfg.get("TechnicalPropertyAreas") or cfg.get("TechnicalProperties"))
        if areas is not None:
            elements.append(areas)

        further = self._further_information(cfg.get("FurtherInformation"))
        if further is not None:
            elements.append(further)

        return model.Submodel(
            id_=f"{self.base_url}/submodels/instances/{system_id}/TechnicalData",
            id_short="TechnicalData",
            kind=model.ModellingKind.INSTANCE,
            semantic_id=self.semantic_factory.TECHNICAL_DATA_SUBMODEL,
            administration=model.AdministrativeInformation(version="2", revision="0"),
            submodel_element=elements,
        )

    def _general_information(self, section, root_config: Dict) -> model.SubmodelElementCollection:
        """Build GeneralInformation, falling back to nameplate-level values.

        Args:
            section: The GeneralInformation config, or None.
            root_config: Full system config, used for manufacturer fallbacks.

        Returns:
            GeneralInformation SubmodelElementCollection.
        """
        section = section if isinstance(section, dict) else {}
        nameplate = root_config.get("DigitalNameplate") or {}
        if not isinstance(nameplate, dict):
            nameplate = {}

        # All four are mandatory; reuse the nameplate value rather than emit nothing.
        fallbacks = {
            "ManufacturerName": nameplate.get("ManufacturerName"),
            "ManufacturerProductDesignation": nameplate.get("ManufacturerProductDesignation"),
            "ManufacturerArticleNumber": nameplate.get("ManufacturerArticleNumber")
            or nameplate.get("ProductArticleNumberOfManufacturer"),
            "ManufacturerOrderCode": nameplate.get("OrderCodeOfManufacturer"),
        }

        children: List[model.SubmodelElement] = []
        for id_short, sid_attr, kind in self._GENERAL_FIELDS:
            value = section.get(id_short) or fallbacks.get(id_short)
            if not value:
                continue
            semantic_id = getattr(self.semantic_factory, sid_attr)
            if kind == "mlp":
                children.append(self.element_factory.create_multi_language_property(
                    id_short=id_short, text=str(value), semantic_id=semantic_id))
            else:
                children.append(self.element_factory.create_property(
                    id_short=id_short, value=str(value),
                    value_type=model.datatypes.String, semantic_id=semantic_id))

        return self.element_factory.create_collection(
            id_short="GeneralInformation",
            elements=children,
            semantic_id=self.semantic_factory.TD_GENERAL_INFORMATION,
        )

    def _product_classifications(self, section) -> Optional[model.SubmodelElementList]:
        """Build the ProductClassifications list, or None when unconfigured.

        Args:
            section: List of classification dicts, or a single dict.

        Returns:
            ProductClassifications SubmodelElementList, or None.
        """
        if isinstance(section, dict):
            section = [section]
        if not isinstance(section, list) or not section:
            return None

        entries: List[model.SubmodelElement] = []
        for item in section:
            if not isinstance(item, dict):
                continue
            children = [
                self.element_factory.create_property(
                    id_short=id_short, value=str(item[id_short]),
                    value_type=model.datatypes.String,
                    semantic_id=getattr(self.semantic_factory, sid_attr))
                for id_short, sid_attr in self._CLASSIFICATION_FIELDS
                if item.get(id_short)
            ]
            if children:
                entries.append(self.element_factory.create_collection(
                    id_short=None, elements=children,
                    semantic_id=self.semantic_factory.TD_PRODUCT_CLASSIFICATION))
        if not entries:
            return None

        return model.SubmodelElementList(
            id_short="ProductClassifications",
            type_value_list_element=model.SubmodelElementCollection,
            semantic_id=self.semantic_factory.TD_PRODUCT_CLASSIFICATIONS,
            value=entries,
        )

    def _property_areas(self, section) -> Optional[model.SubmodelElementList]:
        """Build TechnicalPropertyAreas from the datasheet's property tree.

        IDTA nests the areas as positional SMCs inside the list (AASd-120 bars
        an idShort on a list child), so the datasheet's own group names become
        Section collections one level down. Loose scalars go into "General".

        Args:
            section: Nested dict of datasheet properties.

        Returns:
            TechnicalPropertyAreas SubmodelElementList, or None when empty.
        """
        section = section if isinstance(section, dict) else {}
        if not section:
            return None

        sections: List[model.SubmodelElement] = []
        loose = {k: v for k, v in section.items() if not isinstance(v, dict)}
        for name, value in section.items():
            if isinstance(value, dict):
                sections.append(self.element_factory.create_collection(
                    id_short=str(name), elements=self._arbitrary_elements(value),
                    semantic_id=self.semantic_factory.TD_ARBITRARY))
        if loose:
            sections.append(self.element_factory.create_collection(
                id_short="General", elements=self._arbitrary_elements(loose),
                semantic_id=self.semantic_factory.TD_ARBITRARY))
        if not sections:
            return None

        area = self.element_factory.create_collection(
            id_short=None, elements=sections,
            semantic_id=self.semantic_factory.TD_PROPERTY_AREA)
        return model.SubmodelElementList(
            id_short="TechnicalPropertyAreas",
            type_value_list_element=model.SubmodelElementCollection,
            semantic_id=self.semantic_factory.TD_PROPERTY_AREAS,
            value=[area],
        )

    def _arbitrary_elements(self, section: Dict) -> List[model.SubmodelElement]:
        """Convert a nested datasheet dict into arbitrary-marked SMEs."""
        out: List[model.SubmodelElement] = []
        arbitrary = self.semantic_factory.TD_ARBITRARY
        for name, value in section.items():
            if isinstance(value, dict) and {"min", "max"} <= set(value):
                out.append(self.element_factory.create_range(
                    id_short=str(name), min_value=str(value["min"]),
                    max_value=str(value["max"]),
                    value_type=model.datatypes.String, semantic_id=arbitrary))
            elif isinstance(value, dict):
                out.append(self.element_factory.create_collection(
                    id_short=str(name), elements=self._arbitrary_elements(value),
                    semantic_id=arbitrary))
            elif isinstance(value, (list, tuple)):
                out.append(self.element_factory.create_collection(
                    id_short=str(name),
                    elements=self._arbitrary_elements(
                        {f"{name}{i}": v for i, v in enumerate(value, 1)}),
                    semantic_id=arbitrary))
            elif value not in (None, ""):
                out.append(self.element_factory.create_property(
                    id_short=str(name), value=str(value),
                    value_type=model.datatypes.String, semantic_id=arbitrary))
        return out

    @staticmethod
    def _as_date(value) -> Optional[datetime.date]:
        """Parse an ISO date string (or pass a date through); None if unparseable."""
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.date.fromisoformat(str(value).strip()[:10])
        except (ValueError, TypeError):
            return None

    def _further_information(self, section) -> Optional[model.SubmodelElementCollection]:
        """Build FurtherInformation, or None without a ValidDate.

        Args:
            section: Config with optional TextStatement(s) and a ValidDate.

        Returns:
            FurtherInformation SubmodelElementCollection, or None. IDTA makes
            ValidDate mandatory once the collection exists, so a section without
            one is dropped rather than emitted incomplete.
        """
        if not isinstance(section, dict):
            return None
        valid_date = section.get("ValidDate")
        if not valid_date:
            return None

        statements = section.get("TextStatement") or []
        if isinstance(statements, str):
            statements = [statements]

        children: List[model.SubmodelElement] = [
            self.element_factory.create_multi_language_property(
                id_short="TextStatement", text=str(text),
                semantic_id=self.semantic_factory.TD_TEXT_STATEMENT)
            for text in statements if text
        ]
        # xs:date needs a real date; fall back to a string Property when the
        # source value isn't parseable rather than dropping the element.
        parsed = self._as_date(valid_date)
        children.append(self.element_factory.create_property(
            id_short="ValidDate",
            value=parsed if parsed is not None else str(valid_date),
            value_type=model.datatypes.Date if parsed is not None else model.datatypes.String,
            semantic_id=self.semantic_factory.TD_VALID_DATE))

        return self.element_factory.create_collection(
            id_short="FurtherInformation",
            elements=children,
            semantic_id=self.semantic_factory.TD_FURTHER_INFORMATION,
        )
