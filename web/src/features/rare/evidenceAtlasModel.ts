/** Types for the catalogue-wide evidence profile. Written by tools/evidence_atlas.py,
 *  which imports its grading rules from tools/dossier.py so the two cannot drift. */
import type { Evidence } from "./dossierModel";

export type EvidenceAtlas = {
  generated: string;
  premise: string;
  caveat: string;
  grades: Record<string, string>;
  profile: {
    diseasesWithPhenotypeAnnotations: number;
    annotations: number;
    diseasesWithAQuantifiedSign: number;
    /** The headline: what share of the catalogue has ONE sign from a real series. */
    shareWithAQuantifiedSign: number;
    diseasesWithAnyFraction: number;
    diseasesWithNoFractionAtAll: number;
    shareWithNoFractionAtAll: number;
    diseasesWithNoFrequencyAnywhere: number;
    annotationsByGrade: Record<Evidence, number>;
    denominators: {
      count: number; min: number | null; p25: number | null; median: number | null;
      p75: number | null; p95: number | null; max: number | null;
      underTen: number; underThirty: number;
    };
  };
  bySystem: {
    id: string; name: string; signs: number;
    byGrade: Record<Evidence, number>;
    shareQuantified: number | null;
  }[];
  byPrevalenceBand: Record<string, Record<string, number>>;
  byPrevalenceBandNote: string | null;
  attention: {
    medianAnnotationsWhenQuantified: number | null;
    medianAnnotationsWhenNot: number | null;
    says: string;
  };
};
