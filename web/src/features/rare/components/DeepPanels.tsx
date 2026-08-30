import hivRaw from "../../../data/generated/hiv_resistance.json";
import twinRaw from "../../../data/generated/twin_propagation.json";
import genoRaw from "../../../data/generated/genotype_phenotype.json";
import { useState } from "react";
import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import css from "./MeasuredPanels.module.css";

/** THREE MEASUREMENTS THAT REACHED NO DELIVERY PATH.
 *
 *  Not found by reading — found by `scripts/check-artefacts.mjs`, which exists because audit
 *  A29 had by then been written three times in three comment blocks and caught a fourth time
 *  by hand. The check is the actual fix; these three panels are what it turned up on its
 *  first run.
 *
 *  Each is a different KIND of coverage, which is why they are worth the screens:
 *    - HIV resistance is this method outside rare disease entirely, with positive controls
 *      named before the run and an assumption of the core that the domain breaks.
 *    - Propagation is the multiscale rung `tools/thesis_seed.py` grades as built, reported
 *      against a degree-stratified null because a walk finds hubs whatever you seed it with.
 *    - Truncating-versus-missense is a POWER result: 470 of its 510 tests could not have
 *      detected the effect they were asked about, and that is the finding.
 */

const pct = (v: number, d = 1) => `${(100 * v).toFixed(d)} %`;

/* ============================================================ the method, somewhere else */

