import { useCallback, useEffect, useRef } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  reconnectEdge,
  applyNodeChanges,
  applyEdgeChanges,
  Controls,
  Background,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  type OnNodesDelete,
  type OnReconnect,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useAppStore, type SubmodelKey } from '../../store/useAppStore';
import { useModelStore } from '../../store/useModelStore';
import { useValidation } from '../../hooks/useValidation';
import { addAasShell } from './addAasShell';
import { nodeTypes } from './nodes/nodeTypes';
import { edgeTypes } from './edges/edgeTypes';
import { CatalogPanel } from './CatalogPanel';
import { BuilderToolbar } from './BuilderToolbar';
import { PropertyEditorModal } from './modals/PropertyEditorModal';
import { IdentityEditorModal } from './modals/IdentityEditorModal';
import { GuidancePanel } from '../shared/GuidancePanel';
import type { SubmodelNodeData } from './nodes/SubmodelNode';

// Positions are RELATIVE to the shell container (accounting for the header height)
const SHELL_HEADER_H = 70;

/** Parse a BoM source handle ID to its relationship key, or null if not a BoM handle. */
function bomRelKeyFromHandle(handle: string): 'HasPart' | 'IsPartOf' | null {
  if (handle.endsWith('-hs-haspart')) return 'HasPart';
  if (handle.endsWith('-hs-ispartof')) return 'IsPartOf';
  return null;
}

// AID interface idShorts a row can live under (asset_interfaces_builder.py::_INTERFACE_TYPES).
const AID_IFACE_NAMES = ['InterfaceMQTT', 'InterfaceOPCUA', 'InterfaceHTTP'];

/**
 * Extract the AID affordance key (property/action/event idShort) an AID
 * target handle refers to. AID row ids are `aid-{prop|act|evt}-{ifaceName}-{key}`
 * (see SubmodelNode.tsx's getRows 'AID' case) — strip the known interface
 * name prefix to recover the bare key, which is what InterfaceReference /
 * Skill.interface actually store.
 */
function parseAidAffordanceHandle(handle: string): string | null {
  const m = handle.match(/-aid-(?:prop|act|evt)-(.+)$/);
  if (!m) return null;
  let rest = m[1];
  for (const iface of AID_IFACE_NAMES) {
    if (rest.startsWith(`${iface}-`)) {
      rest = rest.slice(iface.length + 1);
      break;
    }
  }
  return rest || null;
}

/** Extract the name after a `-{marker}-` handle-id fragment, e.g. 'var'/'par'/'sk'. */
function nameAfterMarker(handle: string, marker: string): string | null {
  const needle = `-${marker}-`;
  const idx = handle.indexOf(needle);
  if (idx === -1) return null;
  return handle.slice(idx + needle.length);
}

