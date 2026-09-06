import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';

const DEBOUNCE_MS = 400;

/**
 * Validates only the currently active AAS whenever its data changes (debounced).
 * Results are stored per-node in validationIssuesByNode so the GuidancePanel
 * can show issues per AAS without cross-contamination.
 *
 * buildAasJsonForNode now builds AND validates in one round trip to the
 * server (POST /api/profile-to-aas) — there is no separate local build step
 * any more, so this hook's only job is debouncing + guarding against a slow
 * earlier request clobbering a faster later one.
 *
 * Watches the *entire* active AASNodeState object (aasNodes[activeAasNodeId])
 * rather than a hand-picked subset of its fields. useAppStore's withSync
 * helper gives that object a new reference on every mutation that touches
 * it — identity fields (idShort/id/globalAssetId/assetType), selectedSubmodels
 * (including submodel add/remove/delete), and parsedProfile content all flow
 * through it — so this fires on any change to the active AAS, not just edits
 * to profile fields.
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
