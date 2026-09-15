import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { SEMANTIC_ID_BASE, TECHNICAL_DATA_SUBMODEL } from '../../aas/semanticIds';
import type { TechnicalClassification, TechnicalData, TechnicalValue } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

/** Plain text of a string or MLP [{language,text}] value. */
function textOf(v: unknown): string {
  if (Array.isArray(v)) return String((v[0] as { text?: string } | undefined)?.text ?? '');
  return typeof v === 'string' ? v : '';
}

function isRange(v: TechnicalValue): v is { min?: string; max?: string } {
  return typeof v === 'object' && v !== null && ('min' in v || 'max' in v);
}

/** Datasheet names become idShorts, so strip non-word characters. */
function toIdShort(name: string): string {
  return name.trim().replace(/\W+/g, '_');
}

type GeneralKey = keyof NonNullable<TechnicalData['GeneralInformation']>;

// Field -> DigitalNameplate key the builder falls back to.
const GENERAL_FIELDS: Array<[GeneralKey, string, string]> = [
  ['ManufacturerName', 'Manufacturer name', 'ManufacturerName'],
  ['ManufacturerProductDesignation', 'Product designation', 'ManufacturerProductDesignation'],
  ['ManufacturerArticleNumber', 'Article number', 'ManufacturerArticleNumber'],
  ['ManufacturerOrderCode', 'Order code', 'OrderCodeOfManufacturer'],
];

const CLASSIFICATION_FIELDS: Array<[keyof TechnicalClassification, string, string]> = [
  ['ClassificationSystem', 'System', 'ECLASS'],
  ['ClassificationSystemVersion', 'Version', '12.0'],
  ['ProductClassId', 'Class ID', '0173-1#01-AKJ975#017'],
  ['ProductClassCodedName', 'Coded name', '27-27-03-01'],
];

