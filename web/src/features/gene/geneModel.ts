/** The per-gene join, typed.
 *
 *  Written by `tools/gene_index.py` over every artefact on disk. Nothing is derived here:
 *  the effect sizes, q-values and ranks are the ones Python computed, and a chart that
 *  recomputes its own statistic is a second implementation of the analysis.
 */

export type GeneDependency = {
  score: number;
  n: number;
  nullMean: number;
  nullSd: number;
  z: number;
  rankRaw: number;
  rankCal: number;
  commonEssential: boolean;
  control: boolean;
  medianDependency: number;
  selectivity: number;
};

export type CancerHit = {
  level: "lineage" | "disease" | "subtype";
  subgroup: string;
  /** Effect size: how much more this subgroup needs the gene than everything outside it. */
  d: number;
  q: number;
  lines: number | null;
};

export type GenotypeHit = {
  /** The gene whose damaging mutation DEFINES the subgroup — not this gene. */
  mutatedGene: string;
  d: number;
  q: number;
  lines: number | null;
};

export type NetworkPosition = {
  degree: number;
  community: number | null;
  diseases: number;
};

export type DiseaseLink = {
  id: string;
  name: string;
  /** HPO's own association type. MENDELIAN, POLYGENIC and UNKNOWN are three different
   *  claims and are never collapsed into "associated". */
  assoc: string;
};

export type GeneRecord = {
  /** What the public catalogues hold — see worldModel.ts. Folded in by gene_shards.py so a
   *  gene is one fetch and not two. */
  world?: import("./worldModel").WorldRecord;
  /** Where the variants fall along the molecule — see GeometryPanels.tsx. */
  geo?: import("./GeometryPanels").GeoRecord;
  /** The parts of the protein, from UniProt — the track under the needles. */
  dom?: import("./GeometryPanels").DomRecord;
  /** Routes out of this gene, each with its relation stated. */
  rel?: import("./RelatedGenes").RelRecord;
  /** Order statistics with their test conditions — the datasheet block. */
  ds?: {
    dep?: {
      n: number; min: number; q1: number; median: number; q3: number; max: number;
      mean: number; sd: number | null; dependent: number; strong: number;
    };
    exp?: { types: number; min: number; median: number; max: number; ratio: number | null };
  };
  /** Which cross-layer rules fired for this gene. */
  ins?: string[];
  /** Indexed papers, and how far the VUS share sits from its paper decile's median. */
  att?: { papers: number; vusResidual?: number };
  dep?: GeneDependency;
  cancer?: CancerHit[];
  cancerTotal?: number;
  genotype?: GenotypeHit[];
  genotypeTotal?: number;
  net?: NetworkPosition;
  dis?: DiseaseLink[];
  disTotal?: number;
};

/** The search payload: every symbol and one integer saying how many layers describe it.
 *
 *  185 kB, and it is the ONLY file loaded before someone types. The records themselves live
 *  in 128 shards fetched one at a time — see `shard.ts` and `tools/gene_shards.py`. Loading
 *  twenty megabytes so a reader can look up one symbol is how a page gets closed. */
export type GeneSearchIndex = {
  generated: string;
  shards: number;
  premise: string;
  worldPremise: string;
  geoCaution: string;
  insRules: Record<string, { claim: string; reading: string; rule: string }>;
  insCaution: string;
  attDeciles: { decile: number; papersFrom: number; papersTo: number; genes: number;
                medianVus: number }[];
  attCaution: string;
  attBaseline: string;
  scope: {
    dependency: { genes: number; source?: string };
    cancer: { levels: string[]; subgroups: number };
    genotype: { subgroups: number };
    network: { nodes: number; modularity?: number };
    disease: { pairs: number; genes: number; unnamed?: number };
    genes: number;
    geo?: { genes: number; withPositions?: number; withPathways?: number };
    att?: { genes: number; median: number; p90: number; max: number; withResidual: number };
    ins?: {
      genes: number; withAny: number;
      byRule: Record<string, number>;
      eligible: Record<string, number>;
    };
    world?: {
      protein?: { proteins: number };
      constraint?: { genes: number };
      expression?: { genes: number; cellTypes?: number; floor?: number };
      clinvar?: { genes: number; rows?: number };
    };
  };
  /** symbol -> how many of the six layers say anything. */
  genes: Record<string, number>;
};

/** One shard: the full records for the ~140 symbols that hash into it. */
export type GeneShard = Record<string, GeneRecord>;

/** Which layers have anything to say about this gene, as DATA rather than as a sentence.
 *
 *  Returned for every layer including the empty ones, because the interface has to render
 *  the ABSENCES: "measured in the screen, in no cancer subgroup" is a finding, and a missing
 *  panel is not.
 *
 *  An earlier version built the English string here and the Portuguese reader got
 *  "measured in 1,178 cell lines" under a Portuguese heading. Formatting belongs where the
 *  language is known; this returns the numbers and lets the component say them. */
export type LayerState = {
  id: "dependency" | "cancer" | "genotype" | "network" | "disease" | "world" | "geo";
  present: boolean;
  /** The numbers the sentence needs, whichever language it ends up in. */
  vars: Record<string, number>;
};

export function layersFor(rec: GeneRecord | undefined, scope: GeneSearchIndex["scope"]): LayerState[] {
  const r = rec ?? {};
  return [
    { id: "dependency", present: !!r.dep,
      vars: { n: r.dep?.n ?? 0, scope: scope.dependency.genes } },
    { id: "cancer", present: !!r.cancer?.length,
      vars: { n: r.cancerTotal ?? 0, scope: scope.cancer.subgroups } },
    { id: "genotype", present: !!r.genotype?.length,
      vars: { n: r.genotypeTotal ?? 0, scope: scope.genotype.subgroups } },
    { id: "network", present: !!r.net,
      vars: { n: r.net?.degree ?? 0, diseases: r.net?.diseases ?? 0,
              scope: scope.network.nodes } },
    { id: "disease", present: !!r.dis?.length,
      vars: { n: r.disTotal ?? 0, scope: scope.disease.genes } },
    { id: "geo", present: !!r.geo?.hist,
      vars: { n: r.geo?.placed ?? 0, scope: 0 } },
    { id: "world", present: !!r.world,
      vars: { n: r.world
        ? [r.world.prot, r.world.con, r.world.exp, r.world.clin].filter(Boolean).length
        : 0, scope: 4 } },
  ];
}

/** Rank a search term against the symbol list.
 *
 *  Exact match, then prefix, then substring — in that order and never mixed, because a
 *  reader who types a full symbol expects that gene first and a fuzzy score can bury it
 *  under a longer name that happens to contain it.
 */
export function searchGenes(symbols: string[], query: string, limit = 40): string[] {
  const q = query.trim().toUpperCase();
  if (!q) return [];
  const exact: string[] = [];
  const prefix: string[] = [];
  const inside: string[] = [];
  for (const s of symbols) {
    if (s === q) exact.push(s);
    else if (s.startsWith(q)) prefix.push(s);
    else if (s.includes(q)) inside.push(s);
    if (exact.length + prefix.length >= limit && q.length > 2) break;
  }
  return [...exact, ...prefix, ...inside].slice(0, limit);
}
