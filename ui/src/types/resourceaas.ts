// TypeScript interfaces for the ResourceAAS form state and API responses.

// ── Identity / profile container ─────────────────────────────────────────────

export interface ResourceAASProfile {
  [systemId: string]: SystemConfig;
}

export interface SystemConfig {
  idShort: string;
  id: string;
  globalAssetId: string;
  // Pass-through root-level profile fields (CORE_PROFILE_KEYS in
  // profile_structure.py) -- no form input yet, but they round-trip untouched.
  assetType?: string;
  serialNumber?: string;
  derivedFrom?: string;
  location?: string;
  DigitalNameplate?: DigitalNameplate;
  AID?: Record<string, AIDInterface>;
  Variables?: Record<string, Variable>;
  Parameters?: Record<string, Parameter>;
  HierarchicalStructures?: HierarchicalStructures;
  Capabilities?: Record<string, Capability>;
  Skills?: Record<string, Skill>;
  TechnicalData?: TechnicalData;
  AIMC?: Record<string, AIMCInterfaceMapping>;
  /** Per-submodel AAS id/semanticId overrides. Key = SubmodelKey (e.g. 'Skills'). */
  _meta?: Record<string, { id?: string; semanticId?: string }>;
}

// ── TechnicalData (IDTA 02003) ───────────────────────────────────────────────

export interface TechnicalClassification {
  ClassificationSystem?: string;
  ClassificationSystemVersion?: string;
  ProductClassId?: string;
  ProductClassCodedName?: string;
}

/** Datasheet value: plain string, a {min,max} range, or a nested section. */
export type TechnicalValue = string | { min?: string; max?: string } | { [name: string]: TechnicalValue };

export interface TechnicalData {
  GeneralInformation?: {
    ManufacturerName?: string;
    ManufacturerProductDesignation?: string;
    ManufacturerArticleNumber?: string;
    ManufacturerOrderCode?: string;
  };
  ProductClassifications?: TechnicalClassification[];
  /** Section name -> property name -> value. */
  TechnicalProperties?: Record<string, Record<string, TechnicalValue>>;
  FurtherInformation?: { TextStatement?: string | string[]; ValidDate?: string };
}

// ── AIMC (IDTA 02027) ────────────────────────────────────────────────────────

export interface AIMCMapping {
  /** AID property name under InteractionMetadata.properties. */
  source: string;
  /** OperationalData or Parameters entry name. */
  sink: string;
  sinkSubmodel?: 'OperationalData' | 'Parameters';
  pollingInterval?: string | number;
}

/** One AID interface's mappings, keyed by interface name in the profile. */
export interface AIMCInterfaceMapping {
  DefaultPollingInterval?: string | number;
  Mappings?: AIMCMapping[];
}

// ── Submodel form-state types ─────────────────────────────────────────────────

export interface NameplateAddress {
  Street?: string;
  ZipCode?: string;
  CityTown?: string;
  NationalCode?: string;
}

export interface DigitalNameplate {
  URIOfTheProduct?: string;
  ManufacturerName: string;
  ManufacturerProductDesignation?: string;
  ManufacturerProductFamily?: string;
  ManufacturerArticleNumber?: string;
  OrderCodeOfManufacturer?: string;
  AddressInformation?: NameplateAddress;
  SerialNumber: string;
  YearOfConstruction?: string;   // YYYY
  DateOfManufacture?: string;    // YYYY-MM-DD
  HardwareVersion?: string;
  SoftwareVersion?: string;
  CountryOfOrigin?: string;
}

export type AIDProtocol = 'MQTT' | 'HTTP' | 'MODBUS';

export interface AIDInterface {
  Title?: string;
  protocol?: AIDProtocol;
  EndpointMetadata?: AIDEndpointMetadata;
  InteractionMetadata?: AIDInteractionMetadata;
  supplementalSemanticIds?: string[];
}

export interface AIDEndpointMetadata {
  base: string;
  contentType: string;
  // MODBUS endpoint-level byte/word ordering
  modv_mostSignificantByte?: string;   // 'true' | 'false'
  modv_mostSignificantWord?: string;   // 'true' | 'false'
}

