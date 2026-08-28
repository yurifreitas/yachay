/** The parts of a screen the explorer was not showing: the shortlist, the populations, the
 *  selectivity plane, and what the numbers rest on.
 *
 *  THE MISSING DELIVERABLE. This project's own one-line description is "screen → defensible
 *  shortlist", and the explorer showed six diagnostics and no shortlist. Diagnostics justify a
 *  result; they are not the result. The first panel here is the list, with its inclusion rule
 *  stated above it and its exclusions counted, because a shortlist whose rule is invisible is
 *  an opinion with a table around it.
 *
 *  THE FINDING WAS ALREADY IN THE MANIFEST. `pan_essential_in_raw_top10 = 0.6` says six of the
 *  ten best raw scores are genes that every cell line needs. That is the whole argument for
 *  calibration, sitting unrendered in a JSON file while the page drew ridgelines. It is now the
 *  headline of the populations panel.
 *
 *  ADAPTER-OPTIONAL COLUMNS. A run is only guaranteed to carry (entity, score, n, z). Anything
 *  richer — a control flag, a selectivity, a per-gene median — is adapter-specific, so every
 *  panel here checks for its columns and says plainly when they are absent rather than
 *  rendering an empty axis.
 */
import { useMemo, useState } from "react";
import type { Entity, Run } from "../../lib/dataTypes";
import { fmt, fmtInt, log } from "../../lib/scale";
import { symlog } from "../../lib/viz/scales";
import { HexbinPlot } from "../../components/viz/organisms/HexbinPlot";
import { RaincloudPlot, type RaincloudGroup } from "../../components/viz/organisms/RaincloudPlot";
import { UpSetPlot } from "../../components/viz/organisms/UpSetPlot";
import { RuleX, RuleY } from "../../components/viz/atoms/Axis";
import css from "./Substance.module.css";

const truthy = (v: unknown) => v === true || v === "True" || v === "true" || v === 1;
const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);

type Klass = "control" | "essential" | "candidate";

function classify(e: Entity): Klass {
  if (truthy(e.is_nonessential_control)) return "control";
  if (truthy(e.is_common_essential)) return "essential";
  return "candidate";
}

const KLASS_LABEL: Record<Klass, string> = {
  control: "non-essential control",
  essential: "common essential",
  candidate: "candidate",
};

/* ------------------------------------------------------------------ shortlist */

