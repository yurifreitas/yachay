/** Types for the prevalence audit. Written by tools/prevalence_audit.py.
 *  Entirely derived from the Orphanet XML — there is no authored field in this shape.
 */
export type PrevalenceRecord = {
  type: string | null; qualification: string | null; class: string | null;
  value: string | null; geography: string | null; validation: string | null;
  source: string | null;
};

export type Disagreement = {
  orpha: string; name: string; birthHiRate: number; pointHiRate: number;
  foldDifference: number; foldMagnitude: number; says: string;
};

export type GeoRow = {
  place: string; records: number; share: number;
  populationM: number | null; perHundredM: number | null;
};

export type WatchedDisease = {
  orpha: string; name: string; records: PrevalenceRecord[]; recordCount: number;
  typesPresent: string[];
  validatedPointPrevalence: { lo: number; hi: number } | null;
  worldCohort: { lo: number; hi: number } | null;
};

export type PrevalenceAudit = {
  generated: string;
  input: string;
  premise: string;
  scale: {
    disordersWithPrevalence: number; prevalenceRecords: number;
    meanRecordsPerDisorder: number;
  };
  byType: Record<string, number>;
  byValidation: Record<string, number>;
  byQualification: Record<string, number>;
  byClass: Record<string, number>;
  topGeographies: Record<string, number>;
  mixedTypeDisorders: {
    count: number; fraction: number;
    examples: { orpha: string; name: string; types: string[]; records: number }[];
  };
  typeDisagreements: { count: number; rows: Disagreement[]; says: string };
  cohortBasis: Record<string, number>;
  geography: {
    records: number; namedPlaces: number; placedRecords: number; unplacedRecords: number;
    rows: GeoRow[];
    byRate: GeoRow[];
    leastLookedAt: GeoRow[];
    absentEntirely: { place: string; populationM: number; records: number }[];
    populationCoveredM: number;
    top10Share: number;
    says: string;
  };
  watched: WatchedDisease[];
  finding: string;
};
