/**
 * Reverse parsers: AAS JSON submodel objects → ResourceAASProfile form state.
 *
 * Each function mirrors the corresponding builder in ../builders/, reading back
 * the structures those builders produce.
 */

import type {
  DigitalNameplate,
  HierarchicalStructures,
  BomEntity,
  Skill,
  SkillVariable,
  Capability,
  Variable,
  Parameter,
  AIDInterface,
  AIDEndpointMetadata,
  AIDInteractionMetadata,
  AIDProperty,
  AIDAction,
  AIDEvent,
  AIDForms,
  AIDFormResponse,
  AIMCMappingConfig,
  AIMCRelation,
  SystemConfig,
} from '../../types/resourceaas';

// ── Tiny helpers ──────────────────────────────────────────────────────────────

type AnyEl = Record<string, unknown>;

function els(sm: AnyEl): AnyEl[] {
  return (sm.submodelElements as AnyEl[] | undefined) ?? [];
}

function elsByIdShort(elements: AnyEl[]): Record<string, AnyEl> {
  const map: Record<string, AnyEl> = {};
  for (const el of elements) {
    const id = el.idShort as string | undefined;
    if (id) map[id] = el;
  }
  return map;
}

function propVal(elements: AnyEl[], idShort: string): string | undefined {
  const el = elements.find((e) => e.idShort === idShort && e.modelType === 'Property');
  return el ? (el.value as string) : undefined;
}

function mlpVal(elements: AnyEl[], idShort: string): string | undefined {
  const el = elements.find((e) => e.idShort === idShort && e.modelType === 'MultiLanguageProperty');
  if (!el) return undefined;
  const vals = el.value as Array<{ language: string; text: string }> | undefined;
  if (!vals || vals.length === 0) return undefined;
  const en = vals.find((v) => v.language === 'en') ?? vals[0];
  return en?.text;
}

function smc(elements: AnyEl[], idShort: string): AnyEl | undefined {
  return elements.find((e) => e.idShort === idShort && e.modelType === 'SubmodelElementCollection');
}

function smcValue(el: AnyEl): AnyEl[] {
  return (el.value as AnyEl[] | undefined) ?? [];
}

function sml(elements: AnyEl[], idShort: string): AnyEl | undefined {
  return elements.find((e) => e.idShort === idShort && e.modelType === 'SubmodelElementList');
}

function smlValue(el: AnyEl): AnyEl[] {
  return (el.value as AnyEl[] | undefined) ?? [];
}

// ── 1. DigitalNameplate ───────────────────────────────────────────────────────

const MLP_FIELDS = new Set(['ManufacturerName', 'ManufacturerProductDesignation', 'ManufacturerProductFamily']);

export function parseNameplate(sm: AnyEl): DigitalNameplate {
  const elements = els(sm);
  const result: Record<string, unknown> = {};
  for (const el of elements) {
    const id = el.idShort as string | undefined;
    if (!id) continue;
    if (el.modelType === 'MultiLanguageProperty') {
      result[id] = mlpVal(elements, id);
    } else if (el.modelType === 'Property') {
      result[id] = el.value as string;
    }
  }
  return result as unknown as DigitalNameplate;
}

// ── 2. HierarchicalStructures ─────────────────────────────────────────────────

export function parseHierarchicalStructures(sm: AnyEl): HierarchicalStructures {
  const elements = els(sm);

  const archetype = (propVal(elements, 'ArcheType') ?? 'OneUp') as HierarchicalStructures['Archetype'];

  // Find EntryNode — Entity element (not ArcheType Property)
  const entryNode = elements.find((e) => e.modelType === 'Entity') as AnyEl | undefined;
  const entryName = (entryNode?.idShort as string) ?? '';

  const hasPart: Record<string, BomEntity> = {};
  const isPartOf: Record<string, BomEntity> = {};
  const sameAs: Record<string, BomEntity> = {};

  if (entryNode) {
    const statements = (entryNode.statements as AnyEl[] | undefined) ?? [];
    for (const stmt of statements) {
      if (stmt.modelType !== 'Entity') continue;
      const entityIdShort = stmt.idShort as string;
      const entity: BomEntity = {
        globalAssetId: (stmt.globalAssetId as string) || undefined,
        systemId: entityIdShort.startsWith('SameAs_') ? entityIdShort.slice(7) : entityIdShort,
      };

      if (entityIdShort.startsWith('SameAs_')) {
        sameAs[entity.systemId!] = entity;
      } else {
        // Determine HasPart vs IsPartOf from companion RelationshipElement idShort
        const relEl = statements.find(
          (s) => s.modelType === 'RelationshipElement' && (s.idShort as string).endsWith(`_${entityIdShort}`)
        ) as AnyEl | undefined;
        const relId = (relEl?.idShort as string) ?? '';
        if (relId.startsWith('HasPart_') || archetype === 'OneDown') {
          hasPart[entityIdShort] = entity;
        } else {
          isPartOf[entityIdShort] = entity;
        }
      }
    }
  }

  const result: HierarchicalStructures = {
    Name: entryName,
    Archetype: archetype,
  };
  if (Object.keys(isPartOf).length > 0) result.IsPartOf = isPartOf;
  if (Object.keys(hasPart).length > 0) result.HasPart = hasPart;
  if (Object.keys(sameAs).length > 0) result.SameAs = sameAs;

  return result;
}

