import { ALL_SUBMODELS, SUBMODEL_REGISTRY, type SubmodelKey } from '../../store/submodelRegistry';

/**
 * Fixed grid position (relative to the parent AAS shell) per submodel node type,
 * taken from each registry entry's col/row:
 *   Nameplate     Variables      Parameters
 *   Hierarch.     TechnicalData  AIMC
 *   Capabilities  Skills         AID
 *
 * Gaps are sized from SubmodelNode.tsx's getRows() row caps; row-2 nodes cap
 * their rows to fit above row 3. AID and Skills sit at the bottom of their
 * column so their unbounded content can grow downward.
 */
export const SHELL_HEADER_H = 70;
export const SUBMODEL_START_X = 40;

const COL_X = [SUBMODEL_START_X, SUBMODEL_START_X + 300, SUBMODEL_START_X + 600];

const ROW1_Y = SHELL_HEADER_H + 20;
const ROW_Y = [ROW1_Y, ROW1_Y + 200, ROW1_Y + 350];

export const SUBMODEL_POSITIONS = Object.fromEntries(
  ALL_SUBMODELS.map((key) => {
    const { col, row } = SUBMODEL_REGISTRY[key];
    return [key, { x: COL_X[col - 1], y: ROW_Y[row - 1] }];
  }),
) as Record<SubmodelKey, { x: number; y: number }>;

/** Default AAS shell box size, sized to fit the grid above without overlap
 * for typical (row-cap-sized) content. */
export const DEFAULT_SHELL_WIDTH = 960;
export const DEFAULT_SHELL_HEIGHT = 800;
