import { useMemo, useState } from "react";
import scaleRaw from "../../../data/generated/scale_information.json";
import langRaw from "../../../data/generated/language_coverage.json";
import assocRaw from "../../../data/generated/evidence_conflict.json";
import conflictRaw from "../../../data/generated/conflict_decomposition.json";
import shapeRaw from "../../../data/generated/knowledge_shape.json";
import { useT } from "../../../i18n";
import { MEAS } from "../../../i18n/measured";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import { LanguageMatrix, ScaleSlopegraph, KnowledgePCP, ConflictGrid } from "./HyperViews";
import css from "./MeasuredPanels.module.css";

/** THE ADR 0007 LAYER — the four results on this site that carry a null and an interval.
 *
 *  WHY THESE PANELS SHOW SO MUCH. The first version of this file showed a headline and three
 *  bars per section, and it was shallow in a way that mattered: the artefacts carry a
 *  stratified table, a per-organ-system breakdown of twenty rows, a fourteen-by-twenty-three
 *  coverage matrix, a permutation test of a prediction from 1952, real example variants, and
 *  in every payload a `says` and a `limits` field written by the analysis to bound its own
 *  claim. A page that renders the number and hides the qualification is doing the thing this
 *  whole repository was built to refuse.
 *
 *  So every panel now carries three layers: the finding, the full evidence behind it, and a
 *  `Provenance` disclosure holding the method, the limits and the file that produced it.
 *
 *  NOTHING HERE IS COMPUTED IN THE BROWSER. Every number is read from the artefact the
 *  analysis wrote, which is why `tools/verify_claims.py` can fail the build when prose and
 *  artefact drift apart. Sorting and selection reorder what is drawn; they never recompute.
 *
 *  ONE OF THESE FOUR IS A FAILURE, drawn in the neutral rather than the accent. The colour on
 *  this site means "measured and standing"; the knowledge-shape panel is measured and did not
 *  stand, and giving it the accent would have flattered it.
 */

const pct = (v: number, digits = 1) => `${(100 * v).toFixed(digits)} %`;

/** A number cell with the value drawn as a bar behind it, so a column reads as a
 *  distribution without needing a second chart. */
function BarCell({ value, max, children }: { value: number; max: number; children: React.ReactNode }) {
  return (
    <td className={css.cellBar}>
      <span className={css.cellBarFill} style={{ width: `${Math.max(0, Math.min(100, 100 * value / max))}%` }} />
      <span className={css.cellBarNum}>{children}</span>
    </td>
  );
}

/* ================================================================== what a scale costs */

type ScaleSort = "pathway" | "cell" | "size";

