/** Types for the barrier layer. Written by tools/barriers_seed.py. */
export type Theory = {
  id: string; name: string; field: string; says: string; decides: string; confidence: string;
};
export type Barrier = {
  kind: "molecular" | "delivery" | "trial" | "economic"; what: string; why: string;
};
export type Underused = {
  approach: string; why_it_fits: string; why_not_used: string; confidence: string;
};
export type DiseaseBarriers = {
  catalogueName: string; mechanism: string;
  barriers: Barrier[]; underused: Underused[]; confidence: string;
};
export type Barriers = {
  generated: string; premise: string; provenance: string;
  barrierKinds: { id: string; name: string; note: string }[];
  theories: Theory[];
  diseases: DiseaseBarriers[];
  summary: Record<string, unknown>;
};