// Inner component — must be inside ReactFlowProvider to use useReactFlow()
function ModelBuilderCanvas() {
  const { screenToFlowPosition, getNodes } = useReactFlow();
  const toggleSubmodel = useAppStore((s) => s.toggleSubmodel);
  const setActiveAasNode = useAppStore((s) => s.setActiveAasNode);
  const theme = useAppStore((s) => s.theme);
  const isLight = theme === 'light';

  const nodes = useModelStore((s) => s.nodes);
  const edges = useModelStore((s) => s.edges);
  const setNodes = useModelStore((s) => s.setNodes);
  const setEdges = useModelStore((s) => s.setEdges);
  const edgeLineType = useModelStore((s) => s.edgeLineType);

  // Render all edges with the selected built-in line type.
  const renderedEdges = edges.map((e) => {
    const currentType =
      e.type === 'default' || e.type === 'straight' || e.type === 'smoothstep' || e.type === 'step'
        ? e.type
        : undefined;
    const lineType = currentType ?? edgeLineType;

    if (lineType === 'step') {
      return {
        ...e,
        type: 'editableStep',
        data: { ...(e.data ?? {}) },
      };
    }

    return {
      ...e,
      type: lineType,
    };
  });

  useValidation();

  const seededRef = useRef(false);

  // One-time migration on first mount for state persisted by an older version
  // of the app: ensure aasShell nodes have dragHandle, and that none are
  // still marked deletable:false (the very first shell used to be permanently
  // undeletable; the canvas can now start from -- and be reset to -- zero AAS
  // nodes, so every shell must be deletable). Required-submodel seeding used
  // to also happen here, hardcoded to that one guaranteed initial shell --
  // it now happens per-shell at creation time instead, see addAasShell.
  useEffect(() => {
    if (seededRef.current) return;
    seededRef.current = true;

    const existing = useModelStore.getState().nodes;
    const needsMigration = existing.some(
      (n) => n.type === 'aasShell' && (!n.dragHandle || n.deletable === false)
    );
    if (needsMigration) {
      setNodes((prev) => prev.map((n) =>
        n.type === 'aasShell' ? { ...n, dragHandle: '.mb-drag-handle', deletable: true } : n
      ));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((prev: Node[]) => applyNodeChanges(changes, prev));
    },
    [setNodes]
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      // Remove BoM entities when their connecting edge is deleted
      const currentEdges = useModelStore.getState().edges;
      const currentNodes = useModelStore.getState().nodes;
      for (const change of changes) {
        if (change.type !== 'remove') continue;
        const edge = currentEdges.find((e) => e.id === change.id);
        if (!edge?.sourceHandle || !edge.targetHandle?.includes('-hs-entry')) continue;
        const relKey = bomRelKeyFromHandle(edge.sourceHandle);
        if (!relKey) continue;
        const srcNode = currentNodes.find((n) => n.id === edge.source);
        const tgtNode = currentNodes.find((n) => n.id === edge.target);
        const srcShellId = (srcNode?.data as SubmodelNodeData)?.parentId;
        const tgtShellId = (tgtNode?.data as SubmodelNodeData)?.parentId;
        if (!srcShellId || !tgtShellId) continue;
        const { aasNodes, removeProfileEntryForNode } = useAppStore.getState();
        const srcNs = aasNodes[srcShellId];
        const tgtNs = aasNodes[tgtShellId];
        const edgeData = (edge.data ?? {}) as { hsEntityName?: string; hsRelKey?: string };
        const entityKey = edgeData.hsEntityName ?? tgtNs?.identitySystemId;
        if (srcNs?.identitySystemId && entityKey) {
          removeProfileEntryForNode(srcShellId, [srcNs.identitySystemId, 'HierarchicalStructures', relKey, entityKey]);
        }
      }
      setEdges((prev: Edge[]) => applyEdgeChanges(changes, prev));
    },
    [setEdges]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const { sourceHandle, targetHandle, source: srcId, target: tgtId } = connection;
      const isCapToSkill = sourceHandle?.includes('-cap-') && targetHandle?.includes('-sk-');
      const isVarToAid   = sourceHandle?.includes('-var-') && targetHandle?.includes('-aid-');
      const isParToAid   = sourceHandle?.includes('-par-') && targetHandle?.includes('-aid-');
      const isSkillToAid = sourceHandle?.includes('-sk-')  && targetHandle?.includes('-aid-');
      const isRealizedByOrReference = isCapToSkill || isVarToAid || isParToAid || isSkillToAid;

      setEdges((prev: Edge[]) =>
        addEdge(
          {
            ...connection,
            type: edgeLineType === 'step' ? 'editableStep' : edgeLineType,
            label: isCapToSkill ? 'realizedBy' : isRealizedByOrReference ? 'InterfaceReference' : 'references',
            labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'Inter, system-ui, sans-serif' },
            labelBgStyle: { fill: '#1e293b', fillOpacity: 0.9 },
            labelBgPadding: [4, 2] as [number, number],
            style: { stroke: '#475569' },
          },
          prev
        )
      );

      const allNodes = useModelStore.getState().nodes;

      // Capability → Skill: set realizedBy on the capability
      if (isCapToSkill) {
        const capName   = sourceHandle!.split('-cap-').slice(1).join('-cap-');
        const skillName = targetHandle!.split('-sk-').slice(1).join('-sk-');
        const srcNode   = allNodes.find((n) => n.id === srcId);
        const srcShellId = (srcNode?.data as SubmodelNodeData)?.parentId;
        if (!srcShellId) return;
        const { aasNodes, updateProfileFieldForNode } = useAppStore.getState();
        const ns = aasNodes[srcShellId];
        if (!ns?.identitySystemId) return;
        updateProfileFieldForNode(srcShellId, [ns.identitySystemId, 'Capabilities', capName, 'realizedBy'], skillName);
        return;
      }

      // Variable / Parameter / Skill → AID: set InterfaceReference (or Skill.interface)
      // to the AID property/action/event idShort the connection points at.
      if (isVarToAid || isParToAid || isSkillToAid) {
        const affordanceKey = parseAidAffordanceHandle(targetHandle!);
        if (!affordanceKey) return;
        const srcNode = allNodes.find((n) => n.id === srcId);
        const srcShellId = (srcNode?.data as SubmodelNodeData)?.parentId;
        if (!srcShellId) return;
        const { aasNodes, updateProfileFieldForNode } = useAppStore.getState();
        const ns = aasNodes[srcShellId];
        if (!ns?.identitySystemId) return;

        if (isVarToAid) {
          const varName = nameAfterMarker(sourceHandle!, 'var');
          if (!varName) return;
          updateProfileFieldForNode(srcShellId, [ns.identitySystemId, 'Variables', varName, 'InterfaceReference'], affordanceKey);
        } else if (isParToAid) {
          const parName = nameAfterMarker(sourceHandle!, 'par');
          if (!parName) return;
          updateProfileFieldForNode(srcShellId, [ns.identitySystemId, 'Parameters', parName, 'InterfaceReference'], affordanceKey);
        } else {
          const skillName = nameAfterMarker(sourceHandle!, 'sk');
          if (!skillName) return;
          updateProfileFieldForNode(srcShellId, [ns.identitySystemId, 'Skills', skillName, 'interface'], affordanceKey);
        }
        return;
      }

      // BoM (HasPart / IsPartOf): populate HierarchicalStructures
      if (!sourceHandle || !targetHandle?.includes('-hs-entry')) return;
      const relKey = bomRelKeyFromHandle(sourceHandle);
      if (!relKey) return;
      const srcNode = allNodes.find((n) => n.id === srcId);
      const tgtNode = allNodes.find((n) => n.id === tgtId);
      const srcShellId = (srcNode?.data as SubmodelNodeData)?.parentId;
      const tgtShellId = (tgtNode?.data as SubmodelNodeData)?.parentId;
      if (!srcShellId || !tgtShellId) return;
      const { aasNodes, updateProfileFieldForNode } = useAppStore.getState();
      const srcNs = aasNodes[srcShellId];
      const tgtNs = aasNodes[tgtShellId];
      if (!srcNs?.identitySystemId || !tgtNs?.identitySystemId) return;
      let tgtBaseUrl = '';
      try { tgtBaseUrl = new URL(tgtNs.identityId).origin; } catch { /* ignore */ }
      updateProfileFieldForNode(srcShellId, [srcNs.identitySystemId, 'HierarchicalStructures', relKey, tgtNs.identitySystemId], {
        globalAssetId: tgtNs.identityGlobalAssetId || undefined,
        systemId: tgtNs.identitySystemId,
        ...(tgtBaseUrl ? { submodelId: `${tgtBaseUrl}/submodels/instances/${tgtNs.identitySystemId}/HierarchicalStructures` } : {}),
      });
    },
    [setEdges]
  );

  const onReconnect: OnReconnect = useCallback(
    (oldEdge, newConnection) => {
      setEdges((prev) => {
        const reconnected = reconnectEdge(oldEdge, newConnection, prev);
        return reconnected.map((e) =>
          e.id === oldEdge.id
            ? { ...e, type: edgeLineType === 'step' ? 'editableStep' : edgeLineType }
            : e
        );
      });
    },
    [edgeLineType, setEdges]
  );

  const onNodesDelete: OnNodesDelete = useCallback(
    (deleted: Node[]) => {
      // toggleSubmodel always operates on whichever AAS is currently active,
      // so a deleted node belonging to a *different* (non-active) shell must
      // switch the active AAS to that shell first — otherwise this either
      // silently no-ops (its key isn't in the active shell's list) or, worse,
      // toggles the wrong submodel off on the wrong AAS.
      for (const node of deleted) {
        if (node.type !== 'submodel' || !node.data?.submodelKey) continue;
        const key = node.data.submodelKey as SubmodelKey;
        const shellId = (node.data as SubmodelNodeData)?.parentId;
        if (!shellId) continue;

        const { aasNodes, activeAasNodeId } = useAppStore.getState();
        const ns = aasNodes[shellId];
        if (!ns?.selectedSubmodels.includes(key)) continue;

        if (shellId !== activeAasNodeId) setActiveAasNode(shellId);
        toggleSubmodel(key);
      }
    },
    [toggleSubmodel, setActiveAasNode]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();

      // ── AAS Shell drop ──────────────────────────────────────────────────────
      const aasMarker = e.dataTransfer.getData('application/aas-shell');
      if (aasMarker === 'new') {
        const absPos = screenToFlowPosition({ x: e.clientX, y: e.clientY });
        addAasShell({ x: Math.max(0, absPos.x - 480), y: Math.max(0, absPos.y - 40) });
        return;
      }

      // ── Submodel drop ───────────────────────────────────────────────────────
      const key = e.dataTransfer.getData('application/submodel-key') as SubmodelKey;
      if (!key) return;

      // Convert screen coords to canvas coords
      const absPos = screenToFlowPosition({ x: e.clientX, y: e.clientY });

      // Use getNodes() for up-to-date positions (avoids stale closure over dragged shells)
      const liveNodes = getNodes();
      const shellNodes = liveNodes.filter((n) => n.type === 'aasShell');
      const targetShell = shellNodes.find((shell) => {
        const sx = shell.position.x;
        const sy = shell.position.y;
        const sw = (shell.style?.width as number) ?? 960;
        const sh = (shell.style?.height as number) ?? 600;
        return absPos.x >= sx && absPos.x <= sx + sw && absPos.y >= sy && absPos.y <= sy + sh;
      }) ?? shellNodes[0];

      if (!targetShell) return;

      // Prevent duplicate submodels on the same AAS
      const alreadyExists = liveNodes.some(
        (n) => n.type === 'submodel' &&
          (n.data as SubmodelNodeData)?.submodelKey === key &&
          n.parentId === targetShell.id
      );
      if (alreadyExists) return;

      const shellPos = targetShell.position;
      const relX = Math.max(10, absPos.x - shellPos.x);
      const relY = Math.max(SHELL_HEADER_H + 10, absPos.y - shellPos.y);

      const nodeId = `submodel-${key}-${crypto.randomUUID().slice(0, 8)}`;

      const newNode: Node = {
        id: nodeId,
        type: 'submodel',
        position: { x: relX, y: relY },
        parentId: targetShell.id,
        extent: 'parent' as const,
        data: { submodelKey: key, parentId: targetShell.id } satisfies SubmodelNodeData,
      };

      setNodes((prev: Node[]) => [...prev, newNode]);

      // Switch active AAS to the shell this submodel was dropped onto
      setActiveAasNode(targetShell.id);

      // Sync selection state — read fresh from the store rather than the
      // `selectedSubmodels` hook value above, which is still the *previous*
      // active shell's list until the next render (setActiveAasNode's update
      // hasn't been reflected here yet). Matters whenever the drop target
      // isn't the shell that was already active.
      const targetSelected = useAppStore.getState().aasNodes[targetShell.id]?.selectedSubmodels ?? [];
      if (!targetSelected.includes(key)) {
        toggleSubmodel(key);
      }
    },
    [getNodes, setNodes, screenToFlowPosition, toggleSubmodel, setActiveAasNode]
  );

  return (
    <div className="mb-canvas-area">
      <ReactFlow
        nodes={nodes}
        edges={renderedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onReconnect={onReconnect}
        onNodesDelete={onNodesDelete}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        edgesReconnectable
        reconnectRadius={24}
        defaultEdgeOptions={{ reconnectable: true }}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        deleteKeyCode="Delete"
        className="mb-reactflow"
      >
        <Controls />
        <Background color={isLight ? '#cbd5e1' : '#334155'} gap={24} size={1} />
        <MiniMap
          nodeColor={(n) => (n.type === 'aasShell' ? '#38bdf8' : (isLight ? '#94a3b8' : '#475569'))}
          maskColor={isLight ? 'rgba(148,163,184,0.35)' : 'rgba(15,23,42,0.75)'}
          style={{ background: 'var(--surface2)', border: '1px solid var(--border)' }}
        />
      </ReactFlow>
    </div>
  );
}

// Outer component — provides ReactFlowProvider + layout
export function ModelBuilder() {
  return (
    <div className="mb-shell">
      <BuilderToolbar />
      <div className="mb-body">
        <CatalogPanel />
        <div className="mb-canvas-col">
          <ReactFlowProvider>
            <ModelBuilderCanvas />
          </ReactFlowProvider>
          <GuidancePanel />
        </div>
      </div>
      <PropertyEditorModal />
      <IdentityEditorModal />
    </div>
  );
}
