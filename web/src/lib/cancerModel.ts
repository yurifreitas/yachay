/** Selective dependency by cancer subgroup — the shape written by tools/cancer_subgroups.py.
 *
 *  Mostly this file *arranges*: group, rank, and find the comparisons worth putting next to
 *  each other. The one exception is `regate`, and it is a deliberate exception with a cost.
 *
 *  The gates are applied in Python, where they are registered in `manifests/thresholds.yaml`.
 *  `regate` reimplements that predicate here so a reader can move a threshold and watch the
 *  shortlist move — which is the only way to tell a robust finding from one balanced on the
 *  cut. The cost is that the definition of a hit now exists in two places and can drift.
 *  That is accepted knowingly, on two conditions kept in the code: the artefact ships its own
 *  registered values (`gates.registered`) rather than the interface hardcoding them, and
 *  `hits` — the frozen, registered shortlist — is never overwritten by a re-gated one.
 */

export type Hit = {
  gene: string;
  d: number;
  meanInGroup: number;
  meanElsewhere: number;
  q: number;
  linesInGroup: number;
};

export type Subgroup = {
  subgroup: string;
  candidates?: Hit[];
  lines: number;
  detectableFloor: number | null;
  powered: boolean;
  hits: Hit[];
  hitCount: number;
  positiveControls?: { gene: string; rank: number | null }[];
  says: string;
};

export type CancerLevel = {
  generated: string;
  level: "lineage" | "disease" | "subtype";
  column: string;
  premise: string;
  method: Record<string, unknown>;
  scale: {
    lines: number;
    genesAfterStage3: number;
    panEssentialDropped: number;
    subgroups: number;
    powered: number;
    underpowered: number;
  };
  results: Subgroup[];
};

export type Gates = { q: number; d: number; floor: number };

export const DEFAULT_REGISTERED = { q: 0.05, d: 0.5, dependencyFloor: 0.5 };

/** Re-apply the three gates to a subgroup's candidate set.
 *
 *  The gates live in Python, where they are registered; this recomputes the SAME predicate on
 *  the wider candidate set the artefact ships, so a reader can move a threshold and watch the
 *  shortlist move. It is deliberately the same three conditions in the same order — if this
 *  drifted from `tools/cancer_subgroups.py` the interface would be showing a shortlist the
 *  analysis never produced, which is worse than not offering the control at all.
 *
 *  Falls back to the frozen `hits` when an artefact predates the candidate set, so an older
 *  file renders its registered answer rather than an empty panel.
 */
export function regate(sub: Subgroup, gates: Gates): { rows: Hit[]; total: number } {
  const pool = sub.candidates;
  if (!pool) return { rows: sub.hits, total: sub.hits.length };
  return {
    rows: pool.filter((h) => h.q <= gates.q && h.d >= gates.d && h.meanInGroup >= gates.floor),
    total: pool.length,
  };
}

/** One candidate reduced to the three numbers the gates test. Both analyses produce it, so
 *  the diagnostic below is written once. */
export type GateInput = { q: number; effect: number; level: number };

export function gateInputs(sub: Subgroup): GateInput[] {
  return (sub.candidates ?? sub.hits).map((h) => ({
    q: h.q, effect: h.d, level: h.meanInGroup,
  }));
}

/** WHICH GATE IS ACTUALLY BINDING.
 *
 *  A slider tells a reader what happens when they move it. It does not tell them where the
 *  shortlist is being decided, and on this data that is the more useful fact: for Skin, 26 of
 *  40 candidates fail on the Stage 0 dependency floor ALONE — loosening q from 0.05 to 0.25
 *  and the effect from 0.5 to 0.35 changes the answer by nothing at all.
 *
 *  So each gate is scored by how many candidates it is the SOLE reason for excluding. A gate
 *  excluding nothing exclusively is doing no work; the one excluding the most is where the
 *  shortlist is really being set, and it is usually not the one a reader would guess.
 */
