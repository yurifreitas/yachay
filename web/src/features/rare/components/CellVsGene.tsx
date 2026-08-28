/** Cell versus gene — the axis this whole repository is built on, in a disease.
 *
 *  THE ARGUMENT. `sieve`'s core data structure is a matrix of **cell lines × genes**, and
 *  its central statistic is a top-k over the *cell lines* where a gene matters. The
 *  library's entire premise is that a gene's effect is not a property of the gene; it is a
 *  property of the gene in a context.
 *
 *  Lupus is the clinical form of that premise, and it carries three things the rest of the
 *  atlas cannot:
 *
 *   1. a disease sitting ON the rare-disease boundary rather than inside or outside it;
 *   2. an ultra-rare **monogenic** subset inside a common polygenic disease — the same
 *      gene (TNFAIP3) appearing as a mendelian cause and as a small-effect population risk;
 *   3. an explicit cell axis, where the most striking recent result is a **cell** therapy
 *      rather than a gene therapy.
 *
 *  FORM: a heatmap of gene × cell, because the question is "where does this act", and an
 *  incidence matrix is what answers it. The scale is deliberately coarse — primary /
 *  plausible / not described — because a finer one would imply a precision the sources do
 *  not have. Coarseness that matches the evidence is not a limitation, it is honesty.
 */
import { useMemo, useState } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { chartInk, sequential, categorical, type Mode } from "../../../lib/palette";
import { lupus } from "../data/lupus";
import { Chip } from "../../../components/atoms/Chip";
import { StatusDot } from "../../../components/atoms/StatusDot";
import css from "./CellVsGene.module.css";

const EFFECT_LABEL: Record<string, string> = {
  loss: "loss of function",
  gain: "GAIN of function",
};

