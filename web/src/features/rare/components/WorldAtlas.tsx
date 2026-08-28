/** The real catalogue, at world scale — and what it is missing.
 *
 *  Everything else in this dashboard was hand-seeded and labelled as a demonstration. This
 *  is joined from the field's own catalogues: HPO's gene-to-disease table and annotations,
 *  Orphanet's prevalence classes, and the Human Protein Atlas single-cell expression that
 *  supplies the cell axis.
 *
 *  THE HEADLINE IS NOT THE SIZE. "14,831 diseases" is a number anyone can quote. The
 *  useful number is how far the join gets before it runs out of data — because that is the
 *  shape of what nobody has filled in, measured rather than asserted, and it is the same
 *  argument as the rest of the atlas made against the whole field instead of twelve rows.
 */
import { useMemo } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { categorical, chartInk, sequential, type Mode } from "../../../lib/palette";
import { atlas } from "../data/atlas";
import css from "./WorldAtlas.module.css";

const pct = (v: number) => `${Math.round(v * 100)}%`;
const num = (v: number) => v.toLocaleString("en-US");

export function WorldAtlas() {
  const s = atlas.scale;
  const c = atlas.coverage;

  /** The funnel: catalogue → has a gene → placeable on a cell. Each step is a real join,
   *  and the drop between steps is the finding. */
  const funnel = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const ramp = sequential(mode);
      const steps = [
        { name: "In the catalogue", value: s.diseases },
        { name: "Has a known gene", value: s.diseasesWithGene },
        { name: "Gene has cell-type data", value: s.diseasesPlaceableOnCellAxis },
      ];
      return {
        animation: false,
        grid: { left: 210, right: 96, top: 8, bottom: 34 },
        tooltip: {
          trigger: "item",
          formatter: (o: { dataIndex: number }) =>
            `<strong>${steps[o.dataIndex].name}</strong><br/>` +
            `${num(steps[o.dataIndex].value)} diseases · ` +
            `${pct(steps[o.dataIndex].value / s.diseases)} of the catalogue`,
        },
        xAxis: {
          type: "value",
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11, formatter: (v: number) => num(v) },
          name: "rare diseases",
          nameLocation: "middle", nameGap: 24,
          nameTextStyle: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: steps.map((x) => x.name),
          inverse: true,
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: ink.text, fontSize: 13 },
        },
        series: [
          {
            type: "bar",
            barWidth: 26,
            itemStyle: {
              borderRadius: 4,
              color: (o: { dataIndex: number }) => ramp[Math.min(4, 2 + o.dataIndex)],
            },
            label: {
              show: true, position: "right",
              formatter: (o: { dataIndex: number }) =>
                `${num(steps[o.dataIndex].value)}  (${pct(steps[o.dataIndex].value / s.diseases)})`,
              color: ink.muted, fontSize: 12,
            },
            data: steps.map((x) => x.value),
          },
        ],
      };
    },
    [s]
  );

  /** Prevalence: how the catalogue distributes across Orphanet's own bands. Ordered
   *  rarest first, so the ultra-rare end reads left. */
  const prevalence = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const ramp = sequential(mode);
      const rows = atlas.prevalenceDistribution;
      return {
        animation: false,
        grid: { left: 130, right: 76, top: 8, bottom: 34 },
        tooltip: {
          trigger: "item",
          formatter: (o: { dataIndex: number }) =>
            `<strong>${rows[o.dataIndex].band}</strong><br/>${num(rows[o.dataIndex].diseases)} diseases`,
        },
        xAxis: {
          type: "value",
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11, formatter: (v: number) => num(v) },
          name: "diseases with this prevalence stated",
          nameLocation: "middle", nameGap: 24,
          nameTextStyle: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: rows.map((r) => r.band),
          inverse: true,
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: ink.text, fontSize: 12 },
        },
        series: [
          {
            type: "bar",
            barWidth: 18,
            itemStyle: {
              borderRadius: 3,
              // Rarest bands take the darkest step: prevalence is ordered, so the colour is.
              color: (o: { dataIndex: number }) =>
                ramp[Math.max(0, 4 - Math.min(4, rows[o.dataIndex].rank))],
            },
            label: {
              show: true, position: "right",
              formatter: (o: { dataIndex: number }) => num(rows[o.dataIndex].diseases),
              color: ink.muted, fontSize: 11,
            },
            data: rows.map((r) => r.diseases),
          },
        ],
      };
    },
    []
  );

  /** Where rare disease lives, by cell type — the cell axis, at catalogue scale. */
  const burden = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const [c1] = categorical(mode);
      const rows = atlas.cellBurden.slice(0, 22);
      return {
        animation: false,
        grid: { left: 250, right: 76, top: 8, bottom: 34 },
        tooltip: {
          trigger: "item",
          formatter: (o: { dataIndex: number }) =>
            `<strong>${rows[o.dataIndex].cell}</strong><br/>` +
            `${num(rows[o.dataIndex].diseaseGenes)} disease-genes reach their highest ` +
            `expression in this cell type`,
          extraCssText: "max-width:300px;white-space:normal;line-height:1.5",
        },
        xAxis: {
          type: "value",
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11, formatter: (v: number) => num(v) },
          name: "disease-genes peaking in this cell type",
          nameLocation: "middle", nameGap: 24,
          nameTextStyle: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: rows.map((r) => r.cell),
          inverse: true,
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: ink.text, fontSize: 12 },
        },
        series: [
          {
            type: "bar",
            barWidth: 14,
            itemStyle: { borderRadius: 3, color: c1 },
            label: {
              show: true, position: "right",
              formatter: (o: { dataIndex: number }) => num(rows[o.dataIndex].diseaseGenes),
              color: ink.muted, fontSize: 11,
            },
            data: rows.map((r) => r.diseaseGenes),
          },
        ],
      };
    },
    []
  );

  return (
    <div className={css.root}>
      <div className={css.tiles}>
        <Tile n={num(s.diseases)} label="rare diseases in the catalogue"
              detail={`OMIM ${num(s.diseasesByPrefix.OMIM ?? 0)} · Orphanet ${num(s.diseasesByPrefix.ORPHA ?? 0)} · DECIPHER ${s.diseasesByPrefix.DECIPHER ?? 0}`} />
        <Tile n={num(s.genes)} label="genes associated with them"
              detail={`${num(s.genesWithCellData)} have single-cell expression data`} />
        <Tile n={num(s.cellTypes)} label="human cell types on the axis"
              detail="Human Protein Atlas single-cell RNA" />
        <Tile n={num(s.ultraRare)} label="ultra-rare, by Orphanet's own bands"
              detail={`under 9 per million · ${pct(c.ultraRareGeneKnown)} have a known gene`}
              warn />
      </div>

      <div className={css.pair}>
        <section className={css.panel}>
          <h4 className={css.h4}>The join runs out before the catalogue does</h4>
          <p className={css.sub}>
            Each bar is a real join, not an estimate. The drop between them is how far the
            field's own data reaches.
          </p>
          <EChart build={funnel} height={210} ariaLabel={
            `Funnel: ${num(s.diseases)} diseases, ${num(s.diseasesWithGene)} with a known gene, ` +
            `${num(s.diseasesPlaceableOnCellAxis)} placeable on a cell type.`} />
          <p className={css.note}>
            <strong>{pct(1 - c.geneKnown)} of catalogued rare diseases have no gene</strong>{" "}
            in HPO's table — roughly {num(s.diseases - s.diseasesWithGene)} entries that are
            named and described but not explained. Among the{" "}
            <strong>ultra-rare</strong> the gap is far worse: only{" "}
            <strong>{pct(c.ultraRareGeneKnown)}</strong> of the {num(s.ultraRare)} diseases
            under nine per million have one. <em>The rarer the disease, the less likely
            anyone knows what causes it</em> — which is the pattern the whole atlas exists
            to make visible, now measured against the field rather than a seed.
          </p>
        </section>

        <section className={css.panel}>
          <h4 className={css.h4}>How rare is rare, by Orphanet&rsquo;s own bands</h4>
          <p className={css.sub}>
            Only diseases with a prevalence record appear. The absent ones are not common —
            they are unmeasured, which the earlier sections model as a value rather than a
            blank.
          </p>
          <EChart build={prevalence} height={260} ariaLabel="Distribution of diseases across Orphanet prevalence bands, rarest first." />
        </section>
      </div>

      <section className={css.panel}>
        <h4 className={css.h4}>Where rare disease lives, by cell type</h4>
        <p className={css.sub}>
          For every disease gene, the cell type in which it reaches its highest single-cell
          expression. This is the cell-versus-gene axis at catalogue scale — the twelve-row
          lupus matrix, run against {num(s.genes)} genes and {s.cellTypes} cell types.
        </p>
        <EChart build={burden} height={520} ariaLabel={`Top ${Math.min(22, atlas.cellBurden.length)} cell types by number of disease genes peaking in them.`} />
        <p className={css.note}>
          <strong>Read this as a coarse signal, not an anatomy.</strong> &ldquo;Highest
          expression&rdquo; is not &ldquo;where the disease happens&rdquo;: a gene can be
          expressed everywhere and matter in one place, and single-cell panels sample some
          tissues far better than others. It is a screening question — which is what this
          repository is for.
        </p>
      </section>

      <p className={css.provenance}>
        <strong>Sources.</strong> {atlas.provenance}
        <br />
        <span className={css.mono}>{atlas.sourceHeader}</span>
      </p>
    </div>
  );
}

function Tile({ n, label, detail, warn }: { n: string; label: string; detail: string; warn?: boolean }) {
  return (
    <article className={`${css.tile} ${warn ? css.tileWarn : ""}`}>
      <span className={css.tileN}>{n}</span>
      <span className={css.tileLabel}>{label}</span>
      <span className={css.tileDetail}>{detail}</span>
    </article>
  );
}