export function binding(rows: GateInput[], gates: Gates) {
  const fq = (r: GateInput) => r.q <= gates.q;
  const fd = (r: GateInput) => r.effect >= gates.d;
  const ff = (r: GateInput) => r.level >= gates.floor;
  return {
    q: rows.filter((r) => !fq(r) && fd(r) && ff(r)).length,
    d: rows.filter((r) => fq(r) && !fd(r) && ff(r)).length,
    floor: rows.filter((r) => fq(r) && fd(r) && !ff(r)).length,
  };
}

export const LEVELS = ["lineage", "disease", "subtype"] as const;
export const LEVEL_LABEL: Record<string, string> = {
  lineage: "Lineage",
  disease: "Primary disease",
  subtype: "Subtype",
};
export const LEVEL_BLURB: Record<string, string> = {
  lineage: "35 branches of the Oncotree — the coarsest grouping, and the best powered.",
  disease: "96 primary diseases — the middle rung, where most named cancers sit.",
  subtype: "254 subtypes — the finest, and where 27 of 37 groups cannot detect a large effect.",
};

/** Subgroups worth drawing, most-powered first. An underpowered group is kept and marked,
 *  never dropped: "we could not see it" and "it is not there" are different statements, and
 *  a dashboard that silently omits the first is asserting the second. */
export function ordered(level: CancerLevel): Subgroup[] {
  return [...level.results].sort((a, b) => b.lines - a.lines);
}

/** A gene's footprint across subgroups. The question this answers is the one a target list
 *  cannot answer alone: is this dependency PRIVATE to one cancer, or does it recur? A private
 *  hit is a lineage vulnerability; a recurring one is closer to a pathway, and the two carry
 *  very different consequences for what a therapy would have to be selective against. */
export type Footprint = { gene: string; groups: { subgroup: string; d: number }[] };

export function footprints(level: CancerLevel, minGroups = 2): Footprint[] {
  const by = new Map<string, { subgroup: string; d: number }[]>();
  for (const r of level.results) {
    for (const h of r.hits) {
      const list = by.get(h.gene) ?? [];
      list.push({ subgroup: r.subgroup, d: h.d });
      by.set(h.gene, list);
    }
  }
  return [...by.entries()]
    .filter(([, g]) => g.length >= minGroups)
    .map(([gene, groups]) => ({ gene, groups: groups.sort((a, b) => b.d - a.d) }))
    .sort((a, b) => b.groups.length - a.groups.length || b.groups[0].d - a.groups[0].d);
}

/** Genes found in exactly one subgroup — the private half of the same split. */
export function privateCount(level: CancerLevel): number {
  const seen = new Map<string, number>();
  for (const r of level.results) for (const h of r.hits) seen.set(h.gene, (seen.get(h.gene) ?? 0) + 1);
  return [...seen.values()].filter((n) => n === 1).length;
}

/** Every positive control across the level, with the rank it came back at or null.
 *  Reported whole rather than as a pass rate: four of nine did not come back, and a single
 *  percentage would let that fact be read as noise. */
export function controls(level: CancerLevel) {
  return level.results.flatMap((r) =>
    (r.positiveControls ?? []).map((c) => ({ subgroup: r.subgroup, ...c })),
  );
}

/** THE FINDING THAT JUSTIFIES THE LEVEL SWITCH.
 *
 *  Pooled "Lung" has 126 screened lines — the best-powered subgroup in the whole analysis —
 *  and returns nothing at all. Split into Lung Adenocarcinoma and Small Cell Lung Cancer,
 *  both halves light up, and with the genes their biology predicts. They were cancelling.
 *
 *  This is stated as data read from the two artefacts rather than as a sentence in the
 *  markup, so it stops being true in the interface the moment it stops being true in the run.
 */
export function cancellation(lineage: CancerLevel, subtype: CancerLevel) {
  const pooled = lineage.results.find((r) => r.subgroup === "Lung");
  if (!pooled || pooled.hitCount > 0) return null;
  const parts = subtype.results.filter((r) => /lung/i.test(r.subgroup) && r.hitCount > 0);
  if (parts.length < 2) return null;
  return { pooled, parts };
}
