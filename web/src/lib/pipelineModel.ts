/** Types for the published pipeline state. Written by tools/pipeline_state.py. */
export type Artifact = { path: string; exists: boolean; written: string | null; bytes: number };

export type StageState = {
  name: string;
  summary: string;
  needs: string[];
  inputs: { path: string; exists: boolean }[];
  outputs: Artifact[];
  code: string[];
  stale: boolean;
  reason: string;
  missingInputs: string[];
};

export type PipelineState = {
  generated: string;
  premise: string;
  rule: string;
  stages: StageState[];
  summary: {
    stages: number; stale: number; fresh: number; blocked: number;
    artifacts: number; artifactsPresent: number; staleNames: string[];
  };
};
