import { useMemo, useState } from "react";
import { PlotFrame } from "../../atoms/PlotFrame";
import { AxisX } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { linear } from "../../../../lib/scale";
import { symlog } from "../../../../lib/viz/scales";
import { intervalDomain } from "../../../../lib/viz/intervals";
import css from "./IntervalPlot.module.css";
import type { IntervalPlotProps } from "./IntervalPlot.types";

/** An estimate and its interval, one row per entity, on a shared axis.
 *
 *  THE FORM is the forest plot of meta-analysis, and the reason to reach for it here is the
 *  reason it exists there: the question is never "how big is this number" on its own, it is
 *  "does this number's interval clear the line". A bar chart cannot ask that. A bar encodes
 *  a point as a LENGTH FROM ZERO, which draws an estimate as though it were known, and every
 *  panel in this repository that reported a z was doing exactly that.
 *
 *  WHAT THE MARKS MEAN, in the order a reader meets them:
 *
 *    the band     the 95% interval. Its WIDTH is the finding as often as its position is.
 *    the tick     the point estimate, inside its own band.
 *    hollow       the interval does not clear the reference; the row is drawn grey AND
 *                 hollow, because colour alone fails for a tenth of readers.
 *    a bracket    no interval exists. Drawn as an open bracket at the point with the reason
 *                 printed, rather than as a bare dot that would read as a narrow interval —
 *                 which is the opposite of what "no interval" means.
 *
 *  THE AXIS IS USUALLY SYMLOG, and that is not a flourish. These estimates span three
 *  decades and cross zero: a propagation z of 1825 sits in the same figure as one of 2.3,
 *  and on a linear axis every row but the largest collapses onto the reference line. A
 *  symlog axis keeps both readable and ANNOUNCES ITSELF in the axis note, because a reader
 *  who does not notice the scale reads every distance on it wrong.
 *
 *  WHAT IT DELIBERATELY DOES NOT DO. It does not sort. The order of the rows is an argument
 *  the caller is making — by z, by lower bound, by the artefact's own ranking — and hiding
 *  that decision inside a chart component is how a figure ends up asserting something its
 *  author never chose. ADR 0008: a seriation is an argument.
 */
