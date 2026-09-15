import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import { AIMC_SUBMODEL, SEMANTIC_ID_BASE } from '../../aas/semanticIds';
import type { AIMCInterfaceMapping, AIMCMapping } from '../../types/resourceaas';

function deriveBaseUrl(id: string) {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

type SinkSubmodel = NonNullable<AIMCMapping['sinkSubmodel']>;

export function AIMCForm() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId = useAppStore((s) => s.identityId);
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const { advanced } = useAdvanced();
  const [newIface, setNewIface] = useState('');

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId = Object.keys(parsedProfile)[0];
  const cfg = parsedProfile[systemId];
  const aimc: Record<string, AIMCInterfaceMapping> = cfg?.AIMC ?? {};
  const aid = (cfg?.AID ?? {}) as Record<string, any>;
  const sinkNames: Record<SinkSubmodel, string[]> = {
    OperationalData: Object.keys(cfg?.Variables ?? {}),
    Parameters: Object.keys(cfg?.Parameters ?? {}),
  };

  const baseUrl = deriveBaseUrl(identityId);
  const meta = (cfg as any)?._meta?.AIMC ?? {};
  const metaId = meta.id ?? `${baseUrl}/submodels/instances/${identitySystemId}/AssetInterfacesMappingConfiguration`;
  const metaSemanticId = meta.semanticId ?? AIMC_SUBMODEL;

  // Properties only: SHACL rejects sources pointing at actions or events.
  const propertiesOf = (iface: string): string[] =>
    Object.keys(aid[iface]?.InteractionMetadata?.properties ?? {});

  const setAimc = (next: Record<string, AIMCInterfaceMapping>) =>
    updateProfileField([systemId, 'AIMC'], next);

  const setMappings = (iface: string, mappings: AIMCMapping[]) =>
    setAimc({ ...aimc, [iface]: { ...aimc[iface], Mappings: mappings } });

  const unmapped = Object.keys(aid).filter((name) => !(name in aimc));

  const addInterface = () => {
    const name = (newIface || unmapped[0] || '').trim();
    if (!name || name in aimc) return;
    setAimc({ ...aimc, [name]: { Mappings: [] } });
    setNewIface('');
  };

  const removeInterface = (iface: string) => {
    const clone = { ...aimc };
    delete clone[iface];
    setAimc(clone);
  };

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id" value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AIMC', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AIMC', 'semanticId'], v || undefined)} />
        </div>
      )}

      <div className="submodel-form__controls">
        {unmapped.length > 0 ? (
          <select className="field-input" value={newIface} onChange={(e) => setNewIface(e.target.value)}>
            <option value="">— AID interface —</option>
            {unmapped.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        ) : (
          <input className="field-input" value={newIface} placeholder="AID interface name"
            onChange={(e) => setNewIface(e.target.value)} />
        )}
        <button className="btn btn--sm btn--secondary" onClick={addInterface}>+ Interface</button>
      </div>

      {Object.keys(aid).length === 0 && (
        <p className="empty-state">AIMC maps AID properties. Add an AID interface first.</p>
      )}

      {Object.entries(aimc).map(([iface, entry]) => {
        const mappings = entry?.Mappings ?? [];
        const props = propertiesOf(iface);
        return (
          <div key={iface} className="card">
            <div className="card__header">
              <strong>{iface}</strong>
              <button className="btn btn--xs btn--danger" onClick={() => removeInterface(iface)}>✕</button>
            </div>
            <div className="card__body">
              <div className="field-group">
                <label className="field-label">
                  Default polling interval <span className="field-hint">(ms)</span>
                </label>
                <input
                  className="field-input"
                  type="number"
                  value={entry?.DefaultPollingInterval ?? ''}
                  onChange={(e) => setAimc({
                    ...aimc,
                    [iface]: { ...entry, DefaultPollingInterval: e.target.value || undefined },
                  })}
                />
              </div>

              {mappings.map((m, i) => {
                const target: SinkSubmodel = m.sinkSubmodel ?? 'OperationalData';
                const update = (patch: Partial<AIMCMapping>) =>
                  setMappings(iface, mappings.map((x, j) => (j === i ? { ...x, ...patch } : x)));
                return (
                  <div key={i} className="field-grid">
                    <div className="field-group">
                      <label className="field-label">Source <span className="field-hint">(AID property)</span></label>
                      {props.length > 0 ? (
                        <select className="field-input" value={m.source} onChange={(e) => update({ source: e.target.value })}>
                          <option value="">— property —</option>
                          {props.map((p) => <option key={p} value={p}>{p}</option>)}
                        </select>
                      ) : (
                        <input className="field-input" value={m.source} onChange={(e) => update({ source: e.target.value })} />
                      )}
                    </div>
                    <div className="field-group">
                      <label className="field-label">Sink submodel</label>
                      <select className="field-input" value={target}
                        onChange={(e) => update({ sinkSubmodel: e.target.value as SinkSubmodel })}>
                        <option value="OperationalData">OperationalData</option>
                        <option value="Parameters">Parameters</option>
                      </select>
                    </div>
                    <div className="field-group">
                      <label className="field-label">Sink</label>
                      {sinkNames[target].length > 0 ? (
                        <select className="field-input" value={m.sink} onChange={(e) => update({ sink: e.target.value })}>
                          <option value="">— entry —</option>
                          {sinkNames[target].map((n) => <option key={n} value={n}>{n}</option>)}
                        </select>
                      ) : (
                        <input className="field-input" value={m.sink} onChange={(e) => update({ sink: e.target.value })} />
                      )}
                    </div>
                    <div className="field-group">
                      <label className="field-label">Polling <span className="field-hint">(ms)</span></label>
                      <input className="field-input" type="number" value={m.pollingInterval ?? ''}
                        onChange={(e) => update({ pollingInterval: e.target.value || undefined })} />
                    </div>
                    <button className="btn btn--xs btn--danger"
                      onClick={() => setMappings(iface, mappings.filter((_, j) => j !== i))}>
                      ✕
                    </button>
                  </div>
                );
              })}

              <button className="btn btn--xs btn--secondary"
                onClick={() => setMappings(iface, [...mappings, { source: props[0] ?? '', sink: '' }])}>
                + Mapping
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
