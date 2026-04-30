import type { AasSubmodel, AasElement } from '../types';
import type { Variable } from '../../types/resourceaas';
import { externalRef, OPERATIONAL_DATA_SUBMODEL } from '../semanticIds';

export function buildOperationalDataSubmodel(
  baseUrl: string,
  systemId: string,
  variables: Record<string, Partial<Variable>>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/OperationalData`;

  const elements: AasElement[] = Object.entries(variables).map(([varName, variable]) => ({
    modelType: 'Property' as const,
    idShort: varName,
    valueType: 'xs:anyURI',
    value: variable?.semanticId ?? '',
    ...(variable?.semanticId ? { semanticId: externalRef(variable.semanticId) } : {}),
  }));

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'OperationalData',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? OPERATIONAL_DATA_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: elements,
  };
}