// ── 3. Skills ─────────────────────────────────────────────────────────────────

function parseOpVariables(vars: AnyEl[]): SkillVariable[] {
  return vars.map((v) => {
    const inner = v.value as AnyEl | undefined;
    const desc = inner?.description as Array<{ language: string; text: string }> | undefined;
    return {
      idShort: (inner?.idShort as string) ?? '',
      valueType: (inner?.valueType as string) ?? 'xs:string',
      displayName: desc?.find((d) => d.language === 'en')?.text,
    };
  });
}

export function parseSkills(sm: AnyEl): Record<string, Skill> {
  const skills: Record<string, Skill> = {};
  for (const el of els(sm)) {
    if (el.modelType !== 'SubmodelElementCollection') continue;
    const skillName = el.idShort as string;
    const inner = smcValue(el);

    const semanticIdProp = propVal(inner, 'SemanticId') ?? '';

    const opEl = inner.find((e) => e.modelType === 'Operation') as AnyEl | undefined;
    const qualifiers = (opEl?.qualifiers as AnyEl[] | undefined) ?? [];
    const desc = (opEl?.description as Array<{ language: string; text: string }> | undefined)
      ?.find((d) => d.language === 'en')?.text;

    const invDel = qualifiers.find((q) => q.type === 'invocationDelegation')?.value as string | undefined;
    const callTypeQ = qualifiers.find(
      (q) => q.type === 'Synchronous' || q.type === 'OneWay'
    );
    const callType = callTypeQ?.type as 'Synchronous' | 'OneWay' | undefined;

    const inputVars = parseOpVariables((opEl?.inputVariables as AnyEl[] | undefined) ?? []);
    const outputVars = parseOpVariables((opEl?.outputVariables as AnyEl[] | undefined) ?? []);
    const inoutVars = parseOpVariables((opEl?.inoutputVariables as AnyEl[] | undefined) ?? []);

    const skill: Skill = { semantic_id: semanticIdProp };
    if (desc) skill.description = desc;
    if (invDel) skill.invocationDelegation = invDel;
    if (callType) skill.callType = callType;
    if (inputVars.length > 0) skill.inputVariables = inputVars;
    if (outputVars.length > 0) skill.outputVariables = outputVars;
    if (inoutVars.length > 0) skill.inoutputVariables = inoutVars;

    skills[skillName] = skill;
  }
  return skills;
}

// ── 4. Capabilities ───────────────────────────────────────────────────────────

export function parseCapabilities(sm: AnyEl): Record<string, Capability> {
  const capabilities: Record<string, Capability> = {};

  const elements = els(sm);
  const capSetEl = smc(elements, 'CapabilitySet');
  if (!capSetEl) return capabilities;

  for (const el of smcValue(capSetEl)) {
    if (el.modelType !== 'SubmodelElementCollection') continue;
    const capName = el.idShort as string;
    const inner = smcValue(el);

    const semanticIdVal = propVal(inner, 'SemanticId') ?? '';

    // realizedBy: SubmodelElementList containing a RelationshipElement
    const realizedByList = sml(inner, 'realizedBy');
    let realizedBy: string | undefined;
    if (realizedByList) {
      const relEl = smlValue(realizedByList).find((e) => e.modelType === 'RelationshipElement') as AnyEl | undefined;
      if (relEl) {
        // The idShort of the RelationshipElement is the skill name
        realizedBy = relEl.idShort as string | undefined;
      }
    }

    const cap: Capability = { semantic_id: semanticIdVal };
    if (realizedBy) cap.realizedBy = realizedBy;
    capabilities[capName] = cap;
  }
  return capabilities;
}

