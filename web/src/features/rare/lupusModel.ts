/** Types for the lupus / cell-vs-gene payload. Written by tools/lupus_seed.py. */

export type Cell = { id: string; name: string; role: string; lineage: string };
export type Axis = { id: string; name: string; note: string };

export type MonogenicGene = {
  gene: string;
  alt: string[];
  axis: string;
  cell: string;
  effect: "loss" | "gain";
  inherit: string;
  penetrance: string;
  note: string;
  confidence: "high" | "medium" | "low";
};

export type Therapy = {
  name: string; target: string; cell: string; modality: string;
  status: string; note: string; confidence: string;
};

export type Lupus = {
  generated: string;
  provenance: string;
  cells: Cell[];
  axes: Axis[];
  monogenic: MonogenicGene[];
  sle: {
    name: string; architecture: string; loci: string;
    note: string; confidence: string; disparity: string;
  };
  therapies: Therapy[];
  /** gene x cell incidence: 2 primary, 1 same lineage, 0 not described. */
  matrix: ({ gene: string; axis: string; effect: string } & Record<string, number | string>)[];
  summary: {
    monogenicGenes: number; withAlternates: number; gainOfFunction: number;
    byAxis: Record<string, number>; byCell: Record<string, number>;
    therapiesByCell: Record<string, number>; cellsWithNoTherapy: string[];
  };
};
