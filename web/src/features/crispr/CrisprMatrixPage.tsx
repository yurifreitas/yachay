import { useMemo, useState } from "react";
import { useT } from "../../i18n";
import { CRISPR } from "../../i18n/crispr";
import { DenseMatrix } from "../../components/viz/organisms/DenseMatrix";
import { useRemoteData } from "../../lib/useRemoteData";
import { fmtInt } from "../../lib/scale";
import css from "./CrisprMatrixPage.module.css";

/** The whole DepMap screen, drawn.
 *
 *  WHAT THIS PAGE IS FOR. Everything else on this site that touches DepMap shows a ranked
 *  table or a sampled scatter. Both hide the same three things, and all three are structural:
 *  the common-essential band, the lineage blocks, and how little of the matrix is either. A
 *  ranked table cannot show the third at all — it only ever shows the top.
 *
 *  THE PAYLOAD IS 3.8 MB AND THAT IS THE POINT. It is a byte per cell for 1,178 cell lines by
 *  1,200 gene bins, quantised from 21.1 million measurements. Fetched rather than bundled, on
 *  the one route that draws it.
 */
export function CrisprMatrixPage() {
  const tt = useT();
  const d = useRemoteData<any>("data/crispr_matrix.json");
  const [ordering, setOrdering] = useState("seriated");

  const model = useMemo(() => {
    if (d.state !== "ready") return null;
    const raw = d.data;
    const decode = (b64: string) => {
      const bin = atob(b64);
      const out = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
      return out;
    };
    return {
      raw,
      seriated: decode(raw.image),
      alphabetical: decode(raw.image_alphabetical),
    };
  }, [d]);

  if (d.state === "loading") return <p className={css.loading}>{tt(CRISPR.wholeLoading)}</p>;
  if (!model) return null;
  const { raw } = model;
  const bytes = ordering === "seriated" ? model.seriated : model.alphabetical;
  const rows = raw.shape.lines;
  const cols = raw.shape.bins;

  return (
    <div className={css.page}>
      <header className={css.head}>
        <h1>{tt(CRISPR.wholeTitle)}</h1>
        <p className={css.value}>{fmtInt(raw.shape.values)}</p>
        <p className={css.sub}>{raw.says}</p>
      </header>

      <DenseMatrix
        bytes={bytes}
        rows={rows}
        cols={cols}
        rowLabels={raw.lines.map((l: any) => l.id)}
        rowGroups={
          /* Under the alphabetical control the rows are in file order, so the lineage strip
             would be labelling a different arrangement than the one shipped with it. Dropping
             it there is the honest move: a strip that does not match its matrix is worse than
             no strip. */
          ordering === "seriated" ? raw.lines.map((l: any) => l.lineage) : undefined
        }
        colLabels={raw.bin_names}
        colMargin={ordering === "seriated" ? raw.essential_share : undefined}
        marginLabel={tt(CRISPR.wholeMargin)}
        height={640}
        orderings={{
          lo: raw.scale.low,
          hi: raw.scale.high,
          options: {
            seriated: { says: raw.orderings.seriated.says },
            alphabetical: { says: raw.orderings.alphabetical.says },
          },
        }}
        ordering={ordering}
        onOrdering={setOrdering}
        ariaLabel="CRISPR gene effect across every cell line and gene in the DepMap screen"
        source={`${fmtInt(rows)} cell lines · ${fmtInt(raw.shape.genes)} genes · ${raw.shape.genes_per_bin} genes per column`}
        readAloud={
          <>
            Every gene, every cell line. One row per line, one column per{" "}
            {raw.shape.genes_per_bin} genes, and the colour is the gene effect: blue where the
            cells needed the gene, orange where losing it helped them, and the page&rsquo;s own
            background where it made no difference — which is most of it. The strip on the left
            is the lineage of each row; the strip beneath is what share of each column is a
            known common-essential gene. Switch to <strong>alphabetical</strong> and the blocks
            should dissolve: alphabetical order carries no biology, so any structure that
            survives it is in your eye rather than in the screen.
          </>
        }
      />

      <div className={css.notes}>
        <div className={css.note}>
          <span className={css.noteK}>{tt(CRISPR.wholeOrderingK)}</span>
          <p>{raw.orderings.seriated.says}</p>
          <p className={css.caveat}>{raw.orderings.seriated.cannot}</p>
        </div>
        <div className={css.note}>
          <span className={css.noteK}>{tt(CRISPR.wholeRoughnessK)}</span>
          <p>{raw.roughness.says}</p>
          <ul className={css.rough}>
            <li><strong>{raw.roughness.seriated}</strong> {tt(CRISPR.wholeSeriated)}</li>
            <li><strong>{raw.roughness.alphabetical}</strong> {tt(CRISPR.wholeAlpha)}</li>
            <li><strong>{raw.roughness.shuffled}</strong> {tt(CRISPR.wholeShuffled)}</li>
          </ul>
        </div>
        <div className={css.note}>
          <span className={css.noteK}>{tt(CRISPR.wholeBinningK)}</span>
          <p>{raw.binning}</p>
          <p className={css.caveat}>{raw.scale.says}</p>
        </div>
      </div>
    </div>
  );
}
