/** Genotype-defined subgroups — the shape written by tools/cancer_genotype.py.
 *
 *  The catalogue view asks "what does this *named* cancer need". This asks "what does a cell
 *  carrying a damaging mutation in gene G need" — the grouping a target programme acts on.
 *  Two confounds sit between the question and the answer, and both are in the artefact:
 *  lineage (BRAF mutants are melanoma) and mutational burden (hypermutated lines are mutated
 *  in everything).
 */

export type GenoHit = {
  gene: string;
  dStratified: number;
  dNaive: number;
  confoundShare: number | null;
  dBurdenAdjusted: number | null;
  burdenStrata: number;
  strata: number;
  q: number;
  meanMutant: number;
  meanWildType: number;
};

export type Driver = {
  driver: string;
  candidates?: GenoHit[];
  mutantLines: number;
  detectableFloor: number | null;
  powered: boolean;
  lineagesSpanned: number;
  burdenSeparation: number;
  burdenProxy: boolean;
  hits: GenoHit[];
  hitCount: number;
  says: string;
};

export type Control = {
  driver: string;
  target: string;
  mechanism: string;
  expected: string;
  observed?: string;
  mutantLines?: number;
  dNaive?: number;
  dStratified?: number;
  dBurdenAdjusted?: number | null;
  shrinkage?: number | null;
  burdenSeparation?: number;
  burdenStrata?: number;
  burdenSeparable?: boolean;
  says?: string;
};

export type Genotype = {
  generated: string;
  gates?: { registered: { q: number; d: number; dependencyFloor: number;
                          burdenProxyD?: number } };
  premise: string;
  confound: { statement: string; handling: string; minPerStratum: number };
  prediction: {
    claim: string; written: string; controlsAgreeing: number; controlsTestable: number;
  };
  isNot: string;
  method: Record<string, unknown>;
  scale: {
    lines: number; genesAfterStage3: number; genotypesTested: number;
    lineageStrata: number; powered: number;
  };
  controls: Control[];
  results: Driver[];
};

/** The same three gates as the catalogue view, on the stratified estimate.
 *  `dStratified` and not `dNaive`: the naive number is displayed for comparison, never gated
 *  on, because gating on the confounded estimate is the mistake the panel exists to show. */
export function regateDriver(d: Driver, gates: { q: number; d: number; floor: number }) {
  const pool = d.candidates;
  if (!pool) return { rows: d.hits, total: d.hits.length };
  return {
    rows: pool.filter((h) => h.q <= gates.q && h.dStratified >= gates.d
                             && h.meanMutant >= gates.floor),
    total: pool.length,
  };
}

/** The same three numbers the gates test, from a genotype driver. */
export function driverGateInputs(d: Driver) {
  return (d.candidates ?? d.hits).map((h) => ({
    q: h.q, effect: h.dStratified, level: h.meanMutant,
  }));
}

/** Drivers that produced something, most confident first. A driver with no hits is kept out
 *  of this list but its count still feeds `proxyShare` — the denominator is every genotype
 *  tested, not every genotype that worked. */
export function withHits(g: Genotype): Driver[] {
  return g.results.filter((d) => d.hitCount > 0)
    .sort((a, b) => (b.hits[0]?.dStratified ?? 0) - (a.hits[0]?.dStratified ?? 0));
}

/** THE HEADLINE, and it is about the data rather than about any gene.
 *  Most of a frequency-ranked genotype list is substantially restating mutational burden. */
export function proxyShare(g: Genotype) {
  const flagged = g.results.filter((d) => d.burdenProxy).length;
  return { flagged, total: g.results.length,
           pct: g.results.length ? Math.round((flagged / g.results.length) * 100) : 0 };
}

/** Drivers sorted by how far their two arms separate on burden alone — the diagnostic that
 *  says "this genotype is largely a synonym for hypermutated". */
export function byBurden(g: Genotype): Driver[] {
  return [...g.results].sort((a, b) => b.burdenSeparation - a.burdenSeparation);
}

/** The three estimates of one hit, in the order the confound is peeled back. Rendered as a
 *  slopegraph: three positions on a common scale beat three numbers in a row, because the
 *  question is which way each one moved, not what each one is. */
export function ladder(h: GenoHit) {
  return [
    { key: "naive", label: "naive", value: h.dNaive },
    { key: "lineage", label: "lineage-stratified", value: h.dStratified },
    { key: "burden", label: "burden-adjusted", value: h.dBurdenAdjusted },
  ] as const;
}

export const OBSERVED_TONE: Record<string, "ok" | "warn" | "unknown"> = {
  survives: "ok",
  shrinks: "warn",
  "not separable from burden": "unknown",
};
