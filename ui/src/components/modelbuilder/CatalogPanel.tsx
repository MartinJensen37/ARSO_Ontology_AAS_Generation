import { useState, useRef } from 'react';
import { useAppStore, ALL_SUBMODELS, REQUIRED_SUBMODELS, type SubmodelKey } from '../../store/useAppStore';
import { useModelStore, createShellNodeId } from '../../store/useModelStore';
import { SUBMODEL_META } from './catalogMeta';

const MIN_WIDTH = 160;
const MAX_WIDTH = 420;
const DEFAULT_WIDTH = 230;

export function CatalogPanel() {
  const addAasNode = useAppStore((s) => s.addAasNode);
  const addShellNode = useModelStore((s) => s.addShellNode);

  const [panelWidth, setPanelWidth] = useState(DEFAULT_WIDTH);
  const isDragging = useRef(false);

  const onResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    const startX = e.clientX;
    const startW = panelWidth;

    const onMouseMove = (me: MouseEvent) => {
      if (!isDragging.current) return;
      setPanelWidth(Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startW + (me.clientX - startX))));
    };

    const onMouseUp = () => {
      isDragging.current = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onDragStartSubmodel = (e: React.DragEvent, key: SubmodelKey) => {
    e.dataTransfer.setData('application/submodel-key', key);
    e.dataTransfer.effectAllowed = 'move';
  };

  const onDragStartAas = (e: React.DragEvent) => {
    e.dataTransfer.setData('application/aas-shell', 'new');
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleAddAas = () => {
    const shellNodeId = createShellNodeId();
    addAasNode(shellNodeId);
    addShellNode(shellNodeId);
  };

  return (
    <aside className="mb-catalog" style={{ width: panelWidth }}>
      {/* Right-edge resize handle */}
      <div className="mb-catalog__resize" onMouseDown={onResizeMouseDown} />

      <div className="mb-catalog__inner">
        {/* ── AAS section (compact, no flex growth) ── */}
        <div className="mb-catalog__section">
          <div className="mb-catalog__header">AAS Catalog</div>
          <div className="mb-catalog__list mb-catalog__list--compact">
            <div
              className="mb-catalog__tile mb-catalog__tile--aas"
              draggable
              onDragStart={onDragStartAas}
              onClick={handleAddAas}
              title="Drag or click to add a new Asset Administration Shell"
            >
              <div className="mb-catalog__tile-icon">
                <div className="mb-icon-badge mb-icon-badge--aas" title="AAS">AAS</div>
              </div>
              <div className="mb-catalog__tile-body">
                <span className="mb-catalog__tile-label">Asset Administration Shell</span>
                <span className="mb-catalog__tile-desc">Add a new AAS to the canvas</span>
              </div>
              <span className="mb-catalog__tile-badge mb-catalog__tile-badge--add">+ Add</span>
            </div>
          </div>
        </div>

        {/* ── Submodel section (fills remaining height, scrollable) ── */}
        <div className="mb-catalog__section mb-catalog__section--grow">
          <div className="mb-catalog__header">Submodel Catalog</div>
          <div className="mb-catalog__list">
            {ALL_SUBMODELS.map((key) => {
              const meta = SUBMODEL_META[key];
              const isRequired = REQUIRED_SUBMODELS.includes(key);

              return (
                <div
                  key={key}
                  className={`mb-catalog__tile${isRequired ? ' mb-catalog__tile--required' : ''}`}
                  draggable
                  onDragStart={(e) => onDragStartSubmodel(e, key)}
                  title={`Drag onto an AAS node to add ${meta.label}`}
                >
                  <div className="mb-catalog__tile-icon">
                    <div className="mb-icon-badge" title="Submodel">SM</div>
                  </div>
                  <div className="mb-catalog__tile-body">
                    <span className="mb-catalog__tile-label">{meta.label}</span>
                    <span className="mb-catalog__tile-desc">{meta.description}</span>
                  </div>
                  {isRequired && (
                    <span className="mb-catalog__tile-badge">Required</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
