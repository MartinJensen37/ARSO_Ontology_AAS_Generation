import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  ResourceAASProfile,
  ValidationIssue,
  ValidateResponse,
} from '../types/resourceaas';
import { buildAasEnvironment } from '../aas/serializer';
import { buildNameplateSubmodel } from '../aas/builders/nameplate';
import { buildHierarchicalStructuresSubmodel } from '../aas/builders/hierarchicalStructures';
import { buildAIDSubmodel } from '../aas/builders/aid';
import { buildSkillsSubmodel } from '../aas/builders/skills';
import { buildCapabilitiesSubmodel } from '../aas/builders/capabilities';
import { buildOperationalDataSubmodel } from '../aas/builders/operationalData';
import { buildParametersSubmodel } from '../aas/builders/parameters';
import { buildAIMCSubmodel } from '../aas/builders/aimc';
import { SEMANTIC_ID_BASE } from '../aas/semanticIds';
import type { AasSubmodel } from '../aas/types';
import { parseAasJsonToProfile } from '../aas/parsers/parseAasToProfile';

export type AASType = 'Resource' | 'Product' | 'Process';
export type SubmodelKey =
  | 'Nameplate'
  | 'AID'
  | 'Skills'
  | 'Capabilities'
  | 'Variables'
  | 'Parameters'
  | 'HierarchicalStructures'
  | 'AIMC';

export type SubmodelTab = SubmodelKey;

export const REQUIRED_SUBMODELS: SubmodelKey[] = ['Nameplate', 'HierarchicalStructures'];

export const ALL_SUBMODELS: SubmodelKey[] = [
  'Nameplate',
  'HierarchicalStructures',
  'AID',
  'Skills',
  'Capabilities',
  'Variables',
  'Parameters',
  'AIMC',
];

export const SUBMODEL_FIELD_PREFIXES: Record<SubmodelKey, string[]> = {
  Nameplate: ['DigitalNameplate'],
  HierarchicalStructures: ['HierarchicalStructures'],
  AID: ['AID'],
  Skills: ['Skills'],
  Capabilities: ['Capabilities'],
  Variables: ['Variables'],
  Parameters: ['Parameters'],
  AIMC: ['AIMC'],
};

export const SUBMODEL_YAML_KEYS: Record<SubmodelKey, string> = {
  Nameplate: 'DigitalNameplate',
  HierarchicalStructures: 'HierarchicalStructures',
  AID: 'AID',
  Skills: 'Skills',
  Capabilities: 'Capabilities',
  Variables: 'Variables',
  Parameters: 'Parameters',
  AIMC: 'AIMC',
};

// ── Per-AAS state ─────────────────────────────────────────────────────────────

export interface AASNodeState {
  identitySystemId: string;
  identityIdShort: string;
  identityId: string;
  identityGlobalAssetId: string;
  identityAssetType: string;
  aasType: AASType;
  selectedSubmodels: SubmodelKey[];
  parsedProfile: ResourceAASProfile | null;
}

export const DEFAULT_AAS_NODE_STATE: AASNodeState = {
  identitySystemId: '',
  identityIdShort: '',
  identityId: '',
  identityGlobalAssetId: '',
  identityAssetType: '',
  aasType: 'Resource',
  selectedSubmodels: [...REQUIRED_SUBMODELS],
  parsedProfile: null,
};

/** Initial shell node ID — must match useModelStore.SHELL_NODE_ID */
export const INITIAL_SHELL_NODE_ID = 'aas-shell';

// ── AppState ──────────────────────────────────────────────────────────────────

interface AppState {
  // ── Multi-AAS ──────────────────────────────────────────────────────────
  aasNodes: Record<string, AASNodeState>;
  activeAasNodeId: string;

  // ── "Active AAS" workspace fields (flat copies of aasNodes[activeAasNodeId]) ──
  // These are kept in sync so all existing form code reads them unchanged.
  aasType: AASType;
  selectedSubmodels: SubmodelKey[];
  identitySystemId: string;
  identityIdShort: string;
  identityId: string;
  identityGlobalAssetId: string;
  identityAssetType: string;
  activeTab: SubmodelTab;
  parsedProfile: ResourceAASProfile | null;