export function HivResistance() {
  const tt = useT();
  const d = hivRaw as any;
  const panels = Object.entries(d.panels ?? {}) as [string, any][];
  const [openPanel, setOpen] = useState(panels[0]?.[0] ?? "");
  const cur = (d.panels ?? {})[openPanel];

  const recovered = panels.reduce((a, [, p]) => a + (p.positive_control?.recovered ?? 0), 0);
  const of = panels.reduce((a, [, p]) => a + (p.positive_control?.of ?? 0), 0);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{recovered}/{of}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.hivHeading)}</span>
          {d.control_pool?.why}
        </p>
      </div>

      {/* The gate first. An adapter that did not pass it has no standing here, and the four
          answers are in the artefact rather than in this component's opinion. */}
      <div className={css.block}>
        <span className={css.blockK}>the four-question fit test, answered in writing</span>
        <div className={css.pair}>
          {Object.entries(d.elements ?? {}).map(([k, v]) => (
            <div key={k} className={css.stat}>
              <span className={css.statK}>{k.replace(/_/g, " ")}</span>
              <span className={css.statNote}>{String(v)}</span>
            </div>
          ))}
        </div>
        <p className={css.note}>{d.fit_test?.verdict}</p>
        {/* The weakest control pool of the three the skill ranks, said out loud. */}
        <p className={css.caveat}>
          {d.control_pool?.rank} — {d.control_pool?.cost}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.hivPanels)}</span>
        <div className={css.controls} role="tablist">
          {panels.map(([id, p]) => (
            <button key={id} type="button" role="tab" aria-selected={id === openPanel}
                    className={id === openPanel ? css.chipOn : css.chip}
                    onClick={() => setOpen(id)}>
              {id} · {p.positive_control?.recovered}/{p.positive_control?.of}
            </button>
          ))}
        </div>

        {cur && (
          <>
            <p className={css.blockSub}>
              {cur.description} — {fmtInt(cur.isolates)} isolates, {fmtInt(cur.mutations_scored)}
              {" "}mutations scored over {cur.drugs?.length} drugs.
            </p>
            <div className={css.tableWrap}>
              <table className={css.table}>
                <thead>
                  <tr><th>mutation</th><th>drug</th><th>isolates</th><th>score</th><th>z</th></tr>
                </thead>
                <tbody>
                  {(cur.top ?? []).slice(0, 12).map((r: any) => {
                    const known = (cur.positive_control?.recovered_in_top20 ?? [])
                      .includes(r.mutation);
                    return (
                      <tr key={`${r.mutation}-${r.drug}`}>
                        <td className={css.tdName}>
                          {r.mutation}
                          {known && <span className={css.badgeKnown}> named before the run</span>}
                        </td>
                        <td className={css.tdMuted}>{r.drug}</td>
                        <td className={css.tdMuted}>{fmtInt(r.n)}</td>
                        <td>{r.score?.toFixed(3)}</td>
                        <td>{r.z?.toFixed(1)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className={css.note}>{cur.positive_control?.says}</p>

            <span className={css.blockK}>{tt(DEEP.hivPassengers)}</span>
            <p className={css.blockSub}>
              {(cur.passengers_in_top20?.mutations ?? []).join(" · ")}
            </p>
            <p className={css.caveat}>{cur.passengers_in_top20?.says}</p>
            <p className={css.note}>{cur.carrier_overlap?.says}</p>
          </>
        )}
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.hivBreaks)}</span>
        {/* THE ACTUAL RETURN ON A NEW ADAPTER, per the skill: a domain that did not produce
            the method finds the assumption the method smuggled in. */}
        <p className={css.caveat}>{d.what_this_domain_breaks}</p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.control_pool}
                  says={d.elements} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ============================================================ propagation, against degree */

export function TwinPropagation() {
  const tt = useT();
  const d = twinRaw as any;
  const results: any[] = d.results ?? [];
  const [target, setTarget] = useState(results[0]?.target ?? "");
  const cur = results.find((r) => r.target === target) ?? results[0];
  const maxZ = Math.max(1, ...(cur?.reached ?? []).map((g: any) => g.z));

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(d.method?.nodes ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.twinHeading)}</span>
          {d.method?.whyTheNull}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {results.length} disorders · {d.method?.kernel}
        </span>
        <div className={css.controls} role="tablist">
          {results.map((r) => (
            <button key={r.target} type="button" role="tab" aria-selected={r.target === target}
                    className={r.target === target ? css.chipOn : css.chip}
                    onClick={() => setTarget(r.target)}>
              {r.target}
            </button>
          ))}
        </div>

        {cur && (
          <>
            <p className={css.blockSub}>
              seeds: {cur.seeds?.join(", ")}
              {cur.seedsMissing?.length
                ? ` · not in the graph: ${cur.seedsMissing.join(", ")}`
                : " · every seed is in the graph"}
            </p>
            {/* Degree is printed beside every z, because the whole point of the null is that
                a high score and a high degree are the thing being told apart. */}
            <div className={css.rows}>
              {(cur.reached ?? []).slice(0, 12).map((g: any) => (
                <div key={g.gene} className={css.row}>
                  <span className={css.rowLabel}>{g.gene}</span>
                  <span className={css.track}>
                    <span className={css.bar} style={{ width: `${(100 * g.z) / maxZ}%` }} />
                  </span>
                  <span className={css.rowVal}>{g.z?.toFixed(0)} z</span>
                  <span className={css.rowNote}>degree {g.degree}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.twinIsNot)}</span>
        <p className={css.caveat}>{d.isNot}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.twinLadder)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statK}>built</span>
            {(d.ladder?.built ?? []).map((r: string) => (
              <span key={r} className={css.statNote}>{r}</span>
            ))}
          </div>
          <div className={css.stat}>
            <span className={css.statK}>named only</span>
            {(d.ladder?.stillNamedOnly ?? []).map((r: string) => (
              <span key={r} className={css.statNote}>{r}</span>
            ))}
          </div>
        </div>
        <p className={css.note}>{d.ladder?.says}</p>
      </div>

      <Provenance generated={d.generated} provenance={d.premise} method={d.method}
                  says={d.isNot} limits={d.limits} />
    </div>
  );
}

/* ============================================================ power, reported first */

export function GenotypePhenotype() {
  const tt = useT();
  const d = genoRaw as any;
  const sc = d.scale ?? {};
  const hits: any[] = d.hits ?? [];
  const skipped = Object.entries(d.design?.patientsSkipped ?? {}) as [string, number][];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>{fmtInt(sc.underpowered ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.genoHeading)}</span>
          {d.premise}
        </p>
      </div>

      {/* POWER BEFORE HITS, deliberately. Read the other way round, six significant results
          out of 510 tests looks like a finding; read this way it is six results out of the
          forty tests that could have produced one. */}
      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.genoPower)}</span>
        <div className={css.split} role="img"
             aria-label="tests that could detect the effect, against those that could not">
          <span className={css.splitA}
                style={{ width: `${(100 * (sc.powered ?? 0)) / (sc.tests || 1)}%` }} />
          <span className={css.splitB}
                style={{ width: `${(100 * (sc.underpowered ?? 0)) / (sc.tests || 1)}%` }} />
        </div>
        <div className={css.splitLegend}>
          <span className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchA}`} />
            <span className={css.legendVal}>{fmtInt(sc.powered ?? 0)}</span>
            <span className={css.legendText}>could detect a {100 * (d.design?.effectOfInterest ?? 0)}-point difference</span>
          </span>
          <span className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchB}`} />
            <span className={css.legendVal}>{fmtInt(sc.underpowered ?? 0)}</span>
            <span className={css.legendText}>could not, at these group sizes</span>
          </span>
        </div>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(sc.genesCompared ?? 0)}</span>
            <span className={css.statK}>genes compared</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(sc.poweredAndNull ?? 0)}</span>
            <span className={css.statK}>powered, and null</span>
            <span className={css.statNote}>
              these are the real negatives — a null from an underpowered test is not one
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(sc.significantAfterCorrection ?? 0)}</span>
            <span className={css.statK}>survive {d.design?.multiplicity?.split(",")[0]}</span>
          </div>
        </div>
        <p className={css.note}>{d.design?.powerModel}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.genoHits)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>gene</th><th>feature</th><th>loss of function</th><th>missense</th></tr>
            </thead>
            <tbody>
              {hits.map((h) => (
                <tr key={`${h.gene}-${h.term}`}>
                  <td className={css.tdName}>{h.gene}</td>
                  <td className={css.tdName}>{h.termLabel}</td>
                  <td>
                    {h.lofPresent}/{h.lofAssessed}
                    <span className={css.rowNote}> {pct(h.lofFrequency ?? 0, 0)}</span>
                  </td>
                  <td>
                    {h.missensePresent}/{h.missenseAssessed}
                    <span className={css.rowNote}> {pct(h.missenseFrequency ?? 0, 0)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.caveat}>{d.caveat}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.genoSkipped)}</span>
        <div className={css.rows}>
          {skipped.map(([why, n]) => (
            <div key={why} className={css.corrRow}>
              <span className={css.corrLabel}>{why}</span>
              <span className={css.corrTrack}>
                <span className={css.corrBar}
                      style={{ left: 0, width: `${Math.min(100, (100 * n) / 2500)}%` }} />
              </span>
              <span className={css.corrVal}>{fmtInt(n)}</span>
            </div>
          ))}
        </div>
      </div>

      <p className={css.note}>{d.finding}</p>

      <Provenance generated={d.generated} provenance={d.input} method={d.design}
                  says={d.premise} limits={[d.caveat]} />
    </div>
  );
}
