
const SEMANTIC_URI_PATTERN = /^https?:\/\/smartproductionlab\.aau\.dk\//;

interface Props {
  value: string;
  onChange: (v: string) => void;
  label?: string;
  required?: boolean;
}

export function SemanticIdInput({ value, onChange, label = 'Semantic ID', required }: Props) {
  const isValid = !value || SEMANTIC_URI_PATTERN.test(value);

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
        className={`field-input${!isValid ? ' field-input--error' : ''}`}
        placeholder="https://smartproductionlab.aau.dk/PPR/..."
      />
      {!isValid && (
        <span className="field-error">
          URI must start with https://smartproductionlab.aau.dk/
        </span>
      )}
    </div>
  );
}
