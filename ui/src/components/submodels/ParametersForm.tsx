import { useAppStore } from '../../store/useAppStore';
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

  const update = (paramName: string, field: keyof Parameter, value: string) => {
    updateProfileField([systemId, 'Parameters', paramName, field], value);
  };

  const addParam = () => {
    const name = nextCountName('NewParam', Object.keys(parameters));
    updateProfileField([systemId, 'Parameters', name], {
      ParameterValue: '',
      Unit: '',
    } as Parameter);
  };

  const removeParam = (name: string) => {
    const clone = { ...parameters };
    delete clone[name];
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

      <table className="param-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Value</th>
            <th>Unit</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {Object.entries(parameters).map(([paramName, param]) => (
            <tr key={paramName}>
              <td>
                <code className="param-name">{paramName}</code>
              </td>
              <td>
                <input
                  className="field-input field-input--sm"
                  value={param?.ParameterValue ?? ''}
                  onChange={(e) => update(paramName, 'ParameterValue', e.target.value)}
                />
              </td>
              <td>
                <input
                  className="field-input field-input--sm"
                  value={param?.Unit ?? ''}
                  placeholder="unit"
                  onChange={(e) => update(paramName, 'Unit', e.target.value)}
                />
              </td>
              <td>
                <button
                  className="btn btn--xs btn--danger"
                  onClick={() => removeParam(paramName)}
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
