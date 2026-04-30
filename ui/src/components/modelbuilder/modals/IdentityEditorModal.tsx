import { useEffect } from 'react';
import { useAppStore } from '../../../store/useAppStore';
import { useModelStore } from '../../../store/useModelStore';

export function IdentityEditorModal() {
  const modal = useModelStore((s) => s.modal);
  const closeModal = useModelStore((s) => s.closeModal);
  const setNodes = useModelStore((s) => s.setNodes);

  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const identityIdShort = useAppStore((s) => s.identityIdShort);
  const identityId = useAppStore((s) => s.identityId);
  const identityGlobalAssetId = useAppStore((s) => s.identityGlobalAssetId);
  const identityAssetType = useAppStore((s) => s.identityAssetType);
  const setIdentityField = useAppStore((s) => s.setIdentityField);
  const initProfileFromIdentity = useAppStore((s) => s.initProfileFromIdentity);

  useEffect(() => {
    if (modal.kind !== 'identity') return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeModal();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [modal.kind, closeModal]);

  if (modal.kind !== 'identity') return null;

  const allFilled =
    identitySystemId.trim() &&
    identityIdShort.trim() &&
    identityId.trim() &&
    identityGlobalAssetId.trim();

  // Auto-derive URI fields from systemId for convenience (same logic as AASTypeStep)
  const handleSystemId = (v: string) => {
    setIdentityField('systemId', v);
    if (!identityIdShort || identityIdShort === identitySystemId) {
      setIdentityField('idShort', v);
    }
    const base = 'https://smartproduction.aau.dk';
    if (!identityId || identityId.startsWith(`${base}/aas/`)) {
      setIdentityField('id', v ? `${base}/aas/${v}` : '');
    }
    if (!identityGlobalAssetId || identityGlobalAssetId.startsWith(`${base}/assets/`)) {
      setIdentityField('globalAssetId', v ? `${base}/assets/${v}` : '');
    }
  };

  const shellNodeId = modal.kind === 'identity' ? modal.shellNodeId : '';

  const handleSave = () => {
    initProfileFromIdentity();
    // Update the shell node label so the node title refreshes
    setNodes((prev) =>
      prev.map((n) =>
        n.id === shellNodeId ? { ...n, data: { ...n.data, label: identityIdShort } } : n
      )
    );
    closeModal();
  };

  return (
    <div className="mb-modal-overlay" onClick={closeModal}>
      <div
        className="mb-modal mb-modal--identity"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="AAS Identity"
      >
        <div className="mb-modal__header">
          <div className="mb-icon-badge mb-icon-badge--aas" title="AAS">AAS</div>
          <h2 className="mb-modal__title">AAS Identity</h2>
          <button
            className="mb-modal__close btn btn--ghost"
            onClick={closeModal}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="mb-modal__body">
          <div className="field-grid field-grid--2col">
            <div className="field-group">
              <label className="field-label">
                System ID <span className="required-star">*</span>
                <span className="field-hint"> — short slug</span>
              </label>
              <input
                className="field-input"
                value={identitySystemId}
                placeholder="MY_ASSET_001"
                onChange={(e) => handleSystemId(e.target.value)}
                autoFocus
              />
            </div>
            <div className="field-group">
              <label className="field-label">
                idShort <span className="required-star">*</span>
              </label>
              <input
                className="field-input"
                value={identityIdShort}
                placeholder="MY_ASSET_001"
                onChange={(e) => setIdentityField('idShort', e.target.value)}
              />
            </div>
            <div className="field-group">
              <label className="field-label">
                AAS URI <span className="required-star">*</span>
              </label>
              <input
                className="field-input"
                value={identityId}
                placeholder="https://smartproduction.aau.dk/aas/MY_ASSET_001"
                onChange={(e) => setIdentityField('id', e.target.value)}
              />
            </div>
            <div className="field-group">
              <label className="field-label">
                Asset URI <span className="required-star">*</span>
              </label>
              <input
                className="field-input"
                value={identityGlobalAssetId}
                placeholder="https://smartproduction.aau.dk/assets/MY_ASSET_001"
                onChange={(e) => setIdentityField('globalAssetId', e.target.value)}
              />
            </div>
            <div className="field-group" style={{ gridColumn: '1 / -1' }}>
              <label className="field-label">Asset Type IRI</label>
              <input
                className="field-input"
                value={identityAssetType}
                placeholder="https://example.com/ontology/Robot"
                onChange={(e) => setIdentityField('assetType', e.target.value)}
              />
              <span className="field-hint">
                Semantic class IRI of this asset (e.g. from CSS ontology). Emitted as <code>assetType</code> in the AAS shell.
              </span>
            </div>
          </div>
        </div>

        <div className="mb-modal__footer">
          <button className="btn btn--secondary" onClick={closeModal}>
            Cancel
          </button>
          <button
            className="btn btn--primary"
            onClick={handleSave}
            disabled={!allFilled}
          >
            Save Identity
          </button>
        </div>
      </div>
    </div>
  );
}
