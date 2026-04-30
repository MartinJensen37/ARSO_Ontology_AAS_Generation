import type { ValidationIssue } from '../../types/resourceaas';

interface Props {
  issue: ValidationIssue;
}

const SEVERITY_COLOR: Record<string, string> = {
  Violation: '#ef4444',
  Warning: '#f59e0b',
  Info: '#3b82f6',
};

export function GuidanceCard({ issue }: Props) {
  const color = SEVERITY_COLOR[issue.severity] ?? '#6b7280';

  return (
    <div className="guidance-card guidance-card--hint">
      <div className="guidance-card__header">
        <span className="guidance-card__badge" style={{ background: color }}>
          {issue.severity}
        </span>
        {issue.field && (
          <code className="guidance-card__field">{issue.field}</code>
        )}
      </div>
      <p className="guidance-card__desc">{issue.message}</p>
    </div>
  );
}