export interface AIDInteractionMetadata {
  properties?: Record<string, AIDProperty>;
  actions?: Record<string, AIDAction>;
  events?: Record<string, AIDEvent>;
}

export interface AIDProperty {
  key?: string;
  title?: string;
  observable?: string;    // 'true' | 'false'
  unit?: string;          // e.g. 'kg', 'mm'
  output?: string;        // semantic schema URI for the property value
  forms?: AIDForms;
  semanticId?: string;    // override for WOT_PROPERTY_AFFORDANCE
}

export interface AIDEvent {
  key?: string;
  title?: string;
  output?: string;        // schema URI for the event data payload
  forms?: AIDForms;
  semanticId?: string;    // override for WOT_EVENT_AFFORDANCE
}

export interface AIDAction {
  key?: string;
  title?: string;
  synchronous?: string;   // 'true' | 'false'
  input?: string;         // schema URI for request payload
  output?: string;        // schema URI for response payload
  forms?: AIDForms;       // request channel (subscribe)
  semanticId?: string;    // override for WOT_ACTION_AFFORDANCE
}

export interface AIDForms {
  href: string;
  contentType?: string;
  op?: string;                  // e.g. 'invokeAction', 'readProperty'
  // MQTT bindings (mqv_)
  mqv_retain?: string;          // 'true' | 'false'
  mqv_controlPacket?: string;   // 'subscribe' | 'publish'
  mqv_qos?: string;             // '0' | '1' | '2'
  response?: AIDFormResponse;
  // HTTP bindings (htv_)
  htv_methodName?: string;      // GET | POST | PUT | DELETE | PATCH
  // MODBUS bindings (modv_)
  modv_function?: string;       // readCoils | readHoldingRegisters | etc.
  modv_entity?: string;         // coils | discreteInputs | inputRegisters | holdingRegisters
  modv_zeroBasedAddressing?: string;   // 'true' | 'false'
  modv_pollingTime?: string;           // ms
  modv_timeout?: string;               // ms
  modv_type?: string;                  // xsd:integer | xsd:boolean | etc.
  modv_mostSignificantByte?: string;   // 'true' | 'false'
  modv_mostSignificantWord?: string;   // 'true' | 'false'
}

export interface AIDFormResponse {
  href?: string;
  contentType?: string;
  mqv_controlPacket?: string;
  mqv_retain?: string;
}

export interface Variable {
  // idShort of the AID property/action this variable reads. Key name matches the
  // Python profile dict exactly, since this object is posted as-is.
  InterfaceReference?: string;
  semanticId?: string;
}

export interface Parameter {
  // Same InterfaceReference-based shape as Variable -- parameters_builder.py
  // mirrors variables_builder.py exactly.
  InterfaceReference?: string;
  semanticId?: string;
}

export interface BomEntity {
  globalAssetId?: string;
  systemId?: string;
  aasId?: string;
  submodelId?: string;
}

// Archetype is the ontology's ArcheType owl:oneOf enum. No SameAs field -- the
// builder writes that reference into every IsPartOf/HasPart node itself.
export interface HierarchicalStructures {
  Name: string;
  Archetype?: 'OneUp' | 'OneDown' | 'Full';
  IsPartOf?: Record<string, BomEntity>;
  HasPart?: Record<string, BomEntity>;
}

export interface Capability {
  semantic_id: string;
  realizedBy?: string;
  _containerSemanticId?: string;  // override for CAPABILITY_CONTAINER element semanticId
}

export interface Skill {
  semantic_id: string;
  // idShort of the AID action this skill invokes. Required; Operation variables
  // and qualifiers are derived server-side from that action's schema.
  interface: string;
  description?: string;
}

// ── API response types (mirrors api/models.py) ────────────────────────────────

export interface ValidationIssue {
  severity: string;
  message: string;
  field: string;        // dot-path for UI step routing, e.g. "DigitalNameplate.SerialNumber"
  focus_node?: string;
  result_path?: string;
}

export interface ValidateResponse {
  conforms: boolean;
  issues: ValidationIssue[];
  report_ttl: string;
}