export function ScaleLoss() {
  const tt = useT();
  const d = scaleRaw as any;
  const scales = d.scales ?? {};
  const gene = scales.gene ?? {};
  const systems: any[] = d.per_organ_system ?? [];
  const morph = d.morphogenesis_prediction;
  const [sort, setSort] = useState<ScaleSort>("pathway");

  const ordered = useMemo(() => {
    const rows = [...systems];
    if (sort === "pathway") rows.sort((a, b) => b.pathway_retention - a.pathway_retention);
    if (sort === "cell") rows.sort((a, b) => b.cell_type_retention - a.cell_type_retention);
    if (sort === "size") rows.sort((a, b) => b.diseases - a.diseases);
    return rows;
  }, [sort, systems]);

  const alphabets = ["gene", "cell_type", "pathway"].filter((k) => scales[k]);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(scales.pathway?.retained_vs_gene ?? 0, 0)}</span>
        <p><strong>{tt(MEAS.scaleRetained)}.</strong> {tt(MEAS.scaleSub)}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>excess information about organ system, in bits</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>alphabet</th><th>|F|</th><th>n</th><th>I</th><th>{tt(MEAS.nullLabel)}</th>
                <th>excess</th><th>{tt(MEAS.ci)}</th><th>kept</th>
              </tr>
            </thead>
            <tbody>
              {alphabets.map((k) => {
                const r = scales[k];
                return (
                  <tr key={k}>
                    <td>{k.replace("_", " ")}</td>
                    <td>{fmtInt(r.alphabet)}</td>
                    <td className={css.tdMuted}>{fmtInt(r.diseases)}</td>
                    <td className={css.tdMuted}>{r.mutual_information_bits?.toFixed(4)}</td>
                    <td className={css.tdMuted}>{r.null_mean_bits?.toFixed(4)}</td>
                    <BarCell value={r.excess_bits} max={gene.excess_bits || 1}>
                      {r.excess_bits?.toFixed(4)}
                    </BarCell>
                    <td className={css.tdMuted}>
                      [{r.excess_ci95?.[0]}, {r.excess_ci95?.[1]}]
                    </td>
                    <td>{pct(r.retained_vs_gene ?? 0, 0)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>retention by organ system · all {systems.length}</span>
        <p className={css.blockSub}>{tt(MEAS.scaleSpread)}</p>
        <div className={css.controls}>
          <span className={css.controlK}>{tt(MEAS.sortBy)}</span>
          {([["pathway", MEAS.sortPathway], ["cell", MEAS.sortCell], ["size", MEAS.sortSize]] as const)
            .map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`${css.chip} ${sort === id ? css.chipOn : ""}`}
                aria-pressed={sort === id}
                onClick={() => setSort(id as ScaleSort)}
              >
                {tt(label)}
              </button>
            ))}
        </div>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>organ system</th><th>diseases</th><th>gene-scale bits</th>
                <th>pathway</th><th>cell type</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((s) => (
                <tr key={s.system}>
                  <td className={css.tdName}>{s.name}</td>
                  <td className={css.tdMuted}>{fmtInt(s.diseases)}</td>
                  <td className={css.tdMuted}>{s.gene_excess_bits?.toFixed(4)}</td>
                  <BarCell value={s.pathway_retention} max={0.4}>
                    {s.pathway_retention.toFixed(2)}
                  </BarCell>
                  <BarCell value={s.cell_type_retention} max={0.4}>
                    {s.cell_type_retention.toFixed(2)}
                  </BarCell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={css.block}>
        <ScaleSlopegraph />
      </div>

      {morph && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(MEAS.turing)}</span>
          <p className={css.blockSub}>{tt(MEAS.turingSub)}</p>
          <div className={css.pair}>
            <div className={css.stat}>
              <span className={css.statK}>physiological · {morph.physiological.n}</span>
              <span className={css.statVal}>{morph.physiological.mean_pathway_retention}</span>
              <span className={css.statNote}>{morph.physiological.systems.slice(0, 4).join(" · ")}</span>
            </div>
            <div className={css.stat}>
              <span className={css.statK}>morphogenetic · {morph.morphogenetic.n}</span>
              <span className={css.statVal}>{morph.morphogenetic.mean_pathway_retention}</span>
              <span className={css.statNote}>{morph.morphogenetic.systems.slice(0, 4).join(" · ")}</span>
            </div>
            <div className={css.stat}>
              <span className={css.statK}>difference · permutation p</span>
              <span className={css.statVal}>+{morph.difference}</span>
              <span className={css.statNote}>
                p = {morph.permutation_p_one_sided}, {fmtInt(morph.permutations)} draws, one-sided
              </span>
            </div>
          </div>
          <p className={css.caveat}>{tt(MEAS.turingCaveat)}</p>
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.scaleDirection)}</span>
        <p className={css.blockSub}>{tt(MEAS.scaleDirectionSub)}</p>
        <div className={css.pair}>
          {alphabets.map((k) => {
            const r = scales[k];
            return (
              <div key={k} className={css.stat}>
                <span className={css.statK}>{k.replace("_", " ")}</span>
                <span className={css.statVal}>{r.asymmetry_ratio?.toFixed(2)}×</span>
                <span className={css.statNote}>
                  U(system|features) {r.u_system_given_features?.toFixed(4)} · U(features|system){" "}
                  {r.u_features_given_system?.toFixed(4)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <Provenance
        generated={d.generated} provenance={d.provenance} method={d.estimator}
        says={d.says} limits={d.limits} governedBy={d.governed_by}
      />
    </div>
  );
}

/* ================================================================== what a reader loses */

export function LanguageCoverage() {
  const tt = useT();
  const d = langRaw as any;
  const langs: any[] = d.languages ?? [];
  const [pick, setPick] = useState<string>("pt");
  const picked = d.by_language?.[pick];
  const regions: any[] = d.against_representation?.by_region ?? [];

  const perSystem = useMemo(() => {
    if (!picked?.per_system) return [];
    return Object.entries(picked.per_system as Record<string, number>)
      .map(([id, v]) => ({ id, v }))
      .sort((a, b) => a.v - b.v);
  }, [picked]);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{d.by_language?.pt ? pct(d.by_language.pt.annotation_coverage) : "—"}</span>
        <p><strong>{tt(MEAS.langHeading)}.</strong> {tt(MEAS.langSub)}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {fmtInt(d.totals?.hpo_terms ?? 0)} terms · {fmtInt(d.totals?.annotations ?? 0)} annotations
        </span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>language</th><th>terms</th><th>{tt(MEAS.langTerms)}</th>
                <th>{tt(MEAS.langAnnot)}</th><th>gain</th><th>spread</th><th>weakest system</th>
              </tr>
            </thead>
            <tbody>
              {langs.map((l: any) => (
                <tr key={l.language}>
                  <td className={l.language === "pt" ? undefined : css.tdName}>
                    {l.name}{l.language === "pt" ? " ←" : ""}
                  </td>
                  <td className={css.tdMuted}>{fmtInt(l.terms_translated)}</td>
                  <td className={css.tdMuted}>{pct(l.term_coverage, 0)}</td>
                  <BarCell value={l.annotation_coverage} max={1}>
                    {pct(l.annotation_coverage, 1)}
                  </BarCell>
                  <td className={css.tdMuted}>
                    {l.weighting_gain > 0 ? "+" : ""}{pct(l.weighting_gain, 1)}
                  </td>
                  <td>{l.system_spread == null ? "—" : (100 * l.system_spread).toFixed(1)}</td>
                  <td className={css.tdName}>{l.worst_system?.name ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>{tt(MEAS.langNote)}</p>
      </div>

      <div className={css.block}>
        <LanguageMatrix />
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.pickLanguage)}</span>
        <div className={css.controls}>
          {langs.filter((l: any) => l.annotation_coverage > 0.01).map((l: any) => (
            <button
              key={l.language}
              type="button"
              className={`${css.chip} ${pick === l.language ? css.chipOn : ""}`}
              aria-pressed={pick === l.language}
              onClick={() => setPick(l.language)}
            >
              {l.name}
            </button>
          ))}
        </div>
        <div className={css.rows}>
          {perSystem.map((s) => (
            <div key={s.id} className={css.row}>
              <span className={css.rowLabel}>{s.id}</span>
              <span className={css.track}>
                <span className={css.bar} style={{ width: `${Math.max(1, 100 * s.v)}%` }} />
              </span>
              <span className={css.rowVal}>{pct(s.v, 0)}</span>
            </div>
          ))}
        </div>
      </div>

      {regions.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>against how well each region is represented</span>
          <div className={css.tableWrap}>
            <table className={css.table}>
              <thead>
                <tr><th>region</th><th>representation</th><th>languages</th><th>worst</th><th>best</th></tr>
              </thead>
              <tbody>
                {regions.map((r) => (
                  <tr key={r.region}>
                    <td className={css.tdName}>{r.region}</td>
                    <td>{r.representation_ratio}</td>
                    <td className={css.tdMuted}>{r.languages}</td>
                    <td className={css.tdMuted}>{pct(r.min_annotation_coverage, 0)}</td>
                    <td>{pct(r.max_annotation_coverage, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className={css.note}>{d.against_representation?.says}</p>
        </div>
      )}

      <Provenance
        generated={d.generated} provenance={d.provenance} method={d.method}
        says={d.says} limits={d.limits}
      />
    </div>
  );
}

/* ================================================================== conflict or context */

export function ConflictContext() {
  const tt = useT();
  const d = conflictRaw as any;
  const a = assocRaw as any;
  const head = d.headline ?? {};
  const counts = d.counts ?? {};
  const across = head.across_condition_share ?? 0;
  const within = head.within_condition_share ?? 0;
  const redundancy: any[] = d.redundancy_within_condition?.rows ?? [];
  const sens = d.sensitivity_umbrella_removed?.result ?? {};
  const examples: any[] = d.examples_across_condition ?? [];
  const strata = a.by_submitter_stratum ?? {};
  const bins = ["0", "1", "2", "3", "4+"];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(across)}</span>
        <p><strong>{tt(MEAS.conflictHeading)}.</strong> {tt(MEAS.conflictSub)}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{fmtInt(counts.variants_in_conflict ?? 0)} variants in conflict</span>
        <div className={css.split} role="img"
             aria-label={`${pct(across)} context, ${pct(within)} contradiction`}>
          <span className={css.splitA} style={{ width: `${100 * across}%` }} />
          <span className={css.splitB} style={{ width: `${100 * within}%` }} />
        </div>
        <div className={css.splitLegend}>
          <div className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchA}`} />
            <div>
              <div className={css.legendVal}>{fmtInt(counts.across_condition_only ?? 0)}</div>
              <div className={css.legendText}>{tt(MEAS.conflictAcross)}</div>
            </div>
          </div>
          <div className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchB}`} />
            <div>
              <div className={css.legendVal}>{fmtInt(counts.within_condition ?? 0)}</div>
              <div className={css.legendText}>{tt(MEAS.conflictWithin)}</div>
            </div>
          </div>
        </div>
        <p className={css.note}>
          {tt(MEAS.ci)} [{head.ci95?.[0]}, {head.ci95?.[1]}] · {tt(MEAS.conflictSens)}{" "}
          ({pct(sens.across_condition_share ?? 0)}, n = {fmtInt(sens.variants_in_conflict ?? 0)})
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.assoc)}</span>
        <p className={css.blockSub}>{tt(MEAS.assocSub)}</p>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>{tt(MEAS.submitters)}</th>
                {bins.map((b) => <th key={b}>{b} {tt(MEAS.conditions)}</th>)}
                <th>{tt(MEAS.assocRR)}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(strata).map(([k, row]: [string, any]) => (
                <tr key={k}>
                  <td>{k}</td>
                  {bins.map((b) => (
                    row[b]
                      ? <BarCell key={b} value={row[b].conflict_rate} max={0.4}>
                          {pct(row[b].conflict_rate, 1)}
                        </BarCell>
                      : <td key={b} className={css.tdMuted}>—</td>
                  ))}
                  <td>{row.risk_ratio_4plus_vs_1 ?? "—"}</td>
                </tr>
              ))}
              <tr>
                <td className={css.tdMuted}>marginal</td>
                {bins.map((b) => (
                  a.marginal?.[b]
                    ? <td key={b} className={css.tdMuted}>{pct(a.marginal[b].conflict_rate, 1)}</td>
                    : <td key={b} className={css.tdMuted}>—</td>
                ))}
                <td className={css.tdMuted}>{a.marginal_risk_ratio_4plus_vs_1}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className={css.note}>{a.reading}</p>
        <ConflictGrid />
      </div>

      {redundancy.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>internal disagreement, with the condition held fixed</span>
          <p className={css.blockSub}>{tt(MEAS.conflictRedundancy)}</p>
          <div className={css.rows}>
            {redundancy.map((r) => (
              <div key={r.submitters} className={css.row}>
                <span className={css.rowLabel}>{r.submitters} · {fmtInt(r.pairs)}</span>
                <span className={css.track}>
                  <span className={css.bar} style={{ width: `${Math.max(2, 100 * r.split_rate / 0.3)}%` }} />
                </span>
                <span className={css.rowVal}>{pct(r.split_rate, 1)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {examples.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(MEAS.examples)}</span>
          <p className={css.blockSub}>{tt(MEAS.examplesSub)}</p>
          <div className={css.examples}>
            {examples.slice(0, 6).map((e) => (
              <div key={e.variation_id} className={css.example}>
                <span className={css.exampleId}>ClinVar variation {e.variation_id}</span>
                {Object.entries(e.conditions as Record<string, string[]>).map(([cond, calls]) => (
                  <div key={cond} className={css.exampleRow}>
                    <span className={css.exampleCond}>{cond}</span>
                    <span className={css.exampleCall}>{calls.join(" / ")}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      <Provenance
        generated={d.generated} provenance={d.provenance} method={d.rule}
        says={d.says} limits={d.limits} governedBy={d.governed_by}
      />
    </div>
  );
}

/* ================================================================== the failure */

export function KnowledgeShape() {
  const tt = useT();
  const d = shapeRaw as any;
  const head = d.headline ?? {};
  const corr = d.axis_correlation?.spearman ?? {};
  const depth = d.by_axes_present ?? {};
  const dominant = d.dominant_axis ?? {};
  const axes = d.axes ?? {};
  const pairs = (Object.entries(corr) as [string, number][]).sort((x, y) => y[1] - x[1]);
  const domTotal = Object.values(dominant).reduce((s: number, v: any) => s + v, 0) as number;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>
          {head.z_vs_null?.toFixed(1)}
          <span className={css.unit}>z vs null — the wrong way</span>
        </span>
        <p><strong>{tt(MEAS.shapeHeading)}.</strong> {tt(MEAS.shapeSub)}</p>
      </div>

      <p className={css.caveat}>{d.verdict}</p>

      <div className={css.block}>
        <KnowledgePCP />
      </div>

      <div className={css.pair}>
        <div className={css.stat}>
          <span className={css.statK}>{tt(MEAS.shapeObserved)}</span>
          <span className={css.statVal}>{head.mean_anisotropy}</span>
          <span className={css.statNote}>{fmtInt(d.scale?.diseases_with_a_shape ?? 0)} diseases</span>
        </div>
        <div className={css.stat}>
          <span className={css.statK}>{tt(MEAS.shapeNull)}</span>
          <span className={css.statVal}>{head.null_mean}</span>
          <span className={css.statNote}>higher than observed — the axes rise and fall together</span>
        </div>
        <div className={css.stat}>
          <span className={css.statK}>at or above 0.5</span>
          <span className={css.statVal}>{pct(head.share_at_or_above_half ?? 0, 1)}</span>
          <span className={css.statNote}>{fmtInt(head.diseases_at_or_above_half ?? 0)} diseases</span>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>anisotropy is mostly a count of populated axes</span>
        <div className={css.rows}>
          {Object.entries(depth).map(([k, v]: [string, any]) => (
            <div key={k} className={css.row}>
              <span className={css.rowLabel}>{k} axes · {fmtInt(v.diseases)}</span>
              <span className={css.track}>
                <span className={css.barRef} style={{ width: `${Math.max(2, 100 * v.mean_anisotropy / 0.6)}%` }} />
              </span>
              <span className={css.rowVal}>{v.mean_anisotropy.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.dominant)}</span>
        <div className={css.rows}>
          {Object.entries(dominant).map(([k, v]: [string, any]) => (
            <div key={k} className={css.row}>
              <span className={css.rowLabel}>{k.replace(/_/g, " ")}</span>
              <span className={css.track}>
                <span className={css.barRef} style={{ width: `${100 * v / domTotal}%` }} />
              </span>
              <span className={css.rowVal}>{pct(v / domTotal, 1)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.shapeCorr)}</span>
        <p className={css.blockSub}>{tt(MEAS.shapeCorrSub)}</p>
        <div className={css.corr}>
          {pairs.map(([k, v]) => {
            const artefact = v > 0.5;
            const w = Math.abs(v) * 50;
            return (
              <div key={k} className={css.corrRow}>
                <span className={css.corrLabel}>{k.replace("~", " ~ ").replace(/_/g, " ")}</span>
                <span className={css.corrTrack}>
                  <span className={css.corrZero} />
                  <span
                    className={`${css.corrBar} ${v < 0 ? css.corrBarNeg : ""}`}
                    style={v >= 0 ? { left: "50%", width: `${w}%` } : { right: "50%", width: `${w}%` }}
                  />
                </span>
                <span className={css.corrVal}>
                  {v > 0 ? "+" : ""}{v.toFixed(3)}
                  {artefact && <div className={css.corrFlag}>{tt(MEAS.shapeArtefact)}</div>}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.axesDefs)}</span>
        <dl className={css.provDl}>
          {Object.entries(axes).map(([k, v]: [string, any]) => (
            <div key={k} className={css.provDlRow}>
              <dt>{k.replace(/_/g, " ")}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </div>

      <p className={css.note}>{tt(MEAS.shapeKept)}</p>

      <Provenance
        generated={d.generated} provenance={d.provenance} method={d.statistic}
        says={d.says} limits={d.limits} governedBy={d.governed_by}
      />
    </div>
  );
}
