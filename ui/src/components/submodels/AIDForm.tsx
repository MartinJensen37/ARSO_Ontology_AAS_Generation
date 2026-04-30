import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { AIDInterface, AIDForms, AIDFormResponse, AIDProtocol } from '../../types/resourceaas';
import { useAdvanced } from '../shared/AdvancedContext';
import { AdvField } from '../shared/AdvField';
import {
  AID_SUBMODEL, AID_INTERFACE, AID_INTERACTION_METADATA,
  WOT_PROPERTY_AFFORDANCE, WOT_ACTION_AFFORDANCE, WOT_EVENT_AFFORDANCE,
  SEMANTIC_ID_BASE,
} from '../../aas/semanticIds';

const PROTOCOL_SUPPLEMENTAL: Record<string, string[]> = {
  MQTT:   ['http://www.w3.org/2011/mqtt',   'https://www.w3.org/2019/wot/td'],
  HTTP:   ['http://www.w3.org/2011/http',   'https://www.w3.org/2019/wot/td'],
  MODBUS: ['http://www.w3.org/2011/modbus', 'https://www.w3.org/2019/wot/td'],
};

function deriveBaseUrl(id: string): string {
  try { return new URL(id).origin; } catch { return SEMANTIC_ID_BASE; }
}

function nextCountName(prefix: string, existing: string[]): string {
  let i = 1;
  while (existing.includes(`${prefix}_${String(i).padStart(2, '0')}`)) i++;
  return `${prefix}_${String(i).padStart(2, '0')}`;
}

// ── Protocol-aware forms sub-editor ───────────────────────────────────────────

interface FormsEditorProps {
  forms: AIDForms | undefined;
  protocol: AIDProtocol;
  onChange: (field: string, value: string | undefined) => void;
  showOp?: boolean;
  showResponse?: boolean;
}

