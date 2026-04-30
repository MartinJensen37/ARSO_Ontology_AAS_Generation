import { useState, useEffect } from 'react';

interface Props {
  label: string;
  value: string;
  /** Immediate update — use for editable advanced fields (id, semanticId overrides). */
  onChange?: (value: string) => void;
  /** Blur-commit rename — use when value IS the item key (idShort rename). */
  onRename?: (newName: string) => void;
}

/** Inline advanced metadata field. Editable if onChange or onRename is provided. */
export function AdvField({ label, value, onChange, onRename }: Props) {
  const [localValue, setLocalValue] = useState(value);
  const [copied, setCopied] = useState(false);

  // Sync when external value changes (e.g. after rename completes)
  useEffect(() => { setLocalValue(value); }, [value]);

  const copy = () => {
    navigator.clipboard.writeText(onRename ? localValue : value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const isEditable = onChange || onRename;

  return (
    <div className="adv-field">
      <span className="adv-field__label">{label}</span>
      {isEditable ? (
        <input
          className="field-input field-input--adv"
          value={onRename ? localValue : value}
          onChange={(e) => {
            if (onRename) setLocalValue(e.target.value);
            else onChange?.(e.target.value);
          }}
          onBlur={() => {
            if (onRename && localValue && localValue !== value) {
              onRename(localValue);
            }
          }}
        />
      ) : (
        <span className="adv-field__value" title={value}>{value}</span>
      )}
      <button className="adv-field__copy" type="button" onClick={copy} title="Copy">
        {copied ? '✓' : '⎘'}
      </button>
    </div>
  );
}
