import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useAppStore, DEFAULT_AAS_NODE_STATE } from '../../../store/useAppStore';
import { useModelStore } from '../../../store/useModelStore';
import type { SubmodelKey } from '../../../store/useAppStore';
import type { ValidationIssue } from '../../../types/resourceaas';

// Stable empty array — prevents infinite re-render from `?? []` in Zustand selectors
const EMPTY_ISSUES: ValidationIssue[] = [];
import type {
  ResourceAASProfile,
  SystemConfig,
  DigitalNameplate,
  AIDInterface,
  Skill,
  Capability,
  Variable,
  Parameter,
  HierarchicalStructures,
  AIMCMappingConfig,
} from '../../../types/resourceaas';
import { SUBMODEL_META } from '../catalogMeta';

export interface SubmodelNodeData {
  submodelKey: SubmodelKey;
  /** Shell node ID this submodel belongs to — used to read from the correct AASNodeState */
  parentId?: string;
  [key: string]: unknown;
}

// ── Row type ─────────────────────────────────────────────────────────────────

type HandleType =
  | 'source'  // right handle only  — outgoing reference (HasPart, Skills, Capabilities)
  | 'target'  // left handle only   — incoming reference (IsPartOf, AID, Nameplate)
  | 'both';   // left + right       — bidirectional (SameAs)

