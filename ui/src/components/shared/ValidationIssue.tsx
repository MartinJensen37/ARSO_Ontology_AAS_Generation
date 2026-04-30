import type { ValidationIssue as Issue } from '../../types/resourceaas';

interface Props {
  issue: Issue;
}

const SEV_COLOR: Record<string, string> = {
  Violation: '#ef4444',
  Warning: '#f59e0b',
  Info: '#3b82f6',
};

export function ValidationIssueCard({ issue }: Props) {
  const color = SEV_COLOR[issue.severity] ?? '#6b7280';

  return (
    <div className="validation-issue" style={{ borderLeftColor: color }}>
      <div className="validation-issue__header">
        <span className="validation-issue__severity" style={{ color }}>
          {issue.severity}
        </span>
        {issue.result_path && (
          <code className="validation-issue__path">{issue.result_path}</code>
        )}
      </div>
      <p className="validation-issue__message">{issue.message}</p>
      {issue.focus_node && (
        <p className="validation-issue__node">{issue.focus_node}</p>
      )}
    </div>
  );
}
