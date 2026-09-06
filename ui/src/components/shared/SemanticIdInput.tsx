
interface Props {
  value: string;
  onChange: (v: string) => void;
  label?: string;
  required?: boolean;
}

// Format is enforced backend-side by the arso:*SemanticIdPatternShape SHACL shapes
// (Ontology/SHACL/Manual/arso-rules.shacl.ttl); violations surface through the
// live validation panel rather than being duplicated here.
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
