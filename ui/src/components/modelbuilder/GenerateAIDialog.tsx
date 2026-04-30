import { Fragment, useState, useRef, useEffect } from 'react';
import { useAppStore, ALL_SUBMODELS, REQUIRED_SUBMODELS, type SubmodelKey } from '../../store/useAppStore';
import { SUBMODEL_META } from './catalogMeta';
import { useGenerateAI, type PipelineStages, type StageStatus } from '../../hooks/useGenerateAI';
import { api, type GenerateAasRequest, type GenerationConfig, type SupplementalFilePayload } from '../../api/client';

// ---------------------------------------------------------------------------
// PipelineProgress — node-based progress bar
// ---------------------------------------------------------------------------

const STAGE_DEFS: Array<{ id: keyof PipelineStages; label: string }> = [
  { id: 'preparing',  label: 'Preparing' },
  { id: 'querying',   label: 'Querying LLM' },
  { id: 'validating', label: 'Validating' },
];

function stageIcon(status: StageStatus, isActive: boolean): React.ReactNode {
  if (isActive) return <span className="pp-node__spinner" />;
  if (status === 'success')  return <span className="pp-node__check">✓</span>;
  if (status === 'warning')  return <span className="pp-node__warn">!</span>;
  if (status === 'error')    return <span className="pp-node__x">✕</span>;
  return null;
}

interface PipelineProgressProps {
  pipeline: PipelineStages;
  elapsed: number;
  provider: string;
  modelLabel: string;
}

