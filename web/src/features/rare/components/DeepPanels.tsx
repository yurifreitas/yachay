import hivRaw from "../../../data/generated/hiv_resistance.json";
import twinRaw from "../../../data/generated/twin_propagation.json";
import genoRaw from "../../../data/generated/genotype_phenotype.json";
import conRaw from "../../../data/generated/gene_constraint.json";
import cellsRaw from "../../../data/generated/single_cell_coverage.json";
import { useState } from "react";
import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { fmtInt } from "../../../lib/scale";
import ChoiceGroup from "../../../components/atoms/ChoiceGroup";
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
        {/* NOT TABS. These were `role="tab"` in a `role="tablist"` with no `tabpanel`
            anywhere, no `aria-controls` and no keyboard model — a screen reader announcing
            "tab, selected" with nothing to move to, and arrow keys that a tablist promises
            and did not deliver. Choosing a drug panel re-renders the table beneath, which is
            a radio group; ChoiceGroup carries that contract and implements the keys. */}
        <ChoiceGroup
          label="Drug panel"
          value={openPanel}
          onChange={setOpen}
          choices={panels.map(([id, p]) => ({
            id,
            label: id,
            note: `${p.positive_control?.recovered}/${p.positive_control?.of} controls`,
          }))}
        />

        {cur && (
          <>
            <p className={css.blockSub}>
              {cur.description} — {fmtInt(cur.isolates)} isolates, {fmtInt(cur.mutations_scored)}
              {" "}mutations scored over {cur.drugs?.length} drugs.
            </p>
            <div className={css.tableWrap}>
              <table className={css.table}>
                <thead>
                  <tr>
                    <th>mutation</th><th>drug</th><th>isolates</th>
                    {/* The score column carries the interval rather than sitting beside it:
                        a number and its uncertainty are one quantity, and putting them in
                        two columns invites reading the first without the second. */}
                    <th>score, 95%</th><th>z</th>
                  </tr>
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
                        <td>
                          {r.score?.toFixed(3)}
                          {r.score_ci95 ? (
                            <span className={css.tdMuted}>
                              {" "}[{r.score_ci95[0].toFixed(2)}, {r.score_ci95[1].toFixed(2)}]
                            </span>
                          ) : (
                            /* No interval is a statement, not a blank. A censored score is
                               at the assay's reporting ceiling, so the resample cannot move
                               it and its rank among the other censored mutations comes from
                               the null rather than from the data. */
                            <span className={css.badgeCensored}>
                              {r.censored_at_assay_ceiling ? " at assay ceiling" : " no interval"}
                            </span>
                          )}
                        </td>
                        <td>{r.z?.toFixed(1)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className={css.note}>{cur.positive_control?.says}</p>

            {cur.uncertainty && (
              <>
                <span className={css.blockK}>{tt(DEEP.hivUncK)}</span>
                <p className={css.blockSub}>{cur.uncertainty.says}</p>
                <p className={css.caveat}>{cur.uncertainty.method}</p>
              </>
            )}

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

/** Whether a gene appears in the other ordering. Both lists are short, so a scan is cheaper
 *  than building two sets on every render, and the intent stays readable at the call site. */
const inLb = (cur: any, gene: string) =>
  (cur.reachedByLowerBound ?? []).slice(0, 8).some((g: any) => g.gene === gene);
const inZ = (cur: any, gene: string) =>
  (cur.reached ?? []).slice(0, 8).some((g: any) => g.gene === gene);

/* ============================================================ propagation, against degree */

export function TwinPropagation() {
  const tt = useT();
  const d = twinRaw as any;
  const results: any[] = d.results ?? [];
  const [target, setTarget] = useState(results[0]?.target ?? "");
  const cur = results.find((r) => r.target === target) ?? results[0];
  // THE SCALE HAS TO INCLUDE THE NEGATIVE HALF. The first version of this track ran from 0
  // to the largest upper bound and clamped anything below zero to the left edge — which
  // silently deleted the most important thing several of these intervals say. DNASE2B is
  // published at z = 1825 with an interval of [-1753, +5403]: a track that starts at zero
  // draws that as a band beginning at the edge, and the reader sees a wide estimate instead
  // of an estimate that does not exclude no effect at all.
  //
  // So the domain spans min(0, lowest bound) to the highest bound, and zero is drawn on it.
  const bounds = (cur?.reached ?? []).flatMap((g: any) =>
    g.z_ci95 ? [g.z_ci95[0], g.z_ci95[1]] : [g.z],
  );
  const lo0 = Math.min(0, ...bounds);
  const hi0 = Math.max(1, ...bounds);
  const unc = d.uncertainty;
  const pct = (v: number) =>
    `${Math.max(0, Math.min(100, (100 * (v - lo0)) / (hi0 - lo0)))}%`;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(d.method?.nodes ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.twinHeading)}</span>
          {d.method?.whyTheNull}
        </p>
      </div>

      {unc && (
        <div className={css.finding}>
          <span className={css.value}>
            {unc.reached_genes_surviving}/{unc.reached_genes_scored}
          </span>
          <p>
            <span className={css.answersK}>{tt(DEEP.twinUncK)}</span>
            {unc.reading} {unc.what_it_holds_fixed}
          </p>
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>
          {results.length} disorders · {d.method?.kernel}
        </span>
        <ChoiceGroup
          label="Disorder"
          value={target}
          onChange={setTarget}
          choices={results.map((r) => ({ id: r.target, label: r.target }))}
        />

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
              {(cur.reached ?? []).slice(0, 12).map((g: any) => {
                const ci = g.z_ci95 as [number, number] | null;
                const out = ci ? !g.survives_interval : false;
                return (
                  <div key={g.gene} className={css.row}>
                    <span className={css.rowLabel}>{g.gene}</span>
                    {ci ? (
                      <span className={css.ciTrack}>
                        <span
                          className={`${css.ciBand} ${out ? css.ciBandOut : ""}`}
                          style={{ left: pct(ci[0]), right: `calc(100% - ${pct(ci[1])})` }}
                        />
                        <span
                          className={`${css.ciPoint} ${out ? css.ciPointOut : ""}`}
                          style={{ left: pct(g.z) }}
                        />
                        {/* Zero, and the threshold the survival judgement uses. They sit
                            almost on top of each other whenever an interval is wide, which
                            is the honest picture: at that width, 1.96 and no effect at all
                            are the same distance away. */}
                        <span className={css.ciZero} style={{ left: pct(0) }} />
                        <span className={css.ciRule} style={{ left: pct(1.96) }} />
                      </span>
                    ) : (
                      <span className={css.track}>
                        <span className={css.bar} style={{ width: pct(g.z) }} />
                      </span>
                    )}
                    <span className={`${css.rowVal} ${out ? css.rowValOut : ""}`}>
                      {g.z?.toFixed(0)} z
                    </span>
                    <span className={css.rowNote}>
                      degree {g.degree}
                      {ci ? ` · ${ci[0].toFixed(1)} to ${ci[1].toFixed(1)}` : ""}
                    </span>
                  </div>
                );
              })}
            </div>
            {!cur.reached?.[0]?.z_ci95 && (
              <p className={css.blockSub}>{tt(DEEP.twinNoInterval)}</p>
            )}

            {/* THE SAME LIST IN BOTH ORDERS. Ranking by z and ranking by the bottom of each
                gene's interval are different questions, and for two of the four disorders
                that can be scored they return DISJOINT sets — so showing only one of them
                is a choice about what the reader concludes, not a layout decision.

                Two columns rather than a slopegraph: where the orderings share nothing there
                are no lines to draw, and a slopegraph with no slopes reads as a rendering
                failure instead of as the finding. A shared gene is marked in place. */}
            {cur.reachedByLowerBound?.length > 0 && (
              <div className={css.twoUp}>
                <div>
                  <span className={css.blockK}>{tt(DEEP.twinByZ)}</span>
                  <ol className={css.rankList}>
                    {cur.reached.slice(0, 8).map((g: any) => (
                      <li key={g.gene}
                          className={inLb(cur, g.gene) ? css.rankShared : undefined}>
                        {g.gene} <span className={css.rowNote}>z {g.z?.toFixed(0)}</span>
                      </li>
                    ))}
                  </ol>
                </div>
                <div>
                  <span className={css.blockK}>{tt(DEEP.twinByLb)}</span>
                  <ol className={css.rankList}>
                    {cur.reachedByLowerBound.slice(0, 8).map((g: any) => (
                      <li key={g.gene}
                          className={inZ(cur, g.gene) ? css.rankShared : undefined}>
                        {g.gene} <span className={css.rowNote}>≥ {g.lower?.toFixed(1)}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            )}
            {cur.rankAgreement !== null && cur.rankAgreement !== undefined && (
              <p className={css.caveat}>
                {cur.rankAgreement} {tt(DEEP.twinAgreement)} {cur.reachedByLowerBound?.length}.
              </p>
            )}
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

/* ============================================================ constraint, as an outside axis */

/** THE ONLY AXIS HERE THAT THE CURATION COULD NOT HAVE PRODUCED.
 *
 *  Everything else on this site is measured on catalogues that people built by deciding what
 *  to write down — so a finding about what the catalogue knows is always partly a finding
 *  about who wrote it. gnomAD constraint is not: it is counted in 800,000 exomes from a
 *  population nobody asked about rare disease, and it is therefore the one place this
 *  repository can check its own results against something outside its own process.
 *
 *  THE MATCHED NULL IS THE PANEL. LOEUF is bounded away from small values for short genes —
 *  there is nothing to observe — and disease-gene sets are enriched for long genes. So the
 *  unmatched contrast and the matched one are printed together with the share of the shift
 *  that was length alone, which for the disease genes is most of it.
 */
export function GeneConstraint() {
  const tt = useT();
  const d = conRaw as any;
  const arms = d.arms ?? {};
  const att = arms.attention_vs_constraint ?? {};
  const sets: [string, any][] = [
    ["all disease genes", arms.disease_genes_vs_matched],
    ["the autism-sign set", arms.autism_set_vs_matched],
  ];
  const genome = arms.disease_genes_vs_matched?.genome_mean_unmatched ?? 1;
  const scaleX = (v: number) => `${Math.max(0, Math.min(100, (v / 1.2) * 100))}%`;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{att.spearman}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.conHeading)}</span>
          {att.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.conMatched)}</span>
        <p className={css.blockSub}>{d.instrument?.null}</p>
        {sets.filter(([, a]) => a && a.observed != null).map(([label, a]) => (
          <div key={label} className={css.corrRow}>
            <span className={css.corrLabel}>
              {label}
              <br /><span className={css.corrFlag}>{fmtInt(a.genes)} genes · z {a.z}</span>
            </span>
            <span className={css.corrTrack}>
              {/* Three marks on one axis: the genome, the length-matched draw, and the set.
                  The gap that matters is the last two — the first is printed only so the
                  reader can see how much of the apparent shift the null already took. */}
              <span className={css.corrZero} style={{ left: scaleX(genome) }} />
              <span className={css.corrBar}
                    style={{ left: scaleX(Math.min(a.observed, a.null_mean)),
                             width: `${Math.abs(a.observed - a.null_mean) / 1.2 * 100}%` }} />
            </span>
            <span className={css.corrVal}>{a.observed}</span>
          </div>
        ))}
        <p className={css.note}>
          The vertical mark is the genome-wide mean ({genome}); the bar spans from the
          length-matched null to what the set actually is. Lower LOEUF is more intolerant.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.conLength)}</span>
        <div className={css.pair}>
          {sets.filter(([, a]) => a?.shift_explained_by_length != null).map(([label, a]) => (
            <div key={label} className={css.stat}>
              <span className={css.statVal}>
                {Math.round(100 * a.shift_explained_by_length)} %
              </span>
              <span className={css.statK}>{label}</span>
              <span className={css.statNote}>
                of the distance from the genome mean is reproduced by drawing genes of the
                same length, and is therefore not constraint
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.conBands)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>set</th><th>constrained</th><th>tolerant</th><th>total</th></tr>
            </thead>
            <tbody>
              {[["every gene with constraint", d.scale?.genome_bands],
                ["disease genes", d.scale?.disease_gene_bands]].map(([label, b]: any) => (
                <tr key={label}>
                  <td className={css.tdName}>{label}</td>
                  <td>{fmtInt(b?.constrained ?? 0)}</td>
                  <td className={css.tdMuted}>{fmtInt(b?.tolerant ?? 0)}</td>
                  <td className={css.tdMuted}>
                    {fmtInt((b?.constrained ?? 0) + (b?.tolerant ?? 0))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.caveat}>{d.fit_test?.verdict}</p>
      </div>

      <p className={css.note}>{d.says}</p>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.instrument}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ============================================================ the denominator of the cell axis */

/** WHETHER THE OBSERVATION WAS EVER MADE.
 *
 *  Four layers of this site place a disease on a cell type — scale_information,
 *  autism_convergence, gap_taxonomy and knowledge_void — and every one of them reads the
 *  Human Protein Atlas, which measures NORMAL tissue. Each is therefore a statement about
 *  healthy biology plus an inference that the disease sits there too.
 *
 *  This panel is the denominator none of them had. It does not correct those layers and does
 *  not claim they are wrong; it says how often the inference could have been checked, which
 *  turns out to be 0.52 % of the time. That belongs on the same site as the four layers, in
 *  the reader's path, rather than in a limitation nobody scrolls to.
 */
export function SingleCellCoverage() {
  const tt = useT();
  const d = cellsRaw as any;
  const sc = d.scale ?? {};
  const best: any[] = d.best_covered ?? [];
  const tissues: any[] = d.commonest_tissues ?? [];
  const total = sc.datasets_indexed || 1;
  const normal = sc.datasets_of_normal_tissue ?? 0;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>
          {pct(sc.share_of_catalogue ?? 0, 2)}
          <span className={css.unit}>of the catalogue</span>
        </span>
        <p>
          <span className={css.answersK}>{tt(DEEP.cellHeading)}</span>
          {d.question}
        </p>
      </div>

      <p className={css.caveat}>{d.the_finding}</p>

      <div className={css.block}>
        <span className={css.blockK}>what the index holds, and how much of it is disease</span>
        {/* The normal/disease split first: two thirds of every single-cell dataset in the
            public index is healthy tissue, and that is the shape of the field rather than a
            detail about this particular join. */}
        <div className={css.split} role="img"
             aria-label="datasets of normal tissue against datasets carrying a disease term">
          <span className={css.splitB} style={{ width: `${(100 * normal) / total}%` }} />
          <span className={css.splitA} style={{ width: `${(100 * (total - normal)) / total}%` }} />
        </div>
        <div className={css.splitLegend}>
          <span className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchB}`} />
            <span className={css.legendVal}>{fmtInt(normal)}</span>
            <span className={css.legendText}>datasets of normal tissue</span>
          </span>
          <span className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchA}`} />
            <span className={css.legendVal}>{fmtInt(total - normal)}</span>
            <span className={css.legendText}>carrying a disease term</span>
          </span>
        </div>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(sc.disease_terms_with_cells ?? 0)}</span>
            <span className={css.statK}>distinct disease terms with cells</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(sc.catalogue_diseases_with_cells ?? 0)}</span>
            <span className={css.statK}>
              of {fmtInt(sc.catalogue_diseases ?? 0)} catalogue diseases reachable
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {fmtInt(sc.cellxgene_terms_with_no_omim_or_orpha_crosswalk ?? 0)}
            </span>
            <span className={css.statK}>have cells and no crosswalk</span>
            <span className={css.statNote}>
              the OMIM/ORPHA boundary again: they have data and cannot be attached to a
              catalogue entry
            </span>
          </div>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.cellBest)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>disease</th><th>datasets</th><th>genes</th><th>tissues sampled</th></tr>
            </thead>
            <tbody>
              {best.slice(0, 15).map((r) => (
                <tr key={r.disease}>
                  <td className={css.tdName}>{r.label ?? r.disease}</td>
                  <td>{fmtInt(r.datasets)}</td>
                  <td className={css.tdMuted}>{r.genes || "—"}</td>
                  <td className={css.tdMuted}>{(r.tissues ?? []).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.cellTissue)}</span>
        <div className={css.rows}>
          {tissues.slice(0, 12).map((t) => (
            <div key={t.tissue} className={css.row}>
              <span className={css.rowLabel}>{t.tissue}</span>
              <span className={css.track}>
                <span className={css.bar}
                      style={{ width: `${(100 * t.diseases) / (tissues[0]?.diseases || 1)}%` }} />
              </span>
              <span className={css.rowVal}>{t.diseases}</span>
            </div>
          ))}
        </div>
        <p className={css.note}>
          A disease of a tissue nobody dissociates is unreachable for a different reason than
          a disease nobody has heard of, and this is the list that separates them.
        </p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.not_an_adapter}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}
