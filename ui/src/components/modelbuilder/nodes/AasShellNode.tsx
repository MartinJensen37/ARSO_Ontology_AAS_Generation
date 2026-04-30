import { memo, useCallback, useEffect, useState } from 'react';
import { Handle, Position, NodeResizeControl, type NodeProps } from '@xyflow/react';
import { useAppStore, DEFAULT_AAS_NODE_STATE } from '../../../store/useAppStore';
import { useModelStore } from '../../../store/useModelStore';

export const AasShellNode = memo(function AasShellNode({ id, selected }: NodeProps) {
  const aasNodes = useAppStore((s) => s.aasNodes);
  const setActiveAasNode = useAppStore((s) => s.setActiveAasNode);
  const buildAasJsonForNode = useAppStore((s) => s.buildAasJsonForNode);
  const resetAasNode = useAppStore((s) => s.resetAasNode);
  const openIdentityModal = useModelStore((s) => s.openIdentityModal);
  const removeNodeById = useModelStore((s) => s.removeNodeById);
  const removeAasNode = useAppStore((s) => s.removeAasNode);

  // Shift key → lock aspect ratio while resizing
  const [keepAspectRatio, setKeepAspectRatio] = useState(false);
  useEffect(() => {
    const onDown = (e: KeyboardEvent) => { if (e.key === 'Shift') setKeepAspectRatio(true); };
    const onUp   = (e: KeyboardEvent) => { if (e.key === 'Shift') setKeepAspectRatio(false); };
    window.addEventListener('keydown', onDown);
    window.addEventListener('keyup',   onUp);
    return () => {
      window.removeEventListener('keydown', onDown);
      window.removeEventListener('keyup',   onUp);
    };
  }, []);

  const ns = aasNodes[id] ?? DEFAULT_AAS_NODE_STATE;
  const { identityIdShort, identityId, identitySystemId } = ns;
  const isConfigured = Boolean(identitySystemId.trim());

  const handleDoubleClick = useCallback(() => {
    setActiveAasNode(id);
    openIdentityModal(id);
  }, [id, setActiveAasNode, openIdentityModal]);

  const handleExport = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setActiveAasNode(id);
    const json = buildAasJsonForNode(id);
    if (!json) return;
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${identitySystemId || 'resourceaas'}.aas.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [id, identitySystemId, buildAasJsonForNode, setActiveAasNode]);

  const handleReset = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Reset AAS "${identityIdShort || id}"? All data for this AAS will be cleared.`)) return;
    resetAasNode(id);
  }, [id, identityIdShort, resetAasNode]);

  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete AAS "${identityIdShort || id}"? This cannot be undone.`)) return;
    removeAasNode(id);
    removeNodeById(id);
  }, [id, identityIdShort, removeAasNode, removeNodeById]);

  return (
    <>
      {/* Single resize handle — bottom-right corner only */}
      <NodeResizeControl
        position="bottom-right"
        minWidth={300}
        minHeight={200}
        keepAspectRatio={keepAspectRatio}
        style={{ background: 'transparent', border: 'none' }}
      >
        <div className={`mb-resize-corner${selected ? ' mb-resize-corner--selected' : ''}`} />
      </NodeResizeControl>

      <div
        className="mb-shell-container"
        onDoubleClick={handleDoubleClick}
        style={{ position: 'relative', '--node-color': 'var(--aas-color)' } as React.CSSProperties}
      >
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div className="mb-shell-info-bar">
            {/* Identity info */}
            <div className="mb-shell-info-left">
              <div className="mb-icon-badge mb-icon-badge--aas" title="AAS">AAS</div>
              <div style={{ minWidth: 0 }}>
                <div className="mb-shell-info-title">
                  {identityIdShort || (<em style={{ color: 'var(--text-muted)' }}>Double-click to configure</em>)}
                </div>
                {isConfigured && identityId && (
                  <div className="mb-shell-id" title={identityId}>
                    {identityId.length > 56 ? `…${identityId.slice(-52)}` : identityId}
                  </div>
                )}
              </div>
            </div>

            {/* Action buttons + drag grip */}
            <div className="mb-shell-info-actions">
              <button
                className="btn btn--ghost btn--xs"
                onClick={handleExport}
                disabled={!isConfigured}
                title={isConfigured ? 'Export this AAS as JSON' : 'Set identity first'}
              >
                🡫 Export
              </button>
              <button
                className="btn btn--ghost btn--xs"
                onClick={handleReset}
                title="Reset this AAS data"
              >
                ↺ Reset
              </button>
              {id !== 'aas-shell' && (
                <button
                  className="btn btn--ghost btn--xs btn--danger"
                  onClick={handleDelete}
                  title="Delete this AAS"
                >
                  ✖
                </button>
              )}

              {/* Drag handle — restricted drag zone */}
              <div className="mb-drag-handle" title="Drag to move">
                <svg width="13" height="16" viewBox="0 0 10 16" fill="currentColor" aria-hidden="true">
                  <circle cx="2.5" cy="2.5"  r="1.5" />
                  <circle cx="7.5" cy="2.5"  r="1.5" />
                  <circle cx="2.5" cy="8"    r="1.5" />
                  <circle cx="7.5" cy="8"    r="1.5" />
                  <circle cx="2.5" cy="13.5" r="1.5" />
                  <circle cx="7.5" cy="13.5" r="1.5" />
                </svg>
              </div>
            </div>
          </div>

          <div className="mb-shell-container__body" />
        </div>

        <Handle type="source" position={Position.Right} id="shell-out" style={{ opacity: 0 }} />
      </div>
    </>
  );
});