function PipelineProgress({ pipeline, elapsed, provider, modelLabel }: PipelineProgressProps) {
  const [hovered, setHovered] = useState<keyof PipelineStages | null>(null);

  const queryingStage = pipeline.querying;
  const isRetrying = queryingStage.attempt > 1;
  const maxAttempts = queryingStage.maxAttempts || pipeline.validating.maxAttempts || 1;

  return (
    <div className="pp-wrap">
      {/* Node row */}
      <div className="pp-nodes">
        {STAGE_DEFS.map((def, i) => {
          const s = pipeline[def.id];
          const isActive = s.status === 'active';
          const hasLogs = s.logs.length > 0 || !!s.error;

          return (
            <Fragment key={def.id}>
              {i > 0 && (
                <div
                  className={`pp-arrow${s.status !== 'pending' ? ' pp-arrow--lit' : ''}`}
                  aria-hidden
                >
                  <svg width="32" height="12" viewBox="0 0 32 12">
                    <line x1="0" y1="6" x2="26" y2="6" stroke="currentColor" strokeWidth="1.5" />
                    <polyline points="20,2 26,6 20,10" fill="none" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </div>
              )}

              <div
                className={`pp-node pp-node--${s.status}${hasLogs ? ' pp-node--hoverable' : ''}`}
                onMouseEnter={() => hasLogs ? setHovered(def.id) : undefined}
                onMouseLeave={() => setHovered(null)}
              >
                <div className="pp-node__ring">
                  {stageIcon(s.status, isActive)}
                  {s.status === 'pending' && <span className="pp-node__dot" />}
                </div>
                <div className="pp-node__label">{def.label}</div>
                {def.id === 'querying' && s.attempt > 0 && (
                  <div className={`pp-node__badge${isRetrying ? ' pp-node__badge--retry' : ''}`}>
                    {isRetrying ? `↺ retry ${s.attempt}/${maxAttempts}` : `${s.attempt}/${maxAttempts}`}
                  </div>
                )}

                {/* Hover tooltip */}
                {hovered === def.id && hasLogs && (
                  <div className="pp-tooltip">
                    {s.error && (
                      <div className="pp-tooltip__error">{s.error}</div>
                    )}
                    {s.logs.length > 0 && (
                      <div className="pp-tooltip__logs">
                        {s.logs.slice(-8).map((line, j) => (
                          <div key={j} className="pp-tooltip__line">{line}</div>
                        ))}
                        {s.logs.length > 8 && (
                          <div className="pp-tooltip__more">+{s.logs.length - 8} more lines</div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Fragment>
          );
        })}
      </div>

      {/* Retry arc — shown below nodes when querying is active on attempt ≥ 2 */}
      {isRetrying && pipeline.querying.status === 'active' && (
        <div className="pp-retry-arc" aria-label={`Retry attempt ${queryingStage.attempt} of ${maxAttempts}`}>
          <div className="pp-retry-arc__line" />
          <span className="pp-retry-arc__label">↺ retry — validation failed, sending corrected prompt</span>
        </div>
      )}

      <div className="pp-footer">
        <span className="pp-footer__info">{provider} · {modelLabel} · {elapsed}s elapsed</span>
        <span className="pp-footer__hint">Hover a node to see its logs</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// GenerateAIDialog
// ---------------------------------------------------------------------------

const MODE_LABELS: Record<string, string> = {
  'json-description': 'Profile JSON → AAS (recommended)',
  'json': 'Direct AAS JSON',
};

interface GenerateAIDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (aasJson: string) => void;
}

interface UploadedSpecFile {
  id: string;
  name: string;
  mimeType: string;
  size: number;
  contentBase64: string;
}

export function GenerateAIDialog({ isOpen, onClose, onImport }: GenerateAIDialogProps) {
  const identitySystemId = useAppStore((s) => s.identitySystemId);
  const identityId = useAppStore((s) => s.identityId);

  const defaultBaseUrl = identityId
    ? (() => { try { return new URL(identityId).origin; } catch { return 'https://smartproductionlab.aau.dk'; } })()
    : 'https://smartproductionlab.aau.dk';

  // --- Asset fields ---
  const [specSheetText, setSpecSheetText] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedSpecFile[]>([]);
  const [assetName, setAssetName] = useState(identitySystemId || '');
  const [baseUrl, setBaseUrl] = useState(defaultBaseUrl);
  const [selectedSubmodels, setSelectedSubmodels] = useState<SubmodelKey[]>([...REQUIRED_SUBMODELS]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Generation options ---
  const [genConfig, setGenConfig] = useState<GenerationConfig | null>(null);
  const [provider, setProvider] = useState<string>('gemini');
  const [model, setModel] = useState<string>('');
  const [generationMode, setGenerationMode] = useState<string>('json-description');
  const [useRag, setUseRag] = useState(false);
  const [useExample, setUseExample] = useState(false);
  const [forceFullOutput, setForceFullOutput] = useState(true);
  const [maxPdfChars, setMaxPdfChars] = useState<number | null>(8000);
  const [maxAttempts, setMaxAttempts] = useState(2);
  const [showAdvanced, setShowAdvanced] = useState(true);

  // --- UI state ---
  const { status, result, errorMsg, logs, pipeline, generate, reset } = useGenerateAI();
  const [elapsed, setElapsed] = useState(0);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Load generation config (providers/models) when dialog opens
  // NOTE: use_rag and use_example always default to false regardless of config
  useEffect(() => {
    if (!isOpen) return;
    api.getGenerationConfig()
      .then((cfg) => {
        setGenConfig(cfg);
        if (cfg.defaults.provider) setProvider(String(cfg.defaults.provider));
        if (cfg.defaults.max_pdf_chars !== undefined) setMaxPdfChars(cfg.defaults.max_pdf_chars as number | null);
        if (cfg.defaults.max_attempts !== undefined) setMaxAttempts(Number(cfg.defaults.max_attempts));
        // intentionally NOT applying use_rag / use_example defaults — always start unchecked
      })
      .catch(() => {/* use built-in defaults */});
  }, [isOpen]);

  // Reset model when provider changes
  useEffect(() => { setModel(''); }, [provider]);

  // Elapsed timer
  useEffect(() => {
    if (status !== 'loading') { setElapsed(0); return; }
    setElapsed(0);
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [status]);

  // Auto-scroll live log
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (!isOpen) return null;

  const providerOptions = genConfig?.providers ?? ['gemini', 'groq'];
  const availableModels = genConfig?.models[provider] ?? [];
  const modelLabel = model || availableModels[0] || '(default)';

  const toggleSubmodel = (key: SubmodelKey) => {
    if (REQUIRED_SUBMODELS.includes(key)) return;
    setSelectedSubmodels((prev) =>
      prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key],
    );
  };

  const fileToBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = String(reader.result || '');
        const encoded = dataUrl.includes(',') ? dataUrl.split(',')[1] : '';
        resolve(encoded);
      };
      reader.onerror = () => reject(new Error(`Failed to read file: ${file.name}`));
      reader.readAsDataURL(file);
    });

  const handleFilesChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    const prepared = await Promise.all(files.map(async (file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      mimeType: file.type || 'application/octet-stream',
      size: file.size,
      contentBase64: await fileToBase64(file),
    })));

    setUploadedFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}|${f.size}`));
      const uniqueNew = prepared.filter((f) => !seen.has(`${f.name}|${f.size}`));
      return [...prev, ...uniqueNew];
    });

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleClearFiles = () => {
    setUploadedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const canGenerate = specSheetText.trim().length > 0 || uploadedFiles.length > 0;

  const handleGenerate = async () => {
    if (!canGenerate) return;
    const supplementalFiles: SupplementalFilePayload[] = uploadedFiles.map((f) => ({
      file_name: f.name,
      mime_type: f.mimeType,
      content_base64: f.contentBase64,
    }));

    const req: GenerateAasRequest = {
      asset_name: assetName.replace(/\s+/g, '') || 'UnknownAsset',
      base_url: baseUrl || 'https://smartproductionlab.aau.dk',
      selected_submodels: selectedSubmodels,
      spec_sheet_text: specSheetText,
      supplemental_files: supplementalFiles,
      provider,
      model: model || undefined,
      generation_mode: generationMode,
      use_rag: useRag,
      use_example: useExample,
      force_full_aas_output: forceFullOutput,
      max_pdf_chars: maxPdfChars,
      max_attempts: maxAttempts,
    };
    await generate(req);
  };

  const handleDownload = () => {
    if (!result?.aas_json) return;
    const blob = new Blob([result.aas_json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${assetName || 'aas'}.aas.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    if (result?.aas_json) onImport(result.aas_json);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const isLoading = status === 'loading';
  const hasResult = status === 'success' || status === 'partial';

  return (
    <div className="mb-modal-overlay" onClick={handleClose}>
      <div className="mb-modal generate-ai-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="mb-modal__header">
          <span className="mb-modal__icon">✦</span>
          <h2 className="mb-modal__title">Generate AAS with AI</h2>
          <button className="btn btn--ghost btn--xs mb-modal__close" onClick={handleClose} disabled={isLoading}>✕</button>
        </div>

        <div className="mb-modal__body">

          {/* ===== CONFIG FORM (hidden while loading / after result) ===== */}
          {!isLoading && !hasResult && (
            <>
              <div className="form-row">
                <label className="form-label">Asset Name</label>
                <input className="form-input" type="text" placeholder="e.g. DispensingModule"
                  value={assetName} onChange={(e) => setAssetName(e.target.value)} />
              </div>

              <div className="form-row">
                <label className="form-label">Base URL</label>
                <input className="form-input" type="text" placeholder="https://smartproductionlab.aau.dk"
                  value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
              </div>

              {/* ---- Generation options ---- */}
              <div className="generate-ai-section-divider">
                <button type="button" className="btn btn--ghost btn--xs generate-ai-advanced-toggle"
                  onClick={() => setShowAdvanced((v) => !v)}>
                  {showAdvanced ? '▾' : '▸'} Generation Options
                </button>
              </div>

              {showAdvanced && (
                <div className="generate-ai-advanced">
                  {/* Provider */}
                  <div className="form-row form-row--inline">
                    <label className="form-label">Provider</label>
                    <div className="generate-ai-radio-group">
                      {providerOptions.map((p) => (
                        <label key={p} className={`generate-ai-radio${provider === p ? ' generate-ai-radio--active' : ''}`}>
                          <input type="radio" name="provider" value={p} checked={provider === p}
                            onChange={() => setProvider(p)} />
                          {p}
                        </label>
                      ))}
                    </div>
                  </div>

                  {provider === 'claude' && (
                    <div className="form-row form-row--inline">
                      <label className="form-label">Claude Auth</label>
                      <span className="form-hint">Uses local Claude CLI authentication/session on the backend host.</span>
                    </div>
                  )}

                  {/* Model */}
                  <div className="form-row form-row--inline">
                    <label className="form-label">Model</label>
                    {availableModels.length > 0 ? (
                      <select className="form-input form-input--select" value={model}
                        onChange={(e) => setModel(e.target.value)}>
                        <option value="">Default ({availableModels[0]})</option>
                        {availableModels.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                    ) : (
                      <input className="form-input" type="text" placeholder="e.g. claude-opus-4-5-20251101"
                        value={model} onChange={(e) => setModel(e.target.value)} />
                    )}
                  </div>

                  {/* Generation mode */}
                  <div className="form-row form-row--inline">
                    <label className="form-label">Generation Mode</label>
                    <select className="form-input form-input--select" value={generationMode}
                      onChange={(e) => setGenerationMode(e.target.value)}>
                      {Object.entries(MODE_LABELS).map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                      ))}
                    </select>
                  </div>

                  {/* Max attempts */}
                  <div className="form-row form-row--inline">
                    <label className="form-label">Max Attempts</label>
                    <input className="form-input form-input--narrow" type="number" min={1} max={5}
                      value={maxAttempts}
                      onChange={(e) => setMaxAttempts(Math.max(1, Math.min(5, Number(e.target.value))))} />
                    <span className="form-hint">retries on SHACL failure</span>
                  </div>

                  {/* Max file chars */}
                  <div className="form-row form-row--inline">
                    <label className="form-label">Max file chars</label>
                    <input className="form-input form-input--narrow" type="number" min={0} step={1000}
                      value={maxPdfChars ?? ''} placeholder="unlimited"
                      onChange={(e) => setMaxPdfChars(e.target.value === '' ? null : Number(e.target.value))} />
                    <span className="form-hint">text extraction cap per file (blank = no limit)</span>
                  </div>

                  {/* Toggles */}
                  <div className="form-row generate-ai-toggles">
                    <label className="generate-ai-toggle">
                      <input type="checkbox" checked={useRag} onChange={(e) => setUseRag(e.target.checked)} />
                      Use RAG files (generation/RAG/ folder)
                    </label>
                    <label className="generate-ai-toggle">
                      <input type="checkbox" checked={useExample} onChange={(e) => setUseExample(e.target.checked)} />
                      Include valid example JSON in context (~4k tokens)
                    </label>
                    <label className="generate-ai-toggle">
                      <input type="checkbox" checked={forceFullOutput} onChange={(e) => setForceFullOutput(e.target.checked)} />
                      Save full AAS output even when validation fails
                    </label>
                  </div>
                </div>
              )}

              <div className="form-row">
                <label className="form-label">Submodels to Generate</label>
                <div className="submodel-checkbox-grid">
                  {ALL_SUBMODELS.map((key) => {
                    const meta = SUBMODEL_META[key];
                    const required = REQUIRED_SUBMODELS.includes(key);
                    const checked = selectedSubmodels.includes(key);
                    return (
                      <label key={key}
                        className={`submodel-checkbox-item${required ? ' submodel-checkbox-item--required' : ''}${checked ? ' submodel-checkbox-item--checked' : ''}`}>
                        <input type="checkbox" checked={checked} disabled={required}
                          onChange={() => toggleSubmodel(key)} />
                        <span className="submodel-checkbox-dot" style={{ background: meta.color }} />
                        <span className="submodel-checkbox-label">{meta.label}</span>
                        {required && <span className="submodel-checkbox-required">required</span>}
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Multi-file upload */}
              <div className="form-row">
                <label className="form-label">Specification Files (multi-format)</label>

                <div className="generate-ai-pdf-upload">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.xml,.nodeset,.nodeset2,.json,.yaml,.yml,.txt,.csv"
                    onChange={handleFilesChange}
                    id="supp-files-upload"
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="supp-files-upload" className="btn btn--ghost btn--sm generate-ai-pdf-label">
                    Add Files
                  </label>
                  <span className="generate-ai-pdf-hint">OPC-UA NodeSet XML/NodeSet2, JSON, PDF, text, etc.</span>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="generate-ai-files-list">
                    {uploadedFiles.map((f) => (
                      <div key={f.id} className="generate-ai-pdf-selected">
                        <span className="generate-ai-pdf-name" title={`${f.name} (${Math.ceil(f.size / 1024)} KB)`}>
                          📄 {f.name}
                        </span>
                        <button className="btn btn--ghost btn--xs" onClick={() => handleRemoveFile(f.id)} type="button">
                          ✕ Remove
                        </button>
                      </div>
                    ))}
                    <button className="btn btn--ghost btn--xs" onClick={handleClearFiles} type="button">
                      Clear All Files
                    </button>
                  </div>
                )}
              </div>

              <div className="form-row">
                <label className="form-label">
                  {uploadedFiles.length > 0 ? 'Additional Notes (optional)' : 'Paste Specification Text'}
                </label>
                <textarea className="form-textarea form-textarea--large"
                  placeholder={uploadedFiles.length > 0
                    ? 'Optional: add notes or highlight specific details for the AI...'
                    : 'Paste the component spec sheet, datasheet, or description here.'}
                  value={specSheetText} onChange={(e) => setSpecSheetText(e.target.value)}
                  rows={uploadedFiles.length > 0 ? 3 : 8} />
              </div>

              {status === 'error' && (
                <div className="generate-ai-error">
                  <strong>Error:</strong> {errorMsg}
                </div>
              )}
            </>
          )}

          {/* ===== LOADING — pipeline progress nodes ===== */}
          {isLoading && (
            <div className="generate-ai-loading">
              <PipelineProgress
                pipeline={pipeline}
                elapsed={elapsed}
                provider={provider}
                modelLabel={modelLabel}
              />

              {/* Live log — always visible during loading */}
              {logs.length > 0 && (
                <div className="generate-ai-log">
                  {logs.map((line, i) => (
                    <div key={i} className="generate-ai-log__line">{line}</div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          )}

          {/* ===== RESULT ===== */}
          {hasResult && result && (
            <div className="generate-ai-result">
              {/* Final pipeline state (compact) */}
              <PipelineProgress
                pipeline={pipeline}
                elapsed={elapsed}
                provider={provider}
                modelLabel={modelLabel}
              />

              {status === 'success' ? (
                <div className="generate-ai-result__success">
                  <span className="generate-ai-result__icon">✓</span>
                  <div>
                    <strong>Generated and validated successfully</strong>
                    <p>Completed in {result.attempts} attempt{result.attempts !== 1 ? 's' : ''}. The AAS JSON is SHACL-compliant.</p>
                  </div>
                </div>
              ) : (
                <div className="generate-ai-result__partial">
                  <span className="generate-ai-result__icon generate-ai-result__icon--warn">!</span>
                  <div>
                    <strong>Generated but not fully validated ({result.attempts} attempt{result.attempts !== 1 ? 's' : ''})</strong>
                    <p>The AAS JSON has remaining validation issues. You can still import it and fix manually.</p>
                  </div>
                </div>
              )}

              {result.issues.length > 0 && (
                <div className="generate-ai-issues">
                  <strong>Remaining issues:</strong>
                  <ul>
                    {result.issues.map((issue, i) => (
                      <li key={i} className={`generate-ai-issue generate-ai-issue--${issue.severity.toLowerCase()}`}>
                        <span className="generate-ai-issue__field">{issue.field || 'general'}</span>
                        {issue.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Full log (collapsible) */}
              {logs.length > 0 && (
                <details className="generate-ai-log-details">
                  <summary>Full generation log ({logs.length} lines)</summary>
                  <div className="generate-ai-log generate-ai-log--compact">
                    {logs.map((line, i) => (
                      <div key={i} className="generate-ai-log__line">{line}</div>
                    ))}
                  </div>
                </details>
              )}

              <div className="generate-ai-result__preview">
                <strong>Generated AAS JSON:</strong>
                <pre className="generate-ai-result__json" style={{ maxHeight: '240px', overflowY: 'auto', fontSize: '0.72rem' }}>
                  {result.aas_json}
                </pre>
              </div>

              <button className="btn btn--ghost btn--sm" onClick={reset}>
                ← Generate Again
              </button>
            </div>
          )}
        </div>

        <div className="mb-modal__footer">
          <button className="btn btn--ghost" onClick={handleClose} disabled={isLoading}>
            Cancel
          </button>
          {!isLoading && !hasResult && (
            <button className="btn btn--primary" onClick={handleGenerate} disabled={!canGenerate}>
              Generate
            </button>
          )}
          {hasResult && (
            <>
              <button className="btn btn--ghost" onClick={handleDownload}>🡫 Download JSON</button>
              <button className="btn btn--primary" onClick={handleImport}>
                {status === 'success' ? 'Import to Canvas' : 'Import Anyway'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
