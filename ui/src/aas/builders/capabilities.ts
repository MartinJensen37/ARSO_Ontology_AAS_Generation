import type { AasSubmodel, AasElement, AasSubmodelElementList, AasRelationshipElement } from '../types';
import type { Capability } from '../../types/resourceaas';
import {
  externalRef, modelRef,
  CAPABILITIES_SUBMODEL, CAPABILITY_SET, CAPABILITY_CONTAINER, CAPABILITY_REALIZED_BY,
} from '../semanticIds';

export function buildCapabilitiesSubmodel(
  baseUrl: string,
  systemId: string,
  capabilities: Record<string, Partial<Capability>>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/Capabilities`;
  const skillsSubmodelId = `${baseUrl}/submodels/instances/${systemId}/Skills`;

  const capabilityElements: AasElement[] = Object.entries(capabilities).map(([capName, cap]) => {
    const containerValue: AasElement[] = [
      // SemanticId property (plain string — used by SHACL validation)
      {
        modelType: 'Property',
        idShort: 'SemanticId',
        valueType: 'xs:string',
        value: cap?.semantic_id ?? '',
      },
      // Capability element — formal AAS Capability model type
      {
        modelType: 'Capability',
        idShort: capName,
        ...(cap?.semantic_id ? { semanticId: externalRef(cap.semantic_id) } : {}),
      },
    ];

    // realizedBy — SubmodelElementList of RelationshipElements pointing to a skill
    if (cap?.realizedBy) {
      const rel: AasRelationshipElement = {
        modelType: 'RelationshipElement',
        idShort: cap.realizedBy,
        first: modelRef(submodelId,
          { type: 'SubmodelElementCollection', value: 'CapabilitySet' },
          { type: 'SubmodelElementCollection', value: capName },
        ),
        second: modelRef(skillsSubmodelId,
          { type: 'SubmodelElementCollection', value: cap.realizedBy },
        ),
      };

      const realizedByList: AasSubmodelElementList = {
        modelType: 'SubmodelElementList',
        idShort: 'realizedBy',
        semanticId: externalRef(CAPABILITY_REALIZED_BY),
        orderRelevant: true,
        typeValueListElement: 'RelationshipElement',
        value: [rel],
      };
      containerValue.push(realizedByList);
    }

    return {
      modelType: 'SubmodelElementCollection' as const,
      idShort: capName,
      semanticId: externalRef(cap?._containerSemanticId ?? CAPABILITY_CONTAINER),
      value: containerValue,
    };
  });

  const capabilitySet: AasElement = {
    modelType: 'SubmodelElementCollection',
    idShort: 'CapabilitySet',
    semanticId: externalRef(CAPABILITY_SET),
    value: capabilityElements,
  };

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'Capabilities',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? CAPABILITIES_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: [capabilitySet],
  };
}
