import { useMemo } from "react";
import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { IntervalPlot } from "../../../components/viz/organisms/IntervalPlot";
import { ScatterPair } from "../../../components/viz/organisms/ScatterPair";
import { useRemoteData } from "../../../lib/useRemoteData";
import { fmtInt } from "../../../lib/scale";
import css from "./MeasuredPanels.module.css";

/** A UMAP, and the three questions its ubiquity has made unaskable.
 *
 *  WHY THIS PANEL IS NOT "OUR GENE MAP". Every other embedding figure in biology is published
 *  as a result. This one is published as an OBJECT UNDER TEST, because the interesting fact
 *  about it is not where the genes landed — it is that the three numbers underneath disagree
 *  with each other in a specific and instructive way:
 *
 *    trustworthiness 0.945   the map is locally faithful. Genes near each other on the page
 *                            really were near each other in eleven dimensions.
 *    seed overlap 0.63       and yet a third of every gene's neighbours change when nothing
 *                            changes but the random seed.
 *    HDBSCAN 75% -> 0.01%    on the features, three quarters of genes are unclusterable
 *                            noise. On the picture of the same features, almost none are.
 *
 *  Locally faithful and globally suggestive at once is exactly what makes these figures so
 *  easy to over-read, and it is why the panel leads with the two maps side by side rather than
 *  with one map and a caption.
 */
export function GeneEmbedding() {
  const tt = useT();
  const d = useRemoteData<any>("data/gene_embedding.json");

  const model = useMemo(() => {
    if (d.state !== "ready") return null;
    const e = d.data;
    return {
      e,
      a: { x: e.embedding.x, y: e.embedding.y },
      b: { x: e.embedding_second_seed.x, y: e.embedding_second_seed.y },
    };
  }, [d]);

  if (d.state === "loading") return <p className={css.note}>projecting 8,890 genes…</p>;
  if (!model) return null;
  const { e, a, b } = model;
  const cp = e.clustering_the_picture ?? {};

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{e.trustworthiness?.mean}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.emHeading)}</span>
          {e.trustworthiness?.says}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.emPair)}</span>
        <ScatterPair
          a={a}
          b={b}
          labels={[`seed ${e.embedding?.seed}`, `seed ${e.embedding_second_seed?.seed}`]}
          cluster={e.embedding?.cluster}
          palette={["--known", "--partial", "--unknown", "--critical"]}
          ariaLabel="The same gene embedding at two random seeds, on a shared scale"
          source={e.embedding_second_seed?.aligned_by}
          readAloud={
            <>
              The same {fmtInt(e.genes_embedded)} genes, the same eleven features, the same
              algorithm — and nothing different between the two panels but the random seed.
              Colour is the cluster HDBSCAN found on the left-hand map, carried over so a gene
              keeps its colour in both. The second is Procrustes-aligned to the first, so
              rotation and reflection — which mean nothing in a UMAP — are already removed. What
              is left is real movement:{" "}
              {Math.round((1 - (e.same_map_twice?.neighbour_agreement?.mean ?? 0)) * 100)}% of
              every gene&rsquo;s fifteen nearest neighbours are different between these two
              pictures.
            </>
          }
        />
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.emNumbers)}</span>
        <IntervalPlot
          rows={[
            {
              label: "neighbourhoods kept",
              note: "trustworthiness · k=15",
              point: e.trustworthiness.mean,
              lo: e.trustworthiness.ci95[0],
              hi: e.trustworthiness.ci95[1],
              ok: true,
            },
            {
              label: "same map twice",
              note: "neighbour overlap between seeds",
              point: e.same_map_twice.neighbour_agreement.mean,
              lo: e.same_map_twice.neighbour_agreement.ci95[0],
              hi: e.same_map_twice.neighbour_agreement.ci95[1],
              ok: false,
            },
            {
              label: "picture vs data",
              note: "HDBSCAN on the embedding against on the features",
              point: cp.hdbscan_on_embedding_vs_on_features.mean,
              lo: cp.hdbscan_on_embedding_vs_on_features.ci95[0],
              hi: cp.hdbscan_on_embedding_vs_on_features.ci95[1],
              ok: false,
            },
            {
              label: "picture vs itself",
              note: "HDBSCAN on the embedding across seeds",
              point: cp.hdbscan_between_seeds.mean,
              lo: cp.hdbscan_between_seeds.ci95[0],
              hi: cp.hdbscan_between_seeds.ci95[1],
              ok: true,
            },
          ]}
          xLabel="agreement (1 = identical)"
          scale="linear"
          rowH={30}
          refs={[{ at: 1, label: "identical" }, { at: 0, label: "unrelated" }]}
          format={(v) => v.toFixed(2)}
          ariaLabel="Four measurements of what the embedding is worth"
          source={`${e.genes_embedded} genes · ${e.features?.length} features`}
          readAloud={
            <>
              Four numbers about the same picture. The map keeps its local neighbourhoods and
              its clusters reproduce almost perfectly across seeds — so a practitioner running
              it once and again would see a stable, tidy result. The two in the middle are the
              warning: a third of every neighbourhood changes with the seed, and the clusters
              on the picture have essentially nothing to do with the clusters in the data.
              Reproducible is not the same as correct, and this figure is both at once.
            </>
          }
        />
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.emClusters)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>
              {Math.round((cp.noise_share_on_features ?? 0) * 100)}%
            </span>
            <span className={css.statK}>
              of genes are unclusterable noise in the eleven-dimensional feature space
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>
              {((cp.noise_share_on_embedding ?? 0) * 100).toFixed(2)}%
            </span>
            <span className={css.statK}>
              are noise on the two-dimensional picture of those same features
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{cp.clusters_on_embedding}</span>
            <span className={css.statK}>
              tidy clusters on the picture, against {cp.clusters_on_features} in the data
            </span>
          </div>
        </div>
        <p className={css.caveat}>{cp.says}</p>
        <p className={css.note}>{e.listwise_not_imputed}</p>
      </div>
    </div>
  );
}
