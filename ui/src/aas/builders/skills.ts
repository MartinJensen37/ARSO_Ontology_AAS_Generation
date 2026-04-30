import type { AasSubmodel, AasElement, AasOperation, AasOperationVariable } from '../types';
import type { Skill } from '../../types/resourceaas';
import { externalRef, SKILLS_SUBMODEL } from '../semanticIds';

export function buildSkillsSubmodel(
  baseUrl: string,
  systemId: string,
  skills: Record<string, Partial<Skill>>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/Skills`;

  const elements: AasElement[] = Object.entries(skills).map(([skillName, skill]) => {
    const smcValue: AasElement[] = [
      {
        modelType: 'Property',
        idShort: 'SemanticId',
        valueType: 'xs:string',
        value: skill?.semantic_id ?? '',
      },
    ];

    // Operation element
    const qualifiers = [];
    if (skill?.invocationDelegation) {
      qualifiers.push({ type: 'invocationDelegation', valueType: 'xs:string', value: skill.invocationDelegation, kind: 'ConceptQualifier' });
    }
    if (skill?.callType) {
      qualifiers.push({ type: skill.callType, valueType: 'xs:boolean', value: 'true', kind: 'ConceptQualifier' });
    }

    const toOpVars = (vars: Skill['inputVariables']): AasOperationVariable[] =>
      (vars ?? []).map((v) => ({
        value: {
          modelType: 'Property' as const,
          idShort: v.idShort,
          valueType: v.valueType,
          ...(v.displayName ? { description: [{ language: 'en', text: v.displayName }] } : {}),
          ...(v.description ? { description: [{ language: 'en', text: v.description }] } : {}),
        },
      }));

    const operation: AasOperation = {
      modelType: 'Operation',
      idShort: skillName,
      ...(skill?.semantic_id ? { semanticId: externalRef(skill.semantic_id) } : {}),
      ...(skill?.description ? { description: [{ language: 'en', text: skill.description }] } : {}),
      ...(qualifiers.length > 0 ? { qualifiers } : {}),
      ...(skill?.inputVariables?.length    ? { inputVariables:    toOpVars(skill.inputVariables) }    : {}),
      ...(skill?.outputVariables?.length   ? { outputVariables:   toOpVars(skill.outputVariables) }   : {}),
      ...(skill?.inoutputVariables?.length ? { inoutputVariables: toOpVars(skill.inoutputVariables) } : {}),
    };
    smcValue.push(operation);

    return {
      modelType: 'SubmodelElementCollection' as const,
      idShort: skillName,
      ...(skill?.description ? { description: [{ language: 'en', text: skill.description }] } : {}),
      value: smcValue,
    };
  });

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'Skills',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? SKILLS_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: elements,
  };
}
