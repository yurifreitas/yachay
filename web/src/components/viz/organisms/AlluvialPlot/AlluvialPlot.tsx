import { useMemo, useState } from "react";
import { PlotFrame } from "../../atoms/PlotFrame";
import { ReadAloud } from "../../atoms/ReadAloud";
import css from "./AlluvialPlot.module.css";
import type { AlluvialPlotProps } from "./AlluvialPlot.types";

/** Parallel sets: how the same items are grouped differently by three classifications.
 *
 *  THE QUESTION THIS FORM IS FOR is flow between categorisations, and it is the one question a
 *  bar chart of agreement scores cannot answer. "Two algorithms agree at ARI 0.29" is a number
 *  a reader has to take on faith; a braid of ribbons where half the genes cross is the same
 *  fact as a picture, and it also says WHICH groups the movement is between — which the score
 *  throws away.
 *
 *  EVERYTHING GEOMETRIC IS SOLVED IN PYTHON (ADR 0008). The band order comes from barycentre
 *  sweeps that cut ribbon crossings from 1,542 to 739, and the community matching behind it is
 *  an exact assignment solution rather than a greedy pass. Both are decisions about what the
 *  figure ARGUES, so neither belongs in a render function where it would be recomputed — and
 *  possibly differently — for every reader.
 *
 *  THE RIBBONS THAT MATTER ARE THE ONES THAT CROSS. A ribbon between two communities the
 *  matching paired is agreement, and it is drawn faintly; a ribbon to anywhere else is a gene
 *  the two algorithms disagree about, and it carries the colour. Emphasis by contrast, not by
 *  saturating everything.
 *
 *  WHY NOT A CHORD DIAGRAM, which is the other obvious choice: a chord diagram is for flows
 *  within ONE set of categories. Here there are three different sets in a fixed order, and the
 *  left-to-right reading is the point.
 */
export function AlluvialPlot({
  axes, flows, order, width = 900, height = 560, ariaLabel, readAloud, source,
}: AlluvialPlotProps) {
  const [hover, setHover] = useState<string | null>(null);

  const layout = useMemo(() => {
    const GAP = 3;
    const cols = axes.map((ax, ai) => {
      const ids = order[ax.algorithm] ?? ax.bands.map((b) => b.id);
      const byId = new Map(ax.bands.map((b) => [b.id, b]));
      const ordered = ids.map((id) => byId.get(id)).filter(Boolean) as typeof ax.bands;
      const total = ordered.reduce((s, b) => s + b.genes, 0) || 1;
      const usable = height - 60 - GAP * (ordered.length - 1);
      let y = 30;
      return {
        algorithm: ax.algorithm,
        x: 60 + ai * ((width - 200) / (axes.length - 1)),
        bands: ordered.map((b) => {
          const h = Math.max(1.5, (b.genes / total) * usable);
          const box = { ...b, y, h, key: `${ax.algorithm}:${b.id}` };
          y += h + GAP;
          return box;
        }),
      };
    });

    // A running offset per band, so ribbons stack inside the band they leave and enter rather
    // than all starting from its top edge.
    const outAt = new Map<string, number>();
    const inAt = new Map<string, number>();
    const boxOf = new Map<string, any>();
    for (const c of cols) for (const b of c.bands) boxOf.set(b.key, b);

    const ribbons = flows
      .filter((f) => boxOf.has(f.from) && boxOf.has(f.to))
      .map((f) => {
        const a = boxOf.get(f.from);
        const b = boxOf.get(f.to);
        const ca = cols.find((c) => c.bands.includes(a))!;
        const cb = cols.find((c) => c.bands.includes(b))!;
        const scaleA = a.h / Math.max(a.genes, 1);
        const scaleB = b.h / Math.max(b.genes, 1);
        const w = f.genes;
        const y0 = a.y + (outAt.get(a.key) ?? 0);
        const y1 = b.y + (inAt.get(b.key) ?? 0);
        outAt.set(a.key, (outAt.get(a.key) ?? 0) + w * scaleA);
        inAt.set(b.key, (inAt.get(b.key) ?? 0) + w * scaleB);
        return { ...f, x0: ca.x + 12, x1: cb.x, y0, y1, h0: w * scaleA, h1: w * scaleB };
      });

    return { cols, ribbons };
  }, [axes, flows, order, width, height]);

  return (
    <div className={css.wrap}>
      <PlotFrame width={width} height={height} ariaLabel={ariaLabel} scrollAtWidth={620}
                 margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
        {() => (
          <>
            {layout.ribbons.map((r) => {
              const mid = (r.x0 + r.x1) / 2;
              const on = hover === r.from || hover === r.to;
              const d = `M ${r.x0} ${r.y0}
                         C ${mid} ${r.y0}, ${mid} ${r.y1}, ${r.x1} ${r.y1}
                         L ${r.x1} ${r.y1 + r.h1}
                         C ${mid} ${r.y1 + r.h1}, ${mid} ${r.y0 + r.h0}, ${r.x0} ${r.y0 + r.h0} Z`;
              return (
                <path
                  key={`${r.from}-${r.to}`}
                  d={d}
                  className={r.matched ? css.ribbonMatched : css.ribbonMoved}
                  style={on ? { opacity: 0.85 } : undefined}
                >
                  <title>
                    {r.genes} genes · {r.from} → {r.to}
                    {r.matched ? " (matched)" : " (moved)"}
                  </title>
                </path>
              );
            })}

            {layout.cols.map((c) => (
              <g key={c.algorithm}>
                <text x={c.x + 6} y={18} className={css.axisLabel}>{c.algorithm}</text>
                {c.bands.map((b) => (
                  <g key={b.key}
                     onMouseEnter={() => setHover(b.key)}
                     onMouseLeave={() => setHover(null)}>
                    <rect x={c.x} y={b.y} width={12} height={b.h}
                          className={b.id === -1 ? css.bandOther : css.band} />
                    {/* Only bands with room get a label. A 4px band with a name beside it
                        produces overlapping text and hides the ribbons underneath. */}
                    {b.h > 16 && (
                      <text x={c.x + 16} y={b.y + b.h / 2} dominantBaseline="middle"
                            className={css.bandLabel}>
                        {b.name ? b.name.slice(0, 26) : `#${b.id}`}
                        <tspan className={css.bandCount}> {b.genes}</tspan>
                      </text>
                    )}
                  </g>
                ))}
              </g>
            ))}
          </>
        )}
      </PlotFrame>
      <ReadAloud form="parallel sets" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}
