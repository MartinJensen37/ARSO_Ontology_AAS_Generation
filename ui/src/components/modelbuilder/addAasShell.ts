import type { Node } from '@xyflow/react';
import { useAppStore, REQUIRED_SUBMODELS } from '../../store/useAppStore';
import { useModelStore, createShellNodeId } from '../../store/useModelStore';
import type { SubmodelNodeData } from './nodes/SubmodelNode';
import { SUBMODEL_POSITIONS } from './submodelLayout';

/**
 * Create a new AAS shell (profile state + canvas node) with its required
 * submodel nodes, and make it active. Used by both click-to-add and
 * drag-and-drop; the canvas can hold zero shells, so this creates the first too.
 */
export function addAasShell(position?: { x: number; y: number }): string {
  const shellNodeId = createShellNodeId();
  useAppStore.getState().addAasNode(shellNodeId);
  useModelStore.getState().addShellNode(shellNodeId, position);

  const requiredNodes: Node[] = REQUIRED_SUBMODELS.map((key) => ({
    id: `submodel-${key}-${crypto.randomUUID().slice(0, 8)}`,
    type: 'submodel',
    position: { ...SUBMODEL_POSITIONS[key] },
    parentId: shellNodeId,
    extent: 'parent' as const,
    data: { submodelKey: key, parentId: shellNodeId } satisfies SubmodelNodeData,
  }));
  useModelStore.getState().setNodes((prev) => [...prev, ...requiredNodes]);

  useAppStore.getState().setActiveAasNode(shellNodeId);
  return shellNodeId;
}