function FormsEditor({ forms, protocol, onChange, showOp, showResponse }: FormsEditorProps) {
  const [respOpen, setRespOpen] = useState(false);
  const resp = forms?.response;

  return (
    <div className="aid-forms-block">
      <div className="field-grid field-grid--3col">
        <div className="field-group">
          <label className="field-label">href</label>
          <input className="field-input field-input--sm"
            placeholder={protocol === 'MQTT' ? '/topic/path' : protocol === 'HTTP' ? '/path' : '1'}
            value={forms?.href ?? ''}
            onChange={(e) => onChange('href', e.target.value || undefined)} />
        </div>
        <div className="field-group">
          <label className="field-label">contentType</label>
          <input className="field-input field-input--sm" placeholder="application/json"
            value={forms?.contentType ?? ''}
            onChange={(e) => onChange('contentType', e.target.value || undefined)} />
        </div>
        {showOp && (
          <div className="field-group">
            <label className="field-label">op</label>
            <input className="field-input field-input--sm" placeholder="invokeAction"
              value={forms?.op ?? ''}
              onChange={(e) => onChange('op', e.target.value || undefined)} />
          </div>
        )}

        {/* ── MQTT bindings ── */}
        {protocol === 'MQTT' && (<>
          <div className="field-group">
            <label className="field-label">mqv_controlPacket</label>
            <select className="field-input field-input--sm"
              value={forms?.mqv_controlPacket ?? ''}
              onChange={(e) => onChange('mqv_controlPacket', e.target.value || undefined)}>
              <option value="">—</option>
              <option>subscribe</option>
              <option>publish</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">mqv_retain</label>
            <select className="field-input field-input--sm"
              value={forms?.mqv_retain ?? ''}
              onChange={(e) => onChange('mqv_retain', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">mqv_qos</label>
            <select className="field-input field-input--sm"
              value={forms?.mqv_qos ?? ''}
              onChange={(e) => onChange('mqv_qos', e.target.value || undefined)}>
              <option value="">—</option>
              <option>0</option><option>1</option><option>2</option>
            </select>
          </div>
        </>)}

        {/* ── HTTP bindings ── */}
        {protocol === 'HTTP' && (
          <div className="field-group">
            <label className="field-label">htv_methodName</label>
            <select className="field-input field-input--sm"
              value={forms?.htv_methodName ?? ''}
              onChange={(e) => onChange('htv_methodName', e.target.value || undefined)}>
              <option value="">—</option>
              <option>GET</option><option>POST</option><option>PUT</option>
              <option>DELETE</option><option>PATCH</option>
            </select>
          </div>
        )}

        {/* ── MODBUS bindings ── */}
        {protocol === 'MODBUS' && (<>
          <div className="field-group">
            <label className="field-label">modv_function</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_function ?? ''}
              onChange={(e) => onChange('modv_function', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="readCoils">readCoils (FC01)</option>
              <option value="readDiscreteInputs">readDiscreteInputs (FC02)</option>
              <option value="readHoldingRegisters">readHoldingRegisters (FC03)</option>
              <option value="readInputRegisters">readInputRegisters (FC04)</option>
              <option value="writeSingleCoil">writeSingleCoil (FC05)</option>
              <option value="writeSingleRegister">writeSingleRegister (FC06)</option>
              <option value="writeMultipleCoils">writeMultipleCoils (FC15)</option>
              <option value="writeMultipleRegisters">writeMultipleRegisters (FC16)</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">modv_entity</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_entity ?? ''}
              onChange={(e) => onChange('modv_entity', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="Coil">Coil</option>
              <option value="DiscreteInput">DiscreteInput</option>
              <option value="InputRegister">InputRegister</option>
              <option value="HoldingRegister">HoldingRegister</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">modv_type</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_type ?? ''}
              onChange={(e) => onChange('modv_type', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="xsd:integer">xsd:integer</option>
              <option value="xsd:boolean">xsd:boolean</option>
              <option value="xsd:float">xsd:float</option>
              <option value="xsd:double">xsd:double</option>
              <option value="xsd:string">xsd:string</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">modv_zeroBasedAddressing</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_zeroBasedAddressing ?? ''}
              onChange={(e) => onChange('modv_zeroBasedAddressing', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">modv_pollingTime (ms)</label>
            <input className="field-input field-input--sm" placeholder="1000"
              value={forms?.modv_pollingTime ?? ''}
              onChange={(e) => onChange('modv_pollingTime', e.target.value || undefined)} />
          </div>
          <div className="field-group">
            <label className="field-label">modv_timeout (ms)</label>
            <input className="field-input field-input--sm" placeholder="1000"
              value={forms?.modv_timeout ?? ''}
              onChange={(e) => onChange('modv_timeout', e.target.value || undefined)} />
          </div>
          <div className="field-group">
            <label className="field-label">modv_mostSignificantByte</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_mostSignificantByte ?? ''}
              onChange={(e) => onChange('modv_mostSignificantByte', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">modv_mostSignificantWord</label>
            <select className="field-input field-input--sm"
              value={forms?.modv_mostSignificantWord ?? ''}
              onChange={(e) => onChange('modv_mostSignificantWord', e.target.value || undefined)}>
              <option value="">—</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
        </>)}
      </div>

      {/* MQTT response channel */}
      {showResponse && protocol === 'MQTT' && (
        <div className="aid-response-section">
          <button className="aid-toggle-link" type="button" onClick={() => setRespOpen((o) => !o)}>
            {respOpen ? '▾' : '▸'} Response channel
          </button>
          {respOpen && (
            <div className="field-grid field-grid--2col" style={{ marginTop: 6 }}>
              {(['href', 'contentType', 'mqv_controlPacket', 'mqv_retain'] as (keyof AIDFormResponse)[]).map((f) => (
                <div className="field-group" key={f}>
                  <label className="field-label">{f}</label>
                  {f === 'mqv_controlPacket' ? (
                    <select className="field-input field-input--sm"
                      value={resp?.[f] ?? ''}
                      onChange={(e) => onChange(`response.${f}`, e.target.value || undefined)}>
                      <option value="">—</option>
                      <option>subscribe</option><option>publish</option>
                    </select>
                  ) : f === 'mqv_retain' ? (
                    <select className="field-input field-input--sm"
                      value={resp?.[f] ?? ''}
                      onChange={(e) => onChange(`response.${f}`, e.target.value || undefined)}>
                      <option value="">—</option>
                      <option value="true">true</option>
                      <option value="false">false</option>
                    </select>
                  ) : (
                    <input className="field-input field-input--sm"
                      placeholder={f === 'href' ? '/DATA/response' : ''}
                      value={resp?.[f] ?? ''}
                      onChange={(e) => onChange(`response.${f}`, e.target.value || undefined)} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Protocol badge ─────────────────────────────────────────────────────────────

const PROTOCOL_BADGE_CLASS: Record<AIDProtocol, string> = {
  MQTT:   'aid-badge aid-badge--mqtt',
  HTTP:   'aid-badge aid-badge--http',
  MODBUS: 'aid-badge aid-badge--modbus',
};

// ── Default forms per protocol ─────────────────────────────────────────────────

const DEFAULT_PROP_FORMS: Record<AIDProtocol, AIDForms> = {
  MQTT:   { href: '', contentType: 'application/json', mqv_controlPacket: 'publish', mqv_retain: 'false', mqv_qos: '0' },
  HTTP:   { href: '', contentType: 'application/json', htv_methodName: 'GET' },
  MODBUS: { href: '0', contentType: 'application/json', modv_function: 'readHoldingRegisters', modv_entity: 'HoldingRegister' },
};

const DEFAULT_ACTION_FORMS: Record<AIDProtocol, AIDForms> = {
  MQTT: {
    href: '', contentType: 'application/json', op: 'invokeAction',
    mqv_controlPacket: 'subscribe', mqv_retain: 'false', mqv_qos: '2',
    response: { href: '', contentType: 'application/json', mqv_controlPacket: 'publish', mqv_retain: 'false' },
  },
  HTTP:   { href: '', contentType: 'application/json', op: 'invokeAction', htv_methodName: 'POST' },
  MODBUS: { href: '0', contentType: 'application/json', op: 'invokeAction', modv_function: 'writeSingleRegister', modv_entity: 'HoldingRegister' },
};

const DEFAULT_EVENT_FORMS: Record<AIDProtocol, AIDForms> = {
  MQTT:   { href: '', contentType: 'application/json', mqv_controlPacket: 'publish', mqv_retain: 'false', mqv_qos: '0' },
  HTTP:   { href: '', contentType: 'application/json', htv_methodName: 'GET' },
  MODBUS: { href: '0', contentType: 'application/json', modv_function: 'readInputRegisters', modv_entity: 'InputRegister' },
};

// ── Main form ──────────────────────────────────────────────────────────────────

export function AIDForm() {
  const parsedProfile      = useAppStore((s) => s.parsedProfile);
  const updateProfileField = useAppStore((s) => s.updateProfileField);
  const identityId         = useAppStore((s) => s.identityId);
  const { advanced }       = useAdvanced();

  const [expandedIfaces,  setExpandedIfaces]  = useState<Record<string, boolean>>({});
  const [expandedIM,      setExpandedIM]      = useState<Record<string, boolean>>({});
  const [expandedProps,   setExpandedProps]   = useState<Record<string, boolean>>({});
  const [expandedActions, setExpandedActions] = useState<Record<string, boolean>>({});
  const [expandedEvents,  setExpandedEvents]  = useState<Record<string, boolean>>({});
  const [showPicker,      setShowPicker]      = useState(false);
  // Local pending rename state: old key → draft new name
  const [pendingNames, setPendingNames] = useState<Record<string, string>>({});

  if (!parsedProfile) return <p className="empty-state">No profile loaded.</p>;

  const systemId  = Object.keys(parsedProfile)[0];
  const aid: Record<string, AIDInterface> = parsedProfile[systemId]?.AID ?? {};
  const baseUrl   = deriveBaseUrl(identityId);
  const metaId = (parsedProfile[systemId] as any)?._meta?.AID?.id ?? `${baseUrl}/submodels/instances/${systemId}/AID`;
  const metaSemanticId = (parsedProfile[systemId] as any)?._meta?.AID?.semanticId ?? AID_SUBMODEL;

  const upd = (path: string[], value: unknown) =>
    updateProfileField([systemId, 'AID', ...path] as string[], value);

  const toggleIface  = (k: string) => setExpandedIfaces((p)  => ({ ...p, [k]: !(p[k] ?? true) }));
  const toggleIM     = (k: string) => setExpandedIM((p)      => ({ ...p, [k]: !(p[k] ?? true) }));
  const toggleProp   = (k: string) => setExpandedProps((p)   => ({ ...p, [k]: !p[k] }));
  const toggleAction = (k: string) => setExpandedActions((p) => ({ ...p, [k]: !p[k] }));
  const toggleEvent  = (k: string) => setExpandedEvents((p)  => ({ ...p, [k]: !p[k] }));

  // ── Interface CRUD ──────────────────────────────────────────────────────────

  const addInterface = (protocol: AIDProtocol) => {
    const name = nextCountName(`${protocol}Interface`, Object.keys(aid));
    const baseUri =
      protocol === 'MQTT'   ? 'mqtt://192.168.0.1:1883/base' :
      protocol === 'HTTP'   ? 'http://192.168.0.1:80' :
                              'modbus+tcp://192.168.0.1:502';
    upd([name], {
      Title: `${protocol} Interface`,
      protocol,
      EndpointMetadata: { base: baseUri, contentType: 'application/json' },
      InteractionMetadata: { properties: {}, actions: {}, events: {} },
    } as AIDInterface);
    setExpandedIfaces((p) => ({ ...p, [name]: true }));
    setExpandedIM((p) => ({ ...p, [name]: true }));
    setShowPicker(false);
  };

  const removeInterface = (ifaceName: string) => {
    const next = { ...aid };
    delete next[ifaceName];
    updateProfileField([systemId, 'AID'] as string[], next);
  };

  const renameInterface = (oldName: string) => {
    const newName = (pendingNames[oldName] ?? oldName).trim();
    if (!newName || newName === oldName) return;
    const next: Record<string, AIDInterface> = {};
    for (const [k, v] of Object.entries(aid)) {
      next[k === oldName ? newName : k] = v;
    }
    updateProfileField([systemId, 'AID'] as string[], next);
    setPendingNames((p) => { const c = { ...p }; delete c[oldName]; return c; });
  };

  // ── Property CRUD ───────────────────────────────────────────────────────────

  const addProperty = (ifaceName: string, protocol: AIDProtocol) => {
    const key = nextCountName('NewProperty', Object.keys(aid[ifaceName]?.InteractionMetadata?.properties ?? {}));
    upd([ifaceName, 'InteractionMetadata', 'properties', key], {
      key, title: '', forms: DEFAULT_PROP_FORMS[protocol],
    });
    setExpandedProps((p) => ({ ...p, [`${ifaceName}/${key}`]: true }));
  };

  const removeProperty = (ifaceName: string, propKey: string) => {
    const props = { ...(aid[ifaceName]?.InteractionMetadata?.properties ?? {}) };
    delete props[propKey];
    upd([ifaceName, 'InteractionMetadata', 'properties'], props);
  };

  const updPropForms = (ifaceName: string, propKey: string, field: string, value: string | undefined) => {
    if (field.startsWith('response.')) {
      upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'forms', 'response', field.slice(9)], value);
    } else {
      upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'forms', field], value);
    }
  };

  // ── Action CRUD ─────────────────────────────────────────────────────────────

  const addAction = (ifaceName: string, protocol: AIDProtocol) => {
    const key = nextCountName('NewAction', Object.keys(aid[ifaceName]?.InteractionMetadata?.actions ?? {}));
    upd([ifaceName, 'InteractionMetadata', 'actions', key], {
      key, title: '', synchronous: 'true', forms: DEFAULT_ACTION_FORMS[protocol],
    });
    setExpandedActions((p) => ({ ...p, [`${ifaceName}/${key}`]: true }));
  };

  const removeAction = (ifaceName: string, actionKey: string) => {
    const actions = { ...(aid[ifaceName]?.InteractionMetadata?.actions ?? {}) };
    delete actions[actionKey];
    upd([ifaceName, 'InteractionMetadata', 'actions'], actions);
  };

  const updActionForms = (ifaceName: string, actionKey: string, field: string, value: string | undefined) => {
    if (field.startsWith('response.')) {
      upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'forms', 'response', field.slice(9)], value);
    } else {
      upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'forms', field], value);
    }
  };

  // ── Event CRUD ──────────────────────────────────────────────────────────────

  const addEvent = (ifaceName: string, protocol: AIDProtocol) => {
    const key = nextCountName('NewEvent', Object.keys(aid[ifaceName]?.InteractionMetadata?.events ?? {}));
    upd([ifaceName, 'InteractionMetadata', 'events', key], {
      key, title: '', forms: DEFAULT_EVENT_FORMS[protocol],
    });
    setExpandedEvents((p) => ({ ...p, [`${ifaceName}/${key}`]: true }));
  };

  const removeEvent = (ifaceName: string, eventKey: string) => {
    const events = { ...(aid[ifaceName]?.InteractionMetadata?.events ?? {}) };
    delete events[eventKey];
    upd([ifaceName, 'InteractionMetadata', 'events'], events);
  };

  const updEventForms = (ifaceName: string, eventKey: string, field: string, value: string | undefined) => {
    upd([ifaceName, 'InteractionMetadata', 'events', eventKey, 'forms', field], value);
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="submodel-form">
      {advanced && (
        <div className="adv-block">
          <AdvField label="id"         value={metaId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AID', 'id'], v || undefined)} />
          <AdvField label="semanticId" value={metaSemanticId}
            onChange={(v) => updateProfileField([systemId, '_meta', 'AID', 'semanticId'], v || undefined)} />
        </div>
      )}
      <div className="submodel-form__header">
        <span className="submodel-form__hint">One interface per protocol/endpoint (e.g. InterfaceMQTT).</span>
        <div className="aid-add-iface">
          <button className="btn btn--sm btn--secondary" type="button"
            onClick={() => setShowPicker((v) => !v)}>
            + Interface
          </button>
          {showPicker && (
            <div className="aid-protocol-picker">
              {(['MQTT', 'HTTP', 'MODBUS'] as AIDProtocol[]).map((p) => (
                <button key={p} className={`btn btn--sm ${PROTOCOL_BADGE_CLASS[p]}`}
                  type="button" onClick={() => addInterface(p)}>
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {Object.keys(aid).length === 0 && (
        <p className="empty-state">No interfaces defined. Click "+ Interface" to add one.</p>
      )}

      {Object.entries(aid).map(([ifaceName, iface]) => {
        const protocol = (iface?.protocol ?? 'MQTT') as AIDProtocol;
        const isOpen   = expandedIfaces[ifaceName] ?? true;
        const imOpen   = expandedIM[ifaceName] ?? true;
        const props    = iface?.InteractionMetadata?.properties ?? {};
        const actions  = iface?.InteractionMetadata?.actions    ?? {};
        const events   = iface?.InteractionMetadata?.events     ?? {};

        return (
          <div key={ifaceName} className="card">

            {/* ── Interface header ── */}
            <div className="card__header">
              <button className="card__toggle-btn" type="button" onClick={() => toggleIface(ifaceName)}>
                {isOpen ? '▾' : '▸'}
              </button>
              <span className={PROTOCOL_BADGE_CLASS[protocol]}>{protocol}</span>
              <input
                className="field-input field-input--sm aid-iface-name"
                value={pendingNames[ifaceName] ?? ifaceName}
                title="Interface name (press Enter or click away to apply rename)"
                onChange={(e) => setPendingNames((p) => ({ ...p, [ifaceName]: e.target.value }))}
                onBlur={() => renameInterface(ifaceName)}
                onKeyDown={(e) => { if (e.key === 'Enter') renameInterface(ifaceName); }}
              />
              {iface?.EndpointMetadata?.base && (
                <code className="card__sub">{iface.EndpointMetadata.base}</code>
              )}
              <button className="btn btn--xs btn--danger" type="button"
                onClick={() => removeInterface(ifaceName)} title="Remove interface">✕</button>
            </div>

            {isOpen && (
              <div className="card__body">

                {/* ── Endpoint Metadata ── */}
                <div className="aid-section-label">EndpointMetadata</div>
                <div className="field-grid field-grid--2col">
                  <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                    <label className="field-label">Base URI <span className="required-star">*</span></label>
                    <input className="field-input"
                      placeholder={
                        protocol === 'MQTT'   ? 'mqtt://192.168.0.1:1883/base' :
                        protocol === 'HTTP'   ? 'http://192.168.0.1:80' :
                                               'modbus+tcp://192.168.0.1:502'
                      }
                      value={iface?.EndpointMetadata?.base ?? ''}
                      onChange={(e) => upd([ifaceName, 'EndpointMetadata', 'base'], e.target.value || undefined)} />
                  </div>
                  <div className="field-group">
                    <label className="field-label">Title</label>
                    <input className="field-input" placeholder="Interface title"
                      value={iface?.Title ?? ''}
                      onChange={(e) => upd([ifaceName, 'Title'], e.target.value || undefined)} />
                  </div>
                  <div className="field-group">
                    <label className="field-label">contentType</label>
                    <input className="field-input" placeholder="application/json"
                      value={iface?.EndpointMetadata?.contentType ?? ''}
                      onChange={(e) => upd([ifaceName, 'EndpointMetadata', 'contentType'], e.target.value || undefined)} />
                  </div>
                  {protocol === 'MODBUS' && (<>
                    <div className="field-group">
                      <label className="field-label">modv_mostSignificantByte</label>
                      <select className="field-input"
                        value={iface?.EndpointMetadata?.modv_mostSignificantByte ?? ''}
                        onChange={(e) => upd([ifaceName, 'EndpointMetadata', 'modv_mostSignificantByte'], e.target.value || undefined)}>
                        <option value="">—</option>
                        <option value="true">true</option>
                        <option value="false">false</option>
                      </select>
                    </div>
                    <div className="field-group">
                      <label className="field-label">modv_mostSignificantWord</label>
                      <select className="field-input"
                        value={iface?.EndpointMetadata?.modv_mostSignificantWord ?? ''}
                        onChange={(e) => upd([ifaceName, 'EndpointMetadata', 'modv_mostSignificantWord'], e.target.value || undefined)}>
                        <option value="">—</option>
                        <option value="true">true</option>
                        <option value="false">false</option>
                      </select>
                    </div>
                  </>)}
                </div>
                {advanced && (
                  <div className="adv-block">
                    <AdvField label="semanticId" value={AID_INTERFACE} />
                    {(iface?.supplementalSemanticIds ?? PROTOCOL_SUPPLEMENTAL[protocol] ?? []).map((uri, i) => (
                      <AdvField key={i} label={`supplementalSemanticId[${i}]`} value={uri}
                        onChange={(v) => {
                          const current = iface?.supplementalSemanticIds ?? (PROTOCOL_SUPPLEMENTAL[protocol] ?? []);
                          const next = [...current];
                          next[i] = v;
                          upd([ifaceName, 'supplementalSemanticIds'], next);
                        }} />
                    ))}
                  </div>
                )}

                {/* ── Interaction Metadata ── */}
                <div className="aid-section-label aid-section-label--collapsible">
                  <button className="aid-toggle-btn" type="button" onClick={() => toggleIM(ifaceName)}>
                    {imOpen ? '▾' : '▸'}
                  </button>
                  InteractionMetadata
                  {advanced && (
                    <span className="adv-inline-id">{AID_INTERACTION_METADATA}</span>
                  )}
                </div>

                {imOpen && (<>

                    {/* ── Properties ── */}
                    <div className="subsection">
                      <div className="subsection__header">
                        <span className="subsection__title">Properties</span>
                        <button className="btn btn--xs btn--secondary" type="button"
                          onClick={() => addProperty(ifaceName, protocol)}>
                          + Property
                        </button>
                      </div>
                      {Object.keys(props).length === 0 && (
                        <p className="empty-state empty-state--sm">No properties defined.</p>
                      )}
                      {Object.entries(props).map(([propKey, prop]) => {
                        const eid  = `${ifaceName}/${propKey}`;
                        const open = expandedProps[eid] ?? false;
                        return (
                          <div key={propKey} className="aid-item">
                            <div className="aid-item__header">
                              <button className="aid-toggle-btn" type="button" onClick={() => toggleProp(eid)}>
                                {open ? '▾' : '▸'}
                              </button>
                              <span className="aid-item__key">{prop?.key || propKey}</span>
                              {prop?.forms?.href && <code className="aid-item__href">{prop.forms.href}</code>}
                              <button className="btn btn--xs btn--danger" type="button"
                                onClick={() => removeProperty(ifaceName, propKey)}>✕</button>
                            </div>
                            {open && (
                              <div className="aid-item__body">
                                <div className="field-grid field-grid--2col">
                                  <div className="field-group">
                                    <label className="field-label">key</label>
                                    <input className="field-input field-input--sm" value={prop?.key ?? propKey}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'key'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">title</label>
                                    <input className="field-input field-input--sm" value={prop?.title ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'title'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">observable</label>
                                    <select className="field-input field-input--sm"
                                      value={prop?.observable ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'observable'], e.target.value || undefined)}>
                                      <option value="">—</option>
                                      <option value="true">true</option>
                                      <option value="false">false</option>
                                    </select>
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">unit</label>
                                    <input className="field-input field-input--sm" placeholder="kg, mm, …"
                                      value={prop?.unit ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'unit'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                                    <label className="field-label">output schema URI</label>
                                    <input className="field-input field-input--sm" placeholder="https://example.com/schemas/stationState.schema.json"
                                      value={prop?.output ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'output'], e.target.value || undefined)} />
                                  </div>
                                </div>
                                {advanced && (
                                  <div className="adv-block">
                                    <AdvField label="semanticId" value={prop?.semanticId ?? WOT_PROPERTY_AFFORDANCE}
                                      onChange={(v) => upd([ifaceName, 'InteractionMetadata', 'properties', propKey, 'semanticId'], v || undefined)} />
                                  </div>
                                )}
                                <div className="aid-section-label aid-section-label--sm">forms</div>
                                <FormsEditor
                                  forms={prop?.forms as AIDForms | undefined}
                                  protocol={protocol}
                                  onChange={(f, v) => updPropForms(ifaceName, propKey, f, v)}
                                  showOp={false}
                                  showResponse={false}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* ── Actions ── */}
                    <div className="subsection">
                      <div className="subsection__header">
                        <span className="subsection__title">Actions</span>
                        <button className="btn btn--xs btn--secondary" type="button"
                          onClick={() => addAction(ifaceName, protocol)}>
                          + Action
                        </button>
                      </div>
                      {Object.keys(actions).length === 0 && (
                        <p className="empty-state empty-state--sm">No actions defined.</p>
                      )}
                      {Object.entries(actions).map(([actionKey, action]) => {
                        const eid  = `${ifaceName}/${actionKey}`;
                        const open = expandedActions[eid] ?? false;
                        return (
                          <div key={actionKey} className="aid-item">
                            <div className="aid-item__header">
                              <button className="aid-toggle-btn" type="button" onClick={() => toggleAction(eid)}>
                                {open ? '▾' : '▸'}
                              </button>
                              <span className="aid-item__key">{action?.key || actionKey}</span>
                              {action?.forms?.href && <code className="aid-item__href">{action.forms.href}</code>}
                              {action?.synchronous === 'true' && <span className="aid-badge">sync</span>}
                              <button className="btn btn--xs btn--danger" type="button"
                                onClick={() => removeAction(ifaceName, actionKey)}>✕</button>
                            </div>
                            {open && (
                              <div className="aid-item__body">
                                <div className="field-grid field-grid--2col">
                                  <div className="field-group">
                                    <label className="field-label">key</label>
                                    <input className="field-input field-input--sm" value={action?.key ?? actionKey}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'key'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">title</label>
                                    <input className="field-input field-input--sm" value={action?.title ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'title'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">synchronous</label>
                                    <select className="field-input field-input--sm"
                                      value={action?.synchronous ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'synchronous'], e.target.value || undefined)}>
                                      <option value="">—</option>
                                      <option value="true">true</option>
                                      <option value="false">false</option>
                                    </select>
                                  </div>
                                  <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                                    <label className="field-label">input schema URI</label>
                                    <input className="field-input field-input--sm" placeholder="https://example.com/schemas/command.schema.json"
                                      value={action?.input ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'input'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                                    <label className="field-label">output schema URI</label>
                                    <input className="field-input field-input--sm" placeholder="https://example.com/schemas/commandResponse.schema.json"
                                      value={action?.output ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'output'], e.target.value || undefined)} />
                                  </div>
                                </div>
                                {advanced && (
                                  <div className="adv-block">
                                    <AdvField label="semanticId" value={action?.semanticId ?? WOT_ACTION_AFFORDANCE}
                                      onChange={(v) => upd([ifaceName, 'InteractionMetadata', 'actions', actionKey, 'semanticId'], v || undefined)} />
                                  </div>
                                )}
                                <div className="aid-section-label aid-section-label--sm">forms (request)</div>
                                <FormsEditor
                                  forms={action?.forms as AIDForms | undefined}
                                  protocol={protocol}
                                  onChange={(f, v) => updActionForms(ifaceName, actionKey, f, v)}
                                  showOp
                                  showResponse={protocol === 'MQTT'}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* ── Events ── */}
                    <div className="subsection">
                      <div className="subsection__header">
                        <span className="subsection__title">Events</span>
                        <button className="btn btn--xs btn--secondary" type="button"
                          onClick={() => addEvent(ifaceName, protocol)}>
                          + Event
                        </button>
                      </div>
                      {Object.keys(events).length === 0 && (
                        <p className="empty-state empty-state--sm">No events defined.</p>
                      )}
                      {Object.entries(events).map(([eventKey, event]) => {
                        const eid  = `${ifaceName}/${eventKey}`;
                        const open = expandedEvents[eid] ?? false;
                        return (
                          <div key={eventKey} className="aid-item">
                            <div className="aid-item__header">
                              <button className="aid-toggle-btn" type="button" onClick={() => toggleEvent(eid)}>
                                {open ? '▾' : '▸'}
                              </button>
                              <span className="aid-item__key">{event?.key || eventKey}</span>
                              {event?.forms?.href && <code className="aid-item__href">{event.forms.href}</code>}
                              <button className="btn btn--xs btn--danger" type="button"
                                onClick={() => removeEvent(ifaceName, eventKey)}>✕</button>
                            </div>
                            {open && (
                              <div className="aid-item__body">
                                <div className="field-grid field-grid--2col">
                                  <div className="field-group">
                                    <label className="field-label">key</label>
                                    <input className="field-input field-input--sm" value={event?.key ?? eventKey}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'events', eventKey, 'key'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group">
                                    <label className="field-label">title</label>
                                    <input className="field-input field-input--sm" value={event?.title ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'events', eventKey, 'title'], e.target.value || undefined)} />
                                  </div>
                                  <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                                    <label className="field-label">output schema URI</label>
                                    <input className="field-input field-input--sm" placeholder="https://example.com/schemas/event.schema.json"
                                      value={event?.output ?? ''}
                                      onChange={(e) => upd([ifaceName, 'InteractionMetadata', 'events', eventKey, 'output'], e.target.value || undefined)} />
                                  </div>
                                </div>
                                {advanced && (
                                  <div className="adv-block">
                                    <AdvField label="semanticId" value={event?.semanticId ?? WOT_EVENT_AFFORDANCE}
                                      onChange={(v) => upd([ifaceName, 'InteractionMetadata', 'events', eventKey, 'semanticId'], v || undefined)} />
                                  </div>
                                )}
                                <div className="aid-section-label aid-section-label--sm">forms</div>
                                <FormsEditor
                                  forms={event?.forms as AIDForms | undefined}
                                  protocol={protocol}
                                  onChange={(f, v) => updEventForms(ifaceName, eventKey, f, v)}
                                  showOp={false}
                                  showResponse={false}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                </>)}

              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
