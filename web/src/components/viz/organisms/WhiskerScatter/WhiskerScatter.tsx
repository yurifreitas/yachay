import { useMemo, useState } from "react";
import { PlotFrame, PlotClip } from "../../atoms/PlotFrame";
import { AxisX, AxisY } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { log, linear } from "../../../../lib/scale";
import { symlog } from "../../../../lib/viz/scales";
import css from "./WhiskerScatter.module.css";
import type { WhiskerScatterProps } from "./WhiskerScatter.types";

/** Two variables, where one of them is an estimate with an interval.
 *
 *  THE PROBLEM IT SOLVES. A scatter plot draws each observation as a dot, and a dot asserts
 *  that the value is known. When the y variable carries a 95% interval — as every calibrated
 *  quantity in this repository now does — the dots are the least informative part of the
 *  figure and the WHISKERS are the finding.
 *
 *  WHY THIS FIGURE EXISTS AT ALL. The propagation artefact's degree-matched null was built so
 *  that hubs could not win by being hubs, and at that end it works. Nothing checked the other
 *  end. A gene of degree 5 is missed by almost every null draw, so the null's spread there is
 *  near zero, and any reach at all divides into an enormous z. Ranking by z therefore selects
 *  the rarely reached. That sentence is a claim; this figure is the evidence, and it can only
 *  be made as a figure — the relationship is between three quantities at once (degree, z, and
 *  the width of z's interval) and no table shows a relationship.
 *
 *  BOTH AXES ARE NON-LINEAR AND BOTH SAY SO. Degree runs from 1 to several thousand, so x is
 *  logarithmic. The z values cross zero and span three decades, so y is symlog. Each axis
 *  prints its own note; an unannounced scale is the most common way a chart lies.
 */
export function WhiskerScatter({
  points, xLabel, yLabel, width = 900, height = 380, refs = [], curve = [], curveLabel,
  yScale = "symlog", yFormat, xFormat, ariaLabel, readAloud, source,
}: WhiskerScatterProps) {
  const [hover, setHover] = useState<number | null>(null);

  const [yd, xd] = useMemo(() => {
    const ys: number[] = [];
    const xs: number[] = [];
    for (const p of points) {
      ys.push(p.y);
      if (p.lo != null) ys.push(p.lo);
      if (p.hi != null) ys.push(p.hi);
      xs.push(Math.max(1, p.x));
    }
    for (const r of refs) ys.push(r.at);
    for (const c of curve) { ys.push(c.y); xs.push(Math.max(1, c.x)); }
    return [
      [Math.min(...ys, 0), Math.max(...ys, 1)] as [number, number],
      [Math.max(1, Math.min(...xs)), Math.max(...xs, 2)] as [number, number],
    ];
  }, [points, refs, curve]);

  return (
    <div className={css.wrap}>
      <PlotFrame
        width={width} height={height} ariaLabel={ariaLabel} scrollAtWidth={560}
        margin={{ left: 66, right: 24, top: 16, bottom: 52 }}
      >
        {(box) => {
          const x = log(xd, [box.x0, box.x1]);
          const y = yScale === "linear"
            ? linear(yd, [box.y0, box.y1])
            : symlog(yd, [box.y0, box.y1]);
          const fy = yFormat
            ?? ((v: number) => (Math.abs(v) >= 1000 ? `${Math.round(v / 1000)}k`
                                                    : String(Math.round(v))));
          const fx = xFormat
            ?? ((v: number) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(Math.round(v))));
          return (
            <>
              {refs.map((r) => (
                <g key={r.label}>
                  <line x1={box.x0} x2={box.x1} y1={y(r.at)} y2={y(r.at)}
                        className={css.ref} />
                  <text x={box.x1 - 4} y={y(r.at) - 5} textAnchor="end" className={css.refLabel}>
                    {r.label}
                  </text>
                </g>
              ))}

              <PlotClip id="whisker-clip" box={box}>
                {/* The calibration curve, drawn BEFORE the points so no observation is
                    hidden behind it. Stepped rather than smoothed: it is measured at a set
                    of counts and interpolating it would draw values nobody computed. */}
                {curve.length > 1 && (
                  <>
                    <path
                      d={curve
                        .map((c, i) => `${i ? "L" : "M"} ${x(Math.max(1, c.x))} ${y(c.y)}`)
                        .join(" ")}
                      className={css.curve}
                    />
                    {curveLabel && (
                      <text
                        x={x(Math.max(1, curve[curve.length - 1].x)) - 6}
                        y={y(curve[curve.length - 1].y) - 8}
                        textAnchor="end"
                        className={css.curveLabel}
                      >
                        {curveLabel}
                      </text>
                    )}
                  </>
                )}
                {points.map((p, i) => {
                  const on = hover === i;
                  const px = x(Math.max(1, p.x));
                  return (
                    <g key={`${p.label}-${i}`}
                       onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
                      {p.lo != null && p.hi != null && (
                        <line x1={px} x2={px} y1={y(p.lo)} y2={y(p.hi)}
                              className={p.ok ? css.whisker : css.whiskerOut} />
                      )}
                      <circle cx={px} cy={y(p.y)} r={on ? 5 : 3}
                              className={p.ok ? css.dot : css.dotOut} />
                      {/* Labelled on hover only. Labelling every point in a cloud of a
                          hundred produces a wall of text and hides the shape, which is the
                          only thing this figure is for. */}
                      {on && (
                        <text x={px + 8} y={y(p.y) - 8} className={css.tip}>
                          {p.label} · {fy(p.y)}
                          {p.lo != null && ` [${fy(p.lo)}, ${fy(p.hi!)}]`}
                        </text>
                      )}
                    </g>
                  );
                })}
              </PlotClip>

              <AxisX scale={x} box={box} label={xLabel} ticks={5} format={fx}
                     note="logarithmic" />
              <AxisY scale={y} box={box} label={yLabel} ticks={7} grid format={fy}
                     note={yScale === "symlog" ? "symlog" : undefined} />
            </>
          );
        }}
      </PlotFrame>
      <ReadAloud form="scatter with intervals" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}
