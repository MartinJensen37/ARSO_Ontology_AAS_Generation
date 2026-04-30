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

type Field = { key: string; label: string; required?: boolean; placeholder?: string };

// Required fields first, then URI identifier, then optional fields
const FIELDS: Field[] = [
  { key: 'ManufacturerName', label: 'ManufacturerName', required: true, placeholder: '' },
  { key: 'ManufacturerProductDesignation', label: 'ManufacturerProductDesignation', required: true, placeholder: '' },
  { key: 'SerialNumber', label: 'SerialNumber', required: false, placeholder: '' },
  { key: 'URIOfTheProduct', label: 'URIOfTheProduct', required: false, placeholder: `${NAMEPLATE_INSTANCE_BASE}<name>/DigitalNameplate/<uuid>` },
  { key: 'ManufacturerProductRoot', label: 'ManufacturerProductRoot', required: false, placeholder: '' },
  { key: 'ManufacturerProductFamily', label: 'ManufacturerProductFamily', required: false, placeholder: '' },
  { key: 'ManufacturerProductType', label: 'ManufacturerProductType', required: false, placeholder: '' },
  { key: 'OrderCodeOfManufacturer', label: 'OrderCodeOfManufacturer', required: false, placeholder: '' },
  { key: 'ProductArticleNumberOfManufacturer', label: 'ProductArticleNumberOfManufacturer', required: false, placeholder: '' },
  { key: 'YearOfConstruction', label: 'YearOfConstruction', required: false, placeholder: '' },
  { key: 'DateOfManufacture', label: 'DateOfManufacture', required: false, placeholder: 'YYYY-MM-DD' },
  { key: 'HardwareVersion', label: 'HardwareVersion', required: false, placeholder: '' },
  { key: 'FirmwareVersion', label: 'FirmwareVersion', required: false, placeholder: '' },
  { key: 'SoftwareVersion', label: 'SoftwareVersion', required: false, placeholder: '' },
  { key: 'CountryOfOrigin', label: 'CountryOfOrigin', required: false, placeholder: '' },
  { key: 'AddressInformation', label: 'AddressInformation', required: false, placeholder: '' },
  { key: 'UniqueFacilityIdentifier', label: 'UniqueFacilityIdentifier', required: false, placeholder: '' },
  { key: 'CompanyLogo', label: 'CompanyLogo', required: false, placeholder: '' },
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
    const current = (nameplate as any).URIOfTheProduct;
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
      return typeof txt === 'string' ? txt.replace(/^\"|\"$/g, '') : '';
    }
    if (typeof v === 'object' && v?.value) return String(v.value);
    return String(v ?? '');
  };

  const setFieldValue = (key: string, value: string) => {
    if (!value) {
      updateProfileField([systemId, 'DigitalNameplate', key], undefined);
      return;
    }
    if (key === 'ManufacturerName' || key === 'ManufacturerProductDesignation' || key === 'ManufacturerProductFamily' || key === 'ManufacturerProductRoot') {
      updateProfileField([systemId, 'DigitalNameplate', key], [{ language: 'en', text: value }]);
      return;
    }
    if (key === 'CompanyLogo') {
      updateProfileField([systemId, 'DigitalNameplate', key], value);
      return;
    }
    updateProfileField([systemId, 'DigitalNameplate', key], value);
  };

  // Markings helpers (array of SMC objects) — moved inside component so we have access to state helpers
  const getMarkings = (): any[] => ((nameplate as any).Markings ?? []) as any[];

  const saveMarkings = (arr: any[]) => {
    updateProfileField([systemId, 'DigitalNameplate', 'Markings'], arr.length ? arr : undefined);
  };

  const addMarking = () => {
    const arr = getMarkings().slice();
    arr.push({ MarkingName: '', DesignationOfCertificateOrApproval: '', IssueDate: '', ExpiryDate: '', MarkingFile: undefined, MarkingAdditionalText: [] });
    saveMarkings(arr);
  };

  const removeMarking = (idx: number) => {
    const arr = getMarkings().slice();
    arr.splice(idx, 1);
    saveMarkings(arr);
  };

  const setMarkingField = (idx: number, field: string, value: any) => {
    const arr = getMarkings().slice();
    arr[idx] = { ...(arr[idx] || {}) };
    if (field === 'MarkingAdditionalText') {
      arr[idx][field] = value ? [{ language: 'en', text: value }] : [];
    } else {
      arr[idx][field] = value;
    }
    saveMarkings(arr);
  };

  // AssetSpecificProperties helpers
  const getAssetSpecificProperties = (): any => ((nameplate as any).AssetSpecificProperties ?? {}) as any;

  const saveAssetSpecificProperties = (obj: any) => {
    // if object is empty, unset the field
    const hasAny = (obj && Object.keys(obj).some((k) => (obj[k] && obj[k].length)));
    updateProfileField([systemId, 'DigitalNameplate', 'AssetSpecificProperties'], hasAny ? obj : undefined);
  };

  // ArbitraryProperty: array of strings
  const getArbitraryProperty = (): string[] => (getAssetSpecificProperties().ArbitraryProperty ?? []) as string[];
  const addArbitraryProperty = (value = '') => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryProperty = (obj.ArbitraryProperty ?? []).slice();
    obj.ArbitraryProperty.push(value);
    saveAssetSpecificProperties(obj);
  };
  const setArbitraryProperty = (idx: number, value: string) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryProperty = (obj.ArbitraryProperty ?? []).slice();
    obj.ArbitraryProperty[idx] = value;
    saveAssetSpecificProperties(obj);
  };
  const removeArbitraryProperty = (idx: number) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryProperty = (obj.ArbitraryProperty ?? []).slice();
    obj.ArbitraryProperty.splice(idx, 1);
    saveAssetSpecificProperties(obj);
  };

  // ArbitraryMLP: array of MLP objects (we store as [{language:'en', text: value}])
  const getArbitraryMLP = (): any[] => (getAssetSpecificProperties().ArbitraryMLP ?? []) as any[];
  const addArbitraryMLP = (value = '') => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryMLP = (obj.ArbitraryMLP ?? []).slice();
    obj.ArbitraryMLP.push([{ language: 'en', text: value }]);
    saveAssetSpecificProperties(obj);
  };
  const setArbitraryMLP = (idx: number, value: string) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryMLP = (obj.ArbitraryMLP ?? []).slice();
    obj.ArbitraryMLP[idx] = [{ language: 'en', text: value }];
    saveAssetSpecificProperties(obj);
  };
  const removeArbitraryMLP = (idx: number) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryMLP = (obj.ArbitraryMLP ?? []).slice();
    obj.ArbitraryMLP.splice(idx, 1);
    saveAssetSpecificProperties(obj);
  };

  // ArbitraryFile: array of file URLs
  const getArbitraryFile = (): string[] => (getAssetSpecificProperties().ArbitraryFile ?? []) as string[];
  const addArbitraryFile = (value = '') => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryFile = (obj.ArbitraryFile ?? []).slice();
    obj.ArbitraryFile.push(value);
    saveAssetSpecificProperties(obj);
  };
  const setArbitraryFile = (idx: number, value: string) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryFile = (obj.ArbitraryFile ?? []).slice();
    obj.ArbitraryFile[idx] = value;
    saveAssetSpecificProperties(obj);
  };
  const removeArbitraryFile = (idx: number) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.ArbitraryFile = (obj.ArbitraryFile ?? []).slice();
    obj.ArbitraryFile.splice(idx, 1);
    saveAssetSpecificProperties(obj);
  };

  // GuidelineSpecificProperties: array of SMC objects
  const getGuidelines = (): any[] => (getAssetSpecificProperties().GuidelineSpecificProperties ?? []) as any[];
  const saveGuidelines = (arr: any[]) => {
    const obj = { ...(getAssetSpecificProperties()) };
    obj.GuidelineSpecificProperties = arr.length ? arr : undefined;
    saveAssetSpecificProperties(obj);
  };
  const addGuideline = () => {
    const arr = getGuidelines().slice();
    arr.push({ GuidelineForConformityDeclaration: '', ArbitraryProperty: [], ArbitraryFile: [], ArbitraryMLP: [] });
    saveGuidelines(arr);
  };
  const removeGuideline = (idx: number) => {
    const arr = getGuidelines().slice();
    arr.splice(idx, 1);
    saveGuidelines(arr);
  };
  const setGuidelineField = (idx: number, field: string, value: any) => {
    const arr = getGuidelines().slice();
    arr[idx] = { ...(arr[idx] || {}) };
    arr[idx][field] = value;
    saveGuidelines(arr);
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

      {/* Markings editor */}
      <div className="section">
        <div className="section-header">
          <h4>Markings</h4>
          <button type="button" className="btn" onClick={addMarking}>Add Marking</button>
        </div>
        {(getMarkings() || []).map((m, idx) => (
          <div key={idx} className="nested-group">
            <div className="field-group">
              <label className="field-label">MarkingName</label>
              <input type="text" className="field-input" value={m?.MarkingName ?? ''} onChange={(e) => setMarkingField(idx, 'MarkingName', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">DesignationOfCertificateOrApproval</label>
              <input type="text" className="field-input" value={m?.DesignationOfCertificateOrApproval ?? ''} onChange={(e) => setMarkingField(idx, 'DesignationOfCertificateOrApproval', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">IssueDate</label>
              <input type="date" className="field-input" value={m?.IssueDate ?? ''} onChange={(e) => setMarkingField(idx, 'IssueDate', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">ExpiryDate</label>
              <input type="date" className="field-input" value={m?.ExpiryDate ?? ''} onChange={(e) => setMarkingField(idx, 'ExpiryDate', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">MarkingFile</label>
              <input type="text" className="field-input" value={m?.MarkingFile ?? ''} placeholder="file URL" onChange={(e) => setMarkingField(idx, 'MarkingFile', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">MarkingAdditionalText</label>
              <input type="text" className="field-input" value={(m?.MarkingAdditionalText && m.MarkingAdditionalText[0]?.text) ?? ''} onChange={(e) => setMarkingField(idx, 'MarkingAdditionalText', e.target.value)} />
            </div>
            <div className="field-group">
              <button type="button" className="btn danger" onClick={() => removeMarking(idx)}>Remove</button>
            </div>
          </div>
        ))}
      </div>

      {/* AssetSpecificProperties editor */}
      <div className="section">
        <div className="section-header">
          <h4>AssetSpecificProperties</h4>
        </div>

        <div className="subsection">
          <h5>ArbitraryProperty</h5>
          <button type="button" className="btn" onClick={() => addArbitraryProperty('')}>Add Property</button>
          {(getArbitraryProperty() || []).map((p, i) => (
            <div key={i} className="field-group">
              <input type="text" className="field-input" value={p ?? ''} onChange={(e) => setArbitraryProperty(i, e.target.value)} />
              <button type="button" className="btn danger" onClick={() => removeArbitraryProperty(i)}>Remove</button>
            </div>
          ))}
        </div>

        <div className="subsection">
          <h5>ArbitraryMLP</h5>
          <button type="button" className="btn" onClick={() => addArbitraryMLP('')}>Add MLP</button>
          {(getArbitraryMLP() || []).map((mlp, i) => (
            <div key={i} className="field-group">
              <input type="text" className="field-input" value={(mlp && mlp[0]?.text) ?? ''} onChange={(e) => setArbitraryMLP(i, e.target.value)} />
              <button type="button" className="btn danger" onClick={() => removeArbitraryMLP(i)}>Remove</button>
            </div>
          ))}
        </div>

        <div className="subsection">
          <h5>ArbitraryFile</h5>
          <button type="button" className="btn" onClick={() => addArbitraryFile('')}>Add File</button>
          {(getArbitraryFile() || []).map((f, i) => (
            <div key={i} className="field-group">
              <input type="text" className="field-input" value={f ?? ''} onChange={(e) => setArbitraryFile(i, e.target.value)} placeholder="file URL" />
              <button type="button" className="btn danger" onClick={() => removeArbitraryFile(i)}>Remove</button>
            </div>
          ))}
        </div>

        <div className="subsection">
          <h5>GuidelineSpecificProperties</h5>
          <button type="button" className="btn" onClick={addGuideline}>Add Guideline</button>
          {(getGuidelines() || []).map((g, gi) => (
            <div key={gi} className="nested-group">
              <div className="field-group">
                <label className="field-label">GuidelineForConformityDeclaration</label>
                <input type="text" className="field-input" value={g?.GuidelineForConformityDeclaration ?? ''} onChange={(e) => setGuidelineField(gi, 'GuidelineForConformityDeclaration', e.target.value)} />
              </div>
              <div className="field-group">
                <label className="field-label">ArbitraryProperty</label>
                {(g?.ArbitraryProperty ?? []).map((ap: string, ai: number) => (
                  <div key={ai} className="field-group-inline">
                    <input type="text" className="field-input" value={ap ?? ''} onChange={(e) => {
                      const arr = (getGuidelines()[gi].ArbitraryProperty ?? []).slice(); arr[ai] = e.target.value; setGuidelineField(gi, 'ArbitraryProperty', arr);
                    }} />
                    <button type="button" className="btn danger" onClick={() => {
                      const arr = (getGuidelines()[gi].ArbitraryProperty ?? []).slice(); arr.splice(ai, 1); setGuidelineField(gi, 'ArbitraryProperty', arr);
                    }}>Remove</button>
                  </div>
                ))}
                <button type="button" className="btn" onClick={() => { const arr = (getGuidelines()[gi].ArbitraryProperty ?? []).slice(); arr.push(''); setGuidelineField(gi, 'ArbitraryProperty', arr); }}>Add Property</button>
              </div>

              <div className="field-group">
                <label className="field-label">ArbitraryFile</label>
                {(g?.ArbitraryFile ?? []).map((af: string, ai: number) => (
                  <div key={ai} className="field-group-inline">
                    <input type="text" className="field-input" value={af ?? ''} onChange={(e) => { const arr = (getGuidelines()[gi].ArbitraryFile ?? []).slice(); arr[ai] = e.target.value; setGuidelineField(gi, 'ArbitraryFile', arr); }} />
                    <button type="button" className="btn danger" onClick={() => { const arr = (getGuidelines()[gi].ArbitraryFile ?? []).slice(); arr.splice(ai, 1); setGuidelineField(gi, 'ArbitraryFile', arr); }}>Remove</button>
                  </div>
                ))}
                <button type="button" className="btn" onClick={() => { const arr = (getGuidelines()[gi].ArbitraryFile ?? []).slice(); arr.push(''); setGuidelineField(gi, 'ArbitraryFile', arr); }}>Add File</button>
              </div>

              <div className="field-group">
                <label className="field-label">ArbitraryMLP</label>
                {(g?.ArbitraryMLP ?? []).map((amp: any, ai: number) => (
                  <div key={ai} className="field-group-inline">
                    <input type="text" className="field-input" value={(amp && amp[0]?.text) ?? ''} onChange={(e) => { const arr = (getGuidelines()[gi].ArbitraryMLP ?? []).slice(); arr[ai] = [{ language: 'en', text: e.target.value }]; setGuidelineField(gi, 'ArbitraryMLP', arr); }} />
                    <button type="button" className="btn danger" onClick={() => { const arr = (getGuidelines()[gi].ArbitraryMLP ?? []).slice(); arr.splice(ai, 1); setGuidelineField(gi, 'ArbitraryMLP', arr); }}>Remove</button>
                  </div>
                ))}
                <button type="button" className="btn" onClick={() => { const arr = (getGuidelines()[gi].ArbitraryMLP ?? []).slice(); arr.push([{ language: 'en', text: '' }]); setGuidelineField(gi, 'ArbitraryMLP', arr); }}>Add MLP</button>
              </div>

              <div className="field-group">
                <button type="button" className="btn danger" onClick={() => removeGuideline(gi)}>Remove Guideline</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
