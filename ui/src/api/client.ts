import type { ValidateResponse, ValidationIssue } from '../types/resourceaas';

const BASE = '/api';

async function post<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Generation config (providers + model lists from config.yaml)
// ---------------------------------------------------------------------------

export interface GenerationConfig {
  providers: string[];
  models: Record<string, string[]>;
  defaults: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Generate AAS request / SSE event types
// ---------------------------------------------------------------------------

export interface GenerateAasRequest {
  // Asset
  asset_name: string;
  base_url: string;
  selected_submodels: string[];

  // Specification input
  spec_sheet_text: string;
  spec_sheet_pdf_base64?: string;
  spec_sheet_pdf_mime_type?: string;
  supplemental_files?: SupplementalFilePayload[];

  // Provider & model
  provider?: string;
  model?: string;

  // Generation options
  generation_mode?: string;
  use_rag?: boolean;
  use_example?: boolean;
  force_full_aas_output?: boolean;
  max_pdf_chars?: number | null;
  max_attempts?: number;
}

export interface SupplementalFilePayload {
  file_name: string;
  mime_type?: string;
  content_base64: string;
}

export interface GenerateAasResponse {
  conforms: boolean;
  aas_json: string;
  attempts: number;
  issues: ValidationIssue[];
}

export type SseEvent =
  | { type: 'log'; message: string }
  | { type: 'stage'; stage: string; attempt: number; max_attempts: number }
  | { type: 'result'; conforms: boolean; aas_json: string; attempts: number; issues: ValidationIssue[] }
  | { type: 'error'; message: string };

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const api = {
  validate: (json_text: string) =>
    post<ValidateResponse>('/validate', { json_text }),

  getGenerationConfig: async (): Promise<GenerationConfig> => {
    const res = await fetch(`${BASE}/generation-config`);
    if (!res.ok) throw new Error(`Failed to load generation config (${res.status})`);
    return res.json() as Promise<GenerationConfig>;
  },

  /**
   * Stream AAS generation progress as SSE events.
   * Yields { type: 'log' | 'result' | 'error', ... } objects.
   */
  generateAasStream: async function* (req: GenerateAasRequest): AsyncGenerator<SseEvent> {
    const res = await fetch(`${BASE}/generate-aas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });

    if (!res.ok || !res.body) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Generation failed (${res.status}): ${detail}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE lines are separated by \n\n; data lines start with "data: "
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6)) as SseEvent;
          } catch {
            // malformed SSE line — skip
          }
        }
      }
    }

    // Flush remaining buffer
    if (buffer.startsWith('data: ')) {
      try {
        yield JSON.parse(buffer.slice(6)) as SseEvent;
      } catch {
        // ignore
      }
    }
  },
};
