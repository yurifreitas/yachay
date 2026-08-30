import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { IntervalPlot } from "../../../components/viz/organisms/IntervalPlot";
import { SweepPlot } from "../../../components/viz/organisms/SweepPlot";
import raw from "../../../data/generated/community_stability.json";
import { fmtInt } from "../../../lib/scale";
import css from "./MeasuredPanels.module.css";

/** Whether the published partition is in the graph or in the algorithm.
 *
 *  WHAT THIS ANSWERS. The site reports 2,408 gene communities at modularity 0.8605, from one
 *  Louvain run at one seed and one resolution. Every other number here carries a null and an
 *  interval; that one carried neither, and the three questions it had never been asked are the
 *  three blocks below: is it stable across seeds, does the algorithm decide it, and was the
 *  resolution chosen or inherited.
 *
 *  THE ARI NEEDS ITS OWN NULL, which is why the reference line matters more than it looks. A
 *  rewired graph has no communities to find, and its runs still agree at 0.086 — so 0.9 is
 *  read against 0.086, not against 0.
 */
export function CommunityStability() {
  const tt = useT();
  const d = raw as any;
  if (!d.stability_across_seeds) return null;

  const stab = d.stability_across_seeds;
  const cross = d.agreement_between_algorithms ?? {};
  const nullStab = d.null?.stability_null_mean ?? 0;
  const sweep: any[] = d.resolution_sweep ?? [];
  const con = d.consensus ?? {};

  // Within-algorithm rows carry a real interval over seed pairs; between-algorithm rows carry
  // the observed range, and the two are not the same quantity. Kept in one figure because the
  // comparison IS the finding, and labelled so nobody reads a range as a confidence interval.
  const rows = [
    ...Object.entries(stab).map(([k, v]: [string, any]) => ({
      label: k,
      note: "same method, 12 seeds · 95% CI",
      point: v.mean,
      lo: v.ci95[0],
      hi: v.ci95[1],
      ok: v.mean > 0.8,
    })),
    ...Object.entries(cross).map(([k, v]: [string, any]) => ({
      label: k.replace(/_/g, " "),
      note: "two methods · observed range",
      point: v.mean,
      lo: v.min,
      hi: v.max,
      ok: v.mean > 0.8,
    })),
  ];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{stab.louvain?.mean}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.csHeading)}</span>
          {d.what_was_published?.the_problem}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.csAgreement)}</span>
        <IntervalPlot
          rows={rows}
          xLabel="adjusted Rand index between two partitions"
          scale="linear"
          rowH={30}
          refs={[
            { at: nullStab, label: `${nullStab} — a rewired graph with no communities`, dashed: true },
            { at: 1, label: "identical" },
          ]}
          format={(v) => v.toFixed(2)}
          ariaLabel="Partition agreement within and between clustering algorithms"
          source={`${d.graph?.edges} edges · ${d.libraries?.leidenalg ? `leidenalg ${d.libraries.leidenalg}` : ""}`}
          readAloud={
            <>
              The top three rows are one algorithm run twelve times: how much a partition
              agrees with itself when only the random seed changes. The bottom three are two
              different algorithms at the same seed. The modularity family agrees with itself
              at 0.86 and with label propagation at 0.29 — so most of what separates these
              partitions is the objective function, not the graph. The dashed line is what a
              rewired graph with no communities at all still scores, which is the level any of
              these numbers has to be read against.
            </>
          }
        />
      </div>

      {sweep.length > 1 && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(DEEP.csResolution)}</span>
          <SweepPlot
            x={sweep.map((s) => s.resolution)}
            panels={[
              {
                label: "modularity",
                values: sweep.map((s) => s.modularity),
                format: (v) => v.toFixed(3),
              },
              {
                label: "largest community",
                values: sweep.map((s) => s.largest),
                muted: true,
              },
              {
                label: "communities over one gene",
                values: sweep.map((s) => s.communities_above_one_gene),
                muted: true,
              },
            ]}
            marks={[{
              panel: "largest community",
              y: d.resolution_limit?.sqrt_2m ?? null,
              label: `resolution limit, ${d.resolution_limit?.sqrt_2m} edges`,
            }]}
            xLabel="resolution parameter (gamma)"
            ariaLabel="Modularity, largest community and community count against resolution"
            source={d.resolution_limit?.says}
            readAloud={
              <>
                The same graph partitioned by Leiden at seven resolutions. The top panel is the
                score the method optimises; the two below are what the partition actually looks
                like. Over a twelvefold change in gamma the score moves by 0.03 while the
                largest community falls from {sweep[0].largest} genes to{" "}
                {sweep[sweep.length - 1].largest}. The objective is nearly indifferent across a
                range that changes the answer fourfold — so the resolution was not chosen by
                the data, and the published partition inherited gamma = 1 from a default.
              </>
            }
          />
        </div>
      )}

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.csConsensus)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>
              {Math.round((con["share_at_or_above_0.9"] ?? 0) * 100)}%
            </span>
            <span className={css.statK}>
              of {fmtInt(con.genes_scored ?? 0)} scored genes sit with the same partners in at
              least nine runs of ten
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {Math.round((con["share_below_0.5"] ?? 0) * 100)}%
            </span>
            <span className={css.statK}>below half — assigned by the seed rather than by the graph</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(con.not_scored_singletons ?? 0)}</span>
            <span className={css.statK}>
              isolated genes, given no confidence at all rather than a perfect one
            </span>
          </div>
        </div>
        <p className={css.caveat}>{con.method}</p>
        <p className={css.note}>{d.internally_disconnected?.says}</p>
      </div>
    </div>
  );
}