  // ── Validation ──────────────────────────────────────────────────────────
  validationIssues: ValidationIssue[];           // active AAS (backward compat)
  validationResult: ValidateResponse | null;
  isLoadingValidate: boolean;
  validationIssuesByNode: Record<string, ValidationIssue[]>;
  loadingValidateByNode: Record<string, boolean>;

  // ── Multi-AAS actions ───────────────────────────────────────────────────
  setActiveAasNode: (shellNodeId: string) => void;
  addAasNode: (shellNodeId: string) => void;
  removeAasNode: (shellNodeId: string) => void;
  resetAasNode: (shellNodeId: string) => void;
  buildAasJsonForNode: (shellNodeId: string) => string;
  buildAllAasJson: () => string;

  // ── Existing actions (operate on active AAS) ────────────────────────────
  setAASType: (t: AASType) => void;
  setSelectedSubmodels: (s: SubmodelKey[]) => void;
  toggleSubmodel: (s: SubmodelKey) => void;
  setIdentityField: (field: 'systemId' | 'idShort' | 'id' | 'globalAssetId' | 'assetType', value: string) => void;
  initProfileFromIdentity: () => void;
  setActiveTab: (tab: SubmodelTab) => void;
  updateProfileField: (path: string[], value: unknown) => void;
  /** Directly update a specific AAS node's profile (bypasses active workspace swap). */
  updateProfileFieldForNode: (shellNodeId: string, path: string[], value: unknown) => void;
  /** Remove a nested key from a specific AAS node's profile. */
  removeProfileEntryForNode: (shellNodeId: string, path: string[]) => void;
  setValidationIssues: (issues: ValidationIssue[]) => void;
  setValidateResult: (result: ValidateResponse) => void;
  setLoadingValidate: (v: boolean) => void;
  setValidationIssuesForNode: (nodeId: string, issues: ValidationIssue[]) => void;
  setLoadingValidateForNode: (nodeId: string, v: boolean) => void;
  buildAasJson: () => string;
  resetAll: () => void;

  // ── AI Generation ───────────────────────────────────────────────────────
  /** Import an AAS JSON string generated by the AI pipeline into the active AAS node. */
  importAasJson: (json: string) => void;

