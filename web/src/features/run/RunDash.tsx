/** The run explorer, restructured as a dashboard and given the numbers it was missing.
 *
 *  WHAT WAS WRONG. Seven panels in one scroll, in dependency order, with a comment explaining
 *  that the order was the argument — and no way for a reader to see that argument, because a
 *  long page reads as a list. The order IS the argument: whether the counts vary at all decides
 *  whether the ranking figure can say anything, and whether the null is right decides whether
 *  any of the rest is worth reading. So the order became the navigation.
 *
 *  WHAT WAS MISSING. The page showed the calibration and never said what it DID. A reader could
 *  look at a ridgeline and a rank-shift chart and still not know how many entities changed
 *  position, by how much, or whether the two rankings agree at all. Those are three lines of
 *  arithmetic over data already in the bundle, and they are now the first thing on the page.
 *
 *  THE SUBSET CAVEAT IS LOAD-BEARING. The bundle ships a density-preserving sample of the
 *  entity table, not all of it, so every derived figure here says which denominator it used.
 *  A summary computed on a sample and presented as if it were the population is the same
 *  mistake this whole project is about.
 */
import { useMemo } from "react";
import type { Run } from "../../lib/dataTypes";
import { runs } from "../../lib/data/runs";
import { renderSection } from "../../lib/sectionRegistry";
import { RUN_SECTIONS } from "./runSections";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { SectionWalk } from "../../components/molecules/SectionWalk";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { RUN, RARE } from "../../i18n/strings";
// The design tokens live in their own sheet and were previously imported only by the
// rare-disease page, so every --sp-* and --r-* used here resolved to nothing: the grid
// gaps collapsed to zero and the layout looked broken rather than unstyled.
import css from "./RunDash.module.css";

const GROUPS: NavGroupDef[] = [
  /* IN PIPELINE ORDER, AND THE BANDS FOLLOW IT.
   *
   *  A band heading prints when the tier CHANGES between one group and the next, so a
   *  tier that appears twice non-contiguously prints its heading twice and reads as two
   *  different bands. The first version of this had exactly that: `premise` and `state`
   *  both sit in "the run" and had `null`, `effect` and `result` between them.
   *
   *  Ordering them premise, state, null, effect, result fixes it and is the better
   *  reading anyway — it is the order the pipeline runs in. */
  { id: "premise", label: RUN.gPremise, question: RUN.qPremise, tier: RARE.tRun },
  { id: "state", label: RUN.gState, question: RUN.qState, tier: RARE.tRun },
  { id: "null", label: RUN.gNull, question: RUN.qNull, tier: RARE.tNull },
  { id: "effect", label: RUN.gEffect, question: RUN.qEffect, tier: RARE.tEffect },
  { id: "result", label: RUN.gResult, question: RUN.qResult, tier: RARE.tResult },
];

const TABS: NavSectionDef[] = [
  { id: "shortlist", label: RUN.sShortlist, group: "result" },
  { id: "selectivity", label: RUN.sSelectivity, group: "result" },
  { id: "populations", label: RUN.sPopulations, group: "result" },
  { id: "multiplicity", label: RUN.sMultiplicity, group: "result" },
  { id: "tail", label: RUN.sTail, group: "result" },
  { id: "counts", label: RUN.sCounts, group: "premise" },
  { id: "floor", label: RUN.sFloor, group: "null" },
  { id: "ridge", label: RUN.sRidge, group: "null" },
  { id: "control", label: RUN.sControl, group: "null" },
  { id: "field", label: RUN.sField, group: "null" },
  { id: "event", label: RUN.sEvent, group: "null" },
  { id: "shift", label: RUN.sShift, group: "effect" },
  { id: "bump", label: RUN.sBump, group: "effect" },
  { id: "lineages", label: RUN.sLineages, group: "effect" },
  { id: "movers", label: RUN.sMovers, group: "effect" },
  { id: "overlap", label: RUN.sOverlap, group: "effect" },
  { id: "base", label: RUN.sBase, group: "state" },
  { id: "provenance", label: RUN.sProvenance, group: "state" },
];

/** Spearman's rho between the raw and calibrated orderings. Both are already ranks, so this is
 *  the direct form and needs no re-ranking — and with ties absent by construction it is exact
 *  rather than approximate. */
function spearman(a: number[], b: number[]): number {
  const n = a.length;
  if (n < 2) return NaN;
  let d2 = 0;
  for (let i = 0; i < n; i++) d2 += (a[i] - b[i]) ** 2;
  return 1 - (6 * d2) / (n * (n * n - 1));
}

