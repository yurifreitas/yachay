/** What individual patients say — the layer that existed on disk and was rendered nowhere.
 *
 *  Every other section of this atlas reads an aggregate catalogue: it can say a disease
 *  involves seizures and that a gene has nonsense variants. This one reads 10,377 people,
 *  and the difference is a denominator.
 *
 *  THREE VIEWS, AND EACH USES A FORM THIS APP DID NOT HAVE. The choice is not decoration —
 *  in each case the conventional chart destroys the thing being shown:
 *
 *    bias      FOREST PLOT      an effect with its interval, across four strata. A bar
 *                               chart of the point estimates would hide that one of the
 *                               four intervals crosses zero, which is the finding.
 *    agreement SCATTER + identity line. The single-case cloud is a vertical stripe at
 *                               x = 1.0 spanning the whole y range; no summary statistic
 *                               shows that shape, and the shape is the argument.
 *    clinvar   SANKEY           one category (our variants, all "pathogenic") splitting
 *                               into what the field actually says. A stacked bar loses the
 *                               "from one thing into many" reading that is the whole point.
 *
 *  The intervals arrived a day after the point estimates and corrected two published
 *  sentences (audit A26). Rendering the point estimate without its interval here would put
 *  the dashboard back where the prose was before that correction.
 */
import { useMemo, useState } from "react";
import { useRovingRadio } from "../../../lib/useRovingRadio";
import { EChart } from "../../../components/organisms/EChart";
import { chartInk, diverging } from "../../../lib/palette";
import { useHashParam } from "../../../lib/useHashParam";
import {
  clinvarEvidence, intervals, patientFrequencies, patientVariants,
} from "../data/patient";
import { BUCKET_ORDER, forestDomain } from "../patientModel";
import css from "./PatientEvidence.module.css";

const VIEWS = [
  { id: "bias", label: "What one patient is worth" },
  { id: "agreement", label: "Catalogue against patients" },
  { id: "clinvar", label: "What the field says back" },
];

const nf = (v: number) => v.toLocaleString("en-US");

