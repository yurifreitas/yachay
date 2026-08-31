import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import { useMemo, useState } from "react";
import { IntervalPlot } from "../../../components/viz/organisms/IntervalPlot";
import { MatrixPlot } from "../../../components/viz/organisms/MatrixPlot";
import { AlluvialPlot } from "../../../components/viz/organisms/AlluvialPlot";
import { useRemoteData } from "../../../lib/useRemoteData";
import { SweepPlot } from "../../../components/viz/organisms/SweepPlot";
import raw from "../../../data/generated/community_stability.json";
import identityRaw from "../../../data/generated/community_identity.json";
import flowRaw from "../../../data/generated/partition_flow.json";
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
/** Decode a base64 typed array. The payload ships 38,746 edges and three orderings as bytes
 *  rather than as JSON numbers: 310 kB the browser hands straight to a canvas loop, against
 *  roughly 500 kB of text it would have to parse first. */
function i32(b64: string): Int32Array {
  const bin = atob(b64);
  const buf = new ArrayBuffer(bin.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
  return new Int32Array(buf);
}

function f32(b64: string): Float32Array {
  const bin = atob(b64);
  const buf = new ArrayBuffer(bin.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
  return new Float32Array(buf);
}

/** The matrix, fetched rather than bundled. Half a megabyte of edge list belongs behind a
 *  request on the one screen that draws it, not in the bundle every other screen loads. */
/** A share as a percentage, or an em dash when the artefact has not been regenerated. Written
 *  out because a caption that prints "undefined%" is worse than one that prints nothing. */
const pct = (v?: number) => (v == null ? "—" : `${Math.round(v * 100)}%`);

/** What a block IS, once one is picked.
 *
 *  THE FIGURE WITHOUT THIS WAS DECORATION. It showed 216 blocks named 0 to 215, and a reader
 *  could see structure and learn nothing about biology. The identity comes from Reactome,
 *  which is outside the loop that built the graph — the edges here are gene-disease
 *  co-membership, so a phenotype enrichment would only prove that the thing that made the
 *  edges made the edges.
 *
 *  BOTH ENDS ARE SHOWN, because coverage and specificity disagree. The broad pathway names
 *  the group and says little; the specific one says a lot about a handful of genes. Printing
 *  one would be choosing which half to hide.
 */
function IdentityCard({ community }: { community: number | null }) {
  const rec = useMemo(
    () => (identityRaw as any).communities?.find((c: any) => c.community === community),
    [community],
  );
  if (community == null) return <p className={css.note}>{(identityRaw as any).says}</p>;
  if (!rec) {
    return (
      <p className={css.note}>
        Block {community} is below the size this test can reach — under eight genes with a
        Reactome annotation, where an enrichment is one annotation away from being everything.
        It is still a stable group; the catalogue cannot say what of.
      </p>
    );
  }
  const h = rec.headline;
  const sp = rec.most_specific;
  return (
    <div className={css.pair}>
      <div className={css.stat}>
        <span className={css.statVal}>{rec.genes}</span>
        <span className={css.statK}>
          genes · consensus confidence {rec.mean_confidence ?? "—"} · e.g.{" "}
          {(rec.examples ?? []).slice(0, 4).join(", ")}
        </span>
      </div>
      <div className={css.stat}>
        <span className={css.statVal}>
          {h ? `${Math.round(h.share_of_community * 100)}%` : "—"}
        </span>
        <span className={css.statK}>
          {h ? <>of it is <strong>{h.name}</strong> — {h.genes_in_community} genes against{" "}
                {h.null_mean} expected under an annotation-matched null</>
             : "no pathway covers a tenth of this community: real, and heterogeneous"}
        </span>
      </div>
      <div className={css.stat}>
        <span className={css.statVal}>{sp ? `${sp.fold}×` : "—"}</span>
        <span className={css.statK}>
          {sp ? <>enriched for <strong>{sp.name}</strong>, the most unusual thing about it
                 ({sp.genes_in_community} genes, q {sp.q ?? "—"})</>
              : "nothing specific clears the null"}
        </span>
      </div>
    </div>
  );
}

function NetworkMatrix() {
  const [picked, setPicked] = useState<number | null>(null);
  const net = useRemoteData<any>("data/network_layout.json");
  const model = useMemo(() => {
    if (net.state !== "ready") return null;
    const d = net.data;
    return {
      d,
      edges: { i: i32(d.edges.i), j: i32(d.edges.j) },
      confidence: f32(d.confidence),
      orderings: Object.fromEntries(
        Object.entries<any>(d.orderings).map(([k, v]) => [k, { index: i32(v.index), says: v.says }]),
      ),
    };
  }, [net]);

  if (net.state === "loading") return <p className={css.note}>drawing 38,746 edges…</p>;
  if (!model) return null;
  const { d, edges, confidence, orderings } = model;

  return (
    <>
    <MatrixPlot
      n={d.counts.genes_with_an_edge}
      edges={edges}
      orderings={orderings}
      blocks={d.blocks}
      confidence={confidence}
      labelFor={(g: number) => d.genes[g]}
      picked={picked}
      onPickBlock={setPicked}
      ariaLabel="Gene interaction matrix, reordered by consensus community"
      source={`${d.counts.edges.toLocaleString("en-US")} edges · ${d.counts.isolated_dropped.toLocaleString("en-US")} isolated genes dropped`}
      readAloud={
        <>
          Every gene pair that shares at least one disease, drawn once. The axes are the same
          3,335 genes in the same order, so a mark at row <em>a</em> column <em>b</em> means
          those two are connected; the shade of a pixel is how many pairs fall in it. Blocks
          on the diagonal are communities and the strip on the right is each block&rsquo;s
          consensus confidence. Now switch the ordering, and read the number rather than the
          picture: <strong>consensus</strong> puts{" "}
          {pct(d.locality?.consensus?.share_within_1pct_of_diagonal)} of edges within 1&thinsp;%
          of the diagonal, but it was told where the communities are.{" "}
          <strong>spectral</strong> was not, and still reaches{" "}
          {pct(d.locality?.spectral?.share_within_1pct_of_diagonal)} &mdash; that is the
          evidence the blocks are in the graph. <strong>degree</strong> is the control at{" "}
          {pct(d.locality?.degree?.share_within_1pct_of_diagonal)}, against{" "}
          {pct(d.locality?.random?.share_within_1pct_of_diagonal)} for a random shuffle: some
          structure appears under any ordering, and the question is always how much more.
        </>
      }
    />
    {/* Beneath the figure, not beside it: the card answers a question the reader asks OF the
        figure, and putting it alongside would make the matrix narrower on every screen for
        the sake of a panel that is empty until something is clicked. */}
    <IdentityCard community={picked} />
    </>
  );
}

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

      {/* THE GRAPH ITSELF, FIRST. Every number below describes a partition of 38,746 edges
          that this site had never drawn one of. The measurements are worth more once the
          reader has seen the thing being measured — and the ordering switch turns the whole
          argument about whether the blocks are real into something they can check by eye. */}
      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.csMatrix)}</span>
        <NetworkMatrix />
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

      {/* WHERE THE DISAGREEMENT ACTUALLY IS. The figure above gives an ARI of 0.29 between
          algorithm families, which a reader has to take on faith. This is the same fact as a
          picture, and it carries what the score throws away: which groups the genes move
          between, and whether it is a handful of border cases or a re-partition. */}
      {(flowRaw as any).flows?.length > 0 && (
        <div className={css.block}>
          <span className={css.blockK}>{tt(DEEP.csFlow)}</span>
          <AlluvialPlot
            axes={(flowRaw as any).axes}
            flows={(flowRaw as any).flows}
            order={(flowRaw as any).band_order?.order ?? {}}
            ariaLabel="Genes flowing between the communities found by three clustering algorithms"
            source={(flowRaw as any).band_order?.method}
            readAloud={
              <>
                Each column is one algorithm&rsquo;s partition of the same 3,335 genes, split
                into its communities; a ribbon carries the genes going from one community to
                another and its thickness is how many. Grey ribbons run between communities the
                matching paired — that is agreement. Coloured ribbons are genes the two
                algorithms put in different places. Louvain and Leiden keep{" "}
                {pct((flowRaw as any).matching?.["louvain->leiden"]?.share_matched)} of genes in
                matched communities; Leiden and label propagation keep{" "}
                {pct((flowRaw as any).matching?.["leiden->label_prop"]?.share_matched)}. The
                communities are matched by an exact assignment solution before anything is
                drawn, so the crossings are disagreement rather than an accident of labelling.
              </>
            }
          />
          <p className={css.caveat}>{(flowRaw as any).method}</p>
        </div>
      )}

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
