/** Types for the per-disease dossiers. Written by tools/dossier.py from real sources. */
/** The four amounts of knowledge a sign frequency can represent. Graded by
 *  tools/dossier.py and carried on the record, so no renderer can flatten them back into
 *  one bar chart — which is what this panel used to do. */
export type Evidence = "quantified" | "single-case" | "class" | "none";

export type Sign = {
  id: string; name: string; frequency: string | null;
  kind: string | null; evidence: Evidence;
  k: number | null; n: number | null;
  point: number | null; onset: string | null; sex: string | null;
};

/** One prevalence band and the places that reported it. A disorder normally has several,
 *  and they normally disagree — see references/rare-disease-ancestry.md. */
export type PrevalenceBand = {
  band: string;
  places: string[];
  /** Whether the band sits on the rarity scale. "Unknown" is a real value in this corpus
   *  and has no position on it — a renderer that gives it one draws it as the commonest
   *  band, which is what happened before this flag existed. */
  ordered: boolean;
  rank: number | null;
};
/** One organ system, with the signs that roll up to it. HPO is a DAG, so a sign can be in
 *  several — the counts deliberately sum to more than the number of signs. */
export type SystemRow = {
  id: string;
  name: string;
  signs: number;
  byEvidence: Record<Evidence, number>;
  examples: string[];
};

/** What a trial of the observed size could actually have detected. Stage 2, asked of the
 *  clinical record instead of of a screen. */
export type TrialPower = {
  trialsWithEnrolment: number;
  trialsWithoutEnrolment: number;
  medianEnrolment: number | null;
  medianInterventionalEnrolment: number | null;
  largest: number | null;
  smallest: number | null;
  /** Smallest standardised effect the median interventional trial could find, at 80 %. */
  medianMDE: number | null;
  /** How many interventional trials could not detect even a large (0.8 SD) effect. */
  belowLargeEffect: number;
  interventionalWithEnrolment: number;
  assumption: string;
};

export type TrialTrajectory = {
  firstYear: number | null;
  lastYear: number | null;
  byYear: Record<string, number>;
  startedLastFiveYears: number;
  datedTrials: number;
};

export type TrialSummary = {
  total: number;
  byStatus: Record<string, number>;
  byPhase: Record<string, number>;
  byType: Record<string, number>;
  byIntervention: Record<string, number>;
  recruiting: { nctId: string; title: string; phase: string; enrollment: number | null }[];
  recruitingCount: number;
  byModality: Record<string, number>;
  power: TrialPower;
  trajectory: TrialTrajectory;
  error?: string | null;
};
export type DossierRecord = {
  orpha: string; omim: string; query: string; name: string;
  genes: string[]; geneCount: number;
  inheritance: string[];
  /** The RAREST band on record, not "the prevalence". Named so it cannot be quoted as a
   *  rate without the reader noticing what it is. */
  rarestBand: string | null;
  prevalenceSpread: PrevalenceBand[];
  prevalenceRecords: number;
  prevalenceBands: number;
  prevalenceSpanBands: number | null;
  geographies: string[];
  onsetAges: string[];
  signs: Sign[]; signCount: number; signsWithDenominator: number;
  evidence: Record<Evidence, number>;
  evidenceGrades: Record<string, string>;
  /** Median denominator of the quantified signs, or null when there are none — which is
   *  the answer for most of this portfolio. */
  medianDenominator: number | null;
  systems: SystemRow[];
  systemsMeta: {
    count: number;
    unplacedSigns: number;
    note: string;
    quantifiedSystems: number;
    describedButUnquantified: number;
  };
  cells: Record<string, { topCell: string; topValue: number; expressedIn: number }>;
  trials: TrialSummary;
  naming: {
    catalogueName: string; registryName: string;
    catalogueHits: number; registryHits: number; lostToTheName: number;
  };
};
export type Dossiers = {
  generated: string;
  sources: Record<string, string>;
  caveat: string;
  dossiers: DossierRecord[];
};