// ── 5. OperationalData (Variables) ───────────────────────────────────────────

export function parseOperationalData(sm: AnyEl): Record<string, Variable> {
  const variables: Record<string, Variable> = {};
  for (const el of els(sm)) {
    if (el.modelType !== 'Property') continue;
    const varName = el.idShort as string;
    variables[varName] = { semanticId: (el.value as string) ?? '' };
  }
  return variables;
}

// ── 6. Parameters ─────────────────────────────────────────────────────────────

export function parseParameters(sm: AnyEl): Record<string, Parameter> {
  const parameters: Record<string, Parameter> = {};
  for (const el of els(sm)) {
    if (el.modelType !== 'SubmodelElementCollection') continue;
    const paramName = el.idShort as string;
    const inner = smcValue(el);
    parameters[paramName] = {
      ParameterValue: propVal(inner, 'ParameterValue') ?? '',
      Unit: propVal(inner, 'Unit'),
    };
  }
  return parameters;
}

// ── 7. AID ────────────────────────────────────────────────────────────────────

function parseFormsSmc(formsSmc: AnyEl): AIDForms {
  const fields = smcValue(formsSmc);
  const forms: AIDForms = { href: propVal(fields, 'href') ?? '' };
  const str = (id: string) => propVal(fields, id);
  if (str('contentType'))         forms.contentType = str('contentType');
  if (str('op'))                  forms.op = str('op');
  if (str('mqv_retain'))          forms.mqv_retain = str('mqv_retain');
  if (str('mqv_controlPacket'))   forms.mqv_controlPacket = str('mqv_controlPacket');
  if (str('mqv_qos'))             forms.mqv_qos = str('mqv_qos');
  if (str('htv_methodName'))      forms.htv_methodName = str('htv_methodName');
  if (str('modv_function'))       forms.modv_function = str('modv_function');
  if (str('modv_entity'))         forms.modv_entity = str('modv_entity');
  if (str('modv_zeroBasedAddressing')) forms.modv_zeroBasedAddressing = str('modv_zeroBasedAddressing');
  if (str('modv_pollingTime'))    forms.modv_pollingTime = str('modv_pollingTime');
  if (str('modv_timeout'))        forms.modv_timeout = str('modv_timeout');
  if (str('modv_type'))           forms.modv_type = str('modv_type');
  if (str('modv_mostSignificantByte')) forms.modv_mostSignificantByte = str('modv_mostSignificantByte');
  if (str('modv_mostSignificantWord')) forms.modv_mostSignificantWord = str('modv_mostSignificantWord');

  const respEl = smc(fields, 'response');
  if (respEl) {
    const rf = smcValue(respEl);
    const resp: AIDFormResponse = {};
    if (propVal(rf, 'href'))             resp.href = propVal(rf, 'href');
    if (propVal(rf, 'contentType'))      resp.contentType = propVal(rf, 'contentType');
    if (propVal(rf, 'mqv_controlPacket')) resp.mqv_controlPacket = propVal(rf, 'mqv_controlPacket');
    if (propVal(rf, 'mqv_retain'))       resp.mqv_retain = propVal(rf, 'mqv_retain');
    forms.response = resp;
  }
  return forms;
}

function parseAffordanceSmc(el: AnyEl): { key: string; title?: string; output?: string; forms?: AIDForms; semanticId?: string } {
  const inner = smcValue(el);
  const key = propVal(inner, 'Key') ?? (el.idShort as string);
  const title = propVal(inner, 'Title');
  const outputFile = inner.find((e) => e.modelType === 'File' && e.idShort === 'output') as AnyEl | undefined;
  const output = outputFile ? (outputFile.value as string) : undefined;
  const formsEl = smc(inner, 'Forms');
  const forms = formsEl ? parseFormsSmc(formsEl) : undefined;
  // semanticId: externalRef(uri) → extract uri from keys[0].value
  const semId = el.semanticId as AnyEl | undefined;
  const semUri = (semId?.keys as AnyEl[] | undefined)?.[0]?.value as string | undefined;
  return { key, title, output, forms, semanticId: semUri };
}

