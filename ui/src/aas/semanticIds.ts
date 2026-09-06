/**
 * Semantic ID URI constants — ported from generation/core/semantic_ids.py.
 * Used by the TypeScript AAS builders to set standard semantic IDs.
 */

// ── IDTA submodel semantic IDs ────────────────────────────────────────────────
// These must match the arso:semanticId value(s) declared on the corresponding
// class in Ontology/ARSO/Modules/*.ttl — that's what the backend's
// Transformation/AAS_to_RDF/aas_to_rdf.py converter actually matches against
// to type a submodel. A mismatch here means the submodel silently never gets
// its ARSO type (or the ontology's SHACL validation for it) at all.
export const DIGITAL_NAMEPLATE_SUBMODEL  = 'https://admin-shell.io/idta/nameplate/3/0/Nameplate';
export const HIERARCHICAL_STRUCTURES     = 'https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel';
export const OPERATIONAL_DATA_SUBMODEL   = 'https://smartproductionlab.aau.dk/ARSO/OperationalData/1/0/Submodel';
export const PARAMETERS_SUBMODEL         = 'https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel';

// ── IDTA HierarchicalStructures element semantic IDs ─────────────────────────
export const HIERARCHICAL_ARCHETYPE     = 'https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0';
export const HIERARCHICAL_ENTRY_NODE    = 'https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0';
export const HIERARCHICAL_NODE          = 'https://admin-shell.io/idta/HierarchicalStructures/Node/1/0';
export const HIERARCHICAL_SAME_AS       = 'https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0';
export const HIERARCHICAL_RELATIONSHIP  = 'https://admin-shell.io/idta/HierarchicalStructures/Relationship/1/0';

// ── IDTA AID semantic IDs ─────────────────────────────────────────────────────
export const AID_SUBMODEL               = 'https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Submodel';
export const AID_INTERFACE              = 'https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface';
export const AID_INTERACTION_METADATA   = 'https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata';
export const AID_INTERFACE_REFERENCE    = 'https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InterfaceReference';

// ── W3C WoT ───────────────────────────────────────────────────────────────────
export const WOT_ACTION_AFFORDANCE      = 'https://www.w3.org/2019/wot/td#ActionAffordance';
export const WOT_PROPERTY_AFFORDANCE    = 'https://www.w3.org/2019/wot/td#PropertyAffordance';
export const WOT_EVENT_AFFORDANCE       = 'https://www.w3.org/2019/wot/td#EventAffordance';

// ── W3C WoT supplemental protocol URIs ───────────────────────────────────────
export const WOT_TD                     = 'https://www.w3.org/2019/wot/td';
export const WOT_INTERACTION_AFFORDANCE = 'https://www.w3.org/2019/wot/td#InteractionAffordance';
export const MQTT_PROTOCOL              = 'http://www.w3.org/2011/mqtt';
export const HTTP_PROTOCOL              = 'https://www.w3.org/2019/wot/http';
export const MODBUS_PROTOCOL            = 'https://www.w3.org/2019/wot/modbus';

// ── Custom submodel semantic IDs ──────────────────────────────────────────────
export const SKILLS_SUBMODEL            = 'https://admin-shell.io/idta/ControlComponentType/1/0';
export const CAPABILITIES_SUBMODEL      = 'https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0';
export const CAPABILITY_SET             = 'https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet#1/0';
export const CAPABILITY_CONTAINER       = 'https://smartfactory.de/aas/submodel/OfferedCapabilityDescription/CapabilitySet/CapabilityContainer#1/0';
export const CAPABILITY_REALIZED_BY     = 'https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0';

// ── Base URL for custom semantic IDs ─────────────────────────────────────────
export const SEMANTIC_ID_BASE           = 'https://smartproductionlab.aau.dk';
