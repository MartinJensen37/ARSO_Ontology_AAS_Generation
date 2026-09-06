import { useAppStore } from '../../store/useAppStore';
import { SemanticIdInput } from '../shared/SemanticIdInput';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { PARAMETERS_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { Parameter } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

export function ParametersForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const parameters = parsedProfile[systemId]?.Parameters ?? {};

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.Parameters?.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/Parameters`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.Parameters?.semanticId ?? PARAMETERS_SUBMODEL;

  const updateInterfaceReference = (paramName: string, value: string) => {
    updateProfileField([systemId, 'Parameters', paramName, 'InterfaceReference'], value || undefined);
  };

  const updateSemanticId = (paramName: string, value: string) => {
    updateProfileField([systemId, 'Parameters', paramName, 'semanticId'], value || undefined);
  };

  const addParam = () => {
    const name = nextCountName('NewParam', Object.keys(parameters));
    updateProfileField([systemId, 'Parameters', name], { InterfaceReference: '' } as Parameter);
  };

  const removeParam = (name: string) => {
    const clone = { ...parameters };
    delete clone[name];
    updateProfileField([systemId, 'Parameters'], clone);
  };

  const renameParam = (oldName: string, newName: string) => {
    const clone = { ...parameters };
    clone[newName] = clone[oldName];
    delete clone[oldName];
    updateProfileField([systemId, 'Parameters'], clone);
  };

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Parameters', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Parameters', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        <button className="btn btn--sm btn--secondary" onClick={addParam}>
          + Parameter
        </button>
      </div>

      {Object.keys(parameters).length === 0 && (
        <p className="empty-state">No parameters defined.</p>
      )}

      {Object.entries(parameters).map(([paramName, param]) => (
        <div key={paramName} className="card card--flat">
          <div className="card__header">
            <strong>{paramName}</strong>
            <button className="btn btn--xs btn--danger" onClick={() => removeParam(paramName)}>
              ✕
            </button>
          </div>
          <div className="card__body">
            {advanced && (
              <div className="adv-block">
                <AdvField label="idShort" value={paramName}
                  onRename={(n) => renameParam(paramName, n)} />
              </div>
            )}
            <div className="form-row form-row--inline">
              <label className="form-label">Interface Reference</label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. Setpoint"
                value={param?.InterfaceReference ?? ''}
                onChange={(e) => updateInterfaceReference(paramName, e.target.value)}
              />
              <span className="form-hint">idShort of the AID property/action this parameter writes</span>
            </div>
            <SemanticIdInput
              label="Semantic ID"
              value={param?.semanticId ?? ''}
              onChange={(v) => updateSemanticId(paramName, v)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
