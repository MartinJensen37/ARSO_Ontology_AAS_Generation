import type { AasSubmodel, AasElement, AasEntity, AasRelationshipElement, AasReferenceElement } from '../types';
import type { HierarchicalStructures, BomEntity } from '../../types/resourceaas';
import {
  externalRef, modelRef,
  HIERARCHICAL_STRUCTURES, HIERARCHICAL_ARCHETYPE, HIERARCHICAL_ENTRY_NODE,
  HIERARCHICAL_NODE, HIERARCHICAL_SAME_AS, HIERARCHICAL_RELATIONSHIP,
} from '../semanticIds';

export function buildHierarchicalStructuresSubmodel(
  baseUrl: string,
  systemId: string,
  globalAssetId: string,
  _aasId: string,
  fields: Partial<HierarchicalStructures>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/HierarchicalStructures`;
  // entryNodeId is the asset name — used as idShort of the EntryNode entity
  const entryNodeId = fields.Name ?? systemId;
  const archetype = fields.Archetype ?? 'OneUp';

  // Determine which HasPart/IsPartOf dict to use based on archetype
  const primaryKey = archetype === 'OneDown' || archetype === 'OneUpAndOneDown' ? 'HasPart'
    : archetype === 'OneUp'                                                      ? 'IsPartOf'
    : 'IsPartOf';
  const entityDict: Record<string, BomEntity> = {} as Record<string, BomEntity>;

  // Merge both dicts for OneUpAndOneDown; otherwise use primary
  if (archetype === 'OneUpAndOneDown') {
    Object.assign(entityDict, fields.HasPart ?? {}, fields.IsPartOf ?? {});
  } else {
    Object.assign(entityDict, (fields[primaryKey] as Record<string, BomEntity> | undefined) ?? {});
  }

  const sameAsDict: Record<string, BomEntity> = (fields.SameAs as Record<string, BomEntity> | undefined) ?? {};

  // ── Build Node entities and Relationships inside EntryNode ────────────────
  const entryStatements: AasElement[] = [];

  // HasPart / IsPartOf entities
  for (const [entityName, entityData] of Object.entries(entityDict)) {
    const entityGlobalAssetId = entityData?.globalAssetId ?? '';
    const entitySystemId = entityData?.systemId ?? entityName;

    const entitySubmodelId = entityData?.submodelId ??
      `${baseUrl}/submodels/instances/${entitySystemId.endsWith('AAS') ? entitySystemId : entitySystemId + 'AAS'}/HierarchicalStructures`;

    const sameAsRef: AasReferenceElement = {
      modelType: 'ReferenceElement',
      idShort: 'SameAs',
      semanticId: externalRef(HIERARCHICAL_SAME_AS),
      supplementalSemanticIds: [externalRef(HIERARCHICAL_ENTRY_NODE)],
      value: modelRef(entitySubmodelId, { type: 'Entity', value: entryNodeId }),
    };

    const nodeEntity: AasEntity = {
      modelType: 'Entity',
      idShort: entityName,
      entityType: entityGlobalAssetId ? 'SelfManagedEntity' : 'CoManagedEntity',
      ...(entityGlobalAssetId ? { globalAssetId: entityGlobalAssetId } : {}),
      semanticId: externalRef(HIERARCHICAL_NODE),
      statements: [sameAsRef],
    };
    entryStatements.push(nodeEntity);

    const relIdShort = archetype === 'OneUpAndOneDown'
      ? ((fields.HasPart as any)?.[entityName] ? `HasPart_${entityName}` : `IsPartOf_${entityName}`)
      : `${primaryKey}_${entityName}`;
    const rel: AasRelationshipElement = {
      modelType: 'RelationshipElement',
      idShort: relIdShort,
      semanticId: externalRef(HIERARCHICAL_RELATIONSHIP),
      first: modelRef(submodelId, { type: 'Entity', value: entryNodeId }),
      second: modelRef(submodelId, { type: 'Entity', value: entryNodeId }, { type: 'Entity', value: entityName }),
    };
    entryStatements.push(rel);
  }

  // SameAs entities — symmetric equivalence references
  for (const [entityName, entityData] of Object.entries(sameAsDict)) {
    const entityGlobalAssetId = entityData?.globalAssetId ?? '';
    const entitySystemId = entityData?.systemId ?? entityName;

    const entitySubmodelId = entityData?.submodelId ??
      `${baseUrl}/submodels/instances/${entitySystemId}/HierarchicalStructures`;

    const sameAsRef: AasReferenceElement = {
      modelType: 'ReferenceElement',
      idShort: 'SameAs',
      semanticId: externalRef(HIERARCHICAL_SAME_AS),
      supplementalSemanticIds: [externalRef(HIERARCHICAL_ENTRY_NODE)],
      value: modelRef(entitySubmodelId, { type: 'Entity', value: entryNodeId }),
    };

    const nodeEntity: AasEntity = {
      modelType: 'Entity',
      idShort: `SameAs_${entityName}`,
      entityType: entityGlobalAssetId ? 'SelfManagedEntity' : 'CoManagedEntity',
      ...(entityGlobalAssetId ? { globalAssetId: entityGlobalAssetId } : {}),
      semanticId: externalRef(HIERARCHICAL_NODE),
      statements: [sameAsRef],
    };
    entryStatements.push(nodeEntity);

    const rel: AasRelationshipElement = {
      modelType: 'RelationshipElement',
      idShort: `SameAs_${entityName}`,
      semanticId: externalRef(HIERARCHICAL_SAME_AS),
      first: modelRef(submodelId, { type: 'Entity', value: entryNodeId }),
      second: modelRef(submodelId, { type: 'Entity', value: entryNodeId }, { type: 'Entity', value: `SameAs_${entityName}` }),
    };
    entryStatements.push(rel);
  }

  const entryNode: AasEntity = {
    modelType: 'Entity',
    idShort: entryNodeId,
    entityType: 'SelfManagedEntity',
    globalAssetId,
    semanticId: externalRef(HIERARCHICAL_ENTRY_NODE),
    statements: entryStatements,
  };

  const submodelElements: AasElement[] = [
    {
      modelType: 'Property',
      idShort: 'ArcheType',
      valueType: 'xs:string',
      value: archetype,
      semanticId: externalRef(HIERARCHICAL_ARCHETYPE),
    },
    entryNode,
  ];

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'HierarchicalStructures',
    kind: 'Instance',
    displayName: [{ language: 'en', text: entryNodeId }],
    semanticId: externalRef(meta?.semanticId ?? HIERARCHICAL_STRUCTURES),
    administration: { version: '1', revision: '1' },
    submodelElements,
  };
}
