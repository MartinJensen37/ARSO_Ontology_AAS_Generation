import { useState, useRef } from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { ValidationIssue } from '../../types/resourceaas';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface Props {
  currentStepId?: string;
}

const SEVERITY_ICON: Record<string, string> = {
  Violation: '✕',
  Warning: '⚠',
  Info: 'ℹ',
};

const SEVERITY_CLASS: Record<string, string> = {
  Violation: 'gl-line--violation',
  Warning: 'gl-line--warning',
  Info: 'gl-line--info',
};

interface AnnotatedIssue extends ValidationIssue {
  nodeId: string;
  nodeLabel: string;
}

const MIN_HEIGHT = 80;
const MAX_HEIGHT = 600;
const DEFAULT_HEIGHT = 180;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function GuidancePanel(_props: Props) {
  const aasNodes = useAppStore((s) => s.aasNodes);
  const validationIssuesByNode = useAppStore((s) => s.validationIssuesByNode);
  const loadingValidateByNode = useAppStore((s) => s.loadingValidateByNode);

  const [filterNodeId, setFilterNodeId] = useState<string>('all');
  const [barHeight, setBarHeight] = useState(DEFAULT_HEIGHT);
  const isDragging = useRef(false);

  const nodeEntries = Object.entries(aasNodes).filter(([, ns]) => ns.identitySystemId);
  const nodeLabel = (nodeId: string) => {
    const ns = aasNodes[nodeId];
    return ns?.identityIdShort || ns?.identitySystemId || nodeId;
  };

  const allAnnotated: AnnotatedIssue[] = nodeEntries.flatMap(([nodeId]) =>
    (validationIssuesByNode[nodeId] ?? []).map((issue) => ({
      ...issue,
      nodeId,
      nodeLabel: nodeLabel(nodeId),
    }))
  );

  const visibleIssues: AnnotatedIssue[] =
    filterNodeId === 'all'
      ? allAnnotated
      : allAnnotated.filter((i) => i.nodeId === filterNodeId);

  const isAnyLoading =
    filterNodeId === 'all'
      ? Object.values(loadingValidateByNode).some(Boolean)
      : Boolean(loadingValidateByNode[filterNodeId]);

  const violationCount = visibleIssues.filter((i) => i.severity === 'Violation').length;
  const warningCount = visibleIssues.filter((i) => i.severity === 'Warning').length;

  const onResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    const startY = e.clientY;
    const startH = barHeight;

    const onMouseMove = (me: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = startY - me.clientY; // drag up = taller
      setBarHeight(Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, startH + delta)));
    };

    const onMouseUp = () => {
      isDragging.current = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div className="gl-bar" style={{ height: barHeight }}>
      <div className="gl-resize-handle" onMouseDown={onResizeMouseDown} />

      <div className="gl-bar__header">
        <span className="gl-bar__title">Validation Log</span>

        {violationCount > 0 && (
          <span className="gl-badge gl-badge--violation">{violationCount} violation{violationCount !== 1 ? 's' : ''}</span>
        )}
        {warningCount > 0 && (
          <span className="gl-badge gl-badge--warning">{warningCount} warning{warningCount !== 1 ? 's' : ''}</span>
        )}
        {violationCount === 0 && warningCount === 0 && !isAnyLoading && nodeEntries.length > 0 && (
          <span className="gl-badge gl-badge--ok">All clear</span>
        )}

        <span className="gl-bar__spacer" />

        {isAnyLoading && <span className="gl-spinner" title="Validating…" />}

        {nodeEntries.length > 1 && (
          <select
            className="gl-bar__filter"
            value={filterNodeId}
            onChange={(e) => setFilterNodeId(e.target.value)}
          >
            <option value="all">All AASes</option>
            {nodeEntries.map(([nodeId]) => (
              <option key={nodeId} value={nodeId}>{nodeLabel(nodeId)}</option>
            ))}
          </select>
        )}
      </div>

      <div className="gl-bar__lines">
        {!isAnyLoading && visibleIssues.length === 0 && (
          <span className="gl-bar__empty">
            {nodeEntries.length === 0
              ? 'Add and configure an AAS to see validation results.'
              : 'No issues — all validated AASes look good.'}
          </span>
        )}

        {visibleIssues.map((issue, i) => (
          <div key={i} className={`gl-line ${SEVERITY_CLASS[issue.severity] ?? 'gl-line--info'}`}>
            <span className="gl-line__icon">{SEVERITY_ICON[issue.severity] ?? 'ℹ'}</span>
            {nodeEntries.length > 1 && (
              <span className="gl-line__aas">{issue.nodeLabel}</span>
            )}
            <span className="gl-line__msg">{issue.message}</span>
            {issue.field && (
              <span className="gl-line__field">{issue.field}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