export function parseAID(sm: AnyEl): Record<string, AIDInterface> {
  const interfaces: Record<string, AIDInterface> = {};

  for (const ifaceEl of els(sm)) {
    if (ifaceEl.modelType !== 'SubmodelElementCollection') continue;
    const ifaceName = ifaceEl.idShort as string;
    const inner = smcValue(ifaceEl);

    const iface: AIDInterface = {};

    // title
    const titleVal = propVal(inner, 'title');
    if (titleVal) iface.Title = titleVal;

    // EndpointMetadata
    const epEl = smc(inner, 'EndpointMetadata');
    if (epEl) {
      const epFields = smcValue(epEl);
      const ep: AIDEndpointMetadata = {
        base: propVal(epFields, 'base') ?? '',
        contentType: propVal(epFields, 'contentType') ?? 'application/json',
      };
      if (propVal(epFields, 'modv_mostSignificantByte')) ep.modv_mostSignificantByte = propVal(epFields, 'modv_mostSignificantByte');
      if (propVal(epFields, 'modv_mostSignificantWord')) ep.modv_mostSignificantWord = propVal(epFields, 'modv_mostSignificantWord');
      iface.EndpointMetadata = ep;
    }

    // InteractionMetadata
    const imEl = smc(inner, 'InteractionMetadata');
    if (imEl) {
      const imFields = smcValue(imEl);
      const im: AIDInteractionMetadata = {};

      const propsEl = smc(imFields, 'properties');
      if (propsEl) {
        const props: Record<string, AIDProperty> = {};
        for (const pel of smcValue(propsEl)) {
          if (pel.modelType !== 'SubmodelElementCollection') continue;
          const { key, title, output, forms, semanticId } = parseAffordanceSmc(pel);
          const inner2 = smcValue(pel);
          const observable = propVal(inner2, 'observable');
          const unit = propVal(inner2, 'unit');
          const prop: AIDProperty = { key };
          if (title) prop.title = title;
          if (observable) prop.observable = observable;
          if (unit) prop.unit = unit;
          if (output) prop.output = output;
          if (forms) prop.forms = forms;
          if (semanticId) prop.semanticId = semanticId;
          props[key] = prop;
        }
        if (Object.keys(props).length > 0) im.properties = props;
      }

      const actionsEl = smc(imFields, 'actions');
      if (actionsEl) {
        const actions: Record<string, AIDAction> = {};
        for (const ael of smcValue(actionsEl)) {
          if (ael.modelType !== 'SubmodelElementCollection') continue;
          const { key, title, output, forms, semanticId } = parseAffordanceSmc(ael);
          const inner2 = smcValue(ael);
          const synchronous = propVal(inner2, 'Synchronous');
          const inputFile = inner2.find((e) => e.modelType === 'File' && e.idShort === 'input') as AnyEl | undefined;
          const input = inputFile ? (inputFile.value as string) : undefined;
          const action: AIDAction = { key };
          if (title) action.title = title;
          if (synchronous) action.synchronous = synchronous;
          if (input) action.input = input;
          if (output) action.output = output;
          if (forms) action.forms = forms;
          if (semanticId) action.semanticId = semanticId;
          actions[key] = action;
        }
        if (Object.keys(actions).length > 0) im.actions = actions;
      }

      const eventsEl = smc(imFields, 'events');
      if (eventsEl) {
        const events: Record<string, AIDEvent> = {};
        for (const eel of smcValue(eventsEl)) {
          if (eel.modelType !== 'SubmodelElementCollection') continue;
          const { key, title, output, forms, semanticId } = parseAffordanceSmc(eel);
          const event: AIDEvent = { key };
          if (title) event.title = title;
          if (output) event.output = output;
          if (forms) event.forms = forms;
          if (semanticId) event.semanticId = semanticId;
          events[key] = event;
        }
        if (Object.keys(events).length > 0) im.events = events;
      }

      if (Object.keys(im).length > 0) iface.InteractionMetadata = im;
    }

    interfaces[ifaceName] = iface;
  }
  return interfaces;
}

// ── 8. AIMC ───────────────────────────────────────────────────────────────────

const SUBMODEL_ID_TO_KEY: Record<string, AIMCRelation['sourceSubmodel']> = {
  OperationalData: 'Variables',
  Skills: 'Skills',
  Parameters: 'Parameters',
};

function submodelKeyFromId(id: string): AIMCRelation['sourceSubmodel'] {
  // id typically ends with /OperationalData, /Skills, /Parameters
  for (const [suffix, key] of Object.entries(SUBMODEL_ID_TO_KEY)) {
    if (id.endsWith(`/${suffix}`)) return key;
  }
  return 'Variables';
}

