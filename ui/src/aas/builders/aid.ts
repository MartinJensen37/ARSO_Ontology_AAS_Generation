import type { AasSubmodel, AasElement, AasSubmodelElementCollection, AasFile, AasReference } from '../types';
import type { AIDInterface, AIDForms, AIDFormResponse, AIDProtocol } from '../../types/resourceaas';
import {
  externalRef,
  AID_SUBMODEL, AID_INTERFACE, AID_INTERACTION_METADATA,
  WOT_ACTION_AFFORDANCE, WOT_PROPERTY_AFFORDANCE, WOT_EVENT_AFFORDANCE,
  WOT_INTERACTION_AFFORDANCE,
  MQTT_PROTOCOL, HTTP_PROTOCOL, MODBUS_PROTOCOL, WOT_TD,
} from '../semanticIds';

// ── Protocol → default supplemental semantic IDs ─────────────────────────────

const PROTOCOL_SUPPLEMENTAL: Record<AIDProtocol, string[]> = {
  MQTT:   [MQTT_PROTOCOL, WOT_TD],
  HTTP:   [HTTP_PROTOCOL, WOT_TD],
  MODBUS: [MODBUS_PROTOCOL, WOT_TD],
};

// ── Forms SMC builder ─────────────────────────────────────────────────────────

function buildResponseSmc(resp: AIDFormResponse): AasSubmodelElementCollection {
  const fields: AasElement[] = [];
  if (resp.contentType)      fields.push({ modelType: 'Property', idShort: 'contentType',      valueType: 'xs:string', value: resp.contentType });
  if (resp.href)             fields.push({ modelType: 'Property', idShort: 'href',             valueType: 'xs:string', value: resp.href });
  if (resp.mqv_controlPacket)fields.push({ modelType: 'Property', idShort: 'mqv_controlPacket', valueType: 'xs:string', value: resp.mqv_controlPacket });
  if (resp.mqv_retain)       fields.push({ modelType: 'Property', idShort: 'mqv_retain',       valueType: 'xs:string', value: resp.mqv_retain });
  return { modelType: 'SubmodelElementCollection', idShort: 'response', value: fields };
}

function buildFormsSmc(forms: AIDForms): AasSubmodelElementCollection {
  const fields: AasElement[] = [];

  if (forms.contentType)     fields.push({ modelType: 'Property', idShort: 'contentType',     valueType: 'xs:string', value: forms.contentType });
  if (forms.href)            fields.push({ modelType: 'Property', idShort: 'href',            valueType: 'xs:string', value: forms.href });
  if (forms.op)              fields.push({ modelType: 'Property', idShort: 'op',              valueType: 'xs:string', value: forms.op });

  // MQTT
  if (forms.mqv_retain)        fields.push({ modelType: 'Property', idShort: 'mqv_retain',        valueType: 'xs:string', value: forms.mqv_retain });
  if (forms.mqv_controlPacket) fields.push({ modelType: 'Property', idShort: 'mqv_controlPacket', valueType: 'xs:string', value: forms.mqv_controlPacket });
  if (forms.mqv_qos)           fields.push({ modelType: 'Property', idShort: 'mqv_qos',           valueType: 'xs:string', value: forms.mqv_qos });

  // HTTP
  if (forms.htv_methodName) fields.push({ modelType: 'Property', idShort: 'htv_methodName', valueType: 'xs:string', value: forms.htv_methodName });

  // MODBUS
  if (forms.modv_function)             fields.push({ modelType: 'Property', idShort: 'modv_function',             valueType: 'xs:string', value: forms.modv_function });
  if (forms.modv_entity)               fields.push({ modelType: 'Property', idShort: 'modv_entity',               valueType: 'xs:string', value: forms.modv_entity });
  if (forms.modv_zeroBasedAddressing)  fields.push({ modelType: 'Property', idShort: 'modv_zeroBasedAddressing',  valueType: 'xs:string', value: forms.modv_zeroBasedAddressing });
  if (forms.modv_pollingTime)          fields.push({ modelType: 'Property', idShort: 'modv_pollingTime',          valueType: 'xs:string', value: forms.modv_pollingTime });
  if (forms.modv_timeout)              fields.push({ modelType: 'Property', idShort: 'modv_timeout',              valueType: 'xs:string', value: forms.modv_timeout });
  if (forms.modv_type)                 fields.push({ modelType: 'Property', idShort: 'modv_type',                 valueType: 'xs:string', value: forms.modv_type });
  if (forms.modv_mostSignificantByte)  fields.push({ modelType: 'Property', idShort: 'modv_mostSignificantByte',  valueType: 'xs:string', value: forms.modv_mostSignificantByte });
  if (forms.modv_mostSignificantWord)  fields.push({ modelType: 'Property', idShort: 'modv_mostSignificantWord',  valueType: 'xs:string', value: forms.modv_mostSignificantWord });

  if (forms.response) fields.push(buildResponseSmc(forms.response));

  return { modelType: 'SubmodelElementCollection', idShort: 'Forms', value: fields };
}

