import { useMemo } from "react";
import { UpSetPlot } from "../../../components/viz/organisms/UpSetPlot";
import { gapPatterns, coOccurrence } from "../gapPatternsModel";
import { fmtInt, pct } from "../../../lib/scale";
import css from "./GapPatterns.module.css";

/** WHICH GAPS COME TOGETHER — the third row of `docs/references/visualization-canon.md` §7b,
 *  which had stood as "Not built" since the canon was written.
 *
 *  The gap matrix elsewhere on this page shows twelve seeded diseases, one row each. It
 *  answers "what is missing for THIS disease" and structurally cannot answer "what is
 *  missing TOGETHER" — and the canon says so in its own words: *"the matrix shows which
 *  fields are empty per disease; it cannot show which patterns of emptiness are common."*
 *
 *  The distinction is not academic. If gaps were independent, filling them would be a
 *  curation backlog: 8,574 diseases, each short a field or two, work through the list. They
 *  are not independent. The largest single pattern in the catalogue is a disease missing its
 *  gene AND its onset AND every sign denominator at once, and those are not three tasks —
 *  they are one disease nobody has studied.
 *
 *  THE FIGURE IS BUILT FROM THE SHARED ORGANISM, which is the point of having built one: the
 *  run dashboard's flag overlap and this use the same component, the same set arithmetic and
 *  the same checked code. The only thing this file supplies is which sets, and the words.
 */
export function GapPatterns() {
  const g = gapPatterns;
  const co = useMemo(() => coOccurrence(g), [g]);

  /* The sets are handed in as predicates over a synthetic index, because the measurement
     arrives pre-aggregated: Python counted the combinations over 8,574 diseases, and
     shipping 8,574 rows to re-count them in a browser would be the second implementation
     this project forbids. Each combination becomes one item weighted by its size. */
  const { count, sets } = useMemo(() => {
    // COPIED, not aliased. The complete-record row is appended below, and pushing onto the
    // imported module object would grow the shipped data by one row every time this memo
    // re-ran — a mutation of a JSON import is invisible until the second render.
    const rows = [...g.combinations];
    const expanded: number[] = [];
    rows.forEach((c, i) => { for (let k = 0; k < c.size; k++) expanded.push(i); });
    // THE FULLY-RECORDED DISEASES ARE ITEMS TOO, carrying no gap. Handing the plot only the
    // gapped ones would make its own denominator the gapped subset, and every "% of all"
    // it prints would silently be a percentage of the wrong population. They cost one
    // integer each and they are half the catalogue.
    const none = rows.length;
    for (let k = 0; k < g.complete; k++) expanded.push(none);
    rows.push({ missing: [], size: g.complete });
    return {
      count: expanded.length,
      sets: g.fields.map((f) => ({
        name: `no ${f}`,
        has: (i: number) => rows[expanded[i]].missing.includes(f),
      })),
    };
  }, [g]);

  if (!g.combinations.length) {
    return (
      <p className={css.absent}>
        The gap-pattern measurement has not been generated. Run{" "}
        <code>python tools/gap_patterns.py</code>, then <code>npm run data</code>.
      </p>
    );
  }

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(co.shareOfGapped, 0)}</span>
        <p>
          of the diseases with any gap are missing <strong>three or more fields at once</strong>.
          Emptiness in this catalogue is not a scatter of independent blanks to be filled in;
          it is concentrated on diseases about which almost nothing is recorded. The single
          largest pattern — <em>{co.biggest?.missing.map((m) => `no ${m}`).join(", ")}</em> —
          covers {fmtInt(co.biggest?.size ?? 0)} diseases on its own.
        </p>
      </div>

      <UpSetPlot
        count={count}
        sets={sets}
        itemLabel="diseases"
        maxCombinations={14}
        height={220}
        ariaLabel="Sizes of every combination of missing fields across the OMIM-coded rare diseases"
        readAloud={
          <>
            Each column is a <em>pattern</em> of emptiness: the dark dots say which fields are
            missing together, and the bar says how many diseases carry exactly that pattern.
            The bars on the left are how often each field is missing on its own terms. A tall
            bar over four dots is not four small problems — it is one disease nobody has
            described.
          </>
        }
      />

      <dl className={css.numbers}>
        <div>
          <dt>Population</dt>
          <dd>{fmtInt(g.total)} OMIM-coded diseases</dd>
        </div>
        <div>
          <dt>All four fields recorded</dt>
          <dd>{fmtInt(g.complete)} ({pct(g.complete / g.total, 0)})</dd>
        </div>
        <div>
          <dt>Excluded as unjoinable</dt>
          <dd>{fmtInt(g.unjoinable)}</dd>
        </div>
      </dl>

      {/* THE JOIN FAILURE IS THE OTHER FINDING, and it is not a caveat.
          Prevalence was meant to be the fifth field. It came back missing for 100% of the
          population, which is the shape of a broken join rather than of a fact, so it was
          measured: ORPHA-coded rows in the HPO annotation file carry zero inheritance
          annotations and zero fractional frequencies, while prevalence exists only under
          ORPHA codes. The fields a reader would assume live in one catalogue do not. */}
      <p className={css.split}>
        <strong>Prevalence is not one of the four, and finding out why was the first result.</strong>{" "}
        {g.population} Any figure claiming to show &ldquo;what is known about a rare
        disease&rdquo; across gene, inheritance, onset, signs <em>and</em> prevalence is
        joining two populations that annotate different things — usually without saying so.
      </p>

      <p className={css.caveat}>{g.caveat} Measured by <code>{g.generated}</code> over{" "}
        {g.inputs.map((i) => <code key={i}>{i}</code>).reduce<React.ReactNode[]>(
          (acc, el, i) => (i ? [...acc, " and ", el] : [el]), [])}.
      </p>
    </div>
  );
}