export function parseAIMC(sm: AnyEl): Record<string, AIMCMappingConfig> {
  const result: Record<string, AIMCMappingConfig> = {};

  const elements = els(sm);
  const mappingListEl = sml(elements, 'MappingConfigurations');
  if (!mappingListEl) return result;

  for (const configEl of smlValue(mappingListEl)) {
    if (configEl.modelType !== 'SubmodelElementCollection') continue;
    const mappingName = configEl.idShort as string;
    const inner = smcValue(configEl);

    // InterfaceReference → interfaceName
    const ifaceRefEl = inner.find((e) => e.idShort === 'InterfaceReference' && e.modelType === 'ReferenceElement') as AnyEl | undefined;
    const ifaceKeys = ((ifaceRefEl?.value as AnyEl | undefined)?.keys as AnyEl[] | undefined) ?? [];
    const interfaceName = (ifaceKeys[ifaceKeys.length - 1]?.value as string) ?? mappingName;

    // MappingSourceSinkRelations → relations
    const relListEl = sml(inner, 'MappingSourceSinkRelations');
    const relations: AIMCRelation[] = [];

    for (const relEl of smlValue(relListEl ?? {} as AnyEl)) {
      if (relEl.modelType !== 'RelationshipElement') continue;
      const firstKeys = ((relEl.first as AnyEl | undefined)?.keys as AnyEl[] | undefined) ?? [];
      const secondKeys = ((relEl.second as AnyEl | undefined)?.keys as AnyEl[] | undefined) ?? [];

      // first: [Submodel, Property|SMC]
      const srcSubmodelId = (firstKeys[0]?.value as string) ?? '';
      const srcElement = (firstKeys[firstKeys.length - 1]?.value as string) ?? '';
      const sourceSubmodel = submodelKeyFromId(srcSubmodelId);

      // second: [Submodel, interfaceName, InteractionMetadata, affordanceType, affordanceName]
      const affordanceType = (secondKeys[3]?.value as string) ?? 'properties';
      const affordanceName = (secondKeys[4]?.value as string) ?? '';

      relations.push({
        sourceSubmodel,
        sourceElement: srcElement,
        aidAffordanceType: affordanceType as AIMCRelation['aidAffordanceType'],
        aidAffordance: affordanceName,
      });
    }

    result[mappingName] = { interfaceName, relations };
  }
  return result;
}

// ── Profile JSON fallback ─────────────────────────────────────────────────────
// When the pipeline returns the LLM profile dict instead of a full AAS env JSON,
// map the profile keys directly to the form types (they share the same shape).

