/** Types for the tail-calibration layer. Written by tools/tail_calibration.py. */
export type TailRow = {
  z: number; controlsAbove: number;
  observedFraction: number; normalFraction: number;
  ratio: number | null;
  observedLo: number; observedHi: number;
  normalInsideInterval: boolean;
};

export type Fit = {
  params: Record<string, number>;
  k: number; logLik: number; aic: number; deltaAIC: number; best: boolean;
};

export type Counted = { total: number; candidates: number; controls: number };

export type TailCalibration = {
  generated: string;
  input: string;
  uses: string[];
  premise: string;
  controls: number;
  shape: {
    skew: number; skewSE: number; skewInSEs: number;
    excessKurtosis: number; kurtosisSE: number; kurtosisInSEs: number;
    says: string;
  };
  lambda: { value: number; says: string };
  tail: TailRow[];
  tailVerdict: string;
  fits: Record<string, Fit>;
  bestFit: string;
  consequence: Record<string, { at05: Counted; at01: Counted }>;
  genesChangingStatus: number;
  finding: string;
  lambdaTrap: string;
};
