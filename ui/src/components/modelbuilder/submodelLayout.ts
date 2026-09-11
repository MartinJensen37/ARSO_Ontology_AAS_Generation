import type { SubmodelKey } from '../../store/useAppStore';

/**
 * Fixed grid position (relative to the parent AAS shell) per submodel node type,
 * so every code path that populates a shell lays them out identically:
 *   Nameplate     Variables   Parameters
 *   Hierarch.
 *   Capabilities  Skills      AID
 *
 * Gaps are sized from SubmodelNode.tsx's getRows() row caps. AID and Skills sit
 * at the bottom of their column so their unbounded content can grow downward.
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
