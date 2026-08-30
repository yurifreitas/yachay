import { useMemo } from "react";
import { PlotFrame } from "../../atoms/PlotFrame";
import { AxisX, RuleX } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { kde1d, quantiles, beeswarm } from "../../../../lib/viz/density";
import { fmt, fmtInt } from "../../../../lib/scale";
import css from "./RaincloudPlot.module.css";
import type { RaincloudPlotProps } from "./RaincloudPlot.types";

/** English ordinals, because "every 2th point" is the kind of detail that makes a reader
 *  doubt the arithmetic above it. */
function ordinal(n: number): string {
  const rem100 = n % 100;
  if (rem100 >= 11 && rem100 <= 13) return `${n}th`;
  return `${n}${["th", "st", "nd", "rd"][n % 10] ?? "th"}`;
}

/** Distributions compared as SHAPES, with every observation still on the page.
 *
 *  WHAT WAS WRONG WITH THE BOX PLOT IT REPLACES. A box plot is five numbers. Two
 *  distributions with the same five numbers can be unimodal and bimodal, or symmetric and
 *  violently skewed, and the box draws them identically — the failure Matejka & Fitzmaurice
 *  made unignorable with the Datasaurus dozen. On this site that is not a hypothetical: the
 *  populations panel is the figure that is supposed to show whether the controls sit at the
 *  null and whether the candidates separate from it, and a second mode in either is the most
 *  interesting thing that could happen. The box could not have shown it.
 *
 *  A raincloud (Allen et al., 2019) is three encodings of one group stacked:
 *    - the CLOUD, a half-density, for the shape;
 *    - the BOX, for the summary a reader will quote;
 *    - the RAIN, every observation as a dodged mark, for n and for the outliers.
 *  Nothing is hidden and nothing is asserted twice from different arithmetic — the box and
 *  the cloud are computed from the same array in the same pass.
 *
 *  The dodge is one-dimensional: a point moves only on the axis that means nothing, so it
 *  never leaves the value it represents. Jitter, the usual shortcut, moves it on both.
 */
