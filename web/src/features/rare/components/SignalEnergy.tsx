import raw from "../../../data/generated/signal_energy.json";
import { useT } from "../../../i18n";
import { SAMP } from "../../../i18n/sampled";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import { IntervalPlot } from "../../../components/viz/organisms/IntervalPlot";
import css from "./MeasuredPanels.module.css";

/** A NEGATIVE RESULT AGAINST THIS SITE'S OWN READING OF ITS OWN MEASUREMENT.
 *
 *  `scale_information` measured that a pathway alphabet keeps less of what genes said about
 *  organ system where the abnormality is a FORM than where it is a PROCESS, and reads that as
 *  evidence that the alphabet "has no vocabulary for where and when" — a Turing-shaped
 *  claim about geometry.
 *
 *  That reading treats 29 top-level pathways as one undifferentiated alphabet. Signal
 *  Transduction is the machinery that makes spatial pattern; Metabolism is energy;
 *  Developmental Biology is form, named. If the reading were right, the field families should
 *  carry more about morphogenetic systems than the energy families do.
 *
 *  They do not. Every family leans the same way, and the field families lean towards process
 *  MORE than the energy families. The obvious objection — the two arms have different system
 *  entropies, so the raw difference compares two scales — was tested and does not rescue it.
 *
 *  THIS PANEL EXISTS AT THE SAME SIZE AS THE ONE IT CONTRADICTS. `knowledge_shape` set the
 *  precedent: a site that publishes only its confirmations is advertising. The measurement in
 *  scale_information stands; the sentence it invites does not, and a reader meets both.
 */

const d = raw as any;

