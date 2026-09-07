import type { SubmodelKey } from '../../store/useAppStore';

/**
 * Fixed grid position (relative to the parent AAS shell) for each submodel
 * node type. Shared by addAasShell.ts (new AAS) and BuilderToolbar.tsx
 * (AI-generated / file import) so every code path that populates a shell
 * lays submodels out identically instead of stacking them in one column.
 *
 * Layout (columns left-to-right, rows top-to-bottom):
 *   Nameplate   Variables       Parameters
 *   Hierarch.
 *   Capabilities  Skills        AID
 *
 * Row/column gaps are sized from each submodel's row-count cap in
 * SubmodelNode.tsx's getRows() (header ~36px + rows * 22px), with enough
 * margin that typical content doesn't collide with the node below/right of
 * it. AID and Skills sit at the bottom of their column with nothing below,
 * so their unbounded content (multiple interfaces, many actions) can grow
 * downward without needing to be budgeted for.
 */
export const SHELL_HEADER_H = 70;
export const SUBMODEL_START_X = 40;

const COL1_X = SUBMODEL_START_X;
const COL2_X = COL1_X + 300;
const COL3_X = COL2_X + 300;

const ROW1_Y = SHELL_HEADER_H + 20;
const ROW2_Y = ROW1_Y + 200;
const ROW3_Y = ROW2_Y + 150;

export const SUBMODEL_POSITIONS: Record<SubmodelKey, { x: number; y: number }> = {
  Nameplate:              { x: COL1_X, y: ROW1_Y },
  HierarchicalStructures: { x: COL1_X, y: ROW2_Y },
  Capabilities:           { x: COL1_X, y: ROW3_Y },
  Variables:              { x: COL2_X, y: ROW1_Y },
  Skills:                 { x: COL2_X, y: ROW3_Y },
  Parameters:             { x: COL3_X, y: ROW1_Y },
  AID:                    { x: COL3_X, y: ROW3_Y },
};

/** Default AAS shell box size, sized to fit the grid above without overlap
 * for typical (row-cap-sized) content. */
export const DEFAULT_SHELL_WIDTH = 960;
export const DEFAULT_SHELL_HEIGHT = 800;