interface PropRow {
  id: string;
  label: string;
  value: string;
  handleType: HandleType;
  isHeader?: boolean;  // interface section separator (no handle rendered)
  indent?: boolean;    // indented interaction item under an interface header
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Extract display string from a value that may be an MLP array [{language,text}] */
function mlpStr(v: any): string {
  if (v == null) return '';
  if (Array.isArray(v)) {
    const en = v.find((x: any) => x?.language === 'en');
    return String(en?.text ?? v[0]?.text ?? '');
  }
  return String(v);
}

// ── Per-submodel row generators ──────────────────────────────────────────────

function getRows(
  key: SubmodelKey,
  parsedProfile: ResourceAASProfile | null,
  identitySystemId: string
): PropRow[] {
  if (!parsedProfile || !identitySystemId) return [];
  const cfg: SystemConfig | undefined = parsedProfile[identitySystemId];
  if (!cfg) return [];

  switch (key) {
    case 'Nameplate': {
      const np = cfg.DigitalNameplate as DigitalNameplate | undefined;
      if (!np) return [];
      return ([
        np.ManufacturerName               && { id: 'np-mfr',  label: 'Manufacturer', value: mlpStr(np.ManufacturerName),               handleType: 'target' },
        np.SerialNumber                   && { id: 'np-sn',   label: 'Serial No.',   value: mlpStr(np.SerialNumber),                   handleType: 'target' },
        np.ManufacturerProductDesignation && { id: 'np-prod', label: 'Product',      value: mlpStr(np.ManufacturerProductDesignation), handleType: 'target' },
        np.YearOfConstruction             && { id: 'np-year', label: 'Year',         value: mlpStr(np.YearOfConstruction),             handleType: 'target' },
        np.HardwareVersion                && { id: 'np-hw',   label: 'HW ver.',      value: mlpStr(np.HardwareVersion),                handleType: 'target' },
        np.SoftwareVersion                && { id: 'np-sw',   label: 'SW ver.',      value: mlpStr(np.SoftwareVersion),                handleType: 'target' },
      ] as (PropRow | false)[]).filter(Boolean).slice(0, 5) as PropRow[];
    }

    case 'AID': {
      const aid = cfg.AID as Record<string, AIDInterface> | undefined;
      if (!aid) return [];
      const rows: PropRow[] = [];
      for (const [ifaceName, iface] of Object.entries(aid)) {
        // Interface header row — no handle, purely a visual separator
        rows.push({
          id: `aid-iface-${ifaceName}`,
          label: iface?.protocol ?? 'MQTT',
          value: iface?.Title || ifaceName,
          handleType: 'target',
          isHeader: true,
        });
        const props   = iface?.InteractionMetadata?.properties ?? {};
        const actions = iface?.InteractionMetadata?.actions    ?? {};
        const events  = iface?.InteractionMetadata?.events     ?? {};
        for (const [k, p] of Object.entries(props)) {
          rows.push({ id: `aid-prop-${ifaceName}-${k}`, label: 'property', value: p?.key || k, handleType: 'target', indent: true });
        }
        for (const [k, a] of Object.entries(actions)) {
          rows.push({ id: `aid-act-${ifaceName}-${k}`, label: 'action', value: a?.key || k, handleType: 'target', indent: true });
        }
        for (const [k, e] of Object.entries(events)) {
          rows.push({ id: `aid-evt-${ifaceName}-${k}`, label: 'event', value: e?.key || k, handleType: 'target', indent: true });
        }
      }
      return rows;
    }

    case 'Skills': {
      const skills = cfg.Skills as Record<string, Skill> | undefined;
      if (!skills) return [];
      return Object.entries(skills).slice(0, 8).map(([name, skill]) => ({
        id: `sk-${name}`,
        label: name,
        value: skill?.callType ? `[${skill.callType}]` : '—',
        handleType: 'both' as HandleType,
      }));
    }

    case 'Capabilities': {
      const caps = cfg.Capabilities as Record<string, Capability> | undefined;
      if (!caps) return [];
      return Object.entries(caps).slice(0, 6).map(([name, cap]) => ({
        id: `cap-${name}`,
        label: name,
        value: cap?.realizedBy ? `→ ${cap.realizedBy}` : (cap?.semantic_id?.split('/').pop() ?? '✓'),
        handleType: 'source' as HandleType,
      }));
    }

    case 'Variables': {
      const vars = cfg.Variables as Record<string, Variable> | undefined;
      if (!vars) return [];
      return Object.entries(vars).slice(0, 6).map(([name, v]) => ({
        id: `var-${name}`,
        label: name,
        value: v?.semanticId?.split('/').pop() ?? '✓',
        handleType: 'target' as HandleType,
      }));
    }

    case 'Parameters': {
      const params = cfg.Parameters as Record<string, Parameter> | undefined;
      if (!params) return [];
      return Object.entries(params).slice(0, 6).map(([name, p]) => ({
        id: `par-${name}`,
        label: name,
        value: p?.ParameterValue
          ? `${p.ParameterValue}${p.Unit ? ' ' + p.Unit : ''}`
          : '—',
        handleType: 'target' as HandleType,
      }));
    }

    case 'HierarchicalStructures': {
      const hs = cfg.HierarchicalStructures as HierarchicalStructures | undefined;
      if (!hs) return [];

      const hasPart  = Object.keys(hs.HasPart  ?? {}).length;
      const isPartOf = Object.keys(hs.IsPartOf ?? {}).length;
      const sameAs   = Object.keys(hs.SameAs   ?? {}).length;

      // Always expose all 3 relationship handles so edges can be drawn immediately
      return [
        { id: 'hs-entry',    label: 'EntryNode', value: hs.Name ?? identitySystemId, handleType: 'target' },
        { id: 'hs-haspart',  label: 'HasPart',   value: hasPart  > 0 ? `${hasPart} part${hasPart !== 1 ? 's' : ''}`             : '—', handleType: 'source' },
        { id: 'hs-ispartof', label: 'IsPartOf',  value: isPartOf > 0 ? `${isPartOf} parent${isPartOf !== 1 ? 's' : ''}`         : '—', handleType: 'source' },
        { id: 'hs-sameas',   label: 'SameAs',    value: sameAs   > 0 ? `${sameAs} equiv.`                                       : '—', handleType: 'both'   },
      ];
    }

    case 'AIMC': {
      const aimc = cfg.AIMC as Record<string, AIMCMappingConfig> | undefined;
      if (!aimc) return [];
      return Object.entries(aimc).slice(0, 6).map(([name, config]) => ({
        id: `aimc-${name}`,
        label: name,
        value: config?.interfaceName ? `→ ${config.interfaceName}` : '—',
        handleType: 'target' as HandleType,
      }));
    }

    default:
      return [];
  }
}

// ── Node component ───────────────────────────────────────────────────────────

export const SubmodelNode = memo(function SubmodelNode({ id, data, selected }: NodeProps) {
  const submodelKey = (data as SubmodelNodeData).submodelKey;
  const shellNodeId = (data as SubmodelNodeData).parentId;
  const meta = SUBMODEL_META[submodelKey];
  const openPropertyModal = useModelStore((s) => s.openPropertyModal);
  const setActiveAasNode = useAppStore((s) => s.setActiveAasNode);

  // Read from this node's own AAS state, not the global active workspace.
  // Falls back to DEFAULT_AAS_NODE_STATE so nothing crashes if parentId is missing.
  const aasNodes = useAppStore((s) => s.aasNodes);
  const globalParsedProfile = useAppStore((s) => s.parsedProfile);
  const globalIdentitySystemId = useAppStore((s) => s.identitySystemId);
  // Per-node validation issues — prevents cross-AAS contamination of violation badges.
  // EMPTY_ISSUES is a stable reference to avoid an infinite Zustand snapshot loop.
  const nodeIssues = useAppStore((s) => s.validationIssuesByNode[shellNodeId ?? ''] ?? EMPTY_ISSUES);

  const ownState = shellNodeId ? (aasNodes[shellNodeId] ?? DEFAULT_AAS_NODE_STATE) : null;
  const parsedProfile = ownState?.parsedProfile ?? globalParsedProfile;
  const identitySystemId = ownState?.identitySystemId ?? globalIdentitySystemId;

  const fieldPrefix = submodelKey === 'Nameplate' ? 'DigitalNameplate' : submodelKey;
  const violationCount = nodeIssues.filter(
    (i) => i.severity === 'Violation' && i.field?.startsWith(fieldPrefix)
  ).length;

  const rows = getRows(submodelKey, parsedProfile, identitySystemId);

  const handleDoubleClick = () => {
    // Switch active AAS to this node's parent shell BEFORE opening the modal
    if (shellNodeId) setActiveAasNode(shellNodeId);
    openPropertyModal(submodelKey, id);
  };

  return (
    <div
      className={`mb-node mb-node--submodel${selected ? ' mb-node--selected' : ''}${violationCount > 0 ? ' mb-node--invalid' : ''}`}
      style={{ '--node-color': 'var(--aas-color)' } as React.CSSProperties}
      onDoubleClick={handleDoubleClick}
    >
      {/* ── Header ── */}
      <div className="mb-node__header">
        <div className="mb-icon-badge" title="Submodel" style={{ background: 'var(--submodel-icon-color)' }}>SM</div>
        <div className="mb-node__header-text">
          <div className="mb-node__title">{meta.label}</div>
        </div>
        {violationCount > 0 && (
          <span className="mb-node__issue-badge">{violationCount}</span>
        )}
      </div>

      {/* ── Property rows ── */}
      {rows.length > 0 ? (
        <div className="mb-node__props">
          {rows.map((row) => {
            const showTarget = !row.isHeader && (row.handleType === 'target' || row.handleType === 'both');
            const showSource = !row.isHeader && (row.handleType === 'source' || row.handleType === 'both');
            const rowClass = [
              'mb-node__prop-row',
              row.isHeader ? 'mb-node__prop-row--header' : '',
              row.indent   ? 'mb-node__prop-row--indent'  : '',
            ].filter(Boolean).join(' ');
            return (
              <div key={row.id} className={rowClass} style={{ position: 'relative' }}>
                {showTarget && <span className="mb-node__prop-handle-spacer" />}
                {!showTarget && !row.isHeader && (row.handleType === 'source' || row.handleType === 'both') && (
                  <span className="mb-node__prop-handle-spacer" style={{ visibility: 'hidden' }} />
                )}
                <span className="mb-node__prop-label">{row.label}</span>
                <span className="mb-node__prop-value">{row.value}</span>
                {showSource && <span className="mb-node__prop-handle-spacer" />}

                {showTarget && (
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={`target-${id}-${row.id}`}
                    title={row.handleType === 'both' ? 'incoming equivalence' : 'reference'}
                    className="mb-handle mb-handle--target"
                    style={{ top: '50%', transform: 'translateY(-50%)' }}
                  />
                )}
                {showSource && (
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={`source-${id}-${row.id}`}
                    title={row.handleType === 'both' ? 'outgoing equivalence' : 'reference'}
                    className="mb-handle mb-handle--source"
                    style={{ top: '50%', transform: 'translateY(-50%)' }}
                  />
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mb-node__hint">Double-click to configure</div>
      )}
    </div>
  );
});
