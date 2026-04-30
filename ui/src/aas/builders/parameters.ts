import type { AasSubmodel, AasElement } from '../types';
import type { Parameter } from '../../types/resourceaas';
import { externalRef, PARAMETERS_SUBMODEL } from '../semanticIds';

export function buildParametersSubmodel(baseUrl: string, systemId: string, parameters: Record<string, Partial<Parameter>>, meta?: { id?: string; semanticId?: string }): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/Parameters`;

  const elements: AasElement[] = Object.entries(parameters).map(([paramName, param]) => ({
    modelType: 'SubmodelElementCollection' as const,
    idShort: paramName,
    value: [
      {
        modelType: 'Property' as const,
        idShort: 'ParameterValue',
        valueType: 'xs:string',
        value: param?.ParameterValue ?? '',
      },
      ...(param?.Unit ? [{
        modelType: 'Property' as const,
        idShort: 'Unit',
        valueType: 'xs:string',
        value: param.Unit,
      }] : []),
    ],
  }));

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'Parameters',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? PARAMETERS_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: elements,
  };
}
