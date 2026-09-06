import type { Node } from '@xyflow/react';
import { useAppStore, REQUIRED_SUBMODELS } from '../../store/useAppStore';
import { useModelStore, createShellNodeId } from '../../store/useModelStore';
import type { SubmodelNodeData } from './nodes/SubmodelNode';

// Must match SubmodelNode.tsx's layout constants.
const SHELL_HEADER_H = 70;
const SUBMODEL_START_X = 40;

/**
 * Create a new AAS shell (profile state + canvas node) with its required
 * submodel nodes pre-populated, and make it the active AAS. Shared by the
 * catalog's click-to-add button and the canvas's drag-and-drop "new AAS"
 * handler -- every shell is created this way, including the first, since the
 * canvas can start (and be reset to) zero AAS nodes.
 */
export function addAasShell(position?: { x: number; y: number }): string {
  const shellNodeId = createShellNodeId();
  useAppStore.getState().addAasNode(shellNodeId);
  useModelStore.getState().addShellNode(shellNodeId, position);

  const requiredNodes: Node[] = REQUIRED_SUBMODELS.map((key, i) => ({
    id: `submodel-${key}-${crypto.randomUUID().slice(0, 8)}`,
    type: 'submodel',
    position: { x: SUBMODEL_START_X, y: SHELL_HEADER_H + i * 160 },
    parentId: shellNodeId,
    extent: 'parent' as const,
    data: { submodelKey: key, parentId: shellNodeId } satisfies SubmodelNodeData,
  }));
  useModelStore.getState().setNodes((prev) => [...prev, ...requiredNodes]);

  useAppStore.getState().setActiveAasNode(shellNodeId);
  return shellNodeId;
}
