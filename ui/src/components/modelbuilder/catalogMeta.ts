import { ALL_SUBMODELS, SUBMODEL_REGISTRY, type SubmodelKey } from '../../store/submodelRegistry';

export interface SubmodelMeta {
  icon: string;
  label: string;
  description: string;
  color: string;
}

// Derived from the UI submodel registry.
export const SUBMODEL_META = Object.fromEntries(
  ALL_SUBMODELS.map((key) => {
    const spec = SUBMODEL_REGISTRY[key];
    return [key, { icon: 'SM', label: spec.label, description: spec.description, color: spec.color }];
  }),
) as Record<SubmodelKey, SubmodelMeta>;
