/** Types for the naming layer. Written by tools/nomenclature_seed.py. */
export type Era = { id: string; name: string; span: string; basis: string; note: string };
export type Root = { part: string; origin: string; means: string; example: string };
export type NameCase = {
  id: string; current: string; era: string;
  etymology: string; story: string; verdict: string; consequence: string;
  confidence: "high" | "medium" | "low";
};
export type Nomenclature = {
  generated: string; premise: string; provenance: string;
  eras: Era[]; roots: Root[]; names: NameCase[];
  summary: {
    cases: number; byEra: Record<string, number>;
    renamedForEthics: number; namePreservesError: number;
    twoLiteratures: number; byConfidence: Record<string, number>;
  };
};