export function IntervalPlot({
  rows, xLabel, scale = "symlog", refs = [], width = 900, height, rowH = 26,
  ariaLabel, readAloud, source, format = (v) => String(Math.round(v * 100) / 100),
}: IntervalPlotProps) {
  const [hover, setHover] = useState<number | null>(null);

  const h = height ?? Math.max(180, rows.length * rowH + 72);
  // Wide enough for the longer of the two label lines. 132 was set when a row was one
  // short word; the notes callers pass now are "296 studies · 44,543,900 sample", and a
  // margin that does not hold them clips rather than wraps.
  const LABEL_W = 196;

  // The domain must contain every BOUND and every reference, not every point. A domain built
  // from the points alone clips the bands that run past them, and a clipped interval is a
  // narrower claim than the data makes — the exact failure this plot exists to prevent.
  // The domain lives in lib/viz/intervals.ts because it is arithmetic with a regression
  // behind it, and arithmetic in a component is arithmetic nobody re-derives. check-viz.mjs
  // holds it to reaching past every bound, containing zero, and containing the references.
  const [d0, d1] = useMemo(
    () => intervalDomain(rows, refs.map((r) => r.at)),
    [rows, refs],
  );

  return (
    <div className={css.wrap}>
      <PlotFrame
        width={width}
        height={h}
        margin={{ left: LABEL_W, right: 88, top: 14, bottom: 46 }}
        ariaLabel={ariaLabel}
        scrollAtWidth={560}
      >
        {(box) => {
          const x = scale === "symlog"
            ? symlog([d0, d1], [box.x0, box.x1])
            : linear([d0, d1], [box.x0, box.x1]);
          const y = (i: number) => box.y1 + rowH / 2 + i * rowH;

          return (
            <>
              {/* References first, so every mark is drawn over them rather than under. */}
              {refs.map((r) => (
                <g key={r.label}>
                  <line
                    x1={x(r.at)} x2={x(r.at)} y1={box.y1} y2={box.y0}
                    className={r.dashed ? css.refDashed : css.ref}
                  />
                  <text x={x(r.at)} y={box.y0 + 30} textAnchor="middle" className={css.refLabel}>
                    {r.label}
                  </text>
                </g>
              ))}

              {rows.map((r, i) => {
                const yi = y(i);
                const has = r.lo != null && r.hi != null;
                const on = hover === i;
                return (
                  <g
                    key={`${r.label}-${i}`}
                    onMouseEnter={() => setHover(i)}
                    onMouseLeave={() => setHover(null)}
                    className={on ? css.rowOn : css.row}
                  >
                    {/* A full-width hit area: a 2px tick is not a pointer target. */}
                    <rect x={box.x0} y={yi - rowH / 2} width={box.width} height={rowH}
                          className={css.hit} />

                    {/* ⚠️ THE NOTE USED TO BE A tspan ON THE SAME LINE, and a long one pushed
                        the label off the left edge of the plot — the addiction figure lost the
                        substance name entirely and showed "…tudies · 44,543,900 sample". Text
                        anchored at the end grows leftwards, so an inline note does not wrap,
                        it clips, and it clips the half that names the row.

                        Two lines, and the note gets the smaller size it should have had. When
                        there is no note the label stays vertically centred, so single-line
                        callers are unchanged. */}
                    {r.note ? (
                      <>
                        <text x={box.x0 - 12} y={yi - 6} textAnchor="end"
                              dominantBaseline="middle" className={css.label}>
                          {r.label}
                        </text>
                        <text x={box.x0 - 12} y={yi + 7} textAnchor="end"
                              dominantBaseline="middle" className={css.note}>
                          {r.note}
                        </text>
                      </>
                    ) : (
                      <text x={box.x0 - 12} y={yi} textAnchor="end" dominantBaseline="middle"
                            className={css.label}>
                        {r.label}
                      </text>
                    )}

                    {has ? (
                      <>
                        <line
                          x1={x(r.lo!)} x2={x(r.hi!)} y1={yi} y2={yi}
                          className={r.ok ? css.band : css.bandOut}
                        />
                        {/* Caps. Without them a band that runs off a crowded axis is
                            indistinguishable from a band that continues. */}
                        <line x1={x(r.lo!)} x2={x(r.lo!)} y1={yi - 4} y2={yi + 4}
                              className={r.ok ? css.cap : css.capOut} />
                        <line x1={x(r.hi!)} x2={x(r.hi!)} y1={yi - 4} y2={yi + 4}
                              className={r.ok ? css.cap : css.capOut} />
                        <circle cx={x(r.point)} cy={yi} r={3.5}
                                className={r.ok ? css.point : css.pointOut} />
                      </>
                    ) : (
                      // No interval: an open bracket, never a dot. A dot would read as a
                      // very precise estimate, which is the opposite of what is being said.
                      <>
                        <path
                          d={`M ${x(r.point) + 7} ${yi - 6} L ${x(r.point)} ${yi - 6}
                              L ${x(r.point)} ${yi + 6} L ${x(r.point) + 7} ${yi + 6}`}
                          className={css.bracket}
                        />
                        <text x={x(r.point) + 12} y={yi} dominantBaseline="middle"
                              className={css.bracketNote}>
                          {r.noInterval}
                        </text>
                      </>
                    )}

                    <text x={box.x1 + 8} y={yi} dominantBaseline="middle" className={css.value}>
                      {format(r.point)}
                    </text>
                  </g>
                );
              })}

              <AxisX
                scale={x} box={box} label={xLabel} ticks={7} format={format}
                note={scale === "symlog" ? "symlog: each step is a decade, either side of zero"
                                         : undefined}
              />
            </>
          );
        }}
      </PlotFrame>

      <ReadAloud form="interval plot" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}
