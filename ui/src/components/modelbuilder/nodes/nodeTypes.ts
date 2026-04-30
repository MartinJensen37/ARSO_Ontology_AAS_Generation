import type { NodeTypes } from '@xyflow/react';
import { AasShellNode } from './AasShellNode';
import { SubmodelNode } from './SubmodelNode';

// Must be defined at module scope — never inside a component body.
export const nodeTypes: NodeTypes = {
  aasShell: AasShellNode,
  submodel: SubmodelNode,
};
