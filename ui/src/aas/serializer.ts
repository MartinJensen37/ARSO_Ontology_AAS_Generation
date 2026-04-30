import type { AasShell, AasSubmodel, AasEnvironment } from './types';

/**
 * Assembles a full AAS Environment JSON string from a shell description and submodels.
 * This JSON is sent directly to /api/validate.
 */
export function buildAasEnvironment(
  shellId: string,
  shellIdShort: string,
  globalAssetId: string,
  submodels: AasSubmodel[],
  assetType?: string,
): string {
  const shell: AasShell = {
    modelType: 'AssetAdministrationShell',
    id: shellId,
    idShort: shellIdShort,
    assetInformation: {
      assetKind: 'Instance',
      globalAssetId,
      ...(assetType ? { assetType } : {}),
    },
    submodels: submodels.map((sm) => ({
      type: 'ModelReference' as const,
      keys: [{ type: 'Submodel' as const, value: sm.id }],
    })),
  };

  const env: AasEnvironment = {
    assetAdministrationShells: [shell],
    submodels,
    conceptDescriptions: [],
  };

  return JSON.stringify(env, null, 2);
}
