"""
Convert a YAML generator-profile config dict to a lightweight rdflib Graph
suitable for pre-generation SHACL guidance checking.

This mirrors the RDF conventions of tools/mock_resourceaas_to_rdf.py but works
directly from the YAML profile dict, without requiring a full AAS JSON round-trip.
"""
from __future__ import annotations

from rdflib import Graph, Literal, Namespace, RDF, URIRef

CSS  = Namespace("http://www.w3id.org/hsu-aut/css#")
ARSO = Namespace("http://www.w3id.org/aau-ra/cssx#")
AASV = Namespace("http://www.w3id.org/aau-ra/resourceaas-validation#")


def config_to_rdf(system_id: str, config: dict) -> Graph:
    """
    Build a lightweight RDF graph from a YAML generator-profile config dict.

    The graph uses the same ontology terms as mock_resourceaas_to_rdf.py so
    the same SHACL shapes can validate it.
    """
    g = Graph()
    g.bind("css",  CSS)
    g.bind("arso", ARSO)
    g.bind("aasv", AASV)

    resource_id = config.get("id", f"https://placeholder/{system_id}")
    resource = URIRef(resource_id)
    g.add((resource, RDF.type, CSS.Resource))

    # â”€â”€ DigitalNameplate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    nameplate = config.get("DigitalNameplate")
    if nameplate is not None:
        sm_uri = URIRef(f"{resource_id}#sm-nameplate")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.DigitalNameplateSubmodel))
        if isinstance(nameplate, dict):
            mfr_name = nameplate.get("ManufacturerName")
            if mfr_name:
                mfr_uri = URIRef(f"{resource_id}#manufacturer")
                g.add((mfr_uri, RDF.type, ARSO.Manufacturer))
                g.add((mfr_uri, ARSO.manufacturerName, Literal(str(mfr_name))))
                g.add((resource, ARSO.hasManufacturer, mfr_uri))
            serial = nameplate.get("SerialNumber")
            if serial:
                g.add((resource, ARSO.serialNumber, Literal(str(serial))))
            year = nameplate.get("YearOfConstruction")
            if year is not None:
                g.add((resource, ARSO.yearOfConstruction, Literal(str(year))))
            date_mfr = nameplate.get("DateOfManufacture")
            if date_mfr:
                g.add((resource, ARSO.dateOfManufacture, Literal(str(date_mfr))))

    # â”€â”€ HierarchicalStructures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hs_config = config.get("HierarchicalStructures")
    if hs_config is not None:
        sm_uri = URIRef(f"{resource_id}#sm-hier")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.HierarchicalStructuresSubmodel))
        if isinstance(hs_config, dict):
            name = hs_config.get("Name")
            if name:
                g.add((sm_uri, AASV.bomName, Literal(str(name))))
            archetype = hs_config.get("Archetype")
            if archetype:
                g.add((sm_uri, AASV.bomArchetype, Literal(str(archetype))))
            # Project entity entries so SHACL can validate globalAssetId presence
            entity_dict_key = (
                "IsPartOf" if archetype == "OneUp"
                else "HasPart" if archetype == "OneDown"
                else None
            )
            if entity_dict_key:
                entries = hs_config.get(entity_dict_key) or {}
                for entry_name, entry_data in (entries.items() if isinstance(entries, dict) else []):
                    if not isinstance(entry_data, dict):
                        entry_data = {}
                    safe = entry_name.lower().replace(" ", "-")
                    entry_uri = URIRef(f"{resource_id}#bom-entry-{safe}")
                    g.add((sm_uri, AASV.hasBomEntry, entry_uri))
                    g.add((entry_uri, RDF.type, AASV.BomEntry))
                    g.add((entry_uri, AASV.bomEntryName, Literal(entry_name)))
                    global_asset_id = entry_data.get("globalAssetId")
                    if global_asset_id:
                        g.add((entry_uri, AASV.bomEntryGlobalAssetId, Literal(str(global_asset_id))))

    # â”€â”€ AID â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    aid = config.get("AID") or config.get("AssetInterfacesDescription")
    ri_uri: URIRef | None = None
    if aid:
        sm_uri = URIRef(f"{resource_id}#sm-aid")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.AIDSubmodel))
        ri_uri = URIRef(f"{resource_id}#resource-software-interface-1")
        g.add((ri_uri, RDF.type, ARSO.SoftwareInterface))
        g.add((resource, ARSO.hasResourceInterface, ri_uri))

    # â”€â”€ Variables (OperationalData) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if config.get("Variables"):
        sm_uri = URIRef(f"{resource_id}#sm-opdata")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.OperationalDataSubmodel))
        opdata_uri = URIRef(f"{resource_id}#operational-data-1")
        g.add((opdata_uri, RDF.type, ARSO.OperationalData))
        g.add((resource, ARSO.hasOperationalData, opdata_uri))

    # â”€â”€ Parameters â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if config.get("Parameters"):
        sm_uri = URIRef(f"{resource_id}#sm-params")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.ParametersSubmodel))
        param_uri = URIRef(f"{resource_id}#resource-parameter-1")
        g.add((param_uri, RDF.type, ARSO.ResourceParameter))
        g.add((resource, ARSO.hasResourceParameter, param_uri))

    # â”€â”€ Skills â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Add the submodel marker even when the dict is empty, so SHACL can detect
    # that the Skills submodel has been selected (for co-presence checks).
    skills_config = config.get("Skills")
    if skills_config is not None:
        sm_uri = URIRef(f"{resource_id}#sm-skills")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.SkillsSubmodel))
    skills: dict = skills_config or {}
    skill_uris: dict[str, URIRef] = {}
    for skill_name, skill_data in skills.items():
        if not isinstance(skill_data, dict):
            skill_data = {}
        safe = skill_name.lower().replace(" ", "-")
        skill_uri = URIRef(f"{resource_id}#skill-{safe}")
        skill_uris[skill_name] = skill_uri
        g.add((skill_uri, RDF.type, CSS.Skill))
        g.add((resource, CSS.providesSkill, skill_uri))
        g.add((skill_uri, AASV.sourceIdShort, Literal(skill_name)))
        semantic_id = skill_data.get("semantic_id")
        if semantic_id:
            g.add((skill_uri, AASV.sourceSemanticId, Literal(str(semantic_id))))
        # SkillInterface â€” always add; link to ResourceInterface when AID present
        si_uri = URIRef(f"{resource_id}#skill-interface-{safe}")
        g.add((si_uri, RDF.type, CSS.SkillInterface))
        g.add((skill_uri, CSS.accessibleThrough, si_uri))
        if ri_uri is not None:
            g.add((si_uri, ARSO.skillInterfaceUsesResourceInterface, ri_uri))

    # â”€â”€ Capabilities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Same pattern: marker added even when dict is empty.
    caps_config = config.get("Capabilities")
    if caps_config is not None:
        sm_uri = URIRef(f"{resource_id}#sm-capabilities")
        g.add((resource, AASV.hasSubmodel, sm_uri))
        g.add((sm_uri, RDF.type, AASV.CapabilitiesSubmodel))
    caps: dict = caps_config or {}
    for cap_name, cap_data in caps.items():
        if not isinstance(cap_data, dict):
            cap_data = {}
        safe = cap_name.lower().replace(" ", "-")
        cap_uri = URIRef(f"{resource_id}#capability-{safe}")
        g.add((cap_uri, RDF.type, CSS.Capability))
        g.add((resource, CSS.providesCapability, cap_uri))
        g.add((cap_uri, AASV.sourceIdShort, Literal(cap_name)))
        semantic_id = cap_data.get("semantic_id")
        if semantic_id:
            g.add((cap_uri, AASV.sourceSemanticId, Literal(str(semantic_id))))
        realized_by = cap_data.get("realizedBy")
        if realized_by and realized_by in skill_uris:
            g.add((cap_uri, CSS.isRealizedBySkill, skill_uris[realized_by]))

    return g


