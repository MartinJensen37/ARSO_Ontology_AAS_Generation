import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';

const DEBOUNCE_MS = 400;

/**
 * Debounced validation of the active AAS whenever its data changes.
 * Results are stored per-node in validationIssuesByNode so the GuidancePanel
 * shows issues per AAS without cross-contamination.
 *
 * Watches the whole active AASNodeState, since withSync re-references it on any
 * mutation. Guards against a slow earlier request clobbering a faster later one.
 */
export function useValidation() {
  const activeAasNodeId = useAppStore((s) => s.activeAasNodeId);
  const activeNode = useAppStore((s) => s.aasNodes[s.activeAasNodeId]);
  const buildAasJsonForNode = useAppStore((s) => s.buildAasJsonForNode);
  const setValidationIssuesForNode = useAppStore((s) => s.setValidationIssuesForNode);
  const setLoadingValidateForNode = useAppStore((s) => s.setLoadingValidateForNode);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevNodeIdRef = useRef<string>('');
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    // Cancel any still-in-flight request from a previous tick so a slow
    // earlier response can't overwrite a faster later one.
    abortRef.current?.abort();

    // Switching the active AAS should validate immediately; editing the same
    // AAS's data debounces so we don't fire a request per keystroke.
    const delay = activeAasNodeId !== prevNodeIdRef.current ? 0 : DEBOUNCE_MS;
    prevNodeIdRef.current = activeAasNodeId;

    const nodeId = activeAasNodeId;

    timerRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;

      setLoadingValidateForNode(nodeId, true);
      try {
        const result = await buildAasJsonForNode(nodeId, controller.signal);
        if (controller.signal.aborted) return;
        setValidationIssuesForNode(nodeId, result?.issues ?? []);
      } catch {
        // Silently ignore (backend not running, request superseded, etc.)
      } finally {
        if (!controller.signal.aborted) setLoadingValidateForNode(nodeId, false);
      }
    }, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [activeNode, activeAasNodeId, buildAasJsonForNode, setValidationIssuesForNode, setLoadingValidateForNode]);
}
