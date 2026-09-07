import { useState } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { useAppStore } from '../../store/useAppStore';
import { useModelStore, createShellNodeId, type EdgeLineType } from '../../store/useModelStore';
import { GenerateAIDialog } from './GenerateAIDialog';
import type { SubmodelNodeData } from './nodes/SubmodelNode';
import type { SubmodelKey } from '../../store/useAppStore';
import type { AIDInterface } from '../../types/resourceaas';
import { SUBMODEL_POSITIONS } from './submodelLayout';

/**
 * Find the AID row id (matches SubmodelNode.tsx's getRows 'AID' case:
 * `aid-{prop|act|evt}-{ifaceName}-{key}`) for a given property/action/event
 * key, searching every configured interface. Used to reconstruct
 * Variable/Parameter/Skill → AID edges from InterfaceReference / interface
 * values already present in an imported profile.
 */
function findAidRowId(aid: Record<string, AIDInterface> | undefined, key: string): string | null {
  if (!aid) return null;
  for (const [ifaceName, iface] of Object.entries(aid)) {
    const im = iface?.InteractionMetadata;
    if (im?.properties && key in im.properties) return `aid-prop-${ifaceName}-${key}`;
    if (im?.actions && key in im.actions) return `aid-act-${ifaceName}-${key}`;
    if (im?.events && key in im.events) return `aid-evt-${ifaceName}-${key}`;
  }
  return null;
}

/** Build one reference edge with the same styling ModelBuilder.tsx's onConnect uses. */
function buildRefEdge(srcNodeId: string, srcHandle: string, tgtNodeId: string, tgtHandle: string, label: string): Edge {
  return {
    id: `xy-edge__${srcNodeId}${srcHandle}-${tgtNodeId}${tgtHandle}`,
    source: srcNodeId,
    target: tgtNodeId,
    sourceHandle: srcHandle,
    targetHandle: tgtHandle,
    type: useModelStore.getState().edgeLineType === 'step' ? 'editableStep' : useModelStore.getState().edgeLineType,
    label,
    labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'Inter, system-ui, sans-serif' },
    labelBgStyle: { fill: '#1e293b', fillOpacity: 0.9 },
    labelBgPadding: [4, 2] as [number, number],
    style: { stroke: '#475569' },
  };
}

