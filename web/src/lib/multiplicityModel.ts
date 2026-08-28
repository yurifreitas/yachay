/** Types for the multiplicity layer. Written by tools/multiplicity.py. */
export type FdrRoute = {
  pi0: number; impliedNull: number;
  atFDR01: number; atFDR05: number;
  atFDR01Candidates: number; atFDR05Candidates: number;
  controlsRejectedAt05: number; minQ: number;
};

export type Multiplicity = {
  generated: string;
  input: string;
  uses: string[];
  premise: string;
  scale: { genes: number; controls: number; commonEssential: number; candidates: number };
  assumption: {
    claim: string; testedOn: string;
    controlMean: number; controlSd: number;
    ksStatistic: number; ksP: number;
    shapiroP: number | null;
    cvmStatistic: number; cvmP: number;
    whyItMatters: string; verdict: string;
  };
  empiricalResolution: { controls: number; smallestAttainableP: number; says: string };
  fdr: { parametric: FdrRoute; empirical: FdrRoute };
  naive: {
    zOver3: number; zOver3Candidates: number; says: string; expectedFalsePositives: number;
  };
  finding: string;
};
