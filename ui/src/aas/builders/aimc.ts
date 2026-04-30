import type { AasSubmodel, AasElement, AasSubmodelElementList, AasReferenceElement, AasRelationshipElement } from '../types';
import type { AIMCMappingConfig } from '../../types/resourceaas';
import {
  externalRef,
  AIMC_SUBMODEL,
  AIMC_MAPPING_CONFIGURATIONS,
  AIMC_MAPPING_CONFIGURATION,
  AIMC_INTERFACE_REFERENCE,
  AIMC_MAPPING_SOURCE_SINK_RELATIONS,
  AIMC_MAPPING_SOURCE_SINK_RELATION,
} from '../semanticIds';

function submodelIdForKey(baseUrl: string, systemId: string, key: string): string {
  switch (key) {
    case 'Variables':   return `${baseUrl}/submodels/instances/${systemId}/OperationalData`;
    case 'Skills':      return `${baseUrl}/submodels/instances/${systemId}/Skills`;
    case 'Parameters':  return `${baseUrl}/submodels/instances/${systemId}/Parameters`;
    default:            return '';
  }
}

export function buildAIMCSubmodel(
  baseUrl: string,
  systemId: string,
  aimc: Record<string, AIMCMappingConfig>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/AssetInterfacesMappingConfiguration`;
  const aidSubmodelId = `${baseUrl}/submodels/instances/${systemId}/AID`;

  const mappingConfigElements: AasElement[] = Object.entries(aimc).map(([mappingName, config]) => {
    // InterfaceReference — ReferenceElement pointing to the AID interface SMC
    const interfaceRef: AasReferenceElement = {
      modelType: 'ReferenceElement',
      idShort: 'InterfaceReference',
      semanticId: externalRef(AIMC_INTERFACE_REFERENCE),
      value: {
        type: 'ModelReference',
        keys: [
          { type: 'Submodel', value: aidSubmodelId },
          { type: 'SubmodelElementCollection', value: config.interfaceName },
        ],
      },
    };

    // MappingSourceSinkRelations — list of RelationshipElements
    const relations: AasRelationshipElement[] = (config.relations ?? []).map((rel, idx) => {
      const srcSubmodelId = submodelIdForKey(baseUrl, systemId, rel.sourceSubmodel);

      // first: source element reference
      const firstKeys: Array<{ type: string; value: string }> = [
        { type: 'Submodel', value: srcSubmodelId },
      ];
      if (rel.sourceSubmodel === 'Skills') {
        firstKeys.push({ type: 'SubmodelElementCollection', value: rel.sourceElement });
      } else {
        firstKeys.push({ type: 'Property', value: rel.sourceElement });
      }

      // second: AID affordance reference
      const secondKeys: Array<{ type: string; value: string }> = [
        { type: 'Submodel', value: aidSubmodelId },
        { type: 'SubmodelElementCollection', value: config.interfaceName },
        { type: 'SubmodelElementCollection', value: 'InteractionMetadata' },
        { type: 'SubmodelElementCollection', value: rel.aidAffordanceType },
        { type: 'SubmodelElementCollection', value: rel.aidAffordance },
      ];

      return {
        modelType: 'RelationshipElement' as const,
        idShort: `Relation_${String(idx + 1).padStart(2, '0')}`,
        semanticId: externalRef(AIMC_MAPPING_SOURCE_SINK_RELATION),
        first:  { type: 'ModelReference' as const, keys: firstKeys },
        second: { type: 'ModelReference' as const, keys: secondKeys },
      };
    });

    const relationsList: AasSubmodelElementList = {
      modelType: 'SubmodelElementList',
      idShort: 'MappingSourceSinkRelations',
      semanticId: externalRef(AIMC_MAPPING_SOURCE_SINK_RELATIONS),
      semanticIdListElement: externalRef(AIMC_MAPPING_SOURCE_SINK_RELATION),
      orderRelevant: true,
      typeValueListElement: 'RelationshipElement',
      value: relations,
    };

    return {
      modelType: 'SubmodelElementCollection' as const,
      idShort: mappingName,
      semanticId: externalRef(AIMC_MAPPING_CONFIGURATION),
      value: [interfaceRef, relationsList],
    };
  });

  const mappingConfigList: AasSubmodelElementList = {
    modelType: 'SubmodelElementList',
    idShort: 'MappingConfigurations',
    semanticId: externalRef(AIMC_MAPPING_CONFIGURATIONS),
    semanticIdListElement: externalRef(AIMC_MAPPING_CONFIGURATION),
    orderRelevant: true,
    typeValueListElement: 'SubmodelElementCollection',
    value: mappingConfigElements,
  };

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'AssetInterfacesMappingConfiguration',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? AIMC_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: [mappingConfigList],
  };
}
