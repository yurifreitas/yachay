/** Types for the sparse-structure experiment. Written by tools/interactome_sparse.py. */
export type Locality = {
  bandwidth: number; profile: number;
  meanOffDiagonal: number; medianOffDiagonal: number;
  cacheLinesPerRow: number;
  spmvSeconds: number;
  cacheLineGainVsNatural: number;
  bandwidthGainVsNatural: number;
  spmvGainVsNatural: number;
};

export type Structure = {
  nodes: number; nonzeros: number; density: number; isolatedNodes: number;
  meanDegree: number; medianDegree: number; maxDegree: number;
  degreeSkew: number | null;
  components: number; largestComponent: number;
  communities: number; modularity: number; clustering: number;
  powerLawAlpha: number | null; powerLawCutoff: number;
};

export type Side = { label: string; structure: Structure; orderings: Record<string, Locality> };

export type Verdict = {
  ordering: string; realGain: number; nullGain: number;
  excess: number; biologyHelps: boolean;
};

export type InteractomeSparse = {
  generated: string; input: string; uses: string[];
  premise: string; hypothesis: string;
  graph: {
    associations: number; diseases: number; diseasesWithTwoOrMoreGenes: number;
    genes: number; edges: number;
  };
  real: Side;
  null: Side;
  nullFidelity: {
    requestedEdges: number; actualEdges: number; lostToSimplification: number; note: string;
  };
  verdict: Verdict[];
  versusClassical: {
    communityCacheGain: number | null; rcmCacheGain: number | null;
    communityWins: boolean; says: string;
  };
  finding: string;
  summary: {
    orderingsTested: number; orderingsWhereBiologyHelps: number;
    bestOrdering: string | null; bestExcess: number | null;
    communityExcess: number | null;
  };
};
