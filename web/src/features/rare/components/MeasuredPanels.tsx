import scaleRaw from "../../../data/generated/scale_information.json";
import langRaw from "../../../data/generated/language_coverage.json";
import conflictRaw from "../../../data/generated/conflict_decomposition.json";
import shapeRaw from "../../../data/generated/knowledge_shape.json";
import { useT } from "../../../i18n";
import { MEAS } from "../../../i18n/measured";
import { fmtInt } from "../../../lib/scale";
import css from "./MeasuredPanels.module.css";

/** THE ADR 0007 LAYER — the four results on this site that carry a null and an interval.
 *
 *  These panels exist because the repository's own audit kept finding the same failure: a
 *  dashboard that publishes twenty aggregate layers while its strongest result sits in a JSON
 *  file is publishing that result nowhere. Four constructs were promoted from the theory
 *  atlas, each with a governing decision record, and none of them was rendered until this file.
 *
 *  NOTHING HERE IS COMPUTED IN THE BROWSER. Every number is read from the artefact the
 *  analysis wrote, which is why a reader can trace any figure on screen back to the tool that
 *  produced it — and why `tools/verify_claims.py` can fail the build when prose and artefact
 *  drift apart.
 *
 *  ONE OF THESE FOUR IS A FAILURE, and it is drawn in the neutral rather than in the accent.
 *  The colour on this site means "measured and standing"; the knowledge-shape panel is
 *  measured and did not stand, and giving it the accent would have flattered it.
 */

const pct = (v: number, digits = 1) => `${(100 * v).toFixed(digits)} %`;

/* ------------------------------------------------------------------ what a scale costs */

