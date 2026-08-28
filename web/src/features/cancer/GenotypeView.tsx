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
    </>
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
              return (
                <polyline key={h.gene} points={pts} className={g.slopeLine}
                          vectorEffect="non-scaling-stroke" />
              );
            })}
          </svg>
          {rows.map((h) => (
            <span key={h.gene} className={g.endLabel}
                  style={{ top: `${y(h.dBurdenAdjusted ?? h.dStratified)}%` }}>
              {h.gene}
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
