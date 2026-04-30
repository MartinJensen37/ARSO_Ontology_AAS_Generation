/**
 * Minimal TypeScript types for the AAS JSON format (AAS Part 2, v3.1).
 * Only the subset produced by our builder functions is covered.
 */

export interface AasLangString {
  language: string;
  text: string;
}

export interface AasReference {
  type: 'ExternalReference' | 'ModelReference';
  keys: Array<{ type: string; value: string }>;
}

export interface AasAdministration {
  version: string;
  revision: string;
}

export interface AasQualifier {
  type: string;
  valueType: string;
  value: string;
  kind?: string;
}

// ── SubmodelElements ──────────────────────────────────────────────────────────

export interface AasProperty {
  modelType: 'Property';
  idShort: string;
  valueType: string;
  value?: string;
  semanticId?: AasReference;
  description?: AasLangString[];
  category?: string;
}

export interface AasMultiLanguageProperty {
  modelType: 'MultiLanguageProperty';
  idShort: string;
  value?: AasLangString[];
  semanticId?: AasReference;
  description?: AasLangString[];
}

export interface AasFile {
  modelType: 'File';
  idShort: string;
  contentType: string;
  value?: string;
  semanticId?: AasReference;
  description?: AasLangString[];
}

export interface AasSubmodelElementCollection {
  modelType: 'SubmodelElementCollection';
  idShort: string;
  value?: AasElement[];
  semanticId?: AasReference;
  supplementalSemanticIds?: AasReference[];
  description?: AasLangString[];
}

export interface AasSubmodelElementList {
  modelType: 'SubmodelElementList';
  idShort: string;
  orderRelevant?: boolean;
  typeValueListElement: string;
  semanticId?: AasReference;
  semanticIdListElement?: AasReference;
  value?: AasElement[];
}

export interface AasEntity {
  modelType: 'Entity';
  idShort: string;
  entityType: 'SelfManagedEntity' | 'CoManagedEntity';
  globalAssetId?: string;
  statements?: AasElement[];
  semanticId?: AasReference;
}

export interface AasRelationshipElement {
  modelType: 'RelationshipElement';
  idShort: string;
  first: AasReference;
  second: AasReference;
  semanticId?: AasReference;
  description?: AasLangString[];
}

export interface AasReferenceElement {
  modelType: 'ReferenceElement';
  idShort: string;
  value?: AasReference;
  semanticId?: AasReference;
  supplementalSemanticIds?: AasReference[];
  description?: AasLangString[];
}

export interface AasCapabilityElement {
  modelType: 'Capability';
  idShort: string;
  semanticId?: AasReference;
  description?: AasLangString[];
}

export interface AasOperationVariable {
  value: AasProperty | AasMultiLanguageProperty;
}

export interface AasOperation {
  modelType: 'Operation';
  idShort: string;
  semanticId?: AasReference;
  description?: AasLangString[];
  qualifiers?: AasQualifier[];
  inputVariables?: AasOperationVariable[];
  outputVariables?: AasOperationVariable[];
  inoutputVariables?: AasOperationVariable[];
}

export type AasElement =
  | AasProperty
  | AasMultiLanguageProperty
  | AasFile
  | AasSubmodelElementCollection
  | AasSubmodelElementList
  | AasEntity
  | AasRelationshipElement
  | AasReferenceElement
  | AasCapabilityElement
  | AasOperation;

// ── Submodel ──────────────────────────────────────────────────────────────────

export interface AasSubmodel {
  modelType: 'Submodel';
  id: string;
  idShort: string;
  kind: 'Instance';
  displayName?: AasLangString[];
  semanticId?: AasReference;
  administration?: AasAdministration;
  submodelElements?: AasElement[];
}

// ── Shell ─────────────────────────────────────────────────────────────────────

export interface AasSubmodelRef {
  type: 'ModelReference';
  keys: [{ type: 'Submodel'; value: string }];
}

export interface AasShell {
  modelType: 'AssetAdministrationShell';
  id: string;
  idShort: string;
  assetInformation: {
    assetKind: 'Instance';
    globalAssetId: string;
    assetType?: string;
  };
  submodels: AasSubmodelRef[];
}

// ── Environment ───────────────────────────────────────────────────────────────

export interface AasEnvironment {
  assetAdministrationShells: AasShell[];
  submodels: AasSubmodel[];
  conceptDescriptions: [];
}