export function CellVsGene() {
  const [axis, setAxis] = useState<string | null>(null);
  const genes = useMemo(
    () => (axis ? lupus.monogenic.filter((m) => m.axis === axis) : lupus.monogenic),
    [axis]
  );
  const rows = useMemo(
    () => lupus.matrix.filter((r) => genes.some((g) => g.gene === r.gene)),
    [genes]
  );

  /** gene × cell incidence. The same shape as the screen this library was built on. */
  const build = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const ramp = sequential(mode);
      const cells = lupus.cells;
      const data: [number, number, number][] = [];
      rows.forEach((r, gi) => {
        cells.forEach((c, ci) => {
          data.push([ci, gi, (r as unknown as Record<string, number>)[c.id] ?? 0]);
        });
      });
      return {
        animation: false,
        grid: { left: 118, right: 24, top: 76, bottom: 16 },
        tooltip: {
          formatter: (o: { data: [number, number, number] }) => {
            const [ci, gi, v] = o.data;
            const g = rows[gi];
            const c = cells[ci];
            const where = v === 2 ? "primary site described" : v === 1 ? "same lineage, plausible" : "not described here";
            return `<strong>${g.gene}</strong> in <strong>${c.name}</strong><br/>${where}<br/>` +
                   `<span style="opacity:.7">${c.role}</span>`;
          },
          extraCssText: "max-width:300px;white-space:normal;line-height:1.5",
        },
        xAxis: {
          type: "category",
          position: "top",
          data: cells.map((c) => c.name),
          axisLine: { show: false },
          axisTick: { show: false },
          splitArea: { show: true, areaStyle: { color: ["transparent"] } },
          // Horizontal and wrapped, not rotated: rotated labels are slower to read and
          // were being clipped. Two short lines beat one angled line.
          axisLabel: {
            color: ink.muted, fontSize: 11, interval: 0,
            width: 92, overflow: "break", lineHeight: 14,
            align: "center", verticalAlign: "bottom", margin: 12,
          },
        },
        yAxis: {
          type: "category",
          data: rows.map((r) => r.gene),
          inverse: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: ink.text, fontSize: 12, fontWeight: 500 },
        },
        visualMap: { show: false, min: 0, max: 2, inRange: { color: [ramp[0], ramp[2], ramp[4]] } },
        series: [
          {
            type: "heatmap",
            data,
            itemStyle: { borderWidth: 3, borderColor: ink.surface, borderRadius: 3 },
            emphasis: { itemStyle: { borderColor: ink.text, borderWidth: 2 } },
          },
        ],
      };
    },
    [rows]
  );

  /** Therapies arranged by the CELL they act on — which is how the gap becomes visible. */
  const therapyBuild = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const [c1, , , cGreen, cRed] = categorical(mode);
      const counts = lupus.cells.map(
        (c) => lupus.therapies.filter((t) => t.cell === c.id).length
      );
      return {
        animation: false,
        grid: { left: 176, right: 56, top: 8, bottom: 34 },
        tooltip: {
          trigger: "item",
          formatter: (o: { dataIndex: number }) => {
            const c = lupus.cells[o.dataIndex];
            const ts = lupus.therapies.filter((t) => t.cell === c.id);
            return `<strong>${c.name}</strong><br/>${c.role}<br/><br/>` +
              (ts.length ? ts.map((t) => `· ${t.name} (${t.status})`).join("<br/>")
                         : "<em>nothing points here</em>");
          },
          extraCssText: "max-width:320px;white-space:normal;line-height:1.5",
        },
        xAxis: {
          type: "value", minInterval: 1,
          axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11 },
          name: "therapies pointed at this cell",
          nameLocation: "middle", nameGap: 24,
          nameTextStyle: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: lupus.cells.map((c) => c.name),
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
              color: (o: { value: number }) => (o.value === 0 ? cRed : o.value >= 3 ? cGreen : c1),
            },
            label: {
              show: true, position: "right",
              formatter: (o: { value: number }) => (o.value === 0 ? "none" : String(o.value)),
              color: ink.muted, fontSize: 11,
            },
            data: counts,
          },
        ],
      };
    },
    []
  );

  const orphanCells = lupus.cells.filter((c) => lupus.summary.cellsWithNoTherapy.includes(c.id));

  return (
    <div className={css.root}>
      <div className={css.intro}>
      {/* --- the framing ---------------------------------------------------------- */}
      <div className={css.frame}>
        <p className={css.claim}>
          This repository's own data is a matrix of <strong>cell lines × genes</strong>, and
          its central statistic is a top-<span className="num">k</span> over the cell lines
          where a gene matters. The premise is that a gene's effect is not a property of the
          gene — it is a property of the gene <em>in a context</em>.
        </p>
        <p className={css.claim}>
          Lupus is the clinical form of that premise. Naming a gene rarely tells you what to
          do; naming the <strong>cell</strong> often does. The result that reframed the
          field recently was a <strong>cell</strong> therapy — CD19 CAR-T producing
          drug-free remission in refractory disease — not a gene therapy.
        </p>
      </div>

      {/* --- the boundary --------------------------------------------------------- */}
      <aside className={css.boundary}>
        <h4 className={css.boundaryTitle}>A disease that is rare in one country and not in another</h4>
        <p>{lupus.sle.note}</p>
        <p className={css.disparity}>{lupus.sle.disparity}</p>
        <div className={css.chips}>
          <Chip tone="partial">{lupus.sle.architecture}</Chip>
          <Chip>{lupus.sle.loci}</Chip>
          <StatusDot state="partial" label={`confidence: ${lupus.sle.confidence}`} size="sm" />
        </div>
      </aside>
      </div>

      <div className={css.pair}>
      {/* --- gene x cell ---------------------------------------------------------- */}
      <section className={css.block}>
        <div className={css.blockHead}>
          <div>
            <h4 className={css.h4}>The same matrix shape, in a disease: which gene acts in which cell</h4>
            <p className={css.sub}>
              Twelve genes in which a single lesion is enough to cause lupus — the ultra-rare
              monogenic subset inside a common polygenic disease. Darkest is where the
              mechanism is usually described; mid is the same lineage, plausible.
            </p>
          </div>
          <div className={css.filters} role="group" aria-label="Filter by mechanism">
            <button type="button" className={axis === null ? css.tabOn : css.tab}
                    onClick={() => setAxis(null)}>All mechanisms</button>
            {lupus.axes.map((a) => (
              <button key={a.id} type="button"
                      className={axis === a.id ? css.tabOn : css.tab}
                      onClick={() => setAxis(a.id)} title={a.note}>
                {a.name}
              </button>
            ))}
          </div>
        </div>
        <EChart
          build={build}
          height={Math.max(240, rows.length * 34 + 120)}
          deps={[rows]}
          ariaLabel={`Heatmap of ${rows.length} monogenic lupus genes against seven cell types, showing where each gene's mechanism is described.`}
        />
      </section>

      {/* --- where the therapies point -------------------------------------------- */}
      <section className={css.block}>
        <div>
          <h4 className={css.h4}>Every therapy points at a lymphoid cell or the interferon producer</h4>
          <p className={css.sub}>
            Arranging the therapies by the <strong>cell</strong> they act on rather than the
            molecule they bind makes a gap visible that a drug list hides.
          </p>
        </div>
        <EChart
          build={therapyBuild}
          height={330}
          ariaLabel="Bar chart of therapies per cell type; monocyte, neutrophil and kidney have none."
        />
      </section>
      </div>

      <p className={css.finding}>
        <strong>Nothing points at {orphanCells.map((c) => c.name.toLowerCase()).join(", ")}.</strong>{" "}
        The monocyte is where the mechanism <em>starts</em> — failed clearance of dying
        cells is the debris that becomes the antigen — and the kidney is where it becomes
        organ damage. The field treats the amplifier and the antibody factory, which is
        where the tractable targets are, not where the causal chain begins.{" "}
        <span className={css.caveat}>
          That is an observation about this seed's arrangement, not a claim that such
          programmes do not exist.
        </span>
      </p>

      {/* --- the gene list -------------------------------------------------------- */}
      <ul className={css.genes}>
        {genes.map((g) => (
          <li key={g.gene} className={css.gene}>
            <span className={css.geneName}>
              {g.gene}
              {g.alt.length > 0 && <span className={css.alt}>+{g.alt.join(", ")}</span>}
            </span>
            <span className={css.geneMeta}>
              <Chip tone={g.effect === "gain" ? "unknown" : "known"}>{EFFECT_LABEL[g.effect]}</Chip>
              <Chip>{g.inherit}</Chip>
              <Chip tone={g.penetrance.includes("high") ? "known" : "partial"}>
                penetrance {g.penetrance}
              </Chip>
            </span>
            <span className={css.geneNote}>{g.note}</span>
          </li>
        ))}
      </ul>

      <p className={css.provenance}>
        <strong>Provenance.</strong> {lupus.provenance}
      </p>
    </div>
  );
}
