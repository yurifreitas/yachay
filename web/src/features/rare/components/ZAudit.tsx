import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { IntervalPlot } from "../../../components/viz/organisms/IntervalPlot";
import raw from "../../../data/generated/z_audit.json";
import { fmtInt } from "../../../lib/scale";
import css from "./MeasuredPanels.module.css";

/** What this site's 3,166 z values are worth, measured against the nulls they came from.
 *
 *  WHY THIS PANEL EXISTS. On 2026-08-30 the propagation artefact was given an interval for the
 *  first time and not one of its ten largest z values kept a positive one — the largest, 1825,
 *  ran from -1753 to +5403. The cause was not the genes. A gene of degree five is missed by
 *  almost every draw of a degree-matched null, so the spread in the denominator is near zero
 *  and any reach at all divides into an enormous number.
 *
 *  That is a fact about dividing by an estimated spread, and this site does it in nine
 *  artefacts. So the audit runs across all of them, and this panel publishes the result
 *  against the site's own work rather than in a document nobody opens.
 *
 *  THE FIGURE IS THE POINT. Each artefact's largest z is drawn with the standard error that z
 *  carries purely from having estimated its own denominator from N draws — 1/sqrt(2N) of
 *  itself, which at 200 draws is 5%. The reference line is the largest z those draws can
 *  actually resolve. Every point sits far to the right of it, and that is not a scandal: it is
 *  what a permutation z IS, and the figure exists so the reader can see the difference between
 *  an effect size and a significance claim instead of being asked to take it on trust.
 */
export function ZAudit() {
  const tt = useT();
  const d = raw as any;
  const arts: any[] = (d.artefacts ?? []).filter((a: any) => a.draws);
  const t = d.totals ?? {};

  if (!arts.length) return null;

  // The resolution line is a property of the draw count, and almost every artefact here uses
  // 200. Where one does not — gene_constraint uses 400 — its own line differs, so the figure
  // draws the most common one and the table below carries each artefact's own.
  const common = arts
    .map((a) => a.z_the_draws_resolve)
    .sort((x, y) => arts.filter((a) => a.z_the_draws_resolve === x).length
                  - arts.filter((a) => a.z_the_draws_resolve === y).length)
    .pop() ?? 2.58;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(t.z_published ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.zaHeading)}</span>
          {d.says}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.zaFigure)}</span>
        <IntervalPlot
          rows={arts.map((a) => ({
            label: a.artefact,
            note: `${fmtInt(a.z_published)} z · ${a.draws} draws`,
            point: a.max_abs_z,
            lo: a.max_abs_z - 1.96 * (a.se_of_the_largest_z ?? 0),
            hi: a.max_abs_z + 1.96 * (a.se_of_the_largest_z ?? 0),
            // "ok" here means the modest thing it can mean: the artefact's loudest z is
            // inside what its own draw count resolves. Nothing on this site is, and the
            // figure says so rather than colouring everything green.
            ok: a.max_abs_z <= (a.z_the_draws_resolve ?? 0),
          }))}
          xLabel="largest published |z|, with the error it carries from its own denominator"
          scale="symlog"
          refs={[{ at: common, label: `${common} — what 200 draws resolve`, dashed: true }]}
          format={(v) => (Math.abs(v) >= 100 ? String(Math.round(v)) : v.toFixed(1))}
          ariaLabel="Largest published z per artefact against what its draw count resolves"
          source={`${t.louder_than_10} above 10; ${t.louder_than_10_with_an_interval} of those carry an interval`}
          readAloud={
            <>
              One row per artefact: its loudest published z, and the band is the standard error
              that z carries from having estimated its own denominator from a finite number of
              draws. At 200 draws that error is 5% of the z itself, so the propagation
              artefact&rsquo;s largest value of 2,128 carries an error of ±106 before anything
              about biology is considered. The dashed line is the largest z those 200 draws can
              resolve at all. Every artefact is to the right of it — which is what a
              permutation z is, and why the effect on its own scale has to be published beside
              it.
            </>
          }
        />
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.zaTight)}</span>
        {/* The tight nulls, named. This is the failure mode that is not about tails at all:
            a null whose spread is a rounding error next to its own centre turns any deviation
            into a huge z, and the honest number is the effect on its own scale. */}
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>artefact</th><th>null mean</th><th>null sd</th>
                <th>spread / centre</th><th>largest |z|</th>
              </tr>
            </thead>
            <tbody>
              {arts.filter((a) => a.null_coefficient_of_variation != null).map((a) => (
                <tr key={a.artefact}>
                  <td className={css.tdName}>
                    {a.artefact}
                    {a.tight_null && <span className={css.badgeCensored}> tight null</span>}
                  </td>
                  <td className={css.tdMuted}>{a.null_mean_at_max ?? "—"}</td>
                  <td className={css.tdMuted}>{a.null_sd_at_max ?? "—"}</td>
                  <td>{a.null_coefficient_of_variation}</td>
                  <td>{a.max_abs_z}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.caveat}>{tt(DEEP.zaTightSays)}</p>
      </div>
    </div>
  );
}
