import { useAppStore } from '../../store/useAppStore';
import { SemanticIdInput } from '../shared/SemanticIdInput';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { OPERATIONAL_DATA_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { Variable } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

export function OperationalDataForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const variables = parsedProfile[systemId]?.Variables ?? {};

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.Variables?.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/OperationalData`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.Variables?.semanticId ?? OPERATIONAL_DATA_SUBMODEL;

  const update = (varName: string, value: string) => {
    updateProfileField([systemId, 'Variables', varName, 'semanticId'], value || undefined);
  };

  const addVariable = () => {
    const name = nextCountName('NewVariable', Object.keys(variables));
    updateProfileField([systemId, 'Variables', name], { semanticId: '' } as Variable);
  };

  const removeVariable = (name: string) => {
    const clone = { ...variables };
    delete clone[name];
    updateProfileField([systemId, 'Variables'], clone);
  };

  const renameVariable = (oldName: string, newName: string) => {
    const clone = { ...variables };
    clone[newName] = clone[oldName];
    delete clone[oldName];
    updateProfileField([systemId, 'Variables'], clone);
  };

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Variables', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Variables', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        <button className="btn btn--sm btn--secondary" onClick={addVariable}>
          + Variable
        </button>
      </div>

      {Object.keys(variables).length === 0 && (
        <p className="empty-state">No operational data variables defined.</p>
      )}

      {Object.entries(variables).map(([varName, variable]) => (
        <div key={varName} className="card card--flat">
          <div className="card__header">
            <strong>{varName}</strong>
            <button className="btn btn--xs btn--danger" onClick={() => removeVariable(varName)}>
              ✕
            </button>
          </div>
          <div className="card__body">
            {advanced && (
              <div className="adv-block">
                <AdvField label="idShort" value={varName}
                  onRename={(n) => renameVariable(varName, n)} />
              </div>
            )}
            <SemanticIdInput
              label="Semantic ID"
              required
              value={variable?.semanticId ?? ''}
              onChange={(v) => update(varName, v)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
