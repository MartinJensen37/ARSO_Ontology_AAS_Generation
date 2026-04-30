import { useState } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { useAppStore } from '../../store/useAppStore';
import { useModelStore, createShellNodeId, type EdgeLineType } from '../../store/useModelStore';
import { GenerateAIDialog } from './GenerateAIDialog';
import type { SubmodelNodeData } from './nodes/SubmodelNode';
import type { SubmodelKey } from '../../store/useAppStore';

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

  const configuredCount = Object.values(aasNodes).filter((n) => n.identitySystemId.trim()).length;

  const handleExportAll = () => {
    const json = buildAllAasJson();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resourceaas-all.aas.json';
    a.click();
    URL.revokeObjectURL(url);
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
          disabled={configuredCount === 0}
          title={configuredCount === 0 ? 'Configure at least one AAS first' : 'Download all AASs as JSON array'}
        >
          🡫 Export All AAS(s)
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
      onImport={(json) => {
        // Create a fresh shell node so the import never overwrites an existing AAS
        const newShellId = createShellNodeId();
        const modelStateBeforeImport = useModelStore.getState();
        const shellNodes = modelStateBeforeImport.nodes.filter((n) => n.type === 'aasShell');
        const newPos = { x: 60 + shellNodes.length * 620, y: 40 };

        useAppStore.getState().addAasNode(newShellId);
        useAppStore.getState().setActiveAasNode(newShellId);
        modelStateBeforeImport.addShellNode(newShellId, newPos);

        importAasJson(json);

        // Read updated state synchronously
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

        const SHELL_HEADER_H = 70;
        const SUBMODEL_START_X = 40;

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
        const newNodes: Node[] = selectedKeys.map((key, i) => ({
          id: `submodel-${key}-${crypto.randomUUID().slice(0, 8)}`,
          type: 'submodel' as const,
          position: { x: SUBMODEL_START_X, y: SHELL_HEADER_H + i * 160 },
          parentId: activeShellId,
          extent: 'parent' as const,
          data: { submodelKey: key, parentId: activeShellId } satisfies SubmodelNodeData,
        }));

        modelState.setNodes([...keptNodes, ...newNodes]);

        // Rebuild cap→skill edges from realizedBy in the parsed profile
        const systemId = appState.identitySystemId;
        const profile = appState.parsedProfile;
        const caps = profile?.[systemId]?.Capabilities ?? {};
        const capNodeId = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Capabilities')?.id;
        const skNodeId  = newNodes.find((n) => (n.data as SubmodelNodeData).submodelKey === 'Skills')?.id;

        if (capNodeId && skNodeId) {
          const capSkillEdges: Edge[] = Object.entries(caps)
            .filter(([, cap]) => cap.realizedBy)
            .map(([capName, cap]) => {
              const srcHandle = `source-${capNodeId}-cap-${capName}`;
              const tgtHandle = `target-${skNodeId}-sk-${cap.realizedBy}`;
              return {
                id: `xy-edge__${capNodeId}${srcHandle}-${skNodeId}${tgtHandle}`,
                source: capNodeId,
                target: skNodeId,
                sourceHandle: srcHandle,
                targetHandle: tgtHandle,
                type: useModelStore.getState().edgeLineType === 'step' ? 'editableStep' : useModelStore.getState().edgeLineType,
                label: 'realizedBy',
                labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'Inter, system-ui, sans-serif' },
                labelBgStyle: { fill: '#1e293b', fillOpacity: 0.9 },
                labelBgPadding: [4, 2] as [number, number],
                style: { stroke: '#475569' },
              };
            });
          if (capSkillEdges.length > 0) {
            modelState.setEdges((prev: Edge[]) => [...prev, ...capSkillEdges]);
          }
        }

        setShowGenerateDialog(false);
      }}
    />
    </>
  );
}
