import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';
import type { SubmodelKey } from './useAppStore';

export type EdgeLineType = 'default' | 'straight' | 'smoothstep' | 'step';

export type ModalState =
  | { kind: 'none' }
  | { kind: 'identity'; shellNodeId: string }
  | { kind: 'property'; submodelKey: SubmodelKey; nodeId: string };

interface ModelState {
  nodes: Node[];
  edges: Edge[];
  edgeLineType: EdgeLineType;
  modal: ModalState;

  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  setEdgeLineType: (lineType: EdgeLineType) => void;
  openIdentityModal: (shellNodeId?: string) => void;
  openPropertyModal: (submodelKey: SubmodelKey, nodeId: string) => void;
  closeModal: () => void;
  removeNodeById: (id: string) => void;
  addShellNode: (shellNodeId: string, position?: { x: number; y: number }) => void;
  resetAll: () => void;
}

export const SHELL_NODE_ID = 'aas-shell';

/** Generate a unique shell node ID */
export function createShellNodeId(): string {
  return `aas-shell-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

const initialShellNode: Node = {
  id: SHELL_NODE_ID,
  type: 'aasShell',
  position: { x: 60, y: 40 },
  // Explicit size required for sub-flow parent node and NodeResizer
  style: { width: 540, height: 360 },
  data: { label: 'AAS Shell' },
  dragHandle: '.mb-drag-handle',
  deletable: false,
};

export const useModelStore = create<ModelState>()(
  persist(
    (set, get) => ({
      nodes: [initialShellNode],
      edges: [],
      edgeLineType: 'smoothstep',
      modal: { kind: 'none' },

      setNodes: (nodes) =>
        set((s) => ({ nodes: typeof nodes === 'function' ? nodes(s.nodes) : nodes })),

      setEdges: (edges) =>
        set((s) => ({ edges: typeof edges === 'function' ? edges(s.edges) : edges })),

      setEdgeLineType: (lineType) => set({ edgeLineType: lineType }),

      openIdentityModal: (shellNodeId) =>
        set({ modal: { kind: 'identity', shellNodeId: shellNodeId ?? SHELL_NODE_ID } }),

      openPropertyModal: (submodelKey, nodeId) =>
        set({ modal: { kind: 'property', submodelKey, nodeId } }),

      closeModal: () => set({ modal: { kind: 'none' } }),

      removeNodeById: (id) =>
        set((s) => ({
          nodes: s.nodes.filter((n) => n.id !== id && n.parentId !== id),
          edges: s.edges.filter((e) => e.source !== id && e.target !== id),
        })),

      addShellNode: (shellNodeId, position) => {
        const s = get();
        if (s.nodes.some((n) => n.id === shellNodeId)) return;
        // Offset position from last shell node to avoid overlap
        const shellNodes = s.nodes.filter((n) => n.type === 'aasShell');
        const defaultPos = position ?? {
          x: 60 + shellNodes.length * 600,
          y: 40,
        };
        const newShell: Node = {
          id: shellNodeId,
          type: 'aasShell',
          position: defaultPos,
          style: { width: 540, height: 360 },
          data: { label: 'AAS Shell' },
          dragHandle: '.mb-drag-handle',
          deletable: true,
        };
        set({ nodes: [...s.nodes, newShell] });
      },

      resetAll: () => set({ nodes: [initialShellNode], edges: [], edgeLineType: 'smoothstep', modal: { kind: 'none' } }),
    }),
    {
      name: 'resourceaas-model',
      // Only persist graph layout; modal is ephemeral
      partialize: (s) => ({ nodes: s.nodes, edges: s.edges, edgeLineType: s.edgeLineType }),
    }
  )
);