export function BuilderToolbar() {
  const buildAllAasJson = useAppStore((s) => s.buildAllAasJson);
  const aasNodes = useAppStore((s) => s.aasNodes);
  const isLoadingValidate = useAppStore((s) => s.isLoadingValidate);
  const resetApp = useAppStore((s) => s.resetAll);
  const resetModel = useModelStore((s) => s.resetAll);
  const edgeLineType = useModelStore((s) => s.edgeLineType);
  const setEdgeLineType = useModelStore((s) => s.setEdgeLineType);
  const theme = useAppStore((s) => s.theme);
  const toggleTheme = useAppStore((s) => s.toggleTheme);
  const importAasJson = useAppStore((s) => s.importAasJson);

  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [isExportingAll, setIsExportingAll] = useState(false);

  const configuredCount = Object.values(aasNodes).filter((n) => n.identitySystemId.trim()).length;

  const handleExportAll = async () => {
    setIsExportingAll(true);
    try {
      const json = await buildAllAasJson();
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'resourceaas-all.aas.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch (exc) {
      window.alert(`Export failed: ${exc instanceof Error ? exc.message : exc}`);
    } finally {
      setIsExportingAll(false);
    }
  };

  const handleReset = () => {
    if (!window.confirm('Reset the entire canvas? All AASs and unsaved work will be lost.')) return;
    resetApp();
    resetModel();
  };

  return (
    <>
    <header className="mb-toolbar">
      <div className="mb-toolbar__left">
        <h1 className="mb-toolbar__title">PPR AAS Editor</h1>
        <span className="mb-toolbar__subtitle">Node Canvas</span>
      </div>

      <div className="mb-toolbar__center">
        <span className="mb-toolbar__submodel-count">
        </span>
      </div>

      <div className="mb-toolbar__right">
        {isLoadingValidate && <span className="spinner" title="Validating…" />}

        <label className="mb-toolbar__edge-style" title="Default line type for new or reconnected edges">
          <span>Line</span>
          <select
            className="mb-toolbar__edge-style-select"
            value={edgeLineType}
            onChange={(e) => setEdgeLineType(e.target.value as EdgeLineType)}
          >
            <option value="smoothstep">Smooth</option>
            <option value="default">Bezier</option>
            <option value="straight">Straight</option>
            <option value="step">Step</option>
          </select>
        </label>

        <button
          className="btn btn--accent"
          onClick={() => setShowGenerateDialog(true)}
          title="Generate an AAS from a component spec sheet using Claude AI"
        >
          ✦ Generate with AI
        </button>

        <button
          className="btn btn--primary"
          onClick={handleExportAll}
          disabled={configuredCount === 0 || isExportingAll}
          title={configuredCount === 0 ? 'Configure at least one AAS first' : 'Download all AASs as JSON array'}
        >
          {isExportingAll ? '…' : '🡫 Export All AAS(s)'}
        </button>

        <button
          className="btn btn--ghost btn--reset"
          onClick={handleReset}
          title="Reset canvas — start from scratch"
        >
          ↺ Reset All
        </button>
        
        <button
          className="btn btn--ghost"
          onClick={toggleTheme}
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          {theme === 'light' ? '☾' : '☀'}
        </button>
      </div>
    </header>

    <GenerateAIDialog
      isOpen={showGenerateDialog}
      onClose={() => setShowGenerateDialog(false)}
      onImport={async (json) => {
        // Create a fresh shell node so the import never overwrites an existing AAS
        const newShellId = createShellNodeId();
        const modelStateBeforeImport = useModelStore.getState();
        const shellNodes = modelStateBeforeImport.nodes.filter((n) => n.type === 'aasShell');
        const newPos = { x: 60 + shellNodes.length * 620, y: 40 };

        useAppStore.getState().addAasNode(newShellId);
        useAppStore.getState().setActiveAasNode(newShellId);
        modelStateBeforeImport.addShellNode(newShellId, newPos);

        await importAasJson(json);

        // Read state updated by the import above
        const appState = useAppStore.getState();
        const activeShellId = appState.activeAasNodeId;   // == newShellId
        const selectedKeys = appState.selectedSubmodels as SubmodelKey[];

        const modelState = useModelStore.getState();
        const existingNodes = modelState.nodes;
        const shellNode = existingNodes.find((n) => n.id === activeShellId);
        if (!shellNode) {
          setShowGenerateDialog(false);
          return;
        }

        // Drop all existing submodel nodes and edges for this shell so there
        // are no stale edges referencing old node/handle IDs.
        const keptNodes = existingNodes.filter(
          (n) => !(n.type === 'submodel' && n.parentId === activeShellId)
        );
        modelState.setEdges((prev: Edge[]) =>
          prev.filter((e) => {
            const srcNode = existingNodes.find((n) => n.id === e.source);
            const tgtNode = existingNodes.find((n) => n.id === e.target);
            return (
              srcNode?.parentId !== activeShellId &&
              tgtNode?.parentId !== activeShellId
            );
          })
        );

        // Create fresh submodel nodes for all selected submodels
        const newNodes: Node[] = selectedKeys.map((key) => ({
          id: `submodel-${key}-${crypto.randomUUID().slice(0, 8)}`,
          type: 'submodel' as const,
          position: { ...SUBMODEL_POSITIONS[key] },
          parentId: activeShellId,
          extent: 'parent' as const,
          data: { submodelKey: key, parentId: activeShellId } satisfies SubmodelNodeData,
        }));

        modelState.setNodes([...keptNodes, ...newNodes]);

        // Rebuild reference edges from the parsed profile: Capability → Skill
        // (realizedBy) and Variable/Parameter/Skill → AID (InterfaceReference /
        // interface) — same connectors onConnect in ModelBuilder.tsx writes when
        // drawn by hand, reconstructed here so an imported/generated AAS shows
        // up already wired instead of needing every connection redrawn manually.
        const systemId = appState.identitySystemId;
        const profile = appState.parsedProfile;
        const cfg = profile?.[systemId];
        const caps = cfg?.Capabilities ?? {};
        const vars = cfg?.Variables ?? {};
        const params = cfg?.Parameters ?? {};
        const skills = cfg?.Skills ?? {};
        const aid = cfg?.AID;

        const capNodeId = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Capabilities')?.id;
        const skNodeId  = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Skills')?.id;
        const varNodeId = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Variables')?.id;
        const parNodeId = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Parameters')?.id;
        const aidNodeId = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'AID')?.id;

        const newEdges: Edge[] = [];

        if (capNodeId && skNodeId) {
          for (const [capName, cap] of Object.entries(caps)) {
            if (!cap.realizedBy) continue;
            newEdges.push(buildRefEdge(
              capNodeId, `source-${capNodeId}-cap-${capName}`,
              skNodeId, `target-${skNodeId}-sk-${cap.realizedBy}`,
              'realizedBy'
            ));
          }
        }

        if (aidNodeId && aid) {
          if (varNodeId) {
            for (const [varName, v] of Object.entries(vars)) {
              const aidRowId = v.InterfaceReference ? findAidRowId(aid, v.InterfaceReference) : null;
              if (!aidRowId) continue;
              newEdges.push(buildRefEdge(
                varNodeId, `source-${varNodeId}-var-${varName}`,
                aidNodeId, `target-${aidNodeId}-${aidRowId}`,
                'InterfaceReference'
              ));
            }
          }
          if (parNodeId) {
            for (const [parName, p] of Object.entries(params)) {
              const aidRowId = p.InterfaceReference ? findAidRowId(aid, p.InterfaceReference) : null;
              if (!aidRowId) continue;
              newEdges.push(buildRefEdge(
                parNodeId, `source-${parNodeId}-par-${parName}`,
                aidNodeId, `target-${aidNodeId}-${aidRowId}`,
                'InterfaceReference'
              ));
            }
          }
          if (skNodeId) {
            for (const [skillName, skill] of Object.entries(skills)) {
              const aidRowId = skill.interface ? findAidRowId(aid, skill.interface) : null;
              if (!aidRowId) continue;
              newEdges.push(buildRefEdge(
                skNodeId, `source-${skNodeId}-sk-${skillName}`,
                aidNodeId, `target-${aidNodeId}-${aidRowId}`,
                'interface'
              ));
            }
          }
        }

        if (newEdges.length > 0) {
          modelState.setEdges((prev: Edge[]) => [...prev, ...newEdges]);
        }

        setShowGenerateDialog(false);
      }}
    />
    </>
  );
}
