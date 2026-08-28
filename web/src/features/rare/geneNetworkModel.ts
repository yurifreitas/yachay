/** Types for the shipped gene-gene graph. Written by tools/interactome_sparse.py.
 *
 *  CSR rather than a node/edge list: the interface walks neighbourhoods on demand, and
 *  `indices.slice(indptr[i], indptr[i+1])` is that walk in one line with no index built at
 *  load time. At 5,524 nodes and 38,746 edges the whole adjacency is smaller than one of the
 *  chart bundles.
 */
export type GeneNetwork = {
  generated: string;
  premise: string;
  nodes: string[];
  degree: number[];
  community: number[];
  diseaseCount: number[];
  indptr: number[];
  indices: number[];
  weights: number[];
  communities: number;
  modularity: number;
  stats: {
    nodes: number; edges: number; isolated: number;
    maxDegree: number; medianDegreeConnected: number;
  };
  seedSuggestions: string[];
};