function parseProfileJsonFallback(env: Record<string, unknown>): {
  systemId: string;
  shellIdShort: string;
  shellId: string;
  globalAssetId: string;
  config: SystemConfig;
  presentSubmodelIdShorts: string[];
} | null {
  // Profile JSON has a single top-level key = system name
  const topKeys = Object.keys(env);
  if (topKeys.length !== 1) return null;
  const systemName = topKeys[0];
  const body = env[systemName] as Record<string, unknown> | undefined;
  if (!body || typeof body !== 'object') return null;

  const shellIdShort = (body.idShort as string) ?? `${systemName}AAS`;
  const shellId = (body.id as string) ?? '';
  const globalAssetId = (body.globalAssetId as string) ?? '';
  const systemId = shellIdShort.replace(/_AAS$/i, '').trim() || systemName;

  const presentSubmodelIdShorts: string[] = [];
  const config: SystemConfig = { idShort: shellIdShort, id: shellId, globalAssetId };

  // DigitalNameplate — same shape as form type
  if (body.DigitalNameplate && typeof body.DigitalNameplate === 'object') {
    config.DigitalNameplate = body.DigitalNameplate as DigitalNameplate;
    presentSubmodelIdShorts.push('DigitalNameplate');
  }

  // HierarchicalStructures — same shape
  if (body.HierarchicalStructures && typeof body.HierarchicalStructures === 'object') {
    config.HierarchicalStructures = body.HierarchicalStructures as HierarchicalStructures;
    presentSubmodelIdShorts.push('HierarchicalStructures');
  }

  // Skills — Record<string, Skill>
  const skillsRaw = body.Skills;
  if (skillsRaw && typeof skillsRaw === 'object' && !Array.isArray(skillsRaw)) {
    config.Skills = skillsRaw as Record<string, Skill>;
    presentSubmodelIdShorts.push('Skills');
  }

  // Capabilities
  const capsRaw = body.Capabilities;
  if (capsRaw && typeof capsRaw === 'object' && !Array.isArray(capsRaw)) {
    config.Capabilities = capsRaw as Record<string, Capability>;
    presentSubmodelIdShorts.push('Capabilities');
  }

  // Variables / OperationalData — profile uses string or {semanticId} per variable
  const varRaw = (body.Variables ?? body.OperationalData) as Record<string, unknown> | undefined;
  if (varRaw && typeof varRaw === 'object' && !Array.isArray(varRaw)) {
    const vars: Record<string, Variable> = {};
    for (const [k, v] of Object.entries(varRaw)) {
      if (typeof v === 'string') {
        vars[k] = { semanticId: v };
      } else if (v && typeof v === 'object' && 'semanticId' in (v as object)) {
        vars[k] = v as Variable;
      }
    }
    config.Variables = vars;
    presentSubmodelIdShorts.push('OperationalData');
  }

  // Parameters
  const paramRaw = body.Parameters;
  if (paramRaw && typeof paramRaw === 'object' && !Array.isArray(paramRaw)) {
    config.Parameters = paramRaw as Record<string, Parameter>;
    presentSubmodelIdShorts.push('Parameters');
  }

  // AID — various key names from python normalizer
  const aidRaw = (body.AID ?? body.AssetInterfacesDescription ?? body.AssetInterfaceDescription) as Record<string, unknown> | undefined;
  if (aidRaw && typeof aidRaw === 'object' && !Array.isArray(aidRaw)) {
    config.AID = aidRaw as Record<string, AIDInterface>;
    presentSubmodelIdShorts.push('AID');
  }

  // AIMC
  const aimcRaw = body.AIMC;
  if (aimcRaw && typeof aimcRaw === 'object' && !Array.isArray(aimcRaw)) {
    config.AIMC = aimcRaw as Record<string, AIMCMappingConfig>;
    presentSubmodelIdShorts.push('AssetInterfacesMappingConfiguration');
  }

  return { systemId, shellIdShort, shellId, globalAssetId, config, presentSubmodelIdShorts };
}

// ── Top-level: parse full AAS JSON environment → SystemConfig ─────────────────

export function parseAasJsonToProfile(json: string): {
  systemId: string;
  shellIdShort: string;
  shellId: string;
  globalAssetId: string;
  config: SystemConfig;
  presentSubmodelIdShorts: string[];
} | null {
  let env: Record<string, unknown>;
  try {
    env = JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }

  const shells = env.assetAdministrationShells as Array<Record<string, unknown>> | undefined;
  const shell = shells?.[0];
  if (!shell) {
    // Fallback: try to parse as profile JSON (LLM json-description output)
    return parseProfileJsonFallback(env);
  }

  const shellId = (shell.id as string) ?? '';
  const shellIdShort = (shell.idShort as string) ?? '';
  const assetInfo = shell.assetInformation as Record<string, unknown> | undefined;
  const globalAssetId = (assetInfo?.globalAssetId as string) ?? '';
  const systemId = shellIdShort.replace(/_AAS$/i, '').trim() || shellIdShort;

  const submodelsArr = (env.submodels as AnyEl[] | undefined) ?? [];
  const presentSubmodelIdShorts: string[] = [];

  const config: SystemConfig = {
    idShort: shellIdShort,
    id: shellId,
    globalAssetId,
  };

  for (const sm of submodelsArr) {
    const idShort = sm.idShort as string | undefined;
    if (!idShort) continue;
    presentSubmodelIdShorts.push(idShort);

    switch (idShort) {
      case 'DigitalNameplate':
        config.DigitalNameplate = parseNameplate(sm);
        break;
      case 'HierarchicalStructures':
        config.HierarchicalStructures = parseHierarchicalStructures(sm);
        break;
      case 'Skills':
        config.Skills = parseSkills(sm);
        break;
      case 'Capabilities':
        config.Capabilities = parseCapabilities(sm);
        break;
      case 'OperationalData':
        config.Variables = parseOperationalData(sm);
        break;
      case 'Parameters':
        config.Parameters = parseParameters(sm);
        break;
      case 'AID':
        config.AID = parseAID(sm);
        break;
      case 'AssetInterfacesMappingConfiguration':
        config.AIMC = parseAIMC(sm);
        break;
    }
  }

  return { systemId, shellIdShort, shellId, globalAssetId, config, presentSubmodelIdShorts };
}