  // ── Theme ──────────────────────────────────────────────────────────────
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function deriveBaseUrl(id: string): string {
  try {
    return new URL(id).origin;
  } catch {
    return SEMANTIC_ID_BASE;
  }
}

/** Flatten AASNodeState fields onto the "active workspace" fields. */
function flattenNode(ns: AASNodeState): Partial<AppState> {
  return {
    identitySystemId: ns.identitySystemId,
    identityIdShort: ns.identityIdShort,
    identityId: ns.identityId,
    identityGlobalAssetId: ns.identityGlobalAssetId,
    identityAssetType: ns.identityAssetType,
    aasType: ns.aasType,
    selectedSubmodels: ns.selectedSubmodels,
    parsedProfile: ns.parsedProfile,
  };
}

/** Extract the active workspace fields into an AASNodeState. */
function extractNodeState(s: AppState): AASNodeState {
  return {
    identitySystemId: s.identitySystemId,
    identityIdShort: s.identityIdShort,
    identityId: s.identityId,
    identityGlobalAssetId: s.identityGlobalAssetId,
    identityAssetType: s.identityAssetType,
    aasType: s.aasType,
    selectedSubmodels: s.selectedSubmodels,
    parsedProfile: s.parsedProfile,
  };
}

/** Apply workspace updates AND sync them back to aasNodes[activeAasNodeId]. */
function withSync(s: AppState, updates: Partial<AppState>): Partial<AppState> {
  return {
    ...updates,
    aasNodes: {
      ...s.aasNodes,
      [s.activeAasNodeId]: {
        identitySystemId: (updates.identitySystemId ?? s.identitySystemId),
        identityIdShort: (updates.identityIdShort ?? s.identityIdShort),
        identityId: (updates.identityId ?? s.identityId),
        identityGlobalAssetId: (updates.identityGlobalAssetId ?? s.identityGlobalAssetId),
        identityAssetType: (updates.identityAssetType ?? s.identityAssetType),
        aasType: (updates.aasType ?? s.aasType),
        selectedSubmodels: (updates.selectedSubmodels ?? s.selectedSubmodels),
        parsedProfile: (updates.parsedProfile ?? s.parsedProfile),
      },
    },
  };
}

/** Build submodels array from an AASNodeState. */
function buildSubmodels(ns: AASNodeState): AasSubmodel[] {
  const systemId = ns.identitySystemId;
  const baseUrl = deriveBaseUrl(ns.identityId);
  const systemConfig = (ns.parsedProfile?.[systemId] ?? {}) as Record<string, unknown>;
  const metaOverrides = (systemConfig._meta ?? {}) as Record<string, { id?: string; semanticId?: string }>;
  const submodels: AasSubmodel[] = [];

  for (const sm of ns.selectedSubmodels) {
    switch (sm) {
      case 'Nameplate':
        submodels.push(buildNameplateSubmodel(
          baseUrl, systemId,
          (systemConfig.DigitalNameplate ?? {}) as Parameters<typeof buildNameplateSubmodel>[2],
          metaOverrides.Nameplate
        ));
        break;
      case 'HierarchicalStructures':
        submodels.push(buildHierarchicalStructuresSubmodel(
          baseUrl, systemId, ns.identityGlobalAssetId, ns.identityId,
          (systemConfig.HierarchicalStructures ?? {}) as Parameters<typeof buildHierarchicalStructuresSubmodel>[4],
          metaOverrides.HierarchicalStructures
        ));
        break;
      case 'AID':
        submodels.push(buildAIDSubmodel(
          baseUrl, systemId,
          (systemConfig.AID ?? {}) as Parameters<typeof buildAIDSubmodel>[2],
          metaOverrides.AID
        ));
        break;
      case 'Skills':
        submodels.push(buildSkillsSubmodel(
          baseUrl, systemId,
          (systemConfig.Skills ?? {}) as Parameters<typeof buildSkillsSubmodel>[2],
          metaOverrides.Skills
        ));
        break;
      case 'Capabilities':
        submodels.push(buildCapabilitiesSubmodel(
          baseUrl, systemId,
          (systemConfig.Capabilities ?? {}) as Parameters<typeof buildCapabilitiesSubmodel>[2],
          metaOverrides.Capabilities
        ));
        break;
      case 'Variables':
        submodels.push(buildOperationalDataSubmodel(
          baseUrl, systemId,
          (systemConfig.Variables ?? {}) as Parameters<typeof buildOperationalDataSubmodel>[2],
          metaOverrides.Variables
        ));
        break;
      case 'Parameters':
        submodels.push(buildParametersSubmodel(
          baseUrl, systemId,
          (systemConfig.Parameters ?? {}) as Parameters<typeof buildParametersSubmodel>[2],
          metaOverrides.Parameters
        ));
        break;
      case 'AIMC':
        submodels.push(buildAIMCSubmodel(
          baseUrl, systemId,
          (systemConfig.AIMC ?? {}) as Parameters<typeof buildAIMCSubmodel>[2],
          metaOverrides.AIMC
        ));
        break;
    }
  }
  return submodels;
}

// ── Initial state ─────────────────────────────────────────────────────────────

const INITIAL_NODE_STATE = { ...DEFAULT_AAS_NODE_STATE };

const INITIAL_STATE = {
  aasNodes: { [INITIAL_SHELL_NODE_ID]: INITIAL_NODE_STATE } as Record<string, AASNodeState>,
  activeAasNodeId: INITIAL_SHELL_NODE_ID,
  wizardStep: 0,
  aasType: 'Resource' as const,
  selectedSubmodels: [...REQUIRED_SUBMODELS] as SubmodelKey[],
  identitySystemId: '',
  identityIdShort: '',
  identityId: '',
  identityGlobalAssetId: '',
  identityAssetType: '',
  activeTab: 'Nameplate' as SubmodelKey,
  parsedProfile: null as ResourceAASProfile | null,
  validationIssues: [] as ValidationIssue[],
  validationResult: null as ValidateResponse | null,
  isLoadingValidate: false,
  validationIssuesByNode: {} as Record<string, ValidationIssue[]>,
  loadingValidateByNode: {} as Record<string, boolean>,
  theme: 'light' as 'light' | 'dark',
};

// ── Store ─────────────────────────────────────────────────────────────────────

export const useAppStore = create<AppState>()(
  persist(
  (set, get) => ({
  ...INITIAL_STATE,

  // ── Multi-AAS actions ──────────────────────────────────────────────────

  setActiveAasNode: (shellNodeId) => {
    const s = get();
    // Save current workspace to the outgoing node
    const outgoing = extractNodeState(s);
    const incoming = s.aasNodes[shellNodeId] ?? DEFAULT_AAS_NODE_STATE;
    set({
      aasNodes: { ...s.aasNodes, [s.activeAasNodeId]: outgoing },
      activeAasNodeId: shellNodeId,
      ...flattenNode(incoming),
    });
  },

  addAasNode: (shellNodeId) => {
    const s = get();
    if (s.aasNodes[shellNodeId]) return; // already exists
    set({
      aasNodes: { ...s.aasNodes, [shellNodeId]: { ...DEFAULT_AAS_NODE_STATE } },
    });
  },

  removeAasNode: (shellNodeId) => {
    const s = get();
    const next = { ...s.aasNodes };
    delete next[shellNodeId];
    const updates: Partial<AppState> = { aasNodes: next };
    // If removed was active, switch to first remaining
    if (s.activeAasNodeId === shellNodeId) {
      const remaining = Object.keys(next);
      const fallback = remaining[0] ?? INITIAL_SHELL_NODE_ID;
      const fallbackState = next[fallback] ?? DEFAULT_AAS_NODE_STATE;
      Object.assign(updates, { activeAasNodeId: fallback, ...flattenNode(fallbackState) });
    }
    set(updates as AppState);
  },

  resetAasNode: (shellNodeId) => {
    const s = get();
    const fresh = { ...DEFAULT_AAS_NODE_STATE };
    const next = { ...s.aasNodes, [shellNodeId]: fresh };
    const updates: Partial<AppState> = { aasNodes: next };
    if (s.activeAasNodeId === shellNodeId) {
      Object.assign(updates, flattenNode(fresh));
    }
    set(updates as AppState);
  },

  buildAasJsonForNode: (shellNodeId) => {
    const s = get();
    // Use the live workspace if it's the active node, otherwise use saved state
    const ns = s.activeAasNodeId === shellNodeId
      ? extractNodeState(s)
      : (s.aasNodes[shellNodeId] ?? DEFAULT_AAS_NODE_STATE);
    if (!ns.identitySystemId) return '';
    const submodels = buildSubmodels(ns);
    return buildAasEnvironment(
      ns.identityId, ns.identityIdShort, ns.identityGlobalAssetId,
      submodels, ns.identityAssetType || undefined
    );
  },

  buildAllAasJson: () => {
    const s = get();
    // Collect current workspace state for active node, saved state for others
    const allNodes = {
      ...s.aasNodes,
      [s.activeAasNodeId]: extractNodeState(s),
    };
    // Build each AAS as a separate environment, return as JSON array
    const envs = Object.values(allNodes)
      .filter((ns) => ns.identitySystemId)
      .map((ns) => {
        const submodels = buildSubmodels(ns);
        return JSON.parse(buildAasEnvironment(
          ns.identityId, ns.identityIdShort, ns.identityGlobalAssetId,
          submodels, ns.identityAssetType || undefined
        ));
      });
    return JSON.stringify(envs, null, 2);
  },

  // ── Wizard actions ─────────────────────────────────────────────────────

  setAASType: (t) => set((s) => withSync(s, { aasType: t }) as AppState),

  setSelectedSubmodels: (subs) => set((s) => withSync(s, { selectedSubmodels: subs }) as AppState),

  toggleSubmodel: (sm) => {
    const s = get();
    if (REQUIRED_SUBMODELS.includes(sm)) return;
    const isAdding = !s.selectedSubmodels.includes(sm);
    const next = isAdding
      ? [...s.selectedSubmodels, sm]
      : s.selectedSubmodels.filter((x) => x !== sm);

    let parsedProfile = s.parsedProfile;
    if (parsedProfile && s.identitySystemId) {
      const clone = JSON.parse(JSON.stringify(parsedProfile)) as Record<string, unknown>;
      const sysCfg = (clone[s.identitySystemId] ?? {}) as Record<string, unknown>;
      const profileKey = SUBMODEL_YAML_KEYS[sm];
      if (isAdding) {
        if (!(profileKey in sysCfg)) sysCfg[profileKey] = {};
      } else {
        const val = sysCfg[profileKey];
        if (val === null || val === undefined || (typeof val === 'object' && Object.keys(val as object).length === 0)) {
          delete sysCfg[profileKey];
        }
      }
      clone[s.identitySystemId] = sysCfg;
      parsedProfile = clone as ResourceAASProfile;
    }
    set(withSync(s, { selectedSubmodels: next, parsedProfile }) as AppState);
  },

  setIdentityField: (field, value) => {
    const map = {
      systemId: 'identitySystemId', idShort: 'identityIdShort',
      id: 'identityId', globalAssetId: 'identityGlobalAssetId', assetType: 'identityAssetType',
    } as const;
    set((s) => withSync(s, { [map[field]]: value }) as AppState);
  },

  initProfileFromIdentity: () => {
    const s = get();
    const { identitySystemId, identityIdShort, identityId, identityGlobalAssetId, selectedSubmodels, parsedProfile } = s;
    if (!identitySystemId) return;

    if (parsedProfile && parsedProfile[identitySystemId]) {
      const existing = parsedProfile[identitySystemId];
      const updated = { ...existing };
      let changed = false;
      for (const sm of selectedSubmodels) {
        const key = SUBMODEL_YAML_KEYS[sm] as keyof typeof updated;
        if (!(key in updated)) {
          (updated as Record<string, unknown>)[key] = {};
          changed = true;
        }
      }
      if (changed) set(withSync(s, { parsedProfile: { ...parsedProfile, [identitySystemId]: updated } }) as AppState);
      return;
    }

    const submodelEntries = Object.fromEntries(selectedSubmodels.map((sm) => [SUBMODEL_YAML_KEYS[sm], {}]));
    const profile: ResourceAASProfile = {
      [identitySystemId]: { idShort: identityIdShort, id: identityId, globalAssetId: identityGlobalAssetId, ...submodelEntries },
    };
    set(withSync(s, { parsedProfile: profile }) as AppState);
  },

  // ── Form actions ───────────────────────────────────────────────────────

  setActiveTab: (tab) => set({ activeTab: tab }),

  updateProfileField: (path, value) => {
    const s = get();
    if (!s.parsedProfile) return;
    const clone = JSON.parse(JSON.stringify(s.parsedProfile)) as Record<string, unknown>;
    let node: Record<string, unknown> = clone;
    for (let i = 0; i < path.length - 1; i++) {
      if (!node[path[i]] || typeof node[path[i]] !== 'object') node[path[i]] = {};
      node = node[path[i]] as Record<string, unknown>;
    }
    node[path[path.length - 1]] = value;
    set(withSync(s, { parsedProfile: clone as ResourceAASProfile }) as AppState);
  },

  updateProfileFieldForNode: (shellNodeId, path, value) => {
    const s = get();
    const ns = s.aasNodes[shellNodeId];
    if (!ns?.parsedProfile) return;
    const clone = JSON.parse(JSON.stringify(ns.parsedProfile)) as Record<string, unknown>;
    let node: Record<string, unknown> = clone;
    for (let i = 0; i < path.length - 1; i++) {
      if (!node[path[i]] || typeof node[path[i]] !== 'object') node[path[i]] = {};
      node = node[path[i]] as Record<string, unknown>;
    }
    node[path[path.length - 1]] = value;
    const updatedNs = { ...ns, parsedProfile: clone as ResourceAASProfile };
    set({
      aasNodes: { ...s.aasNodes, [shellNodeId]: updatedNs },
      ...(s.activeAasNodeId === shellNodeId ? { parsedProfile: clone as ResourceAASProfile } : {}),
    });
  },

  removeProfileEntryForNode: (shellNodeId, path) => {
    const s = get();
    const ns = s.aasNodes[shellNodeId];
    if (!ns?.parsedProfile) return;
    const clone = JSON.parse(JSON.stringify(ns.parsedProfile)) as Record<string, unknown>;
    let node: Record<string, unknown> = clone;
    for (let i = 0; i < path.length - 1; i++) {
      if (!node[path[i]] || typeof node[path[i]] !== 'object') return;
      node = node[path[i]] as Record<string, unknown>;
    }
    delete node[path[path.length - 1]];
    const updatedNs = { ...ns, parsedProfile: clone as ResourceAASProfile };
    set({
      aasNodes: { ...s.aasNodes, [shellNodeId]: updatedNs },
      ...(s.activeAasNodeId === shellNodeId ? { parsedProfile: clone as ResourceAASProfile } : {}),
    });
  },

  // ── Validation actions ─────────────────────────────────────────────────

  setValidationIssues: (issues) => set({ validationIssues: issues }),
  setValidateResult: (result) => set({ validationResult: result }),
  setLoadingValidate: (v) => set({ isLoadingValidate: v }),

  setValidationIssuesForNode: (nodeId, issues) =>
    set((s) => ({
      validationIssuesByNode: { ...s.validationIssuesByNode, [nodeId]: issues },
      ...(nodeId === s.activeAasNodeId ? { validationIssues: issues } : {}),
    })),

  setLoadingValidateForNode: (nodeId, v) =>
    set((s) => ({
      loadingValidateByNode: { ...s.loadingValidateByNode, [nodeId]: v },
      ...(nodeId === s.activeAasNodeId ? { isLoadingValidate: v } : {}),
    })),

  // ── AAS JSON builder (active AAS) ──────────────────────────────────────

  buildAasJson: () => {
    const s = get();
    const ns = extractNodeState(s);
    if (!ns.identitySystemId) return '';
    const submodels = buildSubmodels(ns);
    return buildAasEnvironment(
      ns.identityId, ns.identityIdShort, ns.identityGlobalAssetId,
      submodels, ns.identityAssetType || undefined
    );
  },

  // ── AI Generation import ───────────────────────────────────────────────

  importAasJson: (json: string) => {
    const IDSHORT_TO_KEY: Record<string, SubmodelKey> = {
      DigitalNameplate: 'Nameplate',
      HierarchicalStructures: 'HierarchicalStructures',
      AID: 'AID',
      Skills: 'Skills',
      Capabilities: 'Capabilities',
      OperationalData: 'Variables',
      Parameters: 'Parameters',
      AssetInterfacesMappingConfiguration: 'AIMC',
    };

    const parsed = parseAasJsonToProfile(json);
    if (!parsed) {
      console.error('importAasJson: failed to parse AAS JSON');
      return;
    }

    const { systemId, shellIdShort, shellId, globalAssetId, config, presentSubmodelIdShorts } = parsed;

    // Determine which SubmodelKeys are present
    const presentKeys: SubmodelKey[] = presentSubmodelIdShorts
      .filter((id) => IDSHORT_TO_KEY[id])
      .map((id) => IDSHORT_TO_KEY[id]);
    const finalKeys = [...new Set([...REQUIRED_SUBMODELS, ...presentKeys])];

    const profile: ResourceAASProfile = { [systemId]: config };

    const updates: Partial<AppState> = {
      identitySystemId: systemId,
      identityIdShort: shellIdShort,
      identityId: shellId,
      identityGlobalAssetId: globalAssetId,
      selectedSubmodels: finalKeys,
      parsedProfile: profile,
    };

    set((s) => withSync(s, updates) as AppState);
  },

  // ── Theme ──────────────────────────────────────────────────────────────

  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    set({ theme: next });
  },

  // ── Reset ──────────────────────────────────────────────────────────────

  resetAll: () => set({ ...INITIAL_STATE, aasNodes: { [INITIAL_SHELL_NODE_ID]: { ...DEFAULT_AAS_NODE_STATE } } }),
  }),
  {
    name: 'resourceaas-app',
    partialize: (s) => ({
      aasNodes: s.aasNodes,
      activeAasNodeId: s.activeAasNodeId,
      aasType: s.aasType,
      selectedSubmodels: s.selectedSubmodels,
      identitySystemId: s.identitySystemId,
      identityIdShort: s.identityIdShort,
      identityId: s.identityId,
      identityGlobalAssetId: s.identityGlobalAssetId,
      identityAssetType: s.identityAssetType,
      parsedProfile: s.parsedProfile,
      theme: s.theme,
    }),
  }
));
