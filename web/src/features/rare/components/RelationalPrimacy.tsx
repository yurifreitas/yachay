import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { RaincloudPlot } from "../../../components/viz/organisms/RaincloudPlot";
import raw from "../../../data/generated/relational_primacy.json";
import css from "./MeasuredPanels.module.css";

/** Is a gene better predicted by what it IS, or by what it is CONNECTED TO?
 *
 *  THE HARD PART WAS MAKING THE COMPARISON FAIR, and it is worth saying so on the page. The
 *  lazy version of this test hands the relational arm the disease's own seed genes and hands
 *  the attribute arm nothing but a feature vector — the relational arm then wins because it is
 *  the only one that knows which disease is being asked about, and the figure measures the
 *  experimental design. Here both arms get the same seeds and differ only in what they do with
 *  them: resemblance to the seeds, or reach from the seeds.
 *
 *  AND THE FIRST RUN WAS A LEAK. The graph's edges ARE disease co-membership, so the disease
 *  under test was joining its own seeds to its own hidden genes. ΔAUPRC came out at +0.925
 *  with the relational arm winning 100% of 155 diseases — a number that should be read as a
 *  tell rather than a triumph. With the disease removed from the graph before its own genes
 *  are predicted, the effect is a third of that and still decisive.
 */
export function RelationalPrimacy() {
  const tt = useT();
  const d = raw as any;
  if (!d.delta_auprc) return null;

  const per: any[] = [...(d.per_disease ?? []), ...(d.per_disease_worst ?? [])];
  const nul = d.against_a_degree_matched_null ?? {};

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>
          +{d.delta_auprc.mean}
        </span>
        <p>
          <span className={css.answersK}>{tt(DEEP.rpHeading)}</span>
          {d.enunciado}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.rpFair)}</span>
        <p className={css.blockSub}>{d.fairness}</p>
        <p className={css.caveat}>{d.leave_one_disease_out}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.rpResult)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>
              [{d.delta_auprc.ci95[0]}, {d.delta_auprc.ci95[1]}]
            </span>
            <span className={css.statK}>
              95 % interval on relations minus attributes, over {d.diseases_scored} diseases
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {Math.round(d.delta_auprc.share_relational_wins * 100)}%
            </span>
            <span className={css.statK}>of diseases where relations win at all</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>+{nul.mean}</span>
            <span className={css.statK}>
              over a rewiring with the same degree sequence and none of the biology
            </span>
          </div>
        </div>

        {per.length > 20 && (
          <RaincloudPlot
            groups={[{
              label: "relations − attributes",
              values: per.map((r) => r.delta),
              color: "var(--known)",
              marker: { at: 0, label: "no difference" },
            }]}
            xLabel="ΔAUPRC per disease"
            xFormat={(v) => v.toFixed(2)}
            rowHeight={130}
            ariaLabel="Per-disease advantage of relational over attribute prediction"
            readAloud={
              <>
                One droplet per disease: how much better a random walk from the disease&rsquo;s
                known genes recovers its hidden ones than attribute resemblance to those same
                genes does. The mass sits well right of zero. The sample drawn is the
                artefact&rsquo;s published forty best and ten worst, so the tails are
                over-represented on purpose — the mean and interval above are over all{" "}
                {d.diseases_scored}.
              </>
            }
          />
        )}
        <p className={css.note}>{nul.says}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.rpPrecedent)}</span>
        <p className={css.blockSub}>{d.precedent}</p>
        <p className={css.caveat}>{d.whose_hypothesis}</p>
        <p className={css.note}>
          <strong>What would have killed it.</strong>{" "}
          {d.falsifier_as_he_wrote_it?.statement}
        </p>
      </div>
    </div>
  );
}