export function ScaleLoss() {
  const tt = useT();
  const scales = (scaleRaw as any).scales ?? {};
  const gene = scales.gene ?? {};
  const rows = ["gene", "cell_type", "pathway"]
    .filter((k) => scales[k])
    .map((k) => ({ id: k, ...scales[k] }));
  const systems: any[] = (scaleRaw as any).per_organ_system ?? [];
  const top = systems.slice(0, 3);
  const bottom = systems.slice(-3);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(scales.pathway?.retained_vs_gene ?? 0, 0)}</span>
        <p>
          <strong>{tt(MEAS.scaleRetained)}.</strong> {tt(MEAS.scaleSub)}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>bits of excess information about organ system</span>
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.id} className={css.row}>
              <span className={css.rowLabel}>
                {r.id.replace("_", " ")} · {fmtInt(r.alphabet)}
              </span>
              <span className={css.track}>
                <span
                  className={r.id === "gene" ? css.barRef : css.bar}
                  style={{ width: `${Math.max(2, 100 * (r.excess_bits / (gene.excess_bits || 1)))}%` }}
                />
              </span>
              <span className={css.rowVal}>{r.excess_bits?.toFixed(4)}</span>
            </div>
          ))}
        </div>
        <p className={css.note}>
          {tt(MEAS.ci)} {gene.excess_ci95 ? `[${gene.excess_ci95[0]}, ${gene.excess_ci95[1]}]` : "—"}
          {" · "}{tt(MEAS.nullLabel)} {gene.null_mean_bits}
        </p>
      </div>

      {systems.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>pathway retention, by organ system</span>
          <p className={css.blockSub}>{tt(MEAS.scaleSpread)}</p>
          <div className={css.rows}>
            {[...top, ...bottom].map((s) => (
              <div key={s.system} className={css.row}>
                <span className={css.rowLabel}>{s.name}</span>
                <span className={css.track}>
                  <span className={css.bar} style={{ width: `${Math.max(2, 100 * s.pathway_retention / 0.4)}%` }} />
                </span>
                <span className={css.rowVal}>{s.pathway_retention.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.scaleDirection)}</span>
        <p className={css.blockSub}>{tt(MEAS.scaleDirectionSub)}</p>
        <div className={css.pair}>
          {rows.map((r) => (
            <div key={r.id} className={css.stat}>
              <span className={css.statK}>{r.id.replace("_", " ")}</span>
              <span className={css.statVal}>{r.asymmetry_ratio?.toFixed(2)}×</span>
              <span className={css.statNote}>
                U(system|features) {r.u_system_given_features?.toFixed(4)} · U(features|system){" "}
                {r.u_features_given_system?.toFixed(4)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className={css.note}>{tt(MEAS.governed)}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ what a reader loses */

export function LanguageCoverage() {
  const tt = useT();
  const langs: any[] = (langRaw as any).languages ?? [];
  const pt = (langRaw as any).by_language?.pt;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pt ? pct(pt.annotation_coverage) : "—"}</span>
        <p>
          <strong>{tt(MEAS.langHeading)}.</strong> {tt(MEAS.langSub)}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MEAS.langAnnot)}</span>
        <div className={css.rows}>
          {langs
            .filter((l) => l.annotation_coverage > 0)
            .map((l) => (
              <div key={l.language} className={css.row}>
                <span className={css.rowLabel}>{l.name}</span>
                <span className={css.track}>
                  <span
                    className={l.language === "pt" ? css.bar : css.barRef}
                    style={{ width: `${Math.max(1, 100 * l.annotation_coverage)}%` }}
                  />
                </span>
                <span className={css.rowVal}>{pct(l.annotation_coverage, 0)}</span>
              </div>
            ))}
        </div>
        <p className={css.note}>{tt(MEAS.langNote)}</p>
      </div>

      {pt && (
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statK}>{tt(MEAS.langSpread)}</span>
            <span className={css.statVal}>{(100 * pt.system_spread).toFixed(1)}</span>
            <span className={css.statNote}>
              {pct(pt.term_coverage, 0)} {tt(MEAS.langTerms)} ·{" "}
              {pct(pt.annotation_coverage, 0)} {tt(MEAS.langAnnot)}
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statK}>{tt(MEAS.langWorst)}</span>
            <span className={css.statVal}>{pct(pt.worst_system?.coverage ?? 0, 0)}</span>
            <span className={css.statNote}>{pt.worst_system?.name}</span>
          </div>
          <div className={css.stat}>
            <span className={css.statK}>{tt(MEAS.langBest)}</span>
            <span className={css.statVal}>{pct(pt.best_system?.coverage ?? 0, 0)}</span>
            <span className={css.statNote}>{pt.best_system?.name}</span>
          </div>
        </div>
      )}

      <p className={css.note}>{tt(MEAS.governed)}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ conflict or context */

export function ConflictContext() {
  const tt = useT();
  const head = (conflictRaw as any).headline ?? {};
  const counts = (conflictRaw as any).counts ?? {};
  const across = head.across_condition_share ?? 0;
  const within = head.within_condition_share ?? 0;
  const redundancy: any[] = (conflictRaw as any).redundancy_within_condition?.rows ?? [];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(across)}</span>
        <p>
          <strong>{tt(MEAS.conflictHeading)}.</strong> {tt(MEAS.conflictSub)}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {fmtInt(counts.variants_in_conflict ?? 0)} variants in conflict
        </span>
        <div className={css.split} role="img"
             aria-label={`${pct(across)} context, ${pct(within)} contradiction`}>
          <span className={css.splitA} style={{ width: `${100 * across}%` }} />
          <span className={css.splitB} style={{ width: `${100 * within}%` }} />
        </div>
        <div className={css.splitLegend}>
          <div className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchA}`} />
            <div>
              <div className={css.legendVal}>{pct(across)}</div>
              <div className={css.legendText}>{tt(MEAS.conflictAcross)}</div>
            </div>
          </div>
          <div className={css.legendItem}>
            <span className={`${css.swatch} ${css.swatchB}`} />
            <div>
              <div className={css.legendVal}>{pct(within)}</div>
              <div className={css.legendText}>{tt(MEAS.conflictWithin)}</div>
            </div>
          </div>
        </div>
        <p className={css.note}>{tt(MEAS.conflictSens)}</p>
      </div>

      {redundancy.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>internal disagreement, with the condition held fixed</span>
          <p className={css.blockSub}>{tt(MEAS.conflictRedundancy)}</p>
          <div className={css.rows}>
            {redundancy.map((r) => (
              <div key={r.submitters} className={css.row}>
                <span className={css.rowLabel}>
                  {r.submitters} · {fmtInt(r.pairs)}
                </span>
                <span className={css.track}>
                  <span className={css.bar} style={{ width: `${Math.max(2, 100 * r.split_rate / 0.3)}%` }} />
                </span>
                <span className={css.rowVal}>{pct(r.split_rate, 1)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className={css.note}>{tt(MEAS.governed)}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ the failure */

export function KnowledgeShape() {
  const tt = useT();
  const head = (shapeRaw as any).headline ?? {};
  const corr = (shapeRaw as any).axis_correlation?.spearman ?? {};
  const depth = (shapeRaw as any).by_axes_present ?? {};
  const pairs = Object.entries(corr) as [string, number][];
  pairs.sort((a, b) => b[1] - a[1]);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>
          {head.z_vs_null?.toFixed(1)}
          <span className={css.unit}>z vs null</span>
        </span>
        <p>
          <strong>{tt(MEAS.shapeHeading)}.</strong> {tt(MEAS.shapeSub)}
        </p>
      </div>

      <div className={css.pair}>
        <div className={css.stat}>
          <span className={css.statK}>{tt(MEAS.shapeObserved)}</span>
          <span className={css.statVal}>{head.mean_anisotropy}</span>
        </div>
        <div className={css.stat}>
          <span className={css.statK}>{tt(MEAS.shapeNull)}</span>
          <span className={css.statVal}>{head.null_mean}</span>
          <span className={css.statNote}>
            higher than observed — the axes rise and fall together
          </span>
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
        <span className={css.blockK}>{tt(MEAS.shapeCorr)}</span>
        <p className={css.blockSub}>{tt(MEAS.shapeCorrSub)}</p>
        <div className={css.corr}>
          {pairs.map(([k, v]) => {
            const artefact = v > 0.5;
            const w = Math.abs(v) * 50;
            return (
              <div key={k} className={css.corrRow}>
                <span className={css.corrLabel}>{k.replace("~", " ~ ")}</span>
                <span className={css.corrTrack}>
                  <span className={css.corrZero} />
                  <span
                    className={`${css.corrBar} ${v < 0 ? css.corrBarNeg : ""}`}
                    style={v >= 0
                      ? { left: "50%", width: `${w}%` }
                      : { right: "50%", width: `${w}%` }}
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

      <p className={css.note}>{tt(MEAS.shapeKept)}</p>
    </div>
  );
}
