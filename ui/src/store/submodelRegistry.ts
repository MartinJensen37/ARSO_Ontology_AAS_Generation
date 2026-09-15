/**
 * Single UI registry of submodels. Keys and yamlKeys must match
 * Transformation/AAS_Builder/submodel_registry.py.
 *
 * Adding a submodel here makes TypeScript flag every remaining per-key map
 * (FORM_MAP, getRows) that still needs an entry.
 */

export type SubmodelKey =
  | 'Nameplate'
  | 'HierarchicalStructures'
  | 'AID'
  | 'Skills'
  | 'Capabilities'
  | 'Variables'
  | 'Parameters'
  | 'TechnicalData'
  | 'AIMC';

export interface SubmodelUiSpec {
  /** Profile section name the builder reads. */
  yamlKey: string;
  /** Prefix of the backend's issue.field for this submodel. */
  fieldPrefix: string;
  label: string;
  description: string;
  color: string;
  /** Always present on an AAS. */
  required: boolean;
  /** Grid cell inside the AAS shell, 1-based. */
  col: 1 | 2 | 3;
  row: 1 | 2 | 3;
}

export const SUBMODEL_REGISTRY: Record<SubmodelKey, SubmodelUiSpec> = {
  Nameplate: {
    yamlKey: 'DigitalNameplate', fieldPrefix: 'DigitalNameplate',
    label: 'DigitalNameplate', description: 'Manufacturer, serial number, product URI',
    color: '#38bdf8', required: true, col: 1, row: 1,
  },
  HierarchicalStructures: {
    yamlKey: 'HierarchicalStructures', fieldPrefix: 'HierarchicalStructures',
    label: 'BillOfMaterials', description: 'BOM — IsPartOf / HasPart relationships',
    color: '#34d399', required: true, col: 1, row: 2,
  },
  AID: {
    yamlKey: 'AID', fieldPrefix: 'AID',
    label: 'AssetInterfaceDescription', description: 'MQTT/HTTP endpoint + interaction metadata',
    color: '#a78bfa', required: false, col: 3, row: 3,
  },
  Skills: {
    yamlKey: 'Skills', fieldPrefix: 'Skills',
    label: 'Skills', description: 'Executable capabilities of this resource',
    color: '#fb923c', required: false, col: 2, row: 3,
  },
  Capabilities: {
    yamlKey: 'Capabilities', fieldPrefix: 'Capabilities',
    label: 'Capabilities', description: 'Semantic capability declarations',
    color: '#f472b6', required: false, col: 1, row: 3,
  },
  Variables: {
    yamlKey: 'Variables', fieldPrefix: 'OperationalData',
    label: 'OperationalData', description: 'Runtime variable semantic IDs',
    color: '#fbbf24', required: false, col: 2, row: 1,
  },
  Parameters: {
    yamlKey: 'Parameters', fieldPrefix: 'Parameters',
    label: 'Parameters', description: 'Configuration parameters with units',
    color: '#94a3b8', required: false, col: 3, row: 1,
  },
  TechnicalData: {
    yamlKey: 'TechnicalData', fieldPrefix: 'TechnicalData',
    label: 'TechnicalData', description: 'Datasheet properties and classification',
    color: '#2dd4bf', required: false, col: 2, row: 2,
  },
  AIMC: {
    yamlKey: 'AIMC', fieldPrefix: 'AIMC',
    label: 'InterfaceMapping', description: 'Maps AID properties onto data entries',
    color: '#818cf8', required: false, col: 3, row: 2,
  },
};

// Catalog and picker order.
export const ALL_SUBMODELS: SubmodelKey[] = [
  'Nameplate',
  'HierarchicalStructures',
  'AID',
  'Skills',
  'Capabilities',
  'Variables',
  'Parameters',
  'TechnicalData',
  'AIMC',
];

export const REQUIRED_SUBMODELS: SubmodelKey[] = ALL_SUBMODELS.filter(
  (key) => SUBMODEL_REGISTRY[key].required,
);

export const SUBMODEL_YAML_KEYS = Object.fromEntries(
  ALL_SUBMODELS.map((key) => [key, SUBMODEL_REGISTRY[key].yamlKey]),
) as Record<SubmodelKey, string>;

export const SUBMODEL_FIELD_PREFIXES = Object.fromEntries(
  ALL_SUBMODELS.map((key) => [key, [SUBMODEL_REGISTRY[key].yamlKey]]),
) as Record<SubmodelKey, string[]>;
