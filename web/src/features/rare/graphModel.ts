/** Types for the lupus network. Written by tools/lupus_graph.py. */

export type NodeKind = "gene" | "mechanism" | "cell" | "therapy";

export type BaseNode = { id: string; name: string; kind: NodeKind; note?: string; role?: string };

export type GeneNode = BaseNode & {
  kind: "gene";
  mechanism: string; cell: string;
  effect: "loss" | "gain";
  inherit: string; penetrance: string;
  evidence: "monogenic" | "gwas" | "both" | "candidate";
  confidence: string;
  reachable: boolean; hops: number; path: string[];
};
export type MechanismNode = BaseNode & { kind: "mechanism" };
export type CellNode = BaseNode & { kind: "cell"; lineage: string };
export type TherapyNode = BaseNode & {
  kind: "therapy"; target: string; cell: string; mechanism: string;
  modality: string; status: string; confidence: string;
};

export type Edge = { source: string; target: string; kind: string };

export type LupusGraph = {
  generated: string;
  provenance: string;
  nodes: {
    genes: GeneNode[]; mechanisms: MechanismNode[];
    cells: CellNode[]; therapies: TherapyNode[];
  };
  edges: Edge[];
  analysis: {
    unreachableGenes: string[];
    cellsWithNoTherapy: string[];
    mechanismsWithNoTherapy: string[];
    medianHops: number;
  };
  summary: {
    genes: number; cells: number; mechanisms: number; therapies: number; edges: number;
    byEvidence: Record<string, number>; byEffect: Record<string, number>;
    byModality: Record<string, number>; byStatus: Record<string, number>;
  };
};