export function SignalEnergy() {
  const tt = useT();
  const raws: Record<string, number> = d.family_means_form_minus_process ?? {};
  const norm: Record<string, number> = d.family_means_normalised ?? {};
  const rows: any[] = d.pathways ?? [];
  const cis: Record<string, any> = d.family_mean_intervals ?? {};
  const contrast = d.contrast_with_its_interval;
  const families = Object.keys(raws).sort((a, b) => raws[a] - raws[b]);
  // The half-width has to cover the INTERVALS and not just the means, or a whisker leaves
  // its own track and the chart shows a narrower disagreement than the numbers hold.
  const span = Math.max(
    ...Object.values(raws).map((v) => Math.abs(v)),
    ...Object.values(cis).flatMap((c: any) => (c ? c.ci95.map(Math.abs) : [])),
    1e-9,
  );

  const drawn = rows
    .filter((r) => r.form_minus_process != null)
    .sort((a, b) => a.form_minus_process - b.form_minus_process);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>0/2</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.seHeading)}</span>
          {d.question}
        </p>
      </div>

      <p className={css.caveat}>{d.prediction_written_before_the_run}</p>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.seFamilies)}</span>
        {/* Zero-centred, because the prediction was about SIGN: field above zero, energy
            below. Everything landing on one side is the finding, and a bar chart from a
            zero baseline is the only form that shows it at a glance. */}
        <div className={css.corr}>
          {families.map((f) => {
            const v = raws[f];
            const w = Math.min(50, (50 * Math.abs(v)) / span);
            return (
              <div key={f} className={css.corrRow}>
                <span className={css.corrLabel}>
                  {f}
                  <br />
                  <span className={css.corrFlag}>
                    normalised {norm[f] >= 0 ? "+" : ""}{norm[f]}
                  </span>
                </span>
                <span className={css.corrTrack}>
                  <span className={css.corrZero} />
                  <span className={f === "field" ? css.corrBar : `${css.corrBar} ${css.corrBarNeg}`}
                        style={{ left: v < 0 ? `${50 - w}%` : "50%", width: `${w}%` }} />
                  {/* The bar is the mean; the whisker is what the mean is worth. Drawn over
                      the bar rather than beside it, because a family whose interval crosses
                      the zero line has not established a sign — and sign is the entire
                      prediction this chart was built to test. */}
                  {cis[f] && (
                    <span
                      className={css.corrCi}
                      style={{
                        left: `${50 + (50 * cis[f].ci95[0]) / span}%`,
                        width: `${(50 * (cis[f].ci95[1] - cis[f].ci95[0])) / span}%`,
                      }}
                    />
                  )}
                </span>
                <span className={css.corrVal}>{v >= 0 ? "+" : ""}{v}</span>
              </div>
            );
          })}
        </div>
        <p className={css.note}>
          Positive means the family carries more about morphogenetic systems than
          physiological ones. The prediction wanted <strong>field</strong> above zero and{" "}
          <strong>energy</strong> below it.
        </p>
      </div>

      {/* EVERY PATHWAY, NOT FIVE FAMILY MEANS. The bars above average 29 measurements into
          five numbers, and an average is exactly where a result like this can hide: two
          families can differ in their means while most of their members overlap completely.
          Here each pathway keeps its own interval, grouped by family, so a reader can see
          whether the family difference is a shift of the whole group or two outliers pulling
          a mean. It is the second, and that is why the contrast below is reported as fragile.

          Ordered by the contrast itself rather than by family, because the prediction was
          about SIGN: whatever leans towards form belongs at one end. */}
      {drawn.some((r: any) => r.overall?.excess_ci95) && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(SAMP.sePathways)}</span>
          <IntervalPlot
            rows={drawn
              .filter((r: any) => r.overall?.excess_ci95)
              .map((r: any) => ({
                label: (r.name ?? r.pathway ?? "").slice(0, 30),
                note: r.family,
                point: r.overall.excess_bits,
                lo: r.overall.excess_ci95[0],
                hi: r.overall.excess_ci95[1],
                ok: !r.overall.excess_spans_zero,
              }))}
            xLabel="excess mutual information, bits"
            scale="linear"
            rowH={22}
            refs={[{ at: 0, label: "no excess over a permutation" }]}
            format={(v) => v.toFixed(4)}
            ariaLabel="Excess mutual information with 95% intervals, one row per Reactome pathway"
            source="bootstrap over diseases"
            readAloud={
              <>
                One row per Reactome pathway. The band is the 95% interval from resampling the
                diseases; a hollow row is one whose interval contains zero, meaning the pathway
                carries no more information about which organ system fails than a random set of
                diseases of the same size would. Two of the 29 are in that position — the
                per-pathway result is solid. What is fragile is the DIFFERENCE between the
                family means below, which is a much smaller quantity than any row here.
              </>
            }
          />
        </div>
      )}

      {contrast && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(SAMP.seContrast)}</span>
          <div className={css.pair}>
            <div className={css.stat}>
              <span className={css.statVal}>
                {contrast.field_minus_energy >= 0 ? "+" : ""}
                {contrast.field_minus_energy}
              </span>
              <span className={css.statK}>field minus energy, bits</span>
            </div>
            <div className={css.stat}>
              <span className={css.statVal}>
                [{contrast.ci95[0]}, {contrast.ci95[1]}]
              </span>
              <span className={css.statK}>its 95% interval</span>
            </div>
          </div>
          <p className={css.caveat}>{contrast.says}</p>
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.seObjection)}</span>
        <p className={css.caveat}>{d.objection_tested}</p>
        <div className={css.pair}>
          {Object.entries(d.arm_entropies_bits ?? {}).map(([k, v]) => (
            <div key={k} className={css.stat}>
              <span className={css.statVal}>{String(v)}</span>
              <span className={css.statK}>bits of system entropy · {k}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.sePathways)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>pathway</th><th>family</th><th>diseases</th>
                <th>z overall</th><th>form − process</th>
              </tr>
            </thead>
            <tbody>
              {drawn.map((r) => (
                <tr key={r.pathway}>
                  <td className={css.tdName}>{r.name}</td>
                  <td className={css.tdMuted}>{r.family}</td>
                  <td className={css.tdMuted}>{fmtInt(r.diseases)}</td>
                  <td className={css.tdMuted}>{r.overall?.z ?? "—"}</td>
                  <td>{r.form_minus_process >= 0 ? "+" : ""}{r.form_minus_process}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>
          Every pathway's own numbers, so a reader who disagrees with the family grouping —
          which is authored, and says so — can regroup them.
        </p>
      </div>

      <p className={css.caveat}>{d.verdict}</p>

      <Provenance generated={d.generated} provenance={d.provenance}
                  method={d.not_an_adapter} says={d.says} limits={d.limits}
                  governedBy={d.governed_by} />
    </div>
  );
}
