import { useRef, useState } from 'react';
import { api, type GenerateAasRequest, type GenerateAasResponse } from '../api/client';

export type GenerateStatus = 'idle' | 'loading' | 'success' | 'partial' | 'error';

export type StageStatus = 'pending' | 'active' | 'success' | 'warning' | 'error';

export interface StageState {
  status: StageStatus;
  /** Log lines associated with this stage */
  logs: string[];
  attempt: number;
  maxAttempts: number;
  /** Error message if status === 'error' */
  error?: string;
}

export interface PipelineStages {
  preparing: StageState;
  querying: StageState;
  validating: StageState;
}

const INITIAL_STAGE: StageState = { status: 'pending', logs: [], attempt: 0, maxAttempts: 1 };

const initialPipeline = (): PipelineStages => ({
  preparing: { ...INITIAL_STAGE },
  querying: { ...INITIAL_STAGE },
  validating: { ...INITIAL_STAGE },
});

interface UseGenerateAIReturn {
  status: GenerateStatus;
  result: GenerateAasResponse | null;
  errorMsg: string;
  logs: string[];
  pipeline: PipelineStages;
  generate: (req: GenerateAasRequest) => Promise<void>;
  reset: () => void;
}

export function useGenerateAI(): UseGenerateAIReturn {
  const [status, setStatus] = useState<GenerateStatus>('idle');
  const [result, setResult] = useState<GenerateAasResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [pipeline, setPipeline] = useState<PipelineStages>(initialPipeline());

  // Track current stage synchronously so log events can be attributed correctly
  const currentStageRef = useRef<keyof PipelineStages>('preparing');

  const generate = async (req: GenerateAasRequest) => {
    setStatus('loading');
    setResult(null);
    setErrorMsg('');
    setLogs([]);
    setPipeline(initialPipeline());
    currentStageRef.current = 'preparing';

    try {
      for await (const event of api.generateAasStream(req)) {
        if (event.type === 'stage') {
          const newStage = event.stage as keyof PipelineStages;
          const prevStage = currentStageRef.current;
          currentStageRef.current = newStage;

          setPipeline((prev) => {
            const next = { ...prev };
            // Complete the previous stage (unless it was already marked error/warning)
            if (prevStage in next && next[prevStage].status === 'active') {
              next[prevStage] = { ...next[prevStage], status: 'success' };
            }
            // Activate the new stage
            if (newStage in next) {
              next[newStage] = {
                ...next[newStage],
                status: 'active',
                attempt: event.attempt,
                maxAttempts: event.max_attempts,
              };
            }
            return next;
          });

        } else if (event.type === 'log') {
          const stage = currentStageRef.current;
          setLogs((prev) => [...prev, event.message]);
          setPipeline((prev) => ({
            ...prev,
            [stage]: {
              ...prev[stage],
              logs: [...prev[stage].logs, event.message],
            },
          }));

        } else if (event.type === 'result') {
          setResult({
            conforms: event.conforms,
            aas_json: event.aas_json,
            attempts: event.attempts,
            issues: event.issues,
          });
          // Mark validating stage done
          setPipeline((prev) => ({
            ...prev,
            validating: {
              ...prev.validating,
              status: event.conforms ? 'success' : 'warning',
            },
          }));
          setStatus(event.conforms ? 'success' : 'partial');

        } else if (event.type === 'error') {
          const stage = currentStageRef.current;
          setPipeline((prev) => ({
            ...prev,
            [stage]: {
              ...prev[stage],
              status: 'error',
              error: event.message,
            },
          }));
          setErrorMsg(event.message);
          setStatus('error');
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setErrorMsg(msg);
      setStatus('error');
      const stage = currentStageRef.current;
      setPipeline((prev) => ({
        ...prev,
        [stage]: { ...prev[stage], status: 'error', error: msg },
      }));
    }
  };

  const reset = () => {
    setStatus('idle');
    setResult(null);
    setErrorMsg('');
    setLogs([]);
    setPipeline(initialPipeline());
    currentStageRef.current = 'preparing';
  };

  return { status, result, errorMsg, logs, pipeline, generate, reset };
}
