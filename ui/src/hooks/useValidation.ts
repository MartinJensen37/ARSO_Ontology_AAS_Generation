import { useEffect, useRef } from 'react';
import { api } from '../api/client';
import { useAppStore } from '../store/useAppStore';

const DEBOUNCE_MS = 400;

/**
 * Validates only the currently active AAS whenever its data changes (debounced).
 * Results are stored per-node in validationIssuesByNode so the GuidancePanel
 * can show issues per AAS without cross-contamination.
 */
export function useValidation() {
  const parsedProfile = useAppStore((s) => s.parsedProfile);
  const selectedSubmodels = useAppStore((s) => s.selectedSubmodels);
  const activeAasNodeId = useAppStore((s) => s.activeAasNodeId);
  const buildAasJsonForNode = useAppStore((s) => s.buildAasJsonForNode);
  const setValidationIssuesForNode = useAppStore((s) => s.setValidationIssuesForNode);
  const setLoadingValidateForNode = useAppStore((s) => s.setLoadingValidateForNode);
  const setValidateResult = useAppStore((s) => s.setValidateResult);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevDataKeyRef = useRef<string>('');

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    // Key covers data + which node is active — switching nodes triggers re-validate
    const dataKey = JSON.stringify({ parsedProfile, selectedSubmodels, activeAasNodeId });
    const delay = dataKey !== prevDataKeyRef.current ? DEBOUNCE_MS : 0;
    prevDataKeyRef.current = dataKey;

    const nodeId = activeAasNodeId;

    timerRef.current = setTimeout(async () => {
      setLoadingValidateForNode(nodeId, true);
      try {
        const json = buildAasJsonForNode(nodeId);
        if (!json) {
          setValidationIssuesForNode(nodeId, []);
          return;
        }
        const result = await api.validate(json);
        setValidateResult(result);
        setValidationIssuesForNode(nodeId, result.issues);
      } catch {
        // Silently ignore (backend not running, etc.)
      } finally {
        setLoadingValidateForNode(nodeId, false);
      }
    }, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [parsedProfile, selectedSubmodels, activeAasNodeId, buildAasJsonForNode, setValidationIssuesForNode, setLoadingValidateForNode, setValidateResult]);
}
