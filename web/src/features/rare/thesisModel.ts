/** Types for the thesis layer. Written by tools/thesis_seed.py.
 *
 *  `register` and `status` are the load-bearing fields: the first says what KIND of claim a
 *  row is, the second says whether this repository implements it. A view that renders the
 *  claim and drops either of them is rendering a brochure.
 */
export type Register = "founded" | "hypothesis" | "metaphor";
export type BuildStatus = "built" | "partial" | "named-only" | "absent";

export type ScaleRung = {
  id: string; name: string; unit: string;
  whatChanges: string;
  repoArtifact: string;
  status: BuildStatus;
  gap: string | null;
};

export type Insight = {
  n: number; title: string; statement: string;
  register: Register; status: BuildStatus; note: string;
};

export type Supplied = { claim: string; status: string };

export type ArchLayer = { layer: string; holds: string; note: string };

export type Thesis = {
  generated: string;
  premise: string;
  provenance: string;
  thesisScientific: string;
  thesisComputational: string;
  oneLine: string;
  deepest: string;
  scales: ScaleRung[];
  insights: Insight[];
  register: Record<Register, string[]>;
  supplied: Supplied[];
  architecture: ArchLayer[];
  loop: string[];
  summary: {
    scales: number;
    scalesByStatus: Record<string, number>;
    insights: number;
    insightsByRegister: Record<string, number>;
    insightsByStatus: Record<string, number>;
    foundedClaims: number;
    openHypotheses: number;
    metaphorsRetired: number;
    suppliedUnverified: number;
  };
};