export default function RunDash({ runId }: { runId: string }) {
  const run = runs.find((r) => r.id === runId) as Run;
  /* Both nav levels are derived from one URL parameter and published to the rail; this
     page no longer draws its own tab rows. */
  const { section } = useSectionNav({
    owner: `run:${runId}`, groups: GROUPS, sections: TABS, initial: "shortlist",
  });

  // What the calibration actually did, over the entity rows that shipped.
  const effect = useMemo(() => {
    const rows = run.entities ?? [];
    if (!rows.length) return null;
    const byRaw = [...rows].sort((x, y) => y.score - x.score);
    const byCal = [...rows].sort((x, y) => y.z - x.z);
    const rawRank = new Map(byRaw.map((r, i) => [r.entity, i + 1]));
    const calRank = new Map(byCal.map((r, i) => [r.entity, i + 1]));
    const moves = rows.map((r) => Math.abs(
      (rawRank.get(r.entity) as number) - (calRank.get(r.entity) as number)));
    const sorted = [...moves].sort((x, y) => x - y);
    const ns = rows.map((r) => r.n).filter((n) => Number.isFinite(n));
    const top = 20;
    const rawTop = new Set(byRaw.slice(0, top).map((r) => r.entity));
    const calTop = new Set(byCal.slice(0, top).map((r) => r.entity));
    let shared = 0;
    rawTop.forEach((e) => { if (calTop.has(e)) shared++; });
    return {
      rows: rows.length,
      total: run.entitiesTotal,
      rho: spearman(rows.map((r) => rawRank.get(r.entity) as number),
                    rows.map((r) => calRank.get(r.entity) as number)),
      medianMove: sorted[Math.floor(sorted.length / 2)],
      p90Move: sorted[Math.floor(sorted.length * 0.9)],
      maxMove: sorted[sorted.length - 1],
      movedOver100: moves.filter((m) => m > 100).length,
      topOverlap: shared,
      topSize: top,
      nMin: Math.min(...ns),
      nMax: Math.max(...ns),
      nSpread: Math.max(...ns) / Math.max(1, Math.min(...ns)),
    };
  }, [run]);

  return (
    <section className={css.page}>
      <header className={css.hero}>
        <div className={css.heroTop}>
          <div className={css.heroText}>
            <p className={css.eyebrow}>Screen &middot; null-calibrated shortlist</p>
            <h2 className={css.title}>{run.title}</h2>
          </div>
          <div className={css.heroSide}>
            <p className={css.lede}>{run.subtitle}</p>
            <p className={css.statistic}>
              <span className={css.label}>Statistic</span> {run.statistic}
              <span className={css.sep}>&middot;</span>
              <span className={css.label}>Reduction</span> {run.reduce}
            </p>
          </div>
        </div>

        {/* WHAT THE CALIBRATION DID — three lines of arithmetic the page never showed. */}
        {effect && (
          <div className={css.effect}>
            <Cell l="Rank agreement" v={effect.rho.toFixed(3)}
                  s={`Spearman between raw and calibrated order, over the ${effect.rows.toLocaleString("en-US")} rows in the bundle`} />
            <Cell l="Median rank move" v={effect.medianMove.toLocaleString("en-US")}
                  s={`90th percentile ${effect.p90Move.toLocaleString("en-US")}, largest ${effect.maxMove.toLocaleString("en-US")}`} />
            <Cell l="Moved more than 100 places"
                  v={effect.movedOver100.toLocaleString("en-US")}
                  s={`${Math.round((effect.movedOver100 / effect.rows) * 100)}% of the shipped rows`} />
            <Cell l={`Top ${effect.topSize} shared`} v={`${effect.topOverlap}/${effect.topSize}`}
                  s="entities present in both orderings — the shortlist the whole method exists to produce" />
            <Cell l="Observation counts" v={`${effect.nSpread.toFixed(1)}x`}
                  s={`from ${effect.nMin.toLocaleString("en-US")} to ${effect.nMax.toLocaleString("en-US")}; without spread here, calibration by n can change nothing`} />
          </div>
        )}
        <p className={css.caveat}>
          The bundle ships {effect ? effect.rows.toLocaleString("en-US") : "a sample"} of{" "}
          {run.entitiesTotal.toLocaleString("en-US")} entities &mdash; a density-preserving
          sample, not the head and tail &mdash; so every figure in this strip is computed on
          that subset and says so. The ranks inside the panels below are computed in Python over
          all {run.entitiesTotal.toLocaleString("en-US")}.
        </p>
      </header>

      <SectionHeading />

      {/* ONE CALL. The seventeen branches that were here are declared in runSections.tsx,
          because a render chain and a nav array drift apart the moment nothing connects them —
          which is the failure this repository keeps finding in its own prose. */}
      {renderSection(RUN_SECTIONS, section, { run }, {
        className: css.block, headingClass: css.h3, subClass: css.sub, bodyClass: css.blockBody,
      })}
      <SectionWalk />
    </section>
  );
}


function Cell({ l, v, s }: { l: string; v: string; s: string }) {
  return (
    <div className={css.cell}>
      <span className={css.cellL}>{l}</span>
      <span className={css.cellV}>{v}</span>
      <span className={css.cellS}>{s}</span>
    </div>
  );
}