export function PatientEvidence() {
  const [view, setView] = useHashParam("p", "bias");
  const nav = useRovingRadio(VIEWS.map((v) => v.id), view, setView);
  const pf = patientFrequencies;

  return (
    <div className={css.root}>
      <p className={css.caveat}>
        <span className={css.caveatTag}>read this first</span>
        {pf.caveat}
      </p>

      <div className={css.viewNav} {...nav.group} aria-label="Patient evidence views">
        {VIEWS.map((v) => (
          <button key={v.id} type="button" {...nav.option(v.id)}
                  className={view === v.id ? css.viewOn : css.view}
                  onClick={() => setView(v.id)}>
            {v.label}
          </button>
        ))}
      </div>

      {view === "bias" && <Bias />}
      {view === "agreement" && <Agreement />}
      {view === "clinvar" && <ClinVar />}

      <p className={css.provenance}>
        {nf(pf.scale.patients)} patients · {nf(pf.scale.distinctDiseases)} diseases ·{" "}
        {nf(pf.scale.publications)} publications · {nf(patientVariants.scale.variants)}{" "}
        variants over {nf(patientVariants.scale.genes)} genes. Intervals from{" "}
        {nf(intervals.resamples)} resamples. {intervals.resamplingUnit}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------- view 1: forest --- */

function Bias() {
  const buckets = patientFrequencies.singleCaseBias.byCuratedDenominator;
  const rows = useMemo(
    () => BUCKET_ORDER.filter((b) => buckets[b]).map((b) => {
      const v = buckets[b];
      const ci = v.interval?.meanDifference;
      return {
        bucket: b, pairs: v.pairs,
        point: v.meanPatientFrequency - v.meanCuratedPoint,
        lo: ci ? ci[0] : null, hi: ci ? ci[1] : null,
        excludesZero: v.interval?.excludesZero ?? false,
        curated: v.meanCuratedPoint, patient: v.meanPatientFrequency,
      };
    }),
    [buckets]
  );
  const domain = forestDomain(rows);

  return (
    <>
      <p className={css.lede}>
        Grouped by the denominator <strong>the catalogue</strong> used. A curated frequency
        of <code>1/1</code> reads 100 % and is a <strong>selected observation</strong> — the
        first patient written up is not a random patient, and the feature that got them
        written up is the one most likely to be recorded. Selecting the largest of a few
        noisy estimates is positively biased, and the bias should shrink as the denominator
        grows. It does.
      </p>

      {/* A FOREST PLOT. Point estimate and interval per stratum, on one axis, with zero
          drawn — because whether an interval crosses zero is the entire reading and a bar
          chart of the four point estimates hides it. */}
      <div className={css.chart}>
        <EChart
          height={260}
          deps={[rows]}
          ariaLabel={
            "Forest plot of the difference between patient-derived and curated frequency, "
            + "by the denominator the catalogue used. " +
            rows.map((r) => `${r.bucket}: ${r.point.toFixed(3)}, interval `
              + `${r.lo?.toFixed(3)} to ${r.hi?.toFixed(3)}, `
              + `${r.excludesZero ? "excludes" : "includes"} zero`).join(". ")
          }
          build={(mode) => {
            const ink = chartInk(mode);
            const div = diverging(mode);
            const under = div[0];
            const over = div[div.length - 1];
            const ordered = [...rows].reverse();     // ECharts draws bottom-up
            return {
              grid: { left: 92, right: 132, top: 20, bottom: 44 },
              xAxis: {
                type: "value", min: domain[0], max: domain[1],
                name: "patient frequency − curated frequency",
                nameLocation: "middle", nameGap: 28,
                nameTextStyle: { color: ink.muted, fontSize: 11 },
                axisLine: { show: false }, axisTick: { show: false },
                splitLine: { lineStyle: { color: ink.grid } },
                axisLabel: { color: ink.muted },
              },
              yAxis: {
                type: "category", data: ordered.map((r) => r.bucket),
                axisLine: { show: false }, axisTick: { show: false },
                axisLabel: { color: ink.text, fontSize: 12 },
              },
              tooltip: {
                trigger: "item", backgroundColor: ink.surface, borderColor: ink.grid,
                textStyle: { color: ink.text },
                formatter: (p: { dataIndex: number }) => {
                  const r = ordered[p.dataIndex];
                  return `<strong>curated ${r.bucket}</strong><br/>`
                    + `${nf(r.pairs)} pairs<br/>`
                    + `catalogue ${r.curated.toFixed(3)} · patients ${r.patient.toFixed(3)}<br/>`
                    + `difference ${r.point.toFixed(3)} [${r.lo?.toFixed(3)}, ${r.hi?.toFixed(3)}]<br/>`
                    + (r.excludesZero ? "excludes zero" : "<b>includes zero</b>");
                },
              },
              series: [
                {
                  // The whisker, drawn as a thin bar from lo to hi.
                  type: "custom",
                  renderItem: (_p: unknown, api: {
                    value: (i: number) => number;
                    coord: (v: [number, number]) => [number, number];
                  }) => {
                    const y = api.coord([0, api.value(0)])[1];
                    const [x0] = api.coord([api.value(1), 0]);
                    const [x1] = api.coord([api.value(2), 0]);
                    const excl = api.value(3) === 1;
                    const colour = excl ? (api.value(4) < 0 ? under : over) : ink.muted;
                    return {
                      type: "group",
                      children: [
                        { type: "line", shape: { x1: x0, y1: y, x2: x1, y2: y },
                          style: { stroke: colour, lineWidth: 2 } },
                        { type: "line", shape: { x1: x0, y1: y - 5, x2: x0, y2: y + 5 },
                          style: { stroke: colour, lineWidth: 2 } },
                        { type: "line", shape: { x1: x1, y1: y - 5, x2: x1, y2: y + 5 },
                          style: { stroke: colour, lineWidth: 2 } },
                      ],
                    };
                  },
                  data: ordered.map((r, i) => [i, r.lo ?? 0, r.hi ?? 0,
                                               r.excludesZero ? 1 : 0, r.point]),
                  silent: true,
                },
                {
                  type: "scatter", symbolSize: 13,
                  data: ordered.map((r) => ({
                    value: [r.point, r.bucket],
                    itemStyle: {
                      color: r.excludesZero ? (r.point < 0 ? under : over) : ink.muted,
                    },
                  })),
                  markLine: {
                    silent: true, symbol: "none",
                    label: { formatter: "no difference", color: ink.muted, fontSize: 10,
                             position: "end" },
                    lineStyle: { color: ink.muted, type: "dashed", width: 1 },
                    data: [{ xAxis: 0 }],
                  },
                  label: {
                    show: true, position: "right", distance: 12, fontSize: 11,
                    color: ink.text,
                    formatter: (p: { dataIndex: number }) => {
                      const r = ordered[p.dataIndex];
                      return `${r.point >= 0 ? "+" : ""}${r.point.toFixed(3)}`;
                    },
                  },
                },
              ],
            };
          }}
        />
      </div>

      <ul className={css.readings}>
        {rows.map((r) => (
          <li key={r.bucket} className={css.reading}>
            <span className={css.bucket}>{r.bucket}</span>
            <span className={r.excludesZero ? css.real : css.null_}>
              {r.excludesZero ? "excludes zero" : "includes zero"}
            </span>
            <span className={css.readingText}>
              {r.bucket === "n=1"
                ? "the catalogue reads 0.932 where the patients say 0.436"
                : r.excludesZero
                ? (r.point < 0
                  ? "a small real overstatement remains"
                  : "the curated value is slightly conservative here")
                : "no detectable difference at all — not a small one"}
            </span>
          </li>
        ))}
      </ul>

      <p className={css.note}>
        The n = 5–19 row is the one to read carefully. Its interval crosses zero, so the
        honest statement is <em>no detectable difference</em> — which is not the same as a
        small one, and the prose said otherwise until the intervals were computed.
      </p>
    </>
  );
}

/* ----------------------------------------------------------------- view 2: scatter ---- */

function Agreement() {
  const worst = patientFrequencies.agreement.worst;
  const [onlySingle, setOnlySingle] = useState(false);
  const shown = onlySingle ? worst.filter((w) => w.curatedN === 1) : worst;

  return (
    <>
      <div className={css.tiles}>
        <Tile label="Comparable pairs" value={nf(patientFrequencies.agreement.comparable)}
              note="both a curated frequency and a computed one" />
        <Tile label="Agree within 20 points"
              value={nf(patientFrequencies.agreement.within20points)} note="most of them" />
        <Tile label="Differ by 50 or more"
              value={nf(patientFrequencies.agreement.differBy50PointsOrMore)}
              note="and they are not scattered" tone="bad" />
        <Tile label="Patient side has the larger denominator"
              value={nf(patientFrequencies.agreement.biggerDenominator.patients ?? 0)}
              note="91 % of comparable pairs" />
      </div>

      <label className={css.toggle}>
        <input type="checkbox" checked={onlySingle}
               onChange={(e) => setOnlySingle(e.target.checked)} />
        show only the pairs the catalogue rests on a single patient
      </label>

      {/* SCATTER WITH THE IDENTITY LINE. Agreement is the diagonal; the single-case pairs
          form a vertical stripe at x = 1.0 spanning the whole y range, because a 1/1
          frequency is always 100 % whatever the patients show. No summary statistic
          renders that shape and the shape is the argument. */}
      <div className={css.chart}>
        <EChart
          height={340}
          deps={[shown]}
          ariaLabel={
            "Scatter of curated frequency against patient-derived frequency for the "
            + `${shown.length} largest disagreements, with the line of agreement drawn. `
            + "Points on the right edge are curated frequencies of 100 percent."
          }
          build={(mode) => {
            const ink = chartInk(mode);
            const div = diverging(mode);
            return {
              grid: { left: 62, right: 24, top: 20, bottom: 52 },
              xAxis: {
                type: "value", min: 0, max: 1, name: "curated frequency",
                nameLocation: "middle", nameGap: 30,
                nameTextStyle: { color: ink.muted, fontSize: 11 },
                axisLine: { show: false }, axisTick: { show: false },
                splitLine: { lineStyle: { color: ink.grid } },
                axisLabel: { color: ink.muted, formatter: (v: number) => `${v * 100}%` },
              },
              yAxis: {
                type: "value", min: 0, max: 1, name: "patient-derived",
                nameLocation: "middle", nameGap: 42,
                nameTextStyle: { color: ink.muted, fontSize: 11 },
                axisLine: { show: false }, axisTick: { show: false },
                splitLine: { lineStyle: { color: ink.grid } },
                axisLabel: { color: ink.muted, formatter: (v: number) => `${v * 100}%` },
              },
              tooltip: {
                trigger: "item", backgroundColor: ink.surface, borderColor: ink.grid,
                textStyle: { color: ink.text },
                formatter: (p: { data: { m: (typeof worst)[number] } }) => {
                  const m = p.data.m;
                  return `<strong>${m.termLabel}</strong><br/>${m.diseaseLabel}<br/>`
                    + `catalogue ${m.curatedRaw} · patients ${m.observed}/${m.assessed}`;
                },
              },
              series: [
                {
                  type: "line", silent: true, symbol: "none",
                  data: [[0, 0], [1, 1]],
                  lineStyle: { color: ink.muted, type: "dashed", width: 1 },
                  markPoint: {
                    silent: true, symbol: "rect", symbolSize: 0,
                    label: { formatter: "agreement", color: ink.muted, fontSize: 10 },
                    data: [{ coord: [0.86, 0.9] }],
                  },
                },
                {
                  type: "scatter",
                  symbolSize: (v: number[]) => Math.min(22, 6 + Math.sqrt(v[2] ?? 1) * 1.6),
                  data: shown.map((m) => ({
                    value: [m.curatedPoint, m.frequency, m.assessed],
                    m,
                    itemStyle: {
                      color: m.curatedN === 1 ? div[0] : div[div.length - 1],
                      opacity: 0.85, borderColor: ink.surface, borderWidth: 1,
                    },
                  })),
                },
              ],
            };
          }}
        />
      </div>

      <p className={css.note}>
        Marker size is the number of patients actually assessed. Points below the dashed line
        are features the catalogue records as more common than the patients show. The stripe
        at the right edge is <code>1/1</code>: a frequency of one patient is always 100 %,
        whatever anyone found afterwards.
      </p>
    </>
  );
}

/* ------------------------------------------------------------------ view 3: sankey ---- */

function ClinVar() {
  const cv = clinvarEvidence;
  const cc = cv.crossCheck;

  return (
    <>
      <div className={css.tiles}>
        <Tile label="ClinVar of uncertain significance"
              value={`${(cv.significance.vusShare * 100).toFixed(1)}%`}
              note={`${nf(cv.scale.grch38Rows)} GRCh38 records`} tone="bad" />
        <Tile label="At one star or less"
              value={`${(cv.reviewStatus.shareAtOneStarOrLess * 100).toFixed(1)}%`}
              note="on ClinVar's own review scale" tone="bad" />
        <Tile label="Our variants, all pathogenic by construction"
              value={nf(cc.patientVariants)} note="the answer key" />
        <Tile label="Absent from ClinVar entirely" value={nf(cc.notInClinVar)}
              note={`${Math.round(100 * cc.notInClinVar / cc.patientVariants)}% of the corpus`}
              tone="gap" />
      </div>

      {/* A SANKEY. One category — our variants, every one classified PATHOGENIC — splitting
          into what the wider field says about the same coordinates. A stacked bar would
          show the same numbers and lose the "from one thing into many" reading, which is
          the entire point of a cross-check. */}
      <div className={css.chart}>
        <EChart
          height={320}
          ariaLabel={
            `Flow from ${cc.patientVariants} patient variants, all classified pathogenic, `
            + `into what ClinVar says: ${Object.entries(cc.bySignificance)
                .map(([k, v]) => `${v} ${k}`).join(", ")}, and ${cc.notInClinVar} absent.`
          }
          build={(mode) => {
            const ink = chartInk(mode);
            const div = diverging(mode);
            const colourFor = (k: string) =>
              k.includes("pathogenic") && !k.includes("benign") ? div[div.length - 1]
              : k.includes("benign") ? div[0]
              : k === "absent from ClinVar" ? ink.muted
              : div[Math.floor(div.length / 2)];

            // Typed explicitly: `Object.entries` widens to (string|number)[][] once the
            // literal row is appended, and the tuple type is what keeps the sort honest.
            const targets: [string, number][] = ([
              ...Object.entries(cc.bySignificance),
              ["absent from ClinVar", cc.notInClinVar] as [string, number],
            ] as [string, number][]).filter((t) => t[1] > 0).sort((a, b) => b[1] - a[1]);

            return {
              tooltip: {
                trigger: "item", backgroundColor: ink.surface, borderColor: ink.grid,
                textStyle: { color: ink.text },
              },
              series: [{
                type: "sankey",
                left: 8, right: 190, top: 12, bottom: 12,
                nodeWidth: 14, nodeGap: 10,
                label: { color: ink.text, fontSize: 11 },
                lineStyle: { color: "gradient", opacity: 0.42 },
                data: [
                  { name: "our patients: PATHOGENIC",
                    itemStyle: { color: div[div.length - 1] } },
                  ...targets.map(([k]) => ({ name: k, itemStyle: { color: colourFor(k) } })),
                ],
                links: targets.map(([k, v]) => ({
                  source: "our patients: PATHOGENIC", target: k, value: v,
                })),
              }],
            };
          }}
        />
      </div>

      <p className={css.note}>
        Every variant on the left is <code>PATHOGENIC</code> by construction —
        phenopacket-store holds solved cases. The right-hand side is what the field submitted
        about the same coordinates. It does not make the published cases wrong: a variant can
        be causative in one family and never submitted, and ClinVar lags the literature. It
        does mean every rate computed over this corpus inherits a classification the wider
        field has not confirmed.
      </p>
    </>
  );
}

/* ---------------------------------------------------------------------- shared -------- */

function Tile({ label, value, note, tone }:
              { label: string; value: string; note: string; tone?: "bad" | "gap" }) {
  return (
    <div className={css.tile}>
      <span className={css.tileLabel}>{label}</span>
      <span className={`${css.tileValue} ${tone ? css[tone] : ""}`}>{value}</span>
      <span className={css.tileNote}>{note}</span>
    </div>
  );
}
