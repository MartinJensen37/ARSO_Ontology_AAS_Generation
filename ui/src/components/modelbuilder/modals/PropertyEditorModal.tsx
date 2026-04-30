import { useEffect, useState } from 'react';
import { useModelStore } from '../../../store/useModelStore';
import type { SubmodelKey } from '../../../store/useAppStore';
import { DigitalNameplateForm } from '../../submodels/DigitalNameplateForm';
import { AIDForm } from '../../submodels/AIDForm';
import { SkillsForm } from '../../submodels/SkillsForm';
import { CapabilitiesForm } from '../../submodels/CapabilitiesForm';
import { HierarchicalStructuresForm } from '../../submodels/HierarchicalStructuresForm';
import { OperationalDataForm } from '../../submodels/OperationalDataForm';
import { ParametersForm } from '../../submodels/ParametersForm';
import { AIMCForm } from '../../submodels/AIMCForm';
import { SUBMODEL_META } from '../catalogMeta';
import { AdvancedContext } from '../../shared/AdvancedContext';

const FORM_MAP: Record<SubmodelKey, React.ComponentType> = {
  Nameplate: DigitalNameplateForm,
  AID: AIDForm,
  Skills: SkillsForm,
  Capabilities: CapabilitiesForm,
  HierarchicalStructures: HierarchicalStructuresForm,
  Variables: OperationalDataForm,
  Parameters: ParametersForm,
  AIMC: AIMCForm,
};

export function PropertyEditorModal() {
  const modal = useModelStore((s) => s.modal);
  const closeModal = useModelStore((s) => s.closeModal);
  const [advanced, setAdvanced] = useState(false);

  useEffect(() => {
    if (modal.kind !== 'property') return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeModal();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [modal.kind, closeModal]);

  if (modal.kind !== 'property') return null;

  const { submodelKey } = modal;
  const FormComponent = FORM_MAP[submodelKey];
  const meta = SUBMODEL_META[submodelKey];

  return (
    <div className="mb-drawer-backdrop" onClick={closeModal}>
      <div
        className="mb-drawer"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Edit submodel"
      >
        <div className="mb-modal__header">
          <div className="mb-icon-badge" title="Submodel" style={{ background: 'var(--submodel-icon-color)' }}>SM</div>
          <h3 className="submodel-form__title">{meta.label}</h3>
          <label className="adv-toggle" title="Show AAS metadata fields">
            <input
              type="checkbox"
              checked={advanced}
              onChange={() => setAdvanced((v) => !v)}
            />
            <span className="adv-toggle__slider" />
            <span className="adv-toggle__label">Advanced</span>
          </label>
          <button
            className="mb-modal__close btn btn--ghost"
            onClick={closeModal}
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="mb-modal__body">
          <AdvancedContext.Provider value={{ advanced, submodelKey }}>
            <FormComponent />
          </AdvancedContext.Provider>
        </div>
        <div className="mb-modal__footer">
          <button className="btn btn--primary" onClick={closeModal}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
