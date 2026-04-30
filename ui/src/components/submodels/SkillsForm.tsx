import { useAppStore } from '../../store/useAppStore';
import { SemanticIdInput } from '../shared/SemanticIdInput';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { SKILLS_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { Skill, SkillVariable } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

const VALUE_TYPES = [
  'xs:string', 'xs:integer', 'xs:double', 'xs:float', 'xs:boolean',
  'xs:anyURI', 'xs:long', 'xs:short', 'xs:byte',
];

const VAR_KEYS = ['inputVariables', 'outputVariables', 'inoutputVariables'] as const;
type VarKey = typeof VAR_KEYS[number];
const VAR_LABELS: Record<VarKey, string> = {
  inputVariables:    'Input Variables',
  outputVariables:   'Output Variables',
  inoutputVariables: 'In/Out Variables',
};

export function SkillsForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const skills = parsedProfile[systemId]?.Skills ?? {};

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.Skills?.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/Skills`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.Skills?.semanticId ?? SKILLS_SUBMODEL;

  const update = (skillName: string, field: keyof Skill, value: any) => {
    updateProfileField([systemId, 'Skills', skillName, field], value || undefined);
  };

  const addSkill = () => {
    const name = nextCountName('NewSkill', Object.keys(skills));
    updateProfileField([systemId, 'Skills', name], {
      semantic_id: 'https://smartproductionlab.aau.dk/skills/',
      description: '',
    } as Partial<Skill>);
  };

  const removeSkill = (name: string) => {
    const clone = { ...skills };
    delete clone[name];
    updateProfileField([systemId, 'Skills'], clone);
  };

  const renameSkill = (oldName: string, newName: string) => {
    const clone = { ...skills };
    clone[newName] = clone[oldName];
    delete clone[oldName];
    updateProfileField([systemId, 'Skills'], clone);
  };

  // ── Variable list helpers ────────────────────────────────────────────────────

  const addVar = (skillName: string, varKey: VarKey) => {
    const existing = ((skills[skillName]?.[varKey] ?? []) as SkillVariable[]);
    updateProfileField([systemId, 'Skills', skillName, varKey], [
      ...existing,
      { idShort: `var${existing.length + 1}`, valueType: 'xs:string' },
    ]);
  };

  const removeVar = (skillName: string, varKey: VarKey, idx: number) => {
    const existing = [...((skills[skillName]?.[varKey] ?? []) as SkillVariable[])];
    existing.splice(idx, 1);
    updateProfileField([systemId, 'Skills', skillName, varKey], existing.length > 0 ? existing : undefined);
  };

  const updateVar = (skillName: string, varKey: VarKey, idx: number, field: keyof SkillVariable, value: string) => {
    const existing = [...((skills[skillName]?.[varKey] ?? []) as SkillVariable[])];
    existing[idx] = { ...existing[idx], [field]: value || undefined };
    updateProfileField([systemId, 'Skills', skillName, varKey], existing);
  };

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Skills', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Skills', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        <button className="btn btn--sm btn--secondary" onClick={addSkill}>
          + Skill
        </button>
      </div>

      {Object.keys(skills).length === 0 && (
        <p className="empty-state">No skills defined.</p>
      )}

      {Object.entries(skills).map(([skillName, skill]) => (
        <div key={skillName} className="card">
          <div className="card__header">
            <strong>{skillName}</strong>
            <button className="btn btn--xs btn--danger" onClick={() => removeSkill(skillName)}>
              ✕
            </button>
          </div>
          <div className="card__body">
            {advanced && (
              <div className="adv-block">
                <AdvField label="idShort" value={skillName}
                  onRename={(n) => renameSkill(skillName, n)} />
              </div>
            )}
            <div className="field-grid">
              <SemanticIdInput
                label="Semantic ID"
                required
                value={skill?.semantic_id ?? ''}
                onChange={(v) => update(skillName, 'semantic_id', v)}
              />
              <div className="field-group">
                <label className="field-label">Description</label>
                <input
                  className="field-input"
                  value={skill?.description ?? ''}
                  onChange={(e) => update(skillName, 'description', e.target.value)}
                />
              </div>
              <div className="field-group">
                <label className="field-label">
                  Invocation Delegation <span className="field-hint">(endpoint URL)</span>
                </label>
                <input
                  className="field-input"
                  value={skill?.invocationDelegation ?? ''}
                  placeholder="http://..."
                  onChange={(e) => update(skillName, 'invocationDelegation', e.target.value)}
                />
              </div>
              <div className="field-group">
                <label className="field-label">Call Type</label>
                <select
                  className="field-input"
                  value={skill?.callType ?? ''}
                  onChange={(e) => update(skillName, 'callType', e.target.value as any)}
                >
                  <option value="">— none —</option>
                  <option value="Synchronous">Synchronous</option>
                  <option value="OneWay">OneWay</option>
                </select>
              </div>
            </div>

            {/* Variable lists */}
            {VAR_KEYS.map((varKey) => {
              const vars = (skill?.[varKey] ?? []) as SkillVariable[];
              return (
                <div key={varKey} className="skill-vars">
                  <div className="skill-vars__header">
                    <span className="field-label">{VAR_LABELS[varKey]}</span>
                    <button className="btn btn--xs btn--secondary" onClick={() => addVar(skillName, varKey)}>
                      +
                    </button>
                  </div>
                  {vars.length > 0 && (
                    <table className="param-table">
                      <thead>
                        <tr>
                          <th>idShort</th>
                          <th>Type</th>
                          <th>Description</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {vars.map((v, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                className="field-input field-input--sm"
                                value={v.idShort}
                                onChange={(e) => updateVar(skillName, varKey, idx, 'idShort', e.target.value)}
                              />
                            </td>
                            <td>
                              <select
                                className="field-input field-input--sm"
                                value={v.valueType}
                                onChange={(e) => updateVar(skillName, varKey, idx, 'valueType', e.target.value)}
                              >
                                {VALUE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                              </select>
                            </td>
                            <td>
                              <input
                                className="field-input field-input--sm"
                                value={v.description ?? ''}
                                placeholder="optional"
                                onChange={(e) => updateVar(skillName, varKey, idx, 'description', e.target.value)}
                              />
                            </td>
                            <td>
                              <button className="btn btn--xs btn--danger" onClick={() => removeVar(skillName, varKey, idx)}>
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
