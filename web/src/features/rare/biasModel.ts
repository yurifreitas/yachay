/** Types for the bias audit. Written by tools/atlas_bias.py. */
export type BiasFinding = {
  id: string;
  name: string;
  mechanism: string;
  test: string;
  statistic: number | null;
  detail: string;
  verdict: "real" | "small" | "compromising" | "untestable";
  selfTest?: boolean;
  byBand?: Record<string, { diseases: number; withGene: number; share: number }>;
};
export type BiasAuditData = {
  generated: string;
  premise: string;
  findings: BiasFinding[];
  cellPanel: { cell: string; genesMeasured: number; diseaseGenes: number }[];
};
