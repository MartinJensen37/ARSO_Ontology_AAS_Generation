import type { AasSubmodel, AasElement } from '../types';
import type { DigitalNameplate } from '../../types/resourceaas';
import { externalRef, DIGITAL_NAMEPLATE_SUBMODEL } from '../semanticIds';

/** Normalize a field that may be stored as a plain string or as an MLP array. */
function toMlp(v: unknown): Array<{ language: string; text: string }> {
  if (Array.isArray(v)) return v as Array<{ language: string; text: string }>;
  if (typeof v === 'string' && v) return [{ language: 'en', text: v }];
  return [];
}

export function buildNameplateSubmodel(baseUrl: string, systemId: string, fields: Partial<DigitalNameplate>, meta?: { id?: string; semanticId?: string }): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/DigitalNameplate`;
  const elements: AasElement[] = [];

  // MultiLanguageProperty fields (form stores these as [{language, text}] arrays)
  const mlpProps: Array<{ key: keyof DigitalNameplate; idShort: string }> = [
    { key: 'ManufacturerName',               idShort: 'ManufacturerName' },
    { key: 'ManufacturerProductDesignation', idShort: 'ManufacturerProductDesignation' },
    { key: 'ManufacturerProductFamily',      idShort: 'ManufacturerProductFamily' },
  ];

  for (const { key, idShort } of mlpProps) {
    const mlp = toMlp(fields[key]);
    if (mlp.length > 0) {
      elements.push({ modelType: 'MultiLanguageProperty', idShort, value: mlp });
    }
  }

  const stringProps: Array<{ key: keyof DigitalNameplate; idShort: string }> = [
    { key: 'SerialNumber',          idShort: 'SerialNumber' },
    { key: 'URIOfTheProduct',       idShort: 'URIOfTheProduct' },
    { key: 'ManufacturerArticleNumber', idShort: 'ManufacturerArticleNumber' },
    { key: 'BatchNumber',           idShort: 'BatchNumber' },
    { key: 'YearOfConstruction',    idShort: 'YearOfConstruction' },
    { key: 'DateOfManufacture',     idShort: 'DateOfManufacture' },
    { key: 'HardwareVersion',       idShort: 'HardwareVersion' },
    { key: 'SoftwareVersion',       idShort: 'SoftwareVersion' },
    { key: 'CountryOfOrigin',       idShort: 'CountryOfOrigin' },
  ];

  for (const { key, idShort } of stringProps) {
    const value = fields[key] as string | undefined;
    if (value !== undefined && value !== '') {
      elements.push({ modelType: 'Property', idShort, valueType: 'xs:string', value });
    }
  }

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'DigitalNameplate',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? DIGITAL_NAMEPLATE_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: elements,
  };
}
