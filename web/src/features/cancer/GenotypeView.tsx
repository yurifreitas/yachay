import { useMemo } from "react";
import { useHashParam } from "../../lib/useHashParam";
import { useRemoteData } from "../../lib/useRemoteData";
import {
  byBurden, driverGateInputs, ladder, OBSERVED_TONE, proxyShare, regateDriver, withHits,
  type Driver, type GenoHit, type Genotype,
} from "../../lib/genotypeModel";
import { DEFAULT_REGISTERED } from "../../lib/cancerModel";
import GateControls, { useGates } from "./GateControls";
import s from "./CancerPage.module.css";
import g from "./GenotypeView.module.css";

const fmt = (n: number) => n.toLocaleString("en-US");

/** Genotype subgroups, and the two confounds between the question and the answer.
 *
 *  This view exists because the catalogue view answers a different question. "Melanoma" is a
 *  label someone assigned; "carries a damaging mutation in SMARCA4" is a property of the
 *  cell, and it is the one a target programme acts on.
 *
 *  Its centrepiece is deliberately NOT a target list. It is the confound ladder — the same
 *  effect estimated three ways, naive then lineage-stratified then burden-adjusted — because
 *  on this data the movement between those three is the finding. Ninety-two of a hundred and
 *  twenty-one drivers are substantially restating "this line is hypermutated", and a
 *  shortlist that did not show that would be confidently wrong.
 */
