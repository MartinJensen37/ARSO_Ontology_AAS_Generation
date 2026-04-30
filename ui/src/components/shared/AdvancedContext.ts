import { createContext, useContext } from 'react';
import type { SubmodelKey } from '../../store/useAppStore';

export interface AdvancedContextValue {
  advanced: boolean;
  submodelKey: SubmodelKey;
}

export const AdvancedContext = createContext<AdvancedContextValue>({
  advanced: false,
  submodelKey: 'AID',
});

export const useAdvanced = () => useContext(AdvancedContext);
