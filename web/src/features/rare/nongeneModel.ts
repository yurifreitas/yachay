/** Types for the non-gene layer. Written by tools/nongene_seed.py. */
export type Slot = { id: string; name: string; gene: string; note: string };

export type NonGeneClass = {
  id: string;
  name: string;
  oneLine: string;
  /** Keyed by Slot.id — the equivalence table, one column per slot. */
  slots: Record<string, string>;
  mechanism: string;
  whyGeneThinkingFails: string;
  examples: string[];
  confidence: string;
};

export type Phenocopy = {
  nonGene: string;
  genetic: string;
  classId: string;
  convergesOn: string;
  mechanism: string;
};

export type FailureMode = { id: string; name: string; says: string };

export type NonGene = {
  generated: string;
  premise: string;
  provenance: string;
  blindSpot: {
    diseases: number; withGene: number; withoutGene: number;
    fractionWithoutGene: number; says: string;
  };
  slots: Slot[];
  classes: NonGeneClass[];
  phenocopies: Phenocopy[];
  failureModes: FailureMode[];
  summary: {
    classes: number; slots: number; phenocopies: number;
    failureModes: number; examples: number;
    byClassPhenocopies: Record<string, number>;
  };
};
