import { useAppStore } from '../../store/useAppStore';
import { SemanticIdInput } from '../shared/SemanticIdInput';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { SKILLS_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { Skill } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

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

  const update = (skillName: string, field: keyof Skill, value: string) => {
    updateProfileField([systemId, 'Skills', skillName, field], value || undefined);
  };

  const addSkill = () => {
    const name = nextCountName('NewSkill', Object.keys(skills));
    updateProfileField([systemId, 'Skills', name], {
      semantic_id: 'https://smartproductionlab.aau.dk/skills/',
      // Defaults to the skill's own name, matching skills_builder.py's own
      // fallback (skill_data.get('interface', skill_name)) when left as-is.
      interface: name,
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
                <label className="field-label">
                  Interface <span className="field-hint">(AID action idShort this skill invokes)</span>
                </label>
                <input
                  className="field-input"
                  required
                  value={skill?.interface ?? ''}
                  placeholder={skillName}
                  onChange={(e) => update(skillName, 'interface', e.target.value)}
                />
              </div>
              <div className="field-group">
                <label className="field-label">Description</label>
                <input
                  className="field-input"
                  value={skill?.description ?? ''}
                  onChange={(e) => update(skillName, 'description', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