export function TechnicalDataForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();
  const [newSection, setNewSection] = useState('');
  const [newProp, setNewProp] = useState<Record<string, string>>({});

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const td: TechnicalData = parsedProfile[systemId]?.TechnicalData ?? {};
  const general = td.GeneralInformation ?? {};
  const classifications = td.ProductClassifications ?? [];
  const sections = td.TechnicalProperties ?? {};
  const further = td.FurtherInformation ?? {};
  const nameplate = (parsedProfile[systemId]?.DigitalNameplate ?? {}) as Record<string, unknown>;

  const baseUrl = deriveBaseUrl(identityId);
  const meta = (parsedProfile[systemId] as any)?._meta?.TechnicalData ?? {};
  const metaId = meta.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/TechnicalData`;
  const metaSemanticId = meta.semanticId ?? TECHNICAL_DATA_SUBMODEL;

  const setTd = (path: string[], value: unknown) =>
    updateProfileField([systemId, 'TechnicalData', ...path], value);

  const setSections = (next: Record<string, Record<string, TechnicalValue>>) =>
    setTd(['TechnicalProperties'], next);

  const setClassifications = (next: TechnicalClassification[]) =>
    setTd(['ProductClassifications'], next.length ? next : undefined);

  const addSection = () => {
    const name = toIdShort(newSection);
    if (!name || name in sections) return;
    setSections({ ...sections, [name]: {} });
    setNewSection('');
  };

  const removeSection = (name: string) => {
    const clone = { ...sections };
    delete clone[name];
    setSections(clone);
  };

  const setProp = (section: string, prop: string, value: TechnicalValue | undefined) => {
    const props = { ...(sections[section] ?? {}) };
    if (value === undefined) delete props[prop];
    else props[prop] = value;
    setSections({ ...sections, [section]: props });
  };

  const addProp = (section: string, asRange: boolean) => {
    const name = toIdShort(newProp[section] ?? '');
    if (!name || name in (sections[section] ?? {})) return;
    setProp(section, name, asRange ? { min: '', max: '' } : '');
    setNewProp({ ...newProp, [section]: '' });
  };

  const statementText = Array.isArray(further.TextStatement)
    ? further.TextStatement.join('\n')
    : further.TextStatement ?? '';

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id" value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'TechnicalData', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'TechnicalData', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="card">
        <div className="card__header"><strong>General information</strong></div>
        <div className="card__body">
          <div className="field-grid">
            {GENERAL_FIELDS.map(([key, label, nameplateKey]) => (
              <div key={key} className="field-group">
                <label className="field-label">{label}</label>
                <input
                  className="field-input"
                  value={general[key] ?? ''}
                  placeholder={textOf(nameplate[nameplateKey]) || 'from datasheet'}
                  onChange={(e) => setTd(['GeneralInformation', key], e.target.value || undefined)}
                />
              </div>
            ))}
          </div>
          <span className="field-hint">Empty fields reuse the DigitalNameplate value.</span>
        </div>
      </div>

      <div className="card">
        <div className="card__header">
          <strong>Product classifications</strong>
          <button className="btn btn--xs btn--secondary"
            onClick={() => setClassifications([...classifications, { ClassificationSystem: 'ECLASS' }])}>
            + Classification
          </button>
        </div>
        <div className="card__body">
          {classifications.length === 0 && (
            <p className="empty-state">Only add a class the datasheet actually states.</p>
          )}
          {classifications.map((c, i) => (
            <div key={i} className="field-grid">
              {CLASSIFICATION_FIELDS.map(([key, label, placeholder]) => (
                <div key={key} className="field-group">
                  <label className="field-label">{label}</label>
                  <input
                    className="field-input"
                    value={c[key] ?? ''}
                    placeholder={placeholder}
                    onChange={(e) => setClassifications(classifications.map((x, j) =>
                      (j === i ? { ...x, [key]: e.target.value || undefined } : x)))}
                  />
                </div>
              ))}
              <button className="btn btn--xs btn--danger"
                onClick={() => setClassifications(classifications.filter((_, j) => j !== i))}>
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card__header"><strong>Technical properties</strong></div>
        <div className="card__body">
          <div className="submodel-form__controls">
            <input className="field-input" value={newSection} placeholder="Section, e.g. ElectricalRatings"
              onChange={(e) => setNewSection(e.target.value)} />
            <button className="btn btn--sm btn--secondary" onClick={addSection}>+ Section</button>
          </div>

          {Object.keys(sections).length === 0 && (
            <p className="empty-state">No property sections yet.</p>
          )}

          {Object.entries(sections).map(([section, props]) => (
            <div key={section} className="card card--flat">
              <div className="card__header">
                <strong>{section}</strong>
                <button className="btn btn--xs btn--danger" onClick={() => removeSection(section)}>✕</button>
              </div>
              <div className="card__body">
                {Object.entries(props ?? {}).map(([prop, value]) => (
                  <div key={prop} className="form-row form-row--inline">
                    <label className="form-label">{prop}</label>
                    {typeof value === 'string' ? (
                      <input className="form-input" value={value} placeholder="value with unit, e.g. 230 V AC"
                        onChange={(e) => setProp(section, prop, e.target.value)} />
                    ) : isRange(value) ? (
                      <>
                        <input className="form-input" value={value.min ?? ''} placeholder="min"
                          onChange={(e) => setProp(section, prop, { ...value, min: e.target.value })} />
                        <input className="form-input" value={value.max ?? ''} placeholder="max"
                          onChange={(e) => setProp(section, prop, { ...value, max: e.target.value })} />
                      </>
                    ) : (
                      <span className="form-hint">Nested section, preserved as imported</span>
                    )}
                    <button className="btn btn--xs btn--danger" onClick={() => setProp(section, prop, undefined)}>
                      ✕
                    </button>
                  </div>
                ))}
                <div className="submodel-form__controls">
                  <input className="field-input" value={newProp[section] ?? ''} placeholder="Property name"
                    onChange={(e) => setNewProp({ ...newProp, [section]: e.target.value })} />
                  <button className="btn btn--xs btn--secondary" onClick={() => addProp(section, false)}>+ Value</button>
                  <button className="btn btn--xs btn--secondary" onClick={() => addProp(section, true)}>+ Range</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card__header"><strong>Further information</strong></div>
        <div className="card__body">
          <div className="field-grid">
            <div className="field-group">
              <label className="field-label">Text statement <span className="field-hint">(one per line)</span></label>
              <textarea
                className="field-input"
                rows={2}
                value={statementText}
                onChange={(e) => {
                  const lines = e.target.value.split('\n').filter((l) => l.trim());
                  setTd(['FurtherInformation', 'TextStatement'], lines.length > 1 ? lines : lines[0]);
                }}
              />
            </div>
            <div className="field-group">
              <label className="field-label">Valid date</label>
              <input className="field-input" type="date" value={further.ValidDate ?? ''}
                onChange={(e) => setTd(['FurtherInformation', 'ValidDate'], e.target.value || undefined)} />
              <span className="field-hint">Required, or the section is dropped.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
