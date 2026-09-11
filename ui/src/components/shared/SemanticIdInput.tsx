
interface Props {
  value: string;
  onChange: (v: string) => void;
  label?: string;
  required?: boolean;
}

// Format is enforced by the arso:*SemanticIdPatternShape SHACL shapes and
// surfaces through the live validation panel.
export function SemanticIdInput({ value, onChange, label = 'Semantic ID', required }: Props) {
  return (
    <div className="field-group">
      <label className="field-label">
        {label}
        {required && <span className="required-star"> *</span>}
      </label>
      <input
        type="url"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="field-input"
        placeholder="https://smartproductionlab.aau.dk/PPR/..."
      />
    </div>
  );
}
