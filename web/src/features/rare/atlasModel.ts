/** Types for the world-scale atlas. Written by tools/build_atlas.py from public catalogues. */
export type WorldAtlas = {
  generated: string;
  provenance: string;
  sourceHeader: string;
  scale: {
    diseases: number;
    diseasesByPrefix: Record<string, number>;
    diseasesWithGene: number;
    genes: number;
    genesWithCellData: number;
    cellTypes: number;
    diseasesPlaceableOnCellAxis: number;
    orphanetWithPrevalence: number;
    ultraRare: number;
    ultraRareWithGene: number;
    associationTypes: Record<string, number>;
  };
  coverage: { geneKnown: number; cellPlaceable: number; ultraRareGeneKnown: number };
  prevalenceDistribution: { band: string; diseases: number; rank: number }[];
  cellBurden: { cell: string; diseaseGenes: number }[];
  cellTypes: string[];
};
