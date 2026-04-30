import type { SubmodelKey } from '../../store/useAppStore';

export interface SubmodelMeta {
  icon: string;
  label: string;
  description: string;
  color: string;
}

export const SUBMODEL_META: Record<SubmodelKey, SubmodelMeta> = {
  Nameplate: {
    icon: 'SM',
    label: 'DigitalNameplate',
    description: 'Manufacturer, serial number, product URI',
    color: '#38bdf8',
  },
  HierarchicalStructures: {
    icon: 'SM',
    label: 'BillOfMaterials',
    description: 'BOM — IsPartOf / HasPart relationships',
    color: '#34d399',
  },
  AID: {
    icon: 'SM',
    label: 'AssetInterfaceDescription',
    description: 'MQTT/HTTP endpoint + interaction metadata',
    color: '#a78bfa',
  },
  Skills: {
    icon: 'SM',
    label: 'Skills',
    description: 'Executable capabilities of this resource',
    color: '#fb923c',
  },
  Capabilities: {
    icon: 'SM',
    label: 'Capabilities',
    description: 'Semantic capability declarations',
    color: '#f472b6',
  },
  Variables: {
    icon: 'SM',
    label: 'OperationalData',
    description: 'Runtime variable semantic IDs',
    color: '#fbbf24',
  },
  Parameters: {
    icon: 'SM',
    label: 'Parameters',
    description: 'Configuration parameters with units',
    color: '#94a3b8',
  },
  AIMC: {
    icon: 'SM',
    label: 'InterfaceMapping',
    description: 'Maps AID affordances to Variables, Skills, Parameters',
    color: '#6ee7b7',
  },
};
