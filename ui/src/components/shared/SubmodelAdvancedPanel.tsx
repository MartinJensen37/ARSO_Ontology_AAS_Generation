import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { SubmodelKey } from '../../store/useAppStore';
import {
  DIGITAL_NAMEPLATE_SUBMODEL,
  HIERARCHICAL_STRUCTURES,
  HIERARCHICAL_ARCHETYPE, HIERARCHICAL_ENTRY_NODE, HIERARCHICAL_NODE,
  HIERARCHICAL_SAME_AS, HIERARCHICAL_RELATIONSHIP,
  AID_SUBMODEL, AID_INTERFACE, AID_INTERACTION_METADATA,
  WOT_ACTION_AFFORDANCE, WOT_PROPERTY_AFFORDANCE,
  SKILLS_SUBMODEL,
  CAPABILITIES_SUBMODEL, CAPABILITY_SET, CAPABILITY_CONTAINER,
  OPERATIONAL_DATA_SUBMODEL,
  PARAMETERS_SUBMODEL,
  SEMANTIC_ID_BASE,
} from '../../aas/semanticIds';
import type { AIDInterface } from '../../types/resourceaas';

// ── Lookup tables ─────────────────────────────────────────────────────────────

const SUBMODEL_SEMANTIC_ID: Record<SubmodelKey, string> = {
  Nameplate:               DIGITAL_NAMEPLATE_SUBMODEL,
  HierarchicalStructures:  HIERARCHICAL_STRUCTURES,
  AID:                     AID_SUBMODEL,
  Skills:                  SKILLS_SUBMODEL,
  Capabilities:            CAPABILITIES_SUBMODEL,
  Variables:               OPERATIONAL_DATA_SUBMODEL,
  Parameters:              PARAMETERS_SUBMODEL,
};

// Must match what each builder uses as idShort / path segment
const SUBMODEL_IDSHORT: Record<SubmodelKey, string> = {
  Nameplate:               'DigitalNameplate',
  HierarchicalStructures:  'HierarchicalStructures',
  AID:                     'AID',
  Skills:                  'Skills',
  Capabilities:            'Capabilities',
  Variables:               'Variables',
  Parameters:              'Parameters',
};

const PROTOCOL_SUPPLEMENTAL: Record<string, string[]> = {
  MQTT:   ['http://www.w3.org/2011/mqtt', 'https://www.w3.org/2019/wot/td'],
  HTTP:   ['http://www.w3.org/2011/http', 'https://www.w3.org/2019/wot/td'],
  MODBUS: ['http://www.w3.org/2011/modbus', 'https://www.w3.org/2019/wot/td'],
};

// ── Row type ──────────────────────────────────────────────────────────────────

interface AdvRow {
  label: string;
  value: string;
  dim?: boolean;   // muted label (secondary info)
  group?: string;  // section heading
}

function deriveBaseUrl(id: string): string {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

// ── Per-submodel row builders ─────────────────────────────────────────────────

function buildRows(
  key: SubmodelKey,
  baseUrl: string,
  systemId: string,
  parsedProfile: ReturnType<typeof useAppStore.getState>['parsedProfile'],
): AdvRow[] {
  const idShort    = SUBMODEL_IDSHORT[key];
  const semanticId = SUBMODEL_SEMANTIC_ID[key];
  const submodelId = `${baseUrl}/submodels/instances/${systemId}/${idShort}`;

  const common: AdvRow[] = [
    { group: 'Submodel',  label: '', value: '' },
    { label: 'id',        value: submodelId },
    { label: 'idShort',   value: idShort },
    { label: 'semanticId',value: semanticId },
    { label: 'kind',      value: 'Instance',   dim: true },
    { label: 'version',   value: '1',          dim: true },
    { label: 'revision',  value: '1',          dim: true },
  ];

  if (key === 'AID') {
    const cfg = parsedProfile?.[systemId];
    const aid = cfg?.AID as Record<string, AIDInterface> | undefined ?? {};
    const aidRows: AdvRow[] = [
      { group: 'AID element semantic IDs', label: '', value: '' },
      { label: 'Interface semanticId',            value: AID_INTERFACE },
      { label: 'InteractionMetadata semanticId',  value: AID_INTERACTION_METADATA },
      { label: 'PropertyAffordance semanticId',   value: WOT_PROPERTY_AFFORDANCE },
      { label: 'ActionAffordance semanticId',     value: WOT_ACTION_AFFORDANCE },
    ];
    const ifaceRows: AdvRow[] = [];
    for (const [ifaceName, iface] of Object.entries(aid)) {
      const proto = iface?.protocol ?? 'MQTT';
      const suppl = PROTOCOL_SUPPLEMENTAL[proto] ?? [];
      ifaceRows.push({ group: `Interface: ${ifaceName}`, label: '', value: '' });
      ifaceRows.push({ label: 'protocol', value: proto, dim: true });
      suppl.forEach((uri, i) => ifaceRows.push({ label: `supplementalSemanticId[${i}]`, value: uri }));
    }
    return [...common, ...aidRows, ...ifaceRows];
  }

  if (key === 'Capabilities') {
    return [
      ...common,
      { group: 'Capability element semantic IDs', label: '', value: '' },
      { label: 'CapabilitySet semanticId',        value: CAPABILITY_SET },
      { label: 'CapabilityContainer semanticId',  value: CAPABILITY_CONTAINER },
    ];
  }

  if (key === 'HierarchicalStructures') {
    return [
      ...common,
      { group: 'HierarchicalStructures element semantic IDs', label: '', value: '' },
      { label: 'EntryNode semanticId',   value: HIERARCHICAL_ENTRY_NODE },
      { label: 'Archetype semanticId',   value: HIERARCHICAL_ARCHETYPE },
      { label: 'Node semanticId',        value: HIERARCHICAL_NODE },
      { label: 'SameAs semanticId',      value: HIERARCHICAL_SAME_AS },
      { label: 'Relationship semanticId',value: HIERARCHICAL_RELATIONSHIP },
    ];
  }

  return common;
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props { submodelKey: SubmodelKey; }

export function SubmodelAdvancedPanel({ submodelKey }: Props) {
  const [open, setOpen] = useState(false);
  const identityId       = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const parsedProfile    = useAppStore((s) => s.parsedProfile);
  const [copied, setCopied] = useState<string | null>(null);

  const baseUrl = deriveBaseUrl(identityId);
  const rows    = buildRows(submodelKey, baseUrl, identitySystemId, parsedProfile);

  const copy = (value: string) => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(value);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  return (
    <div className="adv-panel">
      <button
        className="adv-panel__toggle"
        type="button"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="adv-panel__chevron">{open ? '▾' : '▸'}</span>
        Advanced — AAS metadata
      </button>

      {open && (
        <div className="adv-panel__body">
          {rows.map((row, i) => {
            if (row.group !== undefined) {
              return (
                <div key={`g-${i}`} className="adv-panel__group-label">
                  {row.group}
                </div>
              );
            }
            return (
              <div key={`r-${i}`} className="adv-panel__row">
                <span className={`adv-panel__label${row.dim ? ' adv-panel__label--dim' : ''}`}>
                  {row.label}
                </span>
                <span className="adv-panel__value" title={row.value}>
                  {row.value}
                </span>
                <button
                  className="adv-panel__copy"
                  type="button"
                  title="Copy"
                  onClick={() => copy(row.value)}
                >
                  {copied === row.value ? '✓' : '⎘'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
