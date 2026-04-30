import { useAppStore } from '../../store/useAppStore';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { AIMC_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { AIMCMappingConfig, AIMCRelation } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

const SOURCE_SUBMODELS = ['Variables', 'Skills', 'Parameters'] as const;
const AFFORDANCE_TYPES = ['properties', 'actions', 'events'] as const;

export function AIMCForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const aimc = (parsedProfile[systemId]?.AIMC ?? {}) as Record<string, AIMCMappingConfig>;
  const aid  = parsedProfile[systemId]?.AID ?? {};

  const baseUrl = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.AIMC?.id ??
    `${baseUrl}/submodels/instances/${identitySystemId}/AssetInterfacesMappingConfiguration`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.AIMC?.semanticId ?? AIMC_SUBMODEL;

  // ── Mapping config CRUD ──────────────────────────────────────────────────────

  const addMapping = () => {
    const name = nextCountName('Mapping', Object.keys(aimc));
    const firstInterface = Object.keys(aid)[0] ?? '';
    updateProfileField([systemId, 'AIMC', name], {
      interfaceName: firstInterface,
      relations: [],
    } as AIMCMappingConfig);
  };

  const removeMapping = (name: string) => {
    const clone = { ...aimc };
    delete clone[name];
    updateProfileField([systemId, 'AIMC'], clone);
  };

  const renameMapping = (oldName: string, newName: string) => {
    const clone = { ...aimc };
    clone[newName] = clone[oldName];
    delete clone[oldName];
    updateProfileField([systemId, 'AIMC'], clone);
  };

  // ── Relation CRUD ────────────────────────────────────────────────────────────

  const addRelation = (mappingName: string) => {
    const existing = aimc[mappingName]?.relations ?? [];
    const interfaceName = aimc[mappingName]?.interfaceName ?? '';
    const firstType = AFFORDANCE_TYPES[0];
    const firstAffordance = Object.keys(aid[interfaceName]?.InteractionMetadata?.[firstType] ?? {})[0] ?? '';
    updateProfileField([systemId, 'AIMC', mappingName, 'relations'], [
      ...existing,
      {
        sourceSubmodel: 'Variables' as const,
        sourceElement: '',
        aidAffordanceType: firstType,
        aidAffordance: firstAffordance,
      } as AIMCRelation,
    ]);
  };

  const removeRelation = (mappingName: string, idx: number) => {
    const existing = [...(aimc[mappingName]?.relations ?? [])];
    existing.splice(idx, 1);
    updateProfileField([systemId, 'AIMC', mappingName, 'relations'], existing.length > 0 ? existing : []);
  };

  const updateRelation = (mappingName: string, idx: number, field: keyof AIMCRelation, value: string) => {
    const existing = [...(aimc[mappingName]?.relations ?? [])];
    existing[idx] = { ...existing[idx], [field]: value };
    updateProfileField([systemId, 'AIMC', mappingName, 'relations'], existing);
  };

  // ── Helpers: available source elements & AID affordances ────────────────────

  const sourceElements = (submodel: string): string[] => {
    switch (submodel) {
      case 'Variables':  return Object.keys(parsedProfile[systemId]?.Variables  ?? {});
      case 'Skills':     return Object.keys(parsedProfile[systemId]?.Skills     ?? {});
      case 'Parameters': return Object.keys(parsedProfile[systemId]?.Parameters ?? {});
      default:           return [];
    }
  };

  const affordancesForType = (interfaceName: string, type: string): string[] =>
    Object.keys((aid[interfaceName]?.InteractionMetadata as any)?.[type] ?? {});

  const ifaceOptions = Object.keys(aid);

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AIMC', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AIMC', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        <button className="btn btn--sm btn--secondary" onClick={addMapping}>
          + Mapping
        </button>
      </div>

      {Object.keys(aimc).length === 0 && (
        <p className="empty-state">
          No mappings defined. Add one to link AID affordances to Variables, Skills, or Parameters.
        </p>
      )}

      {Object.entries(aimc).map(([mappingName, config]) => {
        const ifaceName = config.interfaceName;
        return (
          <div key={mappingName} className="card">
            <div className="card__header">
              <strong>{mappingName}</strong>
              <button className="btn btn--xs btn--danger" onClick={() => removeMapping(mappingName)}>✕</button>
            </div>
            <div className="card__body">
              {advanced && (
                <div className="adv-block">
                  <AdvField label="idShort" value={mappingName}
                    onRename={(n) => renameMapping(mappingName, n)} />
                </div>
              )}

              {/* Interface selector */}
              <div className="field-group" style={{ marginBottom: '0.75rem' }}>
                <label className="field-label">AID Interface</label>
                {ifaceOptions.length > 0 ? (
                  <select
                    className="field-input"
                    value={ifaceName}
                    onChange={(e) => updateProfileField([systemId, 'AIMC', mappingName, 'interfaceName'], e.target.value)}
                  >
                    {ifaceOptions.map((k) => <option key={k} value={k}>{k}</option>)}
                  </select>
                ) : (
                  <input
                    className="field-input"
                    value={ifaceName}
                    placeholder="Interface name (add an AID interface first)"
                    onChange={(e) => updateProfileField([systemId, 'AIMC', mappingName, 'interfaceName'], e.target.value)}
                  />
                )}
              </div>

              {/* Relations table */}
              <div className="skill-vars">
                <div className="skill-vars__header">
                  <span className="field-label">Source → Sink Relations</span>
                  <button className="btn btn--xs btn--secondary" onClick={() => addRelation(mappingName)}>+</button>
                </div>
                {(config.relations ?? []).length > 0 && (
                  <table className="param-table">
                    <thead>
                      <tr>
                        <th>Source submodel</th>
                        <th>Source element</th>
                        <th>Affordance type</th>
                        <th>Affordance</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {(config.relations ?? []).map((rel, idx) => {
                        const srcOptions = sourceElements(rel.sourceSubmodel);
                        const affOptions = affordancesForType(ifaceName, rel.aidAffordanceType);
                        return (
                          <tr key={idx}>
                            <td>
                              <select
                                className="field-input field-input--sm"
                                value={rel.sourceSubmodel}
                                onChange={(e) => updateRelation(mappingName, idx, 'sourceSubmodel', e.target.value)}
                              >
                                {SOURCE_SUBMODELS.map((s) => <option key={s} value={s}>{s}</option>)}
                              </select>
                            </td>
                            <td>
                              {srcOptions.length > 0 ? (
                                <select
                                  className="field-input field-input--sm"
                                  value={rel.sourceElement}
                                  onChange={(e) => updateRelation(mappingName, idx, 'sourceElement', e.target.value)}
                                >
                                  <option value="">— select —</option>
                                  {srcOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                                </select>
                              ) : (
                                <input
                                  className="field-input field-input--sm"
                                  value={rel.sourceElement}
                                  placeholder="element name"
                                  onChange={(e) => updateRelation(mappingName, idx, 'sourceElement', e.target.value)}
                                />
                              )}
                            </td>
                            <td>
                              <select
                                className="field-input field-input--sm"
                                value={rel.aidAffordanceType}
                                onChange={(e) => updateRelation(mappingName, idx, 'aidAffordanceType', e.target.value)}
                              >
                                {AFFORDANCE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                              </select>
                            </td>
                            <td>
                              {affOptions.length > 0 ? (
                                <select
                                  className="field-input field-input--sm"
                                  value={rel.aidAffordance}
                                  onChange={(e) => updateRelation(mappingName, idx, 'aidAffordance', e.target.value)}
                                >
                                  <option value="">— select —</option>
                                  {affOptions.map((a) => <option key={a} value={a}>{a}</option>)}
                                </select>
                              ) : (
                                <input
                                  className="field-input field-input--sm"
                                  value={rel.aidAffordance}
                                  placeholder="affordance name"
                                  onChange={(e) => updateRelation(mappingName, idx, 'aidAffordance', e.target.value)}
                                />
                              )}
                            </td>
                            <td>
                              <button className="btn btn--xs btn--danger" onClick={() => removeRelation(mappingName, idx)}>✕</button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
