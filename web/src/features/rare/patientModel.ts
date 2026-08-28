/** Types for the patient-level layers and the intervals.
 *
 *  These five artefacts existed on disk for a day and were rendered nowhere — the whole
 *  patient-level body of work plus the confidence intervals that bound it. The strongest
 *  result this project has (a curated frequency resting on one patient reads 0.932 where
 *  the patients say 0.436) was reachable only by opening a JSON file.
 */

export type Bucket = {
  pairs: number;
  meanCuratedPoint: number;
  meanPatientFrequency: number;
  meanDifference: number;
  curatedOverstatesBy20OrMore: number;
  share: number;
  interval?: {
    method: string;
    diseases: number;
    meanDifference: [number, number];
    meanCuratedPoint: [number, number];
    meanPatientFrequency: [number, number];
    excludesZero: boolean;
  };
};

export type PatientFrequencies = {
  generated: string;
  premise: string;
  caveat: string;
  scale: {
    patients: number; distinctDiseases: number; publications: number;
    featurePairs: number; diseasesWithAComputedDenominator: number; minAssessed: number;
  };
  denominators: {
    median: number; p75: number; p95: number; max: number;
    atLeastTen: number; atLeastThirty: number;
  };
  agreement: {
    comparable: number; within20points: number; differBy50PointsOrMore: number;
    biggerDenominator: Record<string, number>;
    worst: {
      diseaseLabel: string; termLabel: string;
      observed: number; assessed: number; frequency: number;
      curatedRaw: string; curatedN: number | null; curatedPoint: number;
      difference: number; biggerDenominator: string;
    }[];
  };
  singleCaseBias: {
    byCuratedDenominator: Record<string, Bucket>;
    says: string;
  };
  finding: string;
};

export type ClinvarEvidence = {
  generated: string;
  premise: string;
  scale: { rows: number; grch38Rows: number; genesWithFiftyOrMore: number };
  significance: { counts: Record<string, number>; vusShare: number; conflictingShare: number };
  reviewStatus: {
    byStars: Record<string, number>;
    atOneStarOrLess: number; shareAtOneStarOrLess: number; says: string;
  };
  crossCheck: {
    patientVariants: number; foundInClinVar: number; notInClinVar: number;
    bySignificance: Record<string, number>; says: string;
  };
  vusByGene: { worst: { gene: string; variants: number; vusShare: number }[]; says: string };
};

export type Intervals = {
  generated: string;
  resamples: number;
  premise: string;
  resamplingUnit: string;
  results: {
    claim: string; kind: string; point: number;
    lo: number | null; hi: number | null; width?: number;
    method: string; citedIn: string;
    excludesZero?: boolean; pairs?: number; clusters?: number;
  }[];
  notMeasured: string[];
};

/** The four denominator buckets, in the order that tells the story. Fixed here rather than
 *  read from object key order, which JavaScript does not guarantee for a payload. */
export const BUCKET_ORDER = ["n=1", "n=2-4", "n=5-19", "n>=20"] as const;

/** A forest plot needs a common axis. Widen slightly so the whiskers are not clipped. */
export function forestDomain(rows: { lo: number | null; hi: number | null }[]): [number, number] {
  const los = rows.map((r) => r.lo).filter((v): v is number => v !== null);
  const his = rows.map((r) => r.hi).filter((v): v is number => v !== null);
  if (!los.length) return [-1, 1];
  const lo = Math.min(...los, 0);
  const hi = Math.max(...his, 0);
  const pad = Math.max(0.02, (hi - lo) * 0.08);
  // Rounded to two decimals: the unrounded value renders as `-0.6416200000000001` on the
  // axis, which is floating-point noise presented as precision — the opposite of what a
  // chart about confidence intervals should model.
  const round = (v: number) => Math.round(v * 100) / 100;
  return [round(lo - pad), round(hi + pad)];
}
