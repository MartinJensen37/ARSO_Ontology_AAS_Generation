import type { Edge } from '@xyflow/react';
import { useAppStore } from '../../store/useAppStore';
import { useModelStore } from '../../store/useModelStore';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { HIERARCHICAL_STRUCTURES, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { BomEntity } from '../../types/resourceaas';
import type { SubmodelNodeData } from '../modelbuilder/nodes/SubmodelNode';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

interface WorkspaceAasOption {
  shellId: string;
  systemId: string;
}

type RelKey = 'HasPart' | 'IsPartOf' | 'SameAs';

const ARCHETYPE_SECTIONS: Record<string, RelKey[]> = {
  OneDown:         ['HasPart'],
  OneUp:           ['IsPartOf'],
  OneUpAndOneDown: ['HasPart', 'IsPartOf'],
};

const SECTION_LABELS: Record<RelKey, string> = {
  HasPart:  'HasPart — parts contained by this asset',
  IsPartOf: 'IsPartOf — assemblies this asset belongs to',
  SameAs:   'SameAs — equivalent assets',
};

const HS_HANDLE_ID: Record<RelKey, string> = {
  HasPart:  'hs-haspart',
  IsPartOf: 'hs-ispartof',
  SameAs:   'hs-sameas',
};

function EntityCard({
  entityName,
  entity,
  workspaceAasOptions,
  selectedShellId,
  onSelectShellId,
  onRemove,
  onUpdate,
}: {
  entityName: string;
  entity: BomEntity;
  workspaceAasOptions: WorkspaceAasOption[];
  selectedShellId: string;
  onSelectShellId: (shellId: string) => void;
  onRemove: () => void;
  onUpdate: (field: keyof BomEntity, value: string) => void;
}) {
  return (
    <div className="card">
      <div className="card__header">
        <strong>{entityName}</strong>
        <button className="btn btn--xs btn--danger" onClick={onRemove}>✕</button>
      </div>
      <div className="card__body">
        <div className="field-grid">
          {workspaceAasOptions.length > 0 && (
            <div className="field-group">
              <label className="field-label">Linked workspace AAS</label>
              <select
                className="field-input form-input--select"
                value={selectedShellId}
                onChange={(e) => onSelectShellId(e.target.value)}
                title="Link this entity to a workspace AAS"
              >
                <option value="">Manual / not linked</option>
                {workspaceAasOptions.map((opt) => (
                  <option key={opt.shellId} value={opt.shellId}>{opt.systemId}</option>
                ))}
              </select>
              <span className="field-hint">Selecting an AAS auto-fills IDs and creates/updates the edge.</span>
            </div>
          )}
          <div className="field-group">
            <label className="field-label">Global Asset ID <span className="required-star">*</span></label>
            <input
              className="field-input"
              value={entity?.globalAssetId ?? ''}
              placeholder="https://example.com/assets/robot-001"
              onChange={(e) => onUpdate('globalAssetId', e.target.value)}
            />
            <span className="field-hint">IRI identifying the referenced asset.</span>
          </div>
          <div className="field-group">
            <label className="field-label">System ID <span className="field-hint">(optional)</span></label>
            <input
              className="field-input"
              value={entity?.systemId ?? ''}
              placeholder="e.g. robot_001"
              onChange={(e) => onUpdate('systemId', e.target.value)}
            />
          </div>
          <div className="field-group">
            <label className="field-label">AAS ID <span className="field-hint">(optional)</span></label>
            <input
              className="field-input"
              value={entity?.aasId ?? ''}
              placeholder="https://example.com/aas/robot-001"
              onChange={(e) => onUpdate('aasId', e.target.value)}
            />
          </div>
          <div className="field-group">
            <label className="field-label">Submodel ID <span className="field-hint">(optional)</span></label>
            <input
              className="field-input"
              value={entity?.submodelId ?? ''}
              placeholder="https://example.com/sm/nameplate-robot-001"
              onChange={(e) => onUpdate('submodelId', e.target.value)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/** Find the HS submodel node ID for a given shell node. */
function findHsNodeId(shellNodeId: string): string | undefined {
  const nodes = useModelStore.getState().nodes;
  return nodes.find(
    (n) =>
      n.type === 'submodel' &&
      n.parentId === shellNodeId &&
      (n.data as SubmodelNodeData).submodelKey === 'HierarchicalStructures'
  )?.id;
}

export function HierarchicalStructuresForm() {
  const parsedProfile   = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId      = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const activeAasNodeId = useAppStore((s) => s.activeAasNodeId);
  const aasNodes        = useAppStore((s) => s.aasNodes);
  const { advanced }    = useAdvanced();
  const setEdges        = useModelStore((s) => s.setEdges);
  const edgeLineType    = useModelStore((s) => s.edgeLineType);

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const baseUrl  = deriveBaseUrl(identityId);
  const metaId   = (parsedProfile[systemId] as any)?._meta?.HierarchicalStructures?.id
    ?? `${baseUrl}/submodels/instances/${identitySystemId}/HierarchicalStructures`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.HierarchicalStructures?.semanticId
    ?? HIERARCHICAL_STRUCTURES;
  const hs        = parsedProfile[systemId]?.HierarchicalStructures;
  const archetype = hs?.Archetype;

  // Other AASes in workspace (exclude self)
  const otherAasEntries = Object.entries(aasNodes).filter(
    ([shellId, ns]) => shellId !== activeAasNodeId && ns.identitySystemId
  );
  const workspaceAasOptions: WorkspaceAasOption[] = otherAasEntries.map(([shellId, ns]) => ({
    shellId,
    systemId: ns.identitySystemId,
  }));

  const setArchetype = (value: string) => {
    if (value === '') {
      updateProfileField([systemId, 'HierarchicalStructures', 'Archetype'], undefined);
      updateProfileField([systemId, 'HierarchicalStructures', 'IsPartOf'], undefined);
      updateProfileField([systemId, 'HierarchicalStructures', 'HasPart'], undefined);
    } else {
      updateProfileField([systemId, 'HierarchicalStructures', 'Archetype'], value);
    }
  };

  const addEntity = (relKey: RelKey) => {
    const name = `Entity_${Date.now()}`;
    updateProfileField(
      [systemId, 'HierarchicalStructures', relKey, name],
      { globalAssetId: '' } as BomEntity,
    );
  };

  const removeEntity = (relKey: RelKey, name: string) => {
    const entity = ((hs as any)?.[relKey] ?? {})[name] as BomEntity | undefined;
    const dict = { ...((hs as any)?.[relKey] ?? {}) };
    delete dict[name];
    updateProfileField([systemId, 'HierarchicalStructures', relKey], dict);

    // Keep canvas in sync: deleting an entity should delete its related edge(s).
    const srcHsNodeId = findHsNodeId(activeAasNodeId);
    if (!srcHsNodeId) return;

    setEdges((prev: Edge[]) => {
      const modelNodes = useModelStore.getState().nodes;
      const removedSystemId = entity?.systemId;
      const legacySourceHandleSuffix = `-${HS_HANDLE_ID[relKey]}`;

      return prev.filter((e) => {
        if (e.source !== srcHsNodeId) return true;

        // Preferred path: metadata-tagged edge.
        const data = (e.data ?? {}) as {
          hsEntityName?: string;
          hsRelKey?: RelKey;
          hsSourceShellId?: string;
        };
        if (
          data.hsEntityName === name &&
          data.hsRelKey === relKey &&
          data.hsSourceShellId === activeAasNodeId
        ) {
          return false;
        }

        // Legacy path: id convention used for linked entities.
        const prefix = `xy-edge__hs-${activeAasNodeId}-${relKey}-${name}-`;
        if (e.id.startsWith(prefix)) return false;

        // Fallback for graph-connected edges keyed by target system ID.
        if (!removedSystemId) return true;
        if (!e.sourceHandle?.endsWith(legacySourceHandleSuffix)) return true;
        const targetNode = modelNodes.find((n) => n.id === e.target);
        const targetShellId = (targetNode?.data as SubmodelNodeData | undefined)?.parentId;
        if (!targetShellId) return true;
        const targetNs = aasNodes[targetShellId];
        return targetNs?.identitySystemId !== removedSystemId;
      });
    });
  };

  const updateEntity = (relKey: RelKey, entityName: string, field: keyof BomEntity, value: string) => {
    updateProfileField(
      [systemId, 'HierarchicalStructures', relKey, entityName, field],
      value || undefined,
    );
  };

  const getMatchingShellId = (entity: BomEntity): string => {
    const bySystemId = Object.entries(aasNodes).find(
      ([shellId, ns]) => shellId !== activeAasNodeId && ns.identitySystemId === entity.systemId
    )?.[0];
    return bySystemId ?? '';
  };

  /** Link one existing entity to a workspace AAS and draw/update its edge. */
  const linkEntityToWorkspaceAas = (relKey: RelKey, entityName: string, targetShellId: string) => {
    if (!targetShellId) return;

    const targetNs = aasNodes[targetShellId];
    if (!targetNs) return;

    const targetSystemId   = targetNs.identitySystemId;
    const targetGlobalId   = targetNs.identityGlobalAssetId;
    const targetIdentityId = targetNs.identityId;
    const targetBaseUrl    = deriveBaseUrl(targetIdentityId);

    const updatedEntity: BomEntity = {
      globalAssetId: targetGlobalId || undefined,
      systemId: targetSystemId,
      aasId: targetIdentityId || undefined,
      submodelId: `${targetBaseUrl}/submodels/instances/${targetSystemId}/HierarchicalStructures`,
    };

    // 1. Update this entity in profile
    updateProfileField(
      [systemId, 'HierarchicalStructures', relKey, entityName],
      updatedEntity,
    );

    // 2. Draw/update canvas edge for this specific entity
    const srcHsNodeId = findHsNodeId(activeAasNodeId);
    const tgtHsNodeId = findHsNodeId(targetShellId);
    if (srcHsNodeId && tgtHsNodeId) {
      const srcHandle = `source-${srcHsNodeId}-${HS_HANDLE_ID[relKey]}`;
      const tgtHandle = `target-${tgtHsNodeId}-hs-entry`;
      const edgePrefix = `xy-edge__hs-${activeAasNodeId}-${relKey}-${entityName}-`;
      const edgeId = `${edgePrefix}${targetShellId}`;
      const newEdge: Edge = {
        id: edgeId,
        source: srcHsNodeId,
        target: tgtHsNodeId,
        sourceHandle: srcHandle,
        targetHandle: tgtHandle,
        type: edgeLineType === 'step' ? 'editableStep' : edgeLineType,
        data: {
          hsEntityName: entityName,
          hsRelKey: relKey,
          hsSourceShellId: activeAasNodeId,
        },
        label: relKey,
        labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'Inter, system-ui, sans-serif' },
        labelBgStyle: { fill: '#1e293b', fillOpacity: 0.9 },
        labelBgPadding: [4, 2] as [number, number],
        style: { stroke: '#475569' },
      };
      setEdges((prev: Edge[]) => {
        // Replace old auto-link edge for this same entity when target changes.
        const filtered = prev.filter((e) => !e.id.startsWith(edgePrefix));
        if (filtered.some((e) => e.id === edgeId)) return filtered;
        return [...filtered, newEdge];
      });
    }
  };

  const archetypeSections: RelKey[] = archetype ? (ARCHETYPE_SECTIONS[archetype] ?? []) : [];
  const visibleSections: RelKey[]   = [...archetypeSections, 'SameAs'];

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'HierarchicalStructures', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'HierarchicalStructures', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="field-grid">
        <div className="field-group">
          <label className="field-label">Name <span className="required-star">*</span></label>
          <input
            className="field-input"
            value={hs?.Name ?? ''}
            placeholder="e.g. PHARM_DISP_VF_001"
            onChange={(e) =>
              updateProfileField([systemId, 'HierarchicalStructures', 'Name'], e.target.value)
            }
          />
          <span className="field-hint">Identifier for the BoM root entry (required by SHACL).</span>
        </div>

        <div className="field-group">
          <label className="field-label">Archetype</label>
          <select
            className="field-input"
            value={archetype ?? ''}
            onChange={(e) => setArchetype(e.target.value)}
          >
            <option value="">— none —</option>
            <option value="OneDown">OneDown — this asset contains sub-assets (HasPart)</option>
            <option value="OneUp">OneUp — this asset is part of a larger assembly (IsPartOf)</option>
            <option value="OneUpAndOneDown">OneUpAndOneDown — both HasPart and IsPartOf</option>
          </select>
          <span className="field-hint">
            Controls which hierarchical relationship entries are emitted in the AAS JSON.
          </span>
        </div>
      </div>

      {visibleSections.map((relKey) => {
        const entities: Record<string, BomEntity> = (hs as any)?.[relKey] ?? {};
        return (
          <div key={relKey} style={{ marginTop: '16px' }}>
            <div className="submodel-form__header">
              <h4 className="submodel-form__title" style={{ fontSize: '0.95rem' }}>
                {SECTION_LABELS[relKey]}
              </h4>
              <button
                className="btn btn--sm btn--secondary"
                onClick={() => addEntity(relKey)}
              >
                + Entity
              </button>
            </div>

            {Object.keys(entities).length === 0 && (
              <p className="empty-state">No entries yet. Add an entity, then link it from the entity header.</p>
            )}

            {Object.entries(entities).map(([entityName, entity]) => (
              <EntityCard
                key={entityName}
                entityName={entityName}
                entity={entity}
                workspaceAasOptions={workspaceAasOptions}
                selectedShellId={getMatchingShellId(entity)}
                onSelectShellId={(shellId) => linkEntityToWorkspaceAas(relKey, entityName, shellId)}
                onRemove={() => removeEntity(relKey, entityName)}
                onUpdate={(field, value) => updateEntity(relKey, entityName, field, value)}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}