function schemaFile(idShort: string, uri: string): AasFile {
  return { modelType: 'File', idShort, contentType: 'application/schema+json', value: uri };
}

// ── Main builder ──────────────────────────────────────────────────────────────

export function buildAIDSubmodel(
  baseUrl: string,
  systemId: string,
  interfaces: Record<string, Partial<AIDInterface>>,
  meta?: { id?: string; semanticId?: string },
): AasSubmodel {
  const submodelId = meta?.id ?? `${baseUrl}/submodels/instances/${systemId}/AID`;

  const elements: AasElement[] = Object.entries(interfaces).map(([ifaceName, iface]) => {
    const protocol = iface?.protocol;

    // supplementalSemanticIds: use override if set, else derive from protocol
    const suppUris: string[] = iface?.supplementalSemanticIds?.length
      ? iface.supplementalSemanticIds
      : (protocol ? PROTOCOL_SUPPLEMENTAL[protocol] : []);
    const suppRefs: AasReference[] = suppUris.map(externalRef);

    const innerElements: AasElement[] = [];

    // title
    if (iface?.Title) {
      innerElements.push({ modelType: 'Property', idShort: 'title', valueType: 'xs:string', value: iface.Title });
    }

    // EndpointMetadata
    if (iface?.EndpointMetadata) {
      const epFields: AasElement[] = [
        { modelType: 'Property', idShort: 'base',        valueType: 'xs:anyURI', value: iface.EndpointMetadata.base ?? '' },
        { modelType: 'Property', idShort: 'contentType', valueType: 'xs:string', value: iface.EndpointMetadata.contentType ?? 'application/json' },
      ];
      if (iface.EndpointMetadata.modv_mostSignificantByte)
        epFields.push({ modelType: 'Property', idShort: 'modv_mostSignificantByte', valueType: 'xs:string', value: iface.EndpointMetadata.modv_mostSignificantByte });
      if (iface.EndpointMetadata.modv_mostSignificantWord)
        epFields.push({ modelType: 'Property', idShort: 'modv_mostSignificantWord', valueType: 'xs:string', value: iface.EndpointMetadata.modv_mostSignificantWord });
      innerElements.push({ modelType: 'SubmodelElementCollection', idShort: 'EndpointMetadata', value: epFields });
    }

    // InteractionMetadata
    const interactionElements: AasElement[] = [];

    // — Properties —
    const properties = iface?.InteractionMetadata?.properties ?? {};
    const propElements: AasElement[] = Object.entries(properties).map(([propKey, prop]) => {
      const key = prop?.key ?? propKey;
      const value: AasElement[] = [
        { modelType: 'Property', idShort: 'Key', valueType: 'xs:string', value: key },
        ...(prop?.title  ? [{ modelType: 'Property' as const, idShort: 'Title',  valueType: 'xs:string', value: prop.title }] : []),
        ...(prop?.output ? [schemaFile('output', prop.output)] : []),
        ...(prop?.forms  ? [buildFormsSmc(prop.forms)] : []),
      ];
      return {
        modelType: 'SubmodelElementCollection' as const,
        idShort: key,
        ...(prop?.semanticId ? { semanticId: externalRef(prop.semanticId) } : {}),
        value,
      };
    });
    if (propElements.length > 0) {
      interactionElements.push({
        modelType: 'SubmodelElementCollection',
        idShort: 'properties',
        semanticId: externalRef(WOT_PROPERTY_AFFORDANCE),
        value: propElements,
      });
    }

    // — Actions —
    const actions = iface?.InteractionMetadata?.actions ?? {};
    const actionElements: AasElement[] = Object.entries(actions).map(([actionKey, action]) => {
      const key = action?.key ?? actionKey;
      const value: AasElement[] = [
        { modelType: 'Property', idShort: 'Key', valueType: 'xs:string', value: key },
        ...(action?.title       ? [{ modelType: 'Property' as const, idShort: 'Title',       valueType: 'xs:string',  value: action.title }] : []),
        ...(action?.synchronous ? [{ modelType: 'Property' as const, idShort: 'Synchronous', valueType: 'xs:boolean', value: action.synchronous }] : []),
        ...(action?.input  ? [schemaFile('input',  action.input)]  : []),
        ...(action?.output ? [schemaFile('output', action.output)] : []),
        ...(action?.forms  ? [buildFormsSmc(action.forms)] : []),
      ];
      return {
        modelType: 'SubmodelElementCollection' as const,
        idShort: key,
        ...(action?.semanticId ? { semanticId: externalRef(action.semanticId) } : {}),
        value,
      };
    });
    if (actionElements.length > 0) {
      interactionElements.push({
        modelType: 'SubmodelElementCollection',
        idShort: 'actions',
        semanticId: externalRef(WOT_ACTION_AFFORDANCE),
        value: actionElements,
      });
    }

    // — Events —
    const events = iface?.InteractionMetadata?.events ?? {};
    const eventElements: AasElement[] = Object.entries(events).map(([eventKey, event]) => {
      const key = event?.key ?? eventKey;
      const value: AasElement[] = [
        { modelType: 'Property', idShort: 'Key', valueType: 'xs:string', value: key },
        ...(event?.title  ? [{ modelType: 'Property' as const, idShort: 'Title',  valueType: 'xs:string', value: event.title }] : []),
        ...(event?.output ? [schemaFile('output', event.output)] : []),
        ...(event?.forms  ? [buildFormsSmc(event.forms)] : []),
      ];
      return {
        modelType: 'SubmodelElementCollection' as const,
        idShort: key,
        ...(event?.semanticId ? { semanticId: externalRef(event.semanticId) } : {}),
        value,
      };
    });
    if (eventElements.length > 0) {
      interactionElements.push({
        modelType: 'SubmodelElementCollection',
        idShort: 'events',
        semanticId: externalRef(WOT_EVENT_AFFORDANCE),
        value: eventElements,
      });
    }

    if (interactionElements.length > 0) {
      innerElements.push({
        modelType: 'SubmodelElementCollection',
        idShort: 'InteractionMetadata',
        semanticId: externalRef(AID_INTERACTION_METADATA),
        supplementalSemanticIds: [externalRef(WOT_INTERACTION_AFFORDANCE)],
        value: interactionElements,
      });
    }

    return {
      modelType: 'SubmodelElementCollection' as const,
      idShort: ifaceName,
      semanticId: externalRef(AID_INTERFACE),
      ...(suppRefs.length > 0 ? { supplementalSemanticIds: suppRefs } : {}),
      value: innerElements,
    };
  });

  return {
    modelType: 'Submodel',
    id: submodelId,
    idShort: 'AID',
    kind: 'Instance',
    semanticId: externalRef(meta?.semanticId ?? AID_SUBMODEL),
    administration: { version: '1', revision: '1' },
    submodelElements: elements,
  };
}
