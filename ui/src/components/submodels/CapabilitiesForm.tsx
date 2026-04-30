import { useAppStore } from '../../store/useAppStore';
import { SemanticIdInput } from '../shared/SemanticIdInput';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { CAPABILITIES_SUBMODEL, CAPABILITY_CONTAINER, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { Capability } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

export function CapabilitiesForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const capabilities = parsedProfile[systemId]?.Capabilities ?? {};

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.Capabilities?.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/Capabilities`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.Capabilities?.semanticId ?? CAPABILITIES_SUBMODEL;
  const skills = parsedProfile[systemId]?.Skills ?? {};

  const update = (capName: string, field: keyof Capability, value: string) => {
    updateProfileField([systemId, 'Capabilities', capName, field], value || undefined);
  };

  const addCapability = () => {
    const name = nextCountName('NewCapability', Object.keys(capabilities));
    updateProfileField([systemId, 'Capabilities', name], {
      semantic_id: 'https://smartproductionlab.aau.dk/capabilities/',
      realizedBy: '',
    } as Capability);
  };

  const removeCap = (name: string) => {
    const clone = { ...capabilities };
    delete clone[name];
    updateProfileField([systemId, 'Capabilities'], clone);
  };

  const renameCap = (oldName: string, newName: string) => {
    const clone = { ...capabilities };
    clone[newName] = clone[oldName];
    delete clone[oldName];
    updateProfileField([systemId, 'Capabilities'], clone);
  };

  const skillOptions = Object.keys(skills);

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Capabilities', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'Capabilities', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        <button className="btn btn--sm btn--secondary" onClick={addCapability}>
          + Capability
        </button>
      </div>

      {Object.keys(capabilities).length === 0 && (
        <p className="empty-state">
          No capabilities defined. Add one or let Guidance auto-create from Skills.
        </p>
      )}

      {Object.entries(capabilities).map(([capName, cap]) => (
        <div key={capName} className="card">
          <div className="card__header">
            <strong>{capName}</strong>
            <button className="btn btn--xs btn--danger" onClick={() => removeCap(capName)}>
              ✕
            </button>
          </div>
          <div className="card__body">
            {advanced && (
              <div className="adv-block">
                <AdvField label="idShort"   value={capName}
                  onRename={(n) => renameCap(capName, n)} />
                <AdvField label="semanticId" value={cap?._containerSemanticId ?? CAPABILITY_CONTAINER}
                  onChange={(v) => update(capName, '_containerSemanticId' as keyof Capability, v)} />
              </div>
            )}
            <div className="field-grid">
              <SemanticIdInput
                label="Semantic ID"
                required
                value={cap?.semantic_id ?? ''}
                onChange={(v) => update(capName, 'semantic_id', v)}
              />
              <div className="field-group">
                <label className="field-label">
                  Realized By <span className="field-hint">(Skill name)</span>
                </label>
                {skillOptions.length > 0 ? (
                  <select
                    className="field-input"
                    value={cap?.realizedBy ?? ''}
                    onChange={(e) => update(capName, 'realizedBy', e.target.value)}
                  >
                    <option value="">— select skill —</option>
                    {skillOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="field-input"
                    value={cap?.realizedBy ?? ''}
                    placeholder="SkillName"
                    onChange={(e) => update(capName, 'realizedBy', e.target.value)}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