export function Shortlist({ run }: { run: Run }) {
  const [n, setN] = useState(25);
  const rows = run.entities ?? [];
  const hasClass = rows.some((r) => r.is_common_essential !== undefined);

  const { list, dropped, verdict } = useMemo(() => {
    const sorted = [...rows].sort((a, b) => b.z - a.z);
    const pool = hasClass ? sorted.filter((r) => classify(r) === "candidate") : sorted;
    const picked = pool.slice(0, n);

    // Grade the list against the pool it came from, on the two columns that define the word.
    // A median is used rather than a mean because both distributions are heavily skewed and a
    // mean would be reporting the tail rather than the list.
    const med = (v: number[]) =>
      (v.length ? [...v].sort((a, b) => a - b)[Math.floor(v.length / 2)] : null);
    const col = (set: Entity[], key: string) =>
      set.map((r) => num(r[key])).filter((x): x is number => x !== null);

    const selList = med(col(picked, "selectivity"));
    const selPool = med(col(pool, "selectivity"));
    const depList = med(col(picked, "median_dependency"));
    const depPool = med(col(pool, "median_dependency"));

    return {
      list: picked,
      dropped: sorted.length - pool.length,
      verdict: (selList !== null && selPool !== null)
        ? { selList, selPool, depList, depPool, pool: pool.length }
        : null,
    };
  }, [rows, n, hasClass]);

  return (
    <div className={css.wrap}>
      <div className={css.rule}>
        <span className={css.ruleL}>The inclusion rule, stated before the table</span>
        <p>
          Rank by calibrated <span className={css.mono}>z</span>, not by raw score.
          {hasClass && (
            <>
              {" "}Then remove the genes flagged common-essential: a gene every cell line needs
              is a true dependency and a useless <em>selective</em> one, and leaving them in is
              how a screen produces a shortlist of ribosome subunits.{" "}
              <strong>{fmtInt(dropped)}</strong> of {fmtInt(rows.length)} shipped rows are
              removed by that clause.
            </>
          )}
          {!hasClass && " This adapter ships no essentiality flag, so nothing is excluded and the list is the raw top of the calibrated order."}
        </p>
      </div>

      <div className={css.sizes}>
        <span className={css.label}>Show</span>
        {[10, 25, 50].map((k) => (
          <button key={k} type="button" onClick={() => setN(k)}
                  className={k === n ? css.sizeOn : css.size}>top {k}</button>
        ))}
      </div>

      {verdict && (
        <div className={css.verdict}>
          <span className={css.ruleL}>The list, graded against the pool it came from</span>
          <div className={css.verdictRow}>
            <VCell k="Median selectivity" a={fmt(verdict.selPool, 2)} b={fmt(verdict.selList, 2)}
                   note={`across ${fmtInt(verdict.pool)} candidates, then across this list`} />
            {verdict.depList !== null && verdict.depPool !== null && (
              <VCell k="Median dependency" a={fmt(verdict.depPool, 2)} b={fmt(verdict.depList, 2)}
                     note="how strong the dependency is where it exists" />
            )}
          </div>
          <p className={css.verdictSays}>
            On its own metrics the list passes and passes clearly: it is roughly three times as
            selective as the pool it was drawn from, and the dependency it names is strong where
            the pool&rsquo;s median is near zero.{" "}
            <strong>The names are the uncomfortable part.</strong> Ribosomal subunits,
            spliceosome components and proteasome subunits are the canonical pan-essential
            machinery, and they are here because this dataset&rsquo;s essentiality flag does not
            mark them. Either the flag is incomplete or these genes really are selective in this
            panel of lines — this page cannot tell which, and says so rather than choosing. It
            is exactly the failure the falsification criterion under <em>What this rests on</em>
            was written to catch, half-fired.
          </p>
        </div>
      )}

      <div className={css.scrollX}>
        <table className={css.table}>
          <thead>
            <tr>
              <th>#</th><th>Entity</th>
              <th className={css.r}>z</th>
              <th className={css.r}>raw score</th>
              <th className={css.r}>raw rank</th>
              <th className={css.r}>n</th>
              <th className={css.r}>selectivity</th>
              <th className={css.r}>median dependency</th>
            </tr>
          </thead>
          <tbody>
            {list.map((r, i) => {
              const sel = num(r.selectivity);
              const med = num(r.median_dependency);
              const rawRank = num(r.rank_raw);
              return (
                <tr key={r.entity}>
                  <td className={css.dim}>{i + 1}</td>
                  <td className={css.entity}>{r.entity}</td>
                  <td className={css.r}><strong>{fmt(r.z, 1)}</strong></td>
                  <td className={css.r}>{fmt(r.score, 3)}</td>
                  <td className={css.r}>
                    {rawRank === null ? "—" : (
                      <span className={rawRank > (i + 1) * 3 ? css.promoted : css.dim}>
                        #{fmtInt(rawRank)}
                      </span>
                    )}
                  </td>
                  <td className={css.r}>{fmtInt(r.n)}</td>
                  <td className={css.r}>
                    {sel === null ? "—" : (
                      <span className={css.barCell}>
                        <span className={css.bar} style={{ width: `${Math.max(2, sel * 100)}%` }} />
                        <span className={css.barN}>{fmt(sel, 2)}</span>
                      </span>
                    )}
                  </td>
                  <td className={css.r}>{med === null ? "—" : fmt(med, 2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className={css.foot}>
        A raw rank far below the row number means the gene was promoted by calibration — it
        scored modestly against a null that was low, which is the only kind of promotion this
        method can defend. The table is drawn over the{" "}
        {fmtInt(rows.length)} entities in the bundle, not all{" "}
        {fmtInt(run.entitiesTotal)}; the ranks in the columns were computed in Python over all
        of them.
      </p>
    </div>
  );
}

/* --------------------------------------------------------------- populations */

export function Populations({ run }: { run: Run }) {
  const rows = run.entities ?? [];
  const h = run.headline as Record<string, number | string>;

  /* THE BOX PLOT IS GONE. It drew five numbers per class and this panel exists to answer
     "do the controls sit at the null and do the candidates separate from it" — a question
     about SHAPE. Two classes with identical quartiles can be unimodal and bimodal, and the
     box drew them the same. The z distribution here has its first quartile at -1.4 and its
     median at +12.7, which is not a spread around a centre at all; it is two populations,
     and the old figure could not say so. */
  const clouds = useMemo<RaincloudGroup[]>(() => {
    const by: Record<Klass, number[]> = { control: [], essential: [], candidate: [] };
    rows.forEach((r) => by[classify(r)].push(r.z));
    const colour: Record<Klass, string> = {
      candidate: "var(--series-1)",
      essential: "var(--series-2)",
      control: "var(--series-3)",
    };
    return (Object.keys(by) as Klass[])
      .filter((k) => by[k].length > 0)
      .map((k) => ({ label: KLASS_LABEL[k], values: by[k], color: colour[k] }));
  }, [rows]);

  if (!clouds.length) return null;

  return (
    <div className={css.wrap}>
      {typeof h.pan_essential_in_raw_top10 === "number" && (
        <div className={css.finding}>
          <span className={css.findingV}>
            {Math.round((h.pan_essential_in_raw_top10 as number) * 100)}%
          </span>
          <p>
            of the <strong>raw</strong> top ten are pan-essential genes — genes every cell line
            needs. That is not a selective dependency, it is a measurement of how many
            observations a gene had. This one number is the entire case for calibrating, and it
            was sitting in the manifest unrendered while the page drew diagnostics around it.
          </p>
        </div>
      )}

      <RaincloudPlot
        groups={clouds}
        xLabel="calibrated z"
        zeroLine={0}
        ariaLabel="Distribution of calibrated z for candidates, common-essential genes and non-essential controls, drawn as densities with every observation shown"
        readAloud={
          <>
            Each row is one class. The filled shape on top is the distribution&rsquo;s
            <em> density</em> — where the humps are is where the genes are; the thin bar under
            it is the quartile summary; the dots at the bottom are the genes themselves, moved
            apart sideways only, never along the axis that carries the value. A row with two
            humps is two populations, which no box plot could have told you.
          </>
        }
      />

      <p className={css.mismatch}>
        <strong>These three rows are drawn on the shipped sample, and the control row is not
        the calibration test.</strong> The bundle carries{" "}
        {fmtInt(clouds.find((g) => g.label === KLASS_LABEL.control)?.values.length ?? 0)} of the{" "}
        {fmtInt(h.control_genes as number)} control genes in the run &mdash; a density-preserving
        sample of the whole score distribution is not a representative sample of a small labelled
        subset, and at this size it lands well away from zero. Reading it as a failed
        calibration would be reading the sampling, which is the error this site keeps finding
        elsewhere. The test is the full-run figure below.
        {typeof h.nonessential_mean_z === "number" && (
          <>
            {" "}Across all {fmtInt(h.control_genes as number)} control genes, computed in
            Python over the whole run, the mean is{" "}
            <strong>{fmt(h.nonessential_mean_z as number, 3)}</strong> and the standard
            deviation <strong>{fmt(h.nonessential_sd_z as number, 3)}</strong> — which is what
            passing looks like.
          </>
        )}
      </p>
    </div>
  );
}

/* --------------------------------------------------------------- selectivity */

export function Selectivity({ run }: { run: Run }) {
  const [hide, setHide] = useState(false);
  const rows = run.entities ?? [];
  const usable = useMemo(
    () => rows.filter((r) => num(r.selectivity) !== null && num(r.median_dependency) !== null),
    [rows],
  );

  const xs = useMemo(() => Float64Array.from(usable, (r) => num(r.median_dependency) as number), [usable]);
  const ys = useMemo(() => Float64Array.from(usable, (r) => num(r.selectivity) as number), [usable]);

  if (!usable.length) {
    return (
      <p className={css.absent}>
        This adapter does not ship a selectivity or a per-entity median, so the plane cannot be
        drawn. Said rather than rendered as an empty axis.
      </p>
    );
  }

  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);

  const colour: Record<Klass, string> = {
    candidate: "var(--series-1)",
    essential: "var(--series-2)",
    control: "var(--series-3)",
  };

  return (
    <div className={css.wrap}>
      <p className={css.sub}>
        The two axes that define the word <em>selective</em>. Horizontal: how strong the
        dependency is where it exists. Vertical: how concentrated it is in a few lines. A gene
        in the top-right is strongly needed and needed almost everywhere — real, and useless as
        a target. The interesting quadrant is top-left: needed hard, by few.
      </p>

      <label className={css.check}>
        <input type="checkbox" checked={hide} onChange={(e) => setHide(e.target.checked)} />
        Hide common-essential genes
      </label>

      {/* BOTH AXES ARE NON-LINEAR, AND BOTH SAY SO.
          Median dependency runs from -0.48 to +4.37 with its middle half inside [-0.17, 1.83]:
          on a linear axis three quarters of the width is spent on a tail holding a handful of
          genes, and the bulk the argument is about becomes a vertical smear. It also crosses
          zero, so a log axis is not available — hence symlog, linear within +/-0.25 and
          logarithmic outside it. Selectivity is strictly positive and right-skewed, so it
          takes a plain log.

          The previous version of this figure drew 800 circles on linear axes. The core was a
          solid blob in which fifty genes and five hundred looked identical, which is the one
          thing a plane like this must not do. */}
      <HexbinPlot
        id="selectivity"
        xs={xs}
        ys={ys}
        x={(range) => symlog([xMin * 1.05, xMax * 1.05], range, 0.25)}
        y={(range) => log([Math.max(1e-3, yMin * 0.9), yMax * 1.1], range)}
        keep={hide ? (i) => classify(usable[i]) !== "essential" : undefined}
        colorOf={(i) => colour[classify(usable[i])]}
        labelOf={(i) => usable[i].entity}
        radius={9}
        pointThreshold={2}
        xLabel="median dependency where it exists"
        xNote="symlog, linear within ±0.25"
        yLabel="selectivity"
        yNote="log"
        xFormat={(v) => fmt(v, 2)}
        yFormat={(v) => fmt(v, 2)}
        ariaLabel="Median dependency against selectivity, drawn as hexagonal density with sparse cells shown as individual genes"
        readAloud={
          <>
            Each hexagon holds the genes that fell inside it; darker means more of them. Where
            a cell holds two genes or fewer it is replaced by the genes themselves, coloured by
            class — so the crowded regions read as density and the sparse edges, where a
            screen&rsquo;s candidates live, read as individuals you can hover and name. Both
            axes are non-linear and say so under their labels.
          </>
        }
        /* Two reference lines and no quadrant caption. The caption named a corner, and a
           caption that names a corner is a second claim about the data drawn in a place the
           data cannot contradict — the prose above already makes that argument, where it can
           be read against the axes. The rules mark the two values that are definitions
           rather than opinions: zero dependency, and selectivity one. */
        annotations={(box, x, y) => (
          <>
            <RuleX at={x(0)} box={box} label="no dependency" />
            <RuleY at={y(1)} box={box} label="selectivity 1" />
          </>
        )}
      />

      <div className={css.legend}>
        {(["candidate", "essential", "control"] as Klass[]).map((k) => (
          <span key={k} className={css.legendItem}>
            <i className={css.swatch} data-k={k} /> {KLASS_LABEL[k]}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- flag overlap */

/** THE FIGURE THAT CHECKS THE REST OF THE SITE'S BOOKKEEPING.
 *
 *  Everywhere else an entity gets exactly one class, because a legend wants three colours.
 *  `classify` decides that with an if-else chain, so a gene that is both a labelled control
 *  and a top-ranked candidate is silently filed as a control and never appears as a
 *  candidate again. Nothing in the interface could show that this had happened.
 *
 *  Here the flags are treated as what they are — overlapping sets — and the raw and
 *  calibrated top hundreds are added as two more. The bar over "common essential AND raw top
 *  100" is the site's central claim rendered as a count: those are the genes the uncalibrated
 *  ranking would have handed you.
 */
export function FlagOverlap({ run }: { run: Run }) {
  const rows = run.entities ?? [];

  const sets = useMemo(() => {
    if (!rows.length) return [];
    const byRaw = [...rows].sort((a, b) => b.score - a.score).slice(0, 100);
    const byCal = [...rows].sort((a, b) => b.z - a.z).slice(0, 100);
    const rawTop = new Set(byRaw.map((r) => r.entity));
    const calTop = new Set(byCal.map((r) => r.entity));
    return [
      { name: "raw top 100", has: (i: number) => rawTop.has(rows[i].entity) },
      { name: "calibrated top 100", has: (i: number) => calTop.has(rows[i].entity) },
      { name: "common essential", has: (i: number) => truthy(rows[i].is_common_essential) },
      { name: "non-essential control", has: (i: number) => truthy(rows[i].is_nonessential_control) },
      // 2.326 is the one-sided normal 99th percentile — the same cutoff the noise-floor
      // figure draws, so the two panels cannot disagree about what "clears the floor" means.
      { name: "clears the noise p99", has: (i: number) => rows[i].z > 2.326 },
    ];
  }, [rows]);

  if (!rows.length) return null;

  return (
    <div className={css.wrap}>
      <UpSetPlot
        count={rows.length}
        sets={sets}
        itemLabel="genes"
        labelOf={(i) => rows[i].entity}
        ariaLabel="Sizes of every combination of flags carried by the genes in the shipped sample"
        readAloud={
          <>
            Read a column: the dark dots say which flags that group of genes carries, and the
            bar above says how many genes are in it. Left, the size of each flag on its own.
            The column with dots on <em>raw top 100</em> and <em>common essential</em> is the
            argument for calibrating, counted: genes the uncalibrated ranking would have put in
            front of you that every cell line needs anyway.
          </>
        }
      />
    </div>
  );
}

/* ---------------------------------------------------------------------- base */

export function Base({ run }: { run: Run }) {
  const h = run.headline as Record<string, number | string>;
  const nulls = run.null ?? [];
  return (
    <div className={css.wrap}>
      <div className={css.baseGrid}>
        <Fact k="What was measured"
              v={`${fmtInt(h.cell_lines as number)} cell lines × ${fmtInt(h.genes_scored as number)} genes`}
              s="A genome-wide CRISPR knockout screen: every gene disabled in every line, and the effect on proliferation scored. The score is a per-line dependency, so the matrix is genes by lines and the question is which genes matter in FEW lines." />
        <Fact k="The statistic" v={String(run.statistic)}
              s="The mean of the twenty most-dependent lines per gene. It is a MAX-ORDER statistic: an extreme of a sample, and an extreme rises with sample size on its own. That property is the reason this whole library exists." />
        <Fact k="Reduction" v={String(run.reduce)}
              s="How observations are combined before scoring. `raw` means each line contributes its own value; the sampling model of the null has to match this choice or the calibration is against the wrong thing." />
        <Fact k="The null" v={`${nulls.length} fitted points, blocks by ${String(h.null_blocks)}`}
              s="One null distribution per observation count, resampled with blocks shaped like genes rather than by pooling rows. Pooling rows breaks the correlation structure and produces a null that is far too tight — which is how a control came back at −4." />
        <Fact k="Controls" v={fmtInt(h.control_genes as number)}
              s="Genes known not to be essential. They should calibrate to a mean near zero and a spread near one, and they are the only part of this run that can fail visibly." />
        {typeof h.common_essential_mean_z === "number" && (
          <Fact k="Positive control" v={`z ${fmt(h.common_essential_mean_z as number, 1)}`}
                s="Mean calibrated z across the common-essential genes. A calibration that flattened everything would drag this toward zero too; that it stays high is what says the correction removed a confound rather than removing signal." />
        )}
        <Fact k="Count correlation, raw"
              v={fmt(h.count_spearman_raw as number, 3)}
              s="Spearman between the raw score and the observation count. Near zero here is not reassurance — the count only spans 3.4x in this dataset, so its influence shows up in the tail rather than in a global rank correlation." />
        <Fact k="Count correlation, calibrated"
              v={fmt(h.count_spearman_calibrated as number, 3)}
              s="The same correlation after calibration. Both being small is honest to report and weaker evidence than the control mean above." />
      </div>

      <div className={css.falsify}>
        <span className={css.ruleL}>What would show this is wrong</span>
        <ul>
          <li>
            Non-essential controls whose calibrated mean drifts from zero or whose spread
            departs from one. That is the primary check and it is drawn on this page.
          </li>
          <li>
            A common-essential mean z that collapses toward zero — it would mean the correction
            removed the signal along with the confound.
          </li>
          <li>
            A rank shift that is a clean diagonal: calibration changing nothing means either
            the counts do not vary or the null is not doing anything.
          </li>
          <li>
            A shortlist that is still dominated by pan-essential genes after the exclusion
            clause, which would mean the essentiality flag, not the statistic, was carrying the
            result.
          </li>
        </ul>
      </div>
    </div>
  );
}

function VCell({ k, a, b, note }: { k: string; a: string; b: string; note: string }) {
  return (
    <div className={css.vcell}>
      <span className={css.factK}>{k}</span>
      <span className={css.vpair}>
        <span className={css.vpool}>{a}</span>
        <span className={css.varrow} aria-hidden="true">&rarr;</span>
        <span className={css.vlist}>{b}</span>
      </span>
      <span className={css.factS}>{note}</span>
    </div>
  );
}

function Fact({ k, v, s }: { k: string; v: string; s: string }) {
  return (
    <div className={css.fact}>
      <span className={css.factK}>{k}</span>
      <span className={css.factV}>{v}</span>
      <span className={css.factS}>{s}</span>
    </div>
  );
}