export function RaincloudPlot({
  groups, domain, width = 860, rowHeight = 132, xLabel, xNote, xFormat = (v) => fmt(v, 1),
  ariaLabel, readAloud, zeroLine, maxRain = 400,
}: RaincloudPlotProps) {
  const height = 40 + groups.length * rowHeight + 52;

  const stats = useMemo(
    () => groups.map((g) => {
      const [min, q1, med, q3, max] = quantiles(g.values, [0, 0.25, 0.5, 0.75, 1]);
      const mean = g.values.reduce((s, x) => s + x, 0) / Math.max(1, g.values.length);
      return { ...g, min, q1, med, q3, max, mean };
    }),
    [groups],
  );

  return (
    <div className={css.wrap}>
      {readAloud && (
        <ReadAloud form="Raincloud"
                   source="Allen, Poggiali, Whitaker, Marshall & Kievit (2019), Wellcome Open Research.">
          {readAloud}
        </ReadAloud>
      )}

      <PlotFrame width={width} height={height} ariaLabel={ariaLabel} scrollAtWidth={560}
                 margin={{ top: 24, right: 24, bottom: 52, left: 150 }}>
        {(box) => {
          // The x scale is shared by every row, which is the whole point: the comparison is
          // a position judgement on a COMMON scale, the top of the Cleveland-McGill order.
          const lo = domain?.[0] ?? Math.min(...stats.map((s) => s.min));
          const hi = domain?.[1] ?? Math.max(...stats.map((s) => s.max));
          const pad = (hi - lo) * 0.04;
          const x = (v: number) =>
            box.x0 + ((v - (lo - pad)) / ((hi + pad) - (lo - pad) || 1)) * box.width;
          const scale = Object.assign(x, {
            domain: [lo - pad, hi + pad] as [number, number],
            ticks: (n = 6) => {
              const step = (hi - lo) / n;
              const e = 10 ** Math.floor(Math.log10(Math.abs(step) || 1));
              const f = step / e;
              const nice = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e;
              const out: number[] = [];
              for (let t = Math.ceil(lo / nice) * nice; t <= hi + 1e-9; t += nice)
                out.push(Number(t.toPrecision(12)));
              return out;
            },
          });

          return (
            <>
              <AxisX scale={scale} box={box} label={xLabel} note={xNote} format={xFormat} ticks={6} />
              {zeroLine !== undefined && (
                <RuleX at={x(zeroLine)} box={box} label={`${xFormat(zeroLine)}`} />
              )}

              {stats.map((g, gi) => {
                const top = box.y1 + gi * rowHeight;
                const cloudH = rowHeight * 0.42;
                const rainY = top + rowHeight * 0.72;

                // This group's own marker: the observed value the null beneath it exists to
                // calibrate. Drawn per row rather than as one figure-wide rule, because four
                // arms have four different observed values and collapsing them would be the
                // same error as drawing one null line for a null indexed by count.
                const marker = groups[gi]?.marker;

                // The cloud. Its bandwidth is reported in the row label, because a density
                // curve without its bandwidth is a claim about smoothness, not a measurement.
                const { points, bandwidth } = kde1d(g.values, { grid: 128 });
                const peak = Math.max(...points.map((p) => p.y), 1e-9);
                const area =
                  `M${x(points[0]?.x ?? lo)},${top + cloudH} ` +
                  points.map((p) => `L${x(p.x)},${top + cloudH - (p.y / peak) * cloudH}`).join(" ") +
                  ` L${x(points[points.length - 1]?.x ?? hi)},${top + cloudH} Z`;

                // The rain. Capped, and the cap is stated rather than silently applied —
                // a plot that drops points without saying so is the failure this repository
                // keeps finding elsewhere.
                const shown = g.values.length > maxRain
                  ? g.values.filter((_, i) => i % Math.ceil(g.values.length / maxRain) === 0)
                  : g.values;
                const px = shown.map(x);
                const raw = beeswarm(px, 4.4);
                // THE SWARM IS SCALED TO ITS BAND, NOT CLIPPED.
                // A beeswarm's height is set by local density, so five hundred genes sharing
                // one z value pile into a column hundreds of pixels tall and walk straight
                // through the neighbouring rows — which is what this figure did before the
                // scaling was added. Compressing the offsets uniformly is free: the offset
                // axis carries no units at all, so squeezing it removes no information,
                // whereas clipping would silently delete observations.
                const band = rowHeight * 0.22;
                const widest = Math.max(...raw.map(Math.abs), 1e-6);
                const squeeze = widest > band ? band / widest : 1;
                const dodge = raw.map((o) => o * squeeze);

                return (
                  <g key={g.label}>
                    <text x={box.x0 - 14} y={top + rowHeight * 0.34} textAnchor="end"
                          className={css.rowLabel}>
                      {g.label}
                    </text>
                    <text x={box.x0 - 14} y={top + rowHeight * 0.34 + 15} textAnchor="end"
                          className={css.rowMeta}>
                      n {fmtInt(g.values.length)} · h {fmt(bandwidth, 2)}
                    </text>

                    <path d={area} className={css.cloud} style={{ fill: g.color }} />

                    {/* THE OBSERVED VALUE, INSIDE ITS OWN NULL. This is the whole reading of
                        the figure: the cloud is what a length-matched resample produces, and
                        the rule is what the real gene set produced. Drawn over the cloud and
                        under the rain so it is never hidden by a droplet. */}
                    {marker && (
                      <g>
                        <line x1={x(marker.at)} x2={x(marker.at)}
                              y1={top - 2} y2={top + cloudH + 26}
                              className={css.observed} />
                        <text x={x(marker.at)} y={top - 6} textAnchor="middle"
                              className={css.observedLabel}>
                          {marker.label}
                        </text>
                      </g>
                    )}

                    {/* The box, drawn thin. It is the summary, not the subject. */}
                    <line x1={x(g.min)} x2={x(g.max)} y1={top + cloudH + 16} y2={top + cloudH + 16}
                          className={css.whisker} />
                    <rect x={x(g.q1)} y={top + cloudH + 10} width={Math.max(1, x(g.q3) - x(g.q1))}
                          height={12} className={css.box} style={{ stroke: g.color }} />
                    <line x1={x(g.med)} x2={x(g.med)} y1={top + cloudH + 8} y2={top + cloudH + 24}
                          className={css.median} />

                    {px.map((p, i) => (
                      <circle key={i} cx={p} cy={rainY + dodge[i]} r={1.9}
                              className={css.drop} style={{ fill: g.color }} />
                    ))}

                    {shown.length < g.values.length && (
                      <text x={box.x1} y={top + rowHeight - 6} textAnchor="end"
                            className={css.rowMeta}>
                        {`rain thinned to every ${ordinal(Math.ceil(g.values.length / maxRain))} point; the cloud, the box and the table use all ${fmtInt(g.values.length)}`}
                      </text>
                    )}
                  </g>
                );
              })}
            </>
          );
        }}
      </PlotFrame>

      <table className={css.numbers}>
        <thead>
          <tr><th>group</th><th>n</th><th>min</th><th>q1</th><th>median</th><th>q3</th><th>max</th><th>mean</th></tr>
        </thead>
        <tbody>
          {stats.map((g) => (
            <tr key={g.label}>
              <th scope="row">{g.label}</th>
              <td>{fmtInt(g.values.length)}</td>
              <td>{fmt(g.min, 2)}</td><td>{fmt(g.q1, 2)}</td><td>{fmt(g.med, 2)}</td>
              <td>{fmt(g.q3, 2)}</td><td>{fmt(g.max, 2)}</td><td>{fmt(g.mean, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
