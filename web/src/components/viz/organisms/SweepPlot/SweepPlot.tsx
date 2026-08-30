import { PlotFrame } from "../../atoms/PlotFrame";
import { AxisX, AxisY } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { linear } from "../../../../lib/scale";
import css from "./SweepPlot.module.css";
import type { SweepPlotProps } from "./SweepPlot.types";

/** Several quantities against one swept parameter, as stacked panels on a shared x.
 *
 *  THE FORM is small multiples, which `data-viz-craft` calls the most underrated form
 *  available and which this figure needs for a specific reason: the panels here are on
 *  incompatible scales — a modularity in [0,1] and a community size in the hundreds — and the
 *  alternative is a dual axis. A dual axis lets the author choose where two curves cross by
 *  choosing the axis ranges, which makes the most important visual event in the chart an
 *  authoring decision. Two panels cannot do that.
 *
 *  WHAT IT WAS BUILT TO SHOW. Sweeping the resolution of a modularity objective from 0.25 to 3
 *  moves the score from 0.842 to 0.857 and back to 0.829 — a flat line — while the largest
 *  community goes from 777 genes to 192. The objective function is nearly indifferent across
 *  a range that changes the answer fourfold, which is the resolution limit made visible. Read
 *  as one chart with two axes that fact is arguable; read as a flat line above a collapsing
 *  one it is not.
 *
 *  EACH PANEL KEEPS ITS OWN Y DOMAIN, and none of them is forced to zero. A line does not have
 *  to start at zero the way a bar does, but the omission has to be visible, so every panel
 *  prints its own range in its axis label rather than leaving the reader to infer it.
 */
export function SweepPlot({
  x, panels, xLabel, width = 900, panelHeight = 130, ariaLabel, readAloud, source, marks = [],
}: SweepPlotProps) {
  const height = panels.length * panelHeight + 52;

  return (
    <div className={css.wrap}>
      <PlotFrame width={width} height={height} ariaLabel={ariaLabel} scrollAtWidth={560}
                 margin={{ left: 72, right: 96, top: 14, bottom: 46 }}>
        {(box) => {
          const xs = linear([Math.min(...x), Math.max(...x)], [box.x0, box.x1]);
          const inner = (box.y0 - box.y1) / panels.length;

          return (
            <>
              {panels.map((p, pi) => {
                const top = box.y1 + pi * inner;
                const bottom = top + inner - 18;
                const lo = Math.min(...p.values);
                const hi = Math.max(...p.values);
                const pad = (hi - lo) * 0.15 || Math.abs(hi) * 0.1 || 1;
                const ys = linear([lo - pad, hi + pad], [bottom, top]);
                const fmt = p.format ?? ((v: number) => String(Math.round(v)));

                return (
                  <g key={p.label}>
                    {/* A hairline at each panel's own top and bottom, instead of a frame.
                        The panels are stacked, so without them the eye merges two curves
                        into one. */}
                    <line x1={box.x0} x2={box.x1} y1={bottom} y2={bottom} className={css.base} />

                    <path
                      d={x.map((v, i) => `${i ? "L" : "M"} ${xs(v)} ${ys(p.values[i])}`).join(" ")}
                      className={p.muted ? css.lineMuted : css.line}
                    />
                    {x.map((v, i) => (
                      <circle key={v} cx={xs(v)} cy={ys(p.values[i])} r={2.6}
                              className={p.muted ? css.dotMuted : css.dot} />
                    ))}

                    {/* The value at the right end, labelled directly. A legend for stacked
                        panels is a lookup the reader should not have to do. */}
                    <text x={box.x1 + 8} y={ys(p.values[p.values.length - 1])}
                          dominantBaseline="middle" className={css.endLabel}>
                      {fmt(p.values[p.values.length - 1])}
                    </text>

                    <AxisY scale={ys} box={{ ...box, y0: bottom, y1: top }} label={p.label}
                           ticks={3} format={fmt} />

                    {marks.map((mk) => (
                      mk.y != null && mk.panel === p.label ? (
                        <g key={mk.label}>
                          <line x1={box.x0} x2={box.x1} y1={ys(mk.y)} y2={ys(mk.y)}
                                className={css.mark} />
                          <text x={box.x0 + 6} y={ys(mk.y) - 5} className={css.markLabel}>
                            {mk.label}
                          </text>
                        </g>
                      ) : null
                    ))}
                  </g>
                );
              })}

              <AxisX scale={xs} box={box} label={xLabel} ticks={x.length}
                     format={(v) => String(Math.round(v * 100) / 100)} />
            </>
          );
        }}
      </PlotFrame>
      <ReadAloud form="small multiples" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}
