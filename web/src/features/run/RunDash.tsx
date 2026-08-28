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
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { RUN } from "../../i18n/strings";
import CountVariation from "../overview/CountVariation";
import ControlCalibration from "../nullfloor/ControlCalibration";
import RankShift from "../ranking/RankShift";
import NullRidgeline from "../nullfloor/NullRidgeline";
import { NoiseFloor, Movers, Headline } from "./panels";
import { Shortlist, Populations, Selectivity, Base, FlagOverlap } from "./Substance";
import Multiplicity from "./Multiplicity";
import TailCalibration from "./TailCalibration";
// The design tokens live in their own sheet and were previously imported only by the
// rare-disease page, so every --sp-* and --r-* used here resolved to nothing: the grid
// gaps collapsed to zero and the layout looked broken rather than unstyled.
import css from "./RunDash.module.css";

const GROUPS: NavGroupDef[] = [
  /* THE SHORTLIST IS FIRST, and it was absent entirely. This project describes itself as
     "screen → defensible shortlist" and the explorer opened on a diagnostic. Diagnostics
     justify a result; they are not the result, and putting them first told the reader the
     method was the point. */
  { id: "result", label: RUN.gResult, question: RUN.qResult },
  { id: "premise", label: RUN.gPremise, question: RUN.qPremise },
  { id: "null", label: RUN.gNull, question: RUN.qNull },
  { id: "effect", label: RUN.gEffect, question: RUN.qEffect },
  { id: "state", label: RUN.gState, question: RUN.qState },
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
  { id: "shift", label: RUN.sShift, group: "effect" },
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

      {section === "shortlist" && (
        <Block title="The deliverable, and the rule that produced it"
               sub="Ranked by calibrated z with the common-essential genes removed, because a
                    gene every line needs is a real dependency and a useless selective one. The
                    rule sits above the table rather than in a footnote: a shortlist whose
                    inclusion rule is invisible is an opinion with a table around it.">
          <Shortlist run={run} />
        </Block>
      )}

      {section === "overlap" && (
        <Block title="The flags are sets, and they overlap"
               sub="Everywhere else on this site a gene gets one class, because a legend wants
                    three colours. Here the flags are counted as the overlapping sets they
                    actually are — including the raw and calibrated top hundreds, whose
                    intersection with common-essential is the whole argument for calibrating,
                    stated as a number.">
          <FlagOverlap run={run} />
        </Block>
      )}

      {section === "selectivity" && (
        <Block title="The two axes that define the word selective"
               sub="How strong the dependency is where it exists, against how few lines carry
                    it. Both columns were already in the data and neither had ever been
                    plotted.">
          <Selectivity run={run} />
        </Block>
      )}

      {section === "populations" && (
        <Block title="Three populations that should not look alike"
               sub="Controls should sit at zero with unit spread; common essentials should sit
                    far above it; candidates should be somewhere a person has to think about.
                    If the three collapse together, the calibration has flattened the screen
                    rather than corrected it.">
          <Populations run={run} />
        </Block>
      )}

      {section === "multiplicity" && (
        <Block title="Ranking 17,916 genes is itself a selection operator"
               sub="Calibrating each gene against a null of the right shape fixes half the
                    problem. The other half is that the top of seventeen thousand numbers is
                    extreme for free. This panel converts z to a p-value, tests the assumption
                    that conversion rests on, and reports what a false-discovery-rate cut
                    actually buys over the threshold the shortlist was using.">
          <Multiplicity />
        </Block>
      )}

      {section === "tail" && (
        <Block title="The normality test failed. This is by how much, and where"
               sub="A goodness-of-fit p-value says a distribution is wrong and nothing about
                    where. At this many observations almost anything fails a normality test, so
                    the only question that matters is whether the failure lives in the middle,
                    where nobody looks, or in the tail, where the entire shortlist lives.">
          <TailCalibration />
        </Block>
      )}

      {section === "counts" && (
        <Block title="If the counts do not vary, nothing downstream can"
               sub="Calibration divides by a null that depends on n. Where n is constant the
                    correction is a constant, and every ranking claim collapses to the raw one.
                    This panel is first because it can end the argument.">
          <CountVariation runId={run.id} />
        </Block>
      )}

      {section === "floor" && (
        <Block title="The floor every score is measured against"
               sub="A maximum over many observations rises with the number of observations even
                    when nothing is happening. The null says how much, at each n.">
          <NoiseFloor run={run} />
        </Block>
      )}

      {section === "ridge" && (
        <Block title="The null, by observation count"
               sub="One distribution per n. If these overlap, calibration is cosmetic; if they
                    march, the raw score was measuring the count.">
          <NullRidgeline runId={run.id} />
        </Block>
      )}

      {section === "control" && (
        <Block title="The control, which is where this was caught being wrong"
               sub="Entities that should score at zero. A control that comes back at −4 is not a
                    finding, it is a broken null — and that is exactly what a pooled resample
                    produced before the null was drawn block-shaped.">
          <ControlCalibration runId={run.id} />
        </Block>
      )}

      {section === "shift" && (
        <Block title="What the calibration moves"
               sub="Raw rank against calibrated rank. A diagonal means the correction changed
                    nothing; the departures from it are the entire result.">
          <RankShift runId={run.id} />
        </Block>
      )}

      {section === "movers" && (
        <Block title="Who moved, and by how much"
               sub="The table behind the shift, with both ranks and the distance between them.">
          <Movers run={run} />
        </Block>
      )}

      {section === "base" && (
        <Block title="What every number on this page rests on"
               sub="The dataset, the statistic and why its shape is the problem, the sampling
                    model of the null, the controls — and, at the end, what would show the whole
                    thing is wrong.">
          <Base run={run} />
        </Block>
      )}

      {section === "provenance" && (
        <Block title="Where these numbers came from"
               sub="The manifest the analysis wrote. Nothing on this page is typed by hand; a
                    new adapter appears here without the interface knowing its name.">
          <Headline run={run} />
        </Block>
      )}
    </section>
  );
}

function Block({ title, sub, children }:
               { title: string; sub: string; children: React.ReactNode }) {
  return (
    <section className={css.block}>
      <div>
        <h3 className={css.h3}>{title}</h3>
        <p className={css.sub}>{sub}</p>
      </div>
      <div className={css.blockBody}>{children}</div>
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
