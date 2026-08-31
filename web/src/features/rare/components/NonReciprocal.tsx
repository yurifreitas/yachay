import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { RaincloudPlot } from "../../../components/viz/organisms/RaincloudPlot";
import raw from "../../../data/generated/nonreciprocal.json";
import css from "./MeasuredPanels.module.css";

/** A hypothesis of the author's own, run against the falsifier he wrote for it.
 *
 *  WHY THIS PANEL IS DIFFERENT FROM EVERY OTHER ONE HERE. The rest of this site measures
 *  somebody else's catalogue, or audits its own statistics. This one tests an idea its author
 *  had before the site existed — that a relation need not be reciprocal, and that the
 *  asymmetry is what generates organisation — and it does so on the terms he set: a number
 *  written down in advance that would kill the idea.
 *
 *  THAT IS THE WHOLE REASON IT COUNTS. An idea with a stated falsifier is a hypothesis; the
 *  same idea without one is an analogy, and his own notes say exactly that about the parts of
 *  his framework that have no falsifier. Three of his other constructs are marked there as
 *  currently untestable with public data. This one was not.
 *
 *  THE CONTROL IS THE FINDING. Randomising which of the two directions is the strong one —
 *  keeping the magnitude of the asymmetry exactly — does not merely remove the gain, it goes
 *  negative. A wrong direction is worse than no direction, and the true one is better than
 *  both. That is a sharper statement than "asymmetry helps".
 */
export function NonReciprocal() {
  const tt = useT();
  const d = raw as any;
  if (!d.s_nr) return null;

  const per: any[] = d.per_disease ?? [];
  const worst: any[] = d.per_disease_worst ?? [];
  const f = d.falsifier_as_he_wrote_it ?? {};
  const pc = d.permutation_control ?? {};

  // Both tails, so the reader sees the distribution rather than the mean. The published
  // artefact carries the forty best and ten worst; that is a truncation and it is said here,
  // because a raincloud drawn from a truncated sample looks like a full one.
  const values = [...per, ...worst].map((r) => r.s_nr);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>
          {d.s_nr.mean > 0 ? "+" : ""}{d.s_nr.mean}
        </span>
        <p>
          <span className={css.answersK}>{tt(DEEP.nrHeading)}</span>
          {d.enunciado}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.nrFalsifier)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>
              [{d.s_nr.ci95[0]}, {d.s_nr.ci95[1]}]
            </span>
            <span className={css.statK}>
              95 % interval on the mean gain over {d.diseases_scored} diseases — it excludes
              zero, so the weak form of the falsifier does not trigger
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {Math.round(d.s_nr["share_below_0.01_in_absolute_value"] * 100)}%
            </span>
            <span className={css.statK}>
              of diseases move less than 0.01 — the strict form triggers at 80 %, so this
              passes, and not by much
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {pc.s_nr_under_randomised_direction}
            </span>
            <span className={css.statK}>
              with the direction randomised and its magnitude kept: a wrong direction is worse
              than no direction at all
            </span>
          </div>
        </div>
        <p className={css.caveat}>{f.weak_form} · {f.strict_form}</p>
      </div>

      {values.length > 20 && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(DEEP.nrSpread)}</span>
          <RaincloudPlot
            groups={[{
              label: "S_NR per disease",
              values,
              color: "var(--known)",
              marker: { at: 0, label: "no difference" },
            }]}
            xLabel="AUPRC(asymmetric) − AUPRC(symmetric projection)"
            xFormat={(v) => v.toFixed(2)}
            rowHeight={130}
            ariaLabel="Per-disease difference between the asymmetric operator and its symmetric projection"
            readAloud={
              <>
                One droplet per disease: how much better the asymmetric walk recovers that
                disease&rsquo;s held-out genes than the symmetric projection of the same
                affinities. The mass sits just right of zero — the effect is real and it is
                small, concentrated in a minority of diseases rather than general. The sample
                drawn here is the artefact&rsquo;s published forty best and ten worst, not all{" "}
                {d.diseases_scored}, so the tails are over-represented on purpose.
              </>
            }
          />
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.nrPrecedent)}</span>
        <p className={css.blockSub}>{d.precedent}</p>
        <p className={css.note}>{d.asymmetry_source}</p>
        <p className={css.caveat}>{pc.method}</p>
      </div>
    </div>
  );
}