export default function GenotypeView() {
  const [pick, setPick] = useHashParam("driver", "");
  const remote = useRemoteData<Genotype>("data/cancer_genotype.json");

  if (remote.state === "loading") return <div className={g.skel} role="status" />;
  if (remote.state === "error") {
    return (
      <p className={s.error}>
        Could not load the genotype analysis ({remote.message}). It is written by{" "}
        <code>python tools/cancer_genotype.py</code>.
      </p>
    );
  }

  const data = remote.data;
  const drivers = withHits(data);
  const chosen = drivers.find((d) => d.driver === pick) ?? drivers[0];
  const proxy = proxyShare(data);
  const registered = data.gates?.registered ?? DEFAULT_REGISTERED;

  return (
    <>
      <div className={s.kpis}>
        <Kpi n={fmt(data.scale.genotypesTested)} label="genotypes tested"
             note={`mutated in at least 15 of ${fmt(data.scale.lines)} screened lines`} />
        <Kpi n={`${proxy.flagged}/${proxy.total}`} label="are burden proxies" tone="warn"
             note="their two arms separate by a large effect on mutational burden alone" />
        <Kpi n={fmt(data.scale.lineageStrata)} label="lineage strata"
             note="the contrast is computed inside each, then pooled by inverse variance" />
        <Kpi n={`${data.prediction.controlsAgreeing}/${data.prediction.controlsTestable}`}
             label="controls as predicted" tone="good"
             note="the prediction was written before the run, and half of it was untestable" />
      </div>

      <div className={s.finding}>
        <p className={s.findingTag}>What the data turned out to be</p>
        <h3>
          <strong>{proxy.pct}%</strong> of a frequency-ranked genotype list is substantially
          restating <strong>mutational burden</strong>, not genotype.
        </h3>
        <p>{data.confound.statement}</p>
        <p>
          Hypermutated lines carry damaging mutations everywhere, so a long gene becomes a
          synonym for &ldquo;this line is hypermutated&rdquo;. That is the pan-essential
          confound one level up: the top of the ranking is a property of the assay, not of the
          biology being asked about.
        </p>
        <p className={g.caution}>
          <strong>And it must not be adjusted away blindly.</strong> For a mismatch-repair
          gene the burden separation <em>is</em> the mechanism — MMR loss causes instability
          causes the WRN dependency — so conditioning on burden deletes a correct finding. For
          a passenger it removes an artefact. The arithmetic is identical and the data cannot
          tell them apart. Every estimate below is published; none is chosen for you.
        </p>
      </div>

      <Controls data={data} />

      <section className={s.panel}>
        <h3>Genotypes, by how far their arms separate on burden alone</h3>
        <p className={s.sub}>
          A long bar means the subgroup is close to a restatement of hypermutation. Flagged at
          0.8 &mdash; Cohen&rsquo;s large effect &mdash; and flagged only: nothing is dropped,
          because the flag cannot distinguish a mechanism from an artefact. Click to inspect.
        </p>
        <ul className={g.burdenList}>
          {byBurden(data).slice(0, 26).map((d) => (
            <li key={d.driver}>
              <button
                className={d.driver === chosen?.driver ? g.bRowOn : g.bRow}
                onClick={() => setPick(d.driver)}
                aria-pressed={d.driver === chosen?.driver}
                disabled={!d.hitCount}
              >
                <span className={g.bName}>{d.driver}</span>
                <span className={g.bTrack}>
                  <span className={g.bFlag} />
                  <span
                    className={d.burdenProxy ? g.bFillHot : g.bFill}
                    style={{ width: `${Math.min(100, (d.burdenSeparation / 4) * 100)}%` }}
                  />
                </span>
                <span className={g.bNum}>{d.burdenSeparation.toFixed(2)}</span>
                <span className={g.bLines}>{d.mutantLines}</span>
                <span className={d.hitCount ? g.bHits : g.bHitsNone}>
                  {d.hitCount ? `${d.hitCount} hits` : "—"}
                </span>
              </button>
            </li>
          ))}
        </ul>
        <p className={s.axisNote}>
          bar: standardised separation in log burden (dashed mark = 0.8) · columns: separation,
          mutant lines, hits
        </p>
      </section>

      {chosen && <GatedLadder driver={chosen} registered={registered} />}

      {/* THREE STATEMENTS THAT WERE IN THE ARTEFACT AND ON NO SCREEN.
          `isNot`, `method` and `gates.says` are where this analysis says what it is not, how
          it was computed, and — the one that actually changes how a reader should treat the
          screen above — that moving a slider produces a calibrated number and not a
          pre-registered one. An interface that offers the sliders and hides that sentence is
          letting the distinction blur, which is the thing the sentence exists to prevent. */}
      <section className={s.panel}>
        <h3>What this is not, and how it was computed</h3>
        <p className={g.caution}>{data.isNot}</p>
        <dl className={g.methodList}>
          {Object.entries(data.method ?? {}).map(([k, v]) => (
            <div key={k} className={g.methodRow}>
              <dt>{k.replace(/([A-Z])/g, " $1").toLowerCase()}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
        {data.gates?.says && <p className={s.axisNote}>{data.gates.says}</p>}
      </section>
    </>
  );
}

/** Predicted direction against what the stratification actually did.
 *
 *  One axis: the share of the naive effect still standing after lineage is removed. The
 *  prediction sorts the controls into two groups before the run — should survive, should
 *  shrink — and the question the plot answers is whether those two groups landed apart. If
 *  they overlap completely, stratification is flattening everything and the procedure is
 *  removing signal, which is the failure the prediction was written to detect.
 *
 *  Rows that could not be tested are drawn, greyed, on their own line rather than dropped: a
 *  damaging-mutation matrix has no BRAF V600E in it, and that absence is a result about the
 *  data. Deleting those rows would turn 6 of 8 into 6 of 6.
 */
function PredictionPlot({ data }: { data: Genotype }) {
  const rows = data.controls.map((c) => {
    const kept = c.dNaive && c.dNaive > 0 && c.dStratified != null
      ? Math.max(0, Math.min(1.3, c.dStratified / c.dNaive))
      : null;
    return { c, kept };
  });
  const groups: { key: string; label: string; note: string }[] = [
    { key: "survives", label: "predicted to survive",
      note: "a within-cell mechanism with no lineage story" },
    { key: "shrinks", label: "predicted to shrink",
      note: "real, but concentrated in one lineage" },
  ];

  return (
    <div className={g.predWrap}>
      {groups.map((grp) => {
        const mine = rows.filter(({ c }) => c.expected === grp.key);
        if (!mine.length) return null;
        return (
          <div key={grp.key} className={g.predBand}>
            <span className={g.predLabel}>
              {grp.label}
              <span className={g.predNote}>{grp.note}</span>
            </span>
            <div className={g.predTrack}>
              {/* 100 % is "stratification changed nothing"; the mark is the reference the
                  eye needs, because the claim is about distance from it. */}
              <span className={g.predRef} style={{ left: `${(100 / 1.3)}%` }} />
              {mine.map(({ c, kept }) => (
                <span key={`${c.driver}-${c.target}`}
                      className={c.observed && OBSERVED_TONE[c.observed] === "ok"
                        ? `${g.predDot} ${g.predDotOk}` : g.predDot}
                      style={{ left: kept == null ? "0%" : `${(100 * kept) / 1.3}%` }}
                      title={`${c.driver} → ${c.target}: ${
                        kept == null ? "not testable" : `${Math.round(100 * kept)} % kept`}`}>
                      <span className={g.predDotL}>{c.target}</span>
                </span>
              ))}
            </div>
          </div>
        );
      })}
      <div className={g.predAxis}>
        <span>0 %</span><span>the naive effect that survives stratification</span><span>130 %</span>
      </div>
      {rows.some(({ c }) => !c.observed) && (
        <p className={g.predUntested}>
          {rows.filter(({ c }) => !c.observed).length} of {rows.length} could not be tested at
          all, and are counted in the denominator rather than dropped.
        </p>
      )}
    </div>
  );
}

function Kpi(
  { n, label, note, tone }:
  { n: string; label: string; note: string; tone?: "good" | "warn" },
) {
  return (
    <div className={s.kpi} data-tone={tone}>
      <span className={s.kpiN}>{n}</span>
      <span className={s.kpiL}>{label}</span>
      <span className={s.kpiNote}>{note}</span>
    </div>
  );
}

/* ------------------------------------------------------- the pre-written control set */

function Controls({ data }: { data: Genotype }) {
  return (
    <section className={s.panel}>
      <h3>The prediction, and what happened to it</h3>
      <p className={s.sub}>{data.prediction.claim}</p>

      {/* THE CLAIM WAS DIRECTIONAL AND THE FIGURE WAS A TABLE.
          The prediction does not say "these will be significant" — it says paralog synthetic
          lethality should SURVIVE stratification and oncogene addiction should SHRINK, and
          that if everything flattened equally the procedure would be removing signal rather
          than confound. Eleven rows of eight numeric columns is where you check a row; it is
          not where you see whether two predicted groups actually separated. They are the same
          numbers, on one axis, split by what was predicted before the run. */}
      <PredictionPlot data={data} />

      <div className={g.tableWrap}>
        <table className={s.table}>
          <thead>
            <tr>
              <th>Genotype &rarr; target</th><th>Mechanism</th>
              <th className={g.num}>naive</th>
              <th className={g.num}>lineage</th>
              <th className={g.num}>burden-adj.</th>
              <th className={g.num}>burden sep.</th>
              <th>Predicted</th><th>Observed</th>
            </tr>
          </thead>
          <tbody>
            {data.controls.map((c) => {
              const tone = c.observed ? OBSERVED_TONE[c.observed] ?? "unknown" : "unknown";
              return (
                <tr key={`${c.driver}-${c.target}-${c.mechanism}`}>
                  <td><code>{c.driver}</code> &rarr; <code>{c.target}</code></td>
                  <td className={g.mech}>{c.mechanism}</td>
                  <td className={g.num}>{c.dNaive?.toFixed(2) ?? "—"}</td>
                  <td className={g.num}>{c.dStratified?.toFixed(2) ?? "—"}</td>
                  <td className={g.num}>{c.dBurdenAdjusted?.toFixed(2) ?? "—"}</td>
                  <td className={g.num}>
                    {c.burdenSeparation?.toFixed(2) ?? "—"}
                    {c.burdenStrata === 1 && <span className={g.strataWarn}> 1 stratum</span>}
                  </td>
                  <td className={g.mech}>{c.expected}</td>
                  <td><span className={g.pill} data-tone={tone}>{c.observed ?? "not testable"}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className={s.axisNote}>
        <strong>&ldquo;Not testable&rdquo; is a result about the data, not a gap.</strong> This
        is a matrix of <em>damaging</em> variants, and an activating hotspot is not damaging —
        BRAF V600E is simply absent, so the oncogene-addiction half of the prediction cannot be
        asked here at all. Those rows are kept rather than deleted.{" "}
        <strong>&ldquo;Not separable&rdquo;</strong> marks a row whose burden separation is so
        large that only one stratum has both arms: there is no comparison left to make, and
        calling it a pass would rest the strongest claim on the weakest evidence.
      </p>
    </section>
  );
}

/* ------------------------------------------------------------ the confound ladder */

function GatedLadder(
  { driver, registered }:
  { driver: Driver; registered: { q: number; d: number; dependencyFloor: number } },
) {
  const [gates, set, dirty, reset] = useGates(registered);
  const { rows, total } = regateDriver(driver, gates);
  return (
    <>
      <GateControls gates={gates} set={set} dirty={dirty} reset={reset} reg={registered}
                    kept={rows.length} total={total} rows={driverGateInputs(driver)} />
      <Ladder driver={driver} rows={rows} dirty={dirty} />
    </>
  );
}

function Ladder(
  { driver, rows: all, dirty }:
  { driver: Driver; rows: GenoHit[]; dirty: boolean },
) {
  const rows = all.slice(0, 10);
  const span = useMemo(() => {
    const all = rows.flatMap((h) =>
      [h.dNaive, h.dStratified, h.dBurdenAdjusted].filter((v): v is number => v != null));
    const lo = Math.min(0, ...all), hi = Math.max(1, ...all), pad = (hi - lo) * 0.06;
    return { lo: lo - pad, hi: hi + pad };
  }, [rows]);
  const y = (v: number) => 100 - ((v - span.lo) / (span.hi - span.lo)) * 100;

  /** THE FIGURE WROTE A SENTENCE IT DID NOT DRAW.
   *
   *  The caption says a line that stays flat is an effect lineage and burden do not explain,
   *  and one that falls to the right was largely the confound. Every line was drawn in the
   *  same colour at the same weight, so the reader was asked to do that comparison by eye
   *  across ten crossing polylines — which is the comparison the whole panel exists to make.
   *
   *  It is now in the ink. `kept` is the share of the naive effect that survives peeling the
   *  confound back; a line that keeps most of it is drawn at full strength, one that loses
   *  most of it fades toward the neutral. No new statistic — the same three numbers already
   *  on the row, encoded instead of narrated. */
  const survival = (h: GenoHit) => {
    const end = h.dBurdenAdjusted ?? h.dStratified;
    if (!h.dNaive || h.dNaive <= 0 || end == null) return 1;
    return Math.max(0, Math.min(1.2, end / h.dNaive));
  };

  /** Ten labels placed at their own y collide: that is what direct labelling costs when the
   *  values are close, and it is why the previous version was readable only at the top. A
   *  single downward pass pushes each label below the one above it when they would overlap,
   *  which keeps the order true even where the positions are nudged. */
  const labelled = useMemo(() => {
    const MIN = 4.2; // percent of the plot height, ~13px at 320px
    const out = rows
      .map((h) => ({ h, at: y(h.dBurdenAdjusted ?? h.dStratified) }))
      .sort((a, b) => a.at - b.at);
    for (let i = 1; i < out.length; i++) {
      if (out[i].at - out[i - 1].at < MIN) out[i].at = out[i - 1].at + MIN;
    }
    return out;
  }, [rows, span.lo, span.hi]);

  return (
    <section className={s.panel}>
      <h3>
        {driver.driver}
        <span className={s.badge}>{driver.mutantLines} mutant lines</span>
        {driver.burdenProxy && <span className={g.badgeHot}>burden proxy</span>}
        {dirty && <span className={g.badgeHot}>re-gated</span>}
      </h3>
      <p className={s.sub}>{driver.says}</p>
      <p className={s.sub}>
        Each line is one dependency, drawn at its three estimates as the confound is peeled
        back. A line that <strong>stays flat</strong> is an effect lineage and burden do not
        explain. One that <strong>falls to the right</strong> was largely the confound.{" "}
        {driver.burdenProxy && (
          <>Because this driver is flagged, the third position is a diagnostic and not a
          correction &mdash; whether burden is a mediator or a confounder here is a question
          about mechanism, and this dataset does not contain the answer.</>
        )}
      </p>

      {rows.length === 0 ? (
        <p className={s.empty}>
          {dirty
            ? "Nothing clears the gates as you have set them. An empty list at thresholds "
              + "chosen after seeing the data says something about the thresholds, not about "
              + "this genotype."
            : "No dependency cleared the registered gates for this genotype."}
        </p>
      ) : (
      <>
      <div className={g.slopeWrap}>
        <div className={g.slope}>
          {["naive", "lineage", "burden-adj."].map((label, i) => (
            <span key={label} className={g.axisLabel} style={{ left: `${i * 50}%` }}>
              {label}
            </span>
          ))}
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className={g.svg}>
            {[0, 1, 2].map((i) => (
              <line key={i} x1={i * 50} y1="0" x2={i * 50} y2="100"
                    className={g.gridline} vectorEffect="non-scaling-stroke" />
            ))}
            {rows.map((h) => {
              const pts = ladder(h)
                .map((p, i) => (p.value == null ? null : `${i * 50},${y(p.value)}`))
                .filter(Boolean).join(" ");
              const kept = survival(h);
              return (
                <polyline key={h.gene} points={pts}
                          className={kept >= 0.85 ? g.slopeHeld : g.slopeLost}
                          style={{ opacity: 0.35 + 0.6 * Math.min(1, kept) }}
                          vectorEffect="non-scaling-stroke" />
              );
            })}
          </svg>
          {labelled.map(({ h, at }) => (
            <span key={h.gene}
                  className={survival(h) >= 0.85 ? `${g.endLabel} ${g.endHeld}` : g.endLabel}
                  style={{ top: `${at}%` }}>
              {h.gene}
              <span className={g.endKept}>{Math.round(100 * survival(h))} %</span>
            </span>
          ))}
        </div>
      </div>

      <ul className={g.hitTable}>
        {rows.map((h) => (
          <li key={h.gene}>
            <span className={g.hitGene}>{h.gene}</span>
            <span className={g.num}>{h.dNaive.toFixed(2)}</span>
            <span className={g.num}>{h.dStratified.toFixed(2)}</span>
            <span className={g.num}>{h.dBurdenAdjusted?.toFixed(2) ?? "—"}</span>
            <span className={g.qv}>
              q&nbsp;{h.q < 1e-4 ? h.q.toExponential(0) : h.q.toFixed(4)}
            </span>
            <span className={g.strata}>{h.strata} lineages</span>
          </li>
        ))}
      </ul>
      <p className={s.axisNote}>
        columns: naive d · lineage-stratified d · burden-adjusted d · q · lineage strata
        contributing
      </p>
      </>
      )}
    </section>
  );
}
