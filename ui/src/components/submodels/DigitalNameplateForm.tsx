import { useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { DIGITAL_NAMEPLATE_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { DigitalNameplate } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

const NAMEPLATE_INSTANCE_BASE = 'https://smartproduction.aau.dk/submodels/instances/';

// Fields the MLP write-path (setFieldValue below) must wrap as [{language,text}] --
// exactly ManufacturerName and ManufacturerProductDesignation per
// nameplate_builder.py (every other field, including ManufacturerProductFamily,
// is a plain string Property there, not a MultiLanguageProperty).
const MLP_FIELDS = new Set(['ManufacturerName', 'ManufacturerProductDesignation']);

type Field = { key: string; label: string; required?: boolean; placeholder?: string };

// Every field here must correspond 1:1 to an idShort
// nameplate_builder.py actually reads/emits -- see that file's
// `optional_string_fields` dict and the ManufacturerName/
// ManufacturerProductDesignation/OrderCodeOfManufacturer handling above it.
// AddressInformation (ContactInformation SMC) is edited separately below,
// it's not a flat string field.
const FIELDS: Field[] = [
  { key: 'ManufacturerName', label: 'ManufacturerName', required: true, placeholder: '' },
  { key: 'ManufacturerProductDesignation', label: 'ManufacturerProductDesignation', required: true, placeholder: '' },
  { key: 'OrderCodeOfManufacturer', label: 'OrderCodeOfManufacturer', required: true, placeholder: '' },
  { key: 'SerialNumber', label: 'SerialNumber', required: false, placeholder: '' },
  { key: 'URIOfTheProduct', label: 'URIOfTheProduct', required: false, placeholder: `${NAMEPLATE_INSTANCE_BASE}<name>/DigitalNameplate/<uuid>` },
  { key: 'ManufacturerProductFamily', label: 'ManufacturerProductFamily', required: false, placeholder: '' },
  { key: 'ManufacturerArticleNumber', label: 'ManufacturerArticleNumber', required: false, placeholder: '' },
  { key: 'YearOfConstruction', label: 'YearOfConstruction', required: false, placeholder: '' },
  { key: 'DateOfManufacture', label: 'DateOfManufacture', required: false, placeholder: 'YYYY-MM-DD' },
  { key: 'HardwareVersion', label: 'HardwareVersion', required: false, placeholder: '' },
  { key: 'SoftwareVersion', label: 'SoftwareVersion', required: false, placeholder: '' },
  { key: 'CountryOfOrigin', label: 'CountryOfOrigin', required: false, placeholder: '' },
];

export function DigitalNameplateForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const identityId = useAppStore((s) => s.identityId);
  const { advanced } = useAdvanced();

  const systemId = parsedProfile ? Object.keys(parsedProfile)[0] : '';
  const nameplate: DigitalNameplate = (parsedProfile?.[systemId]?.DigitalNameplate ?? {}) as DigitalNameplate;

  // Auto-populate URIOfTheProduct with the instance URI when the field is empty
  useEffect(() => {
    if (!parsedProfile || !systemId || !identitySystemId) return;
    const current = nameplate.URIOfTheProduct;
    if (!current) {
      const shortId = crypto.randomUUID().split('-')[0];
      const defaultUri = `${NAMEPLATE_INSTANCE_BASE}${identitySystemId}/DigitalNameplate/${shortId}`;
      updateProfileField([systemId, 'DigitalNameplate', 'URIOfTheProduct'], defaultUri);
    }
  }, [systemId, identitySystemId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!parsedProfile) {
    return <p className="empty-state">No profile loaded. Complete the AAS Identity step first.</p>;
  }

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.Nameplate?.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/DigitalNameplate`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.Nameplate?.semanticId ?? DIGITAL_NAMEPLATE_SUBMODEL;

  // Template-aware getters/setters
  const getFieldValue = (key: string): string => {
    const v: any = (nameplate as any)[key];
    if (v == null) return '';
    if (Array.isArray(v)) {
      const en = v.find((x: any) => x?.language === 'en');
      const txt = en?.text ?? v[0]?.text ?? '';
      return typeof txt === 'string' ? txt : '';
    }
    return String(v ?? '');
  };

  const setFieldValue = (key: string, value: string) => {
    if (!value) {
      updateProfileField([systemId, 'DigitalNameplate', key], undefined);
      return;
    }
    if (MLP_FIELDS.has(key)) {
      updateProfileField([systemId, 'DigitalNameplate', key], [{ language: 'en', text: value }]);
      return;
    }
    updateProfileField([systemId, 'DigitalNameplate', key], value);
  };

  // AddressInformation — nested object (ContactInformation SMC in
  // nameplate_builder.py), not a flat string. All 4 sub-fields are
  // individually mandatory once ContactInformation exists at all; the
  // builder no longer fabricates placeholders for missing ones (a real
  // extraction failure should surface as a SHACL violation, not be hidden),
  // so filling these in here is how a human resolves that violation.
  const getAddressInformation = (): Record<string, string> =>
    (nameplate.AddressInformation ?? {}) as Record<string, string>;

  const setAddressField = (field: 'Street' | 'ZipCode' | 'CityTown' | 'NationalCode', value: string) => {
    const obj = { ...getAddressInformation() };
    if (value) obj[field] = value; else delete obj[field];
    const hasAny = Object.keys(obj).length > 0;
    updateProfileField([systemId, 'DigitalNameplate', 'AddressInformation'], hasAny ? obj : undefined);
  };

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Nameplate', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Nameplate', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="field-grid">
        {FIELDS.map(({ key, label, required, placeholder }) => (
          <div key={key} className="field-group">
            <label className="field-label">
              {label}
              {required && <span className="required-star"> *</span>}
            </label>
            <input
              type="text"
              className="field-input"
              value={getFieldValue(key)}
              placeholder={placeholder}
              onChange={(e) => setFieldValue(key, e.target.value)}
            />
          </div>
        ))}
      </div>

      {/* AddressInformation editor (ContactInformation SMC) */}
      <div className="section">
        <div className="section-header">
          <h4>AddressInformation <span className="required-star">*</span></h4>
        </div>
        <div className="field-grid">
          <div className="field-group">
            <label className="field-label">Street</label>
            <input type="text" className="field-input" value={getAddressInformation().Street ?? ''}
              onChange={(e) => setAddressField('Street', e.target.value)} />
          </div>
          <div className="field-group">
            <label className="field-label">ZipCode</label>
            <input type="text" className="field-input" value={getAddressInformation().ZipCode ?? ''}
              onChange={(e) => setAddressField('ZipCode', e.target.value)} />
          </div>
          <div className="field-group">
            <label className="field-label">CityTown</label>
            <input type="text" className="field-input" value={getAddressInformation().CityTown ?? ''}
              onChange={(e) => setAddressField('CityTown', e.target.value)} />
          </div>
          <div className="field-group">
            <label className="field-label">NationalCode</label>
            <input type="text" className="field-input" value={getAddressInformation().NationalCode ?? ''}
              placeholder="e.g. DE" onChange={(e) => setAddressField('NationalCode', e.target.value)} />
          </div>
        </div>
      </div>
    </div>
  );
}
