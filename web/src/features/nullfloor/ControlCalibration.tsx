/** Do the genes that do nothing score like nothing?
 *
 * FORM: a normal quantile-quantile plot, with the density overlay demoted to a strip
 * underneath. Wilk & Gnanadesikan (1968) introduced the Q-Q plot for exactly this
 * comparison, and it dominates a density overlay here for a specific reason:
 *
 *   - a DENSITY curve shows that two distributions differ, and compresses the tails —
 *     the region a shortlist is actually drawn from — into a flat line near zero;
 *   - a Q-Q plot maps the tails onto the ends of a straight line, where a departure is
 *     a visible bend rather than an invisible sliver, and decomposes the disagreement
 *     into three readable parts: OFFSET from the diagonal is bias, SLOPE is the wrong
 *     spread, CURVATURE at the ends is tail misfit.
 *
 * That decomposition is why this view exists. The density version said "the pooled null
 * is displaced". The Q-Q version says the blocked null is right in the body (median
 * -0.12) and still has a heavy RIGHT tail (99.95th percentile 8.9 against 3.3 expected)
 * — a fact about control-set purity that no density overlay in this repository ever
 * showed.
 *
 * Perceptual basis: position along a common scale is the most accurately decoded visual
 * encoding (Cleveland & McGill 1984), and a Q-Q plot spends that encoding on the thing
 * being judged. A density overlay spends it on the mode, which is not in question.
 */
import { useMemo, useState } from "react";
import { figures } from "../../lib/data/figures";
import { linear, fmt } from "../../lib/scale";
import { AxisX, AxisY, Figure, Grid, Legend, PAD, useTooltip } from "../../components/chart";
import { Sonifier } from "../../components/molecules/Sonifier";
import { playQQ } from "../../lib/sonify";

const W = 620;
const H = 460;

export default function ControlCalibration({ runId }: { runId: string }) {
  const fig = figures[runId]?.control_qq;
  const dens = figures[runId]?.control_calibration;
  const { setTip, node } = useTooltip();
  const [zoomBody, setZoomBody] = useState(false);
  // Index the sonification is currently sweeping, so the plot marks what is being heard.
  const [cursor, setCursor] = useState(-1);

  const { x, y, lim } = useMemo(() => {
    if (!fig) return { x: null, y: null, lim: 0 };
    const all = fig.series.flatMap((s) => s.sample);
    // Squaring the axes matters: on unequal scales a 45-degree reference line is a lie,
    // and the eye reads slope off the drawn angle, not off the tick labels.
    const raw = Math.max(Math.abs(Math.min(...all)), Math.max(...all), 4);
    const l = zoomBody ? 4 : Math.ceil(raw);
    const s = linear([-l, l], [PAD.left, W - PAD.right]);
    const t = linear([-l, l], [H - PAD.bottom, PAD.top]);
    return { x: s, y: t, lim: l };
  }, [fig, zoomBody]);

  if (!fig || !x || !y) return null;

  const COLORS: Record<string, string> = {
    pooled: "var(--series-2)",
    blocked: "var(--series-1)",
  };

  return (
    <Figure
      title="Do the controls read zero?"
      subtitle="Normal Q-Q. Entities known to carry no effect must fall on the diagonal: offset is bias, slope is the wrong spread, curvature at the ends is tail misfit."
      note={
        <>
          The diagonal is not a fit — it is the answer the null <em>claims</em> to give.
          Reading it: the pooled series sits far below the line and rises far too steeply,
          which is bias and inflated spread together. The blocked series lands on the line
          through the body and then <strong>bends away at the top</strong>. That bend is
          real and unexplained: a handful of genes in the nonessential control set behave
          like strong dependencies, so the "known to do nothing" set is not entirely inert.
          A density overlay of the same numbers hides this completely.
        </>
      }
      table={
        <table className="data">
          <thead>
            <tr><th>quantile</th><th>expected</th>{fig.series.map((s) => <th key={s.id}>{s.label}</th>)}</tr>
          </thead>
          <tbody>
            {[0, Math.floor(fig.theoretical.length * 0.25), Math.floor(fig.theoretical.length / 2),
              Math.floor(fig.theoretical.length * 0.75), fig.theoretical.length - 1].map((i) => (
              <tr key={i}>
                <td className="num">{fmt(i / (fig.theoretical.length - 1), 3)}</td>
                <td className="num">{fmt(fig.theoretical[i], 2)}</td>
                {fig.series.map((s) => <td key={s.id} className="num">{fmt(s.sample[i], 2)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="controls">
        <label className="check">
          <input type="checkbox" checked={zoomBody} onChange={(e) => setZoomBody(e.target.checked)} />
          Clip to ±4 (hides the tail, shows the body)
        </label>
        <Legend items={fig.series.map((s) => ({ color: COLORS[s.id], label: s.label }))} />
      </div>

      <div className="plot-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img"
             aria-label="Normal quantile-quantile plot of the calibrated control scores">
          <Grid y={y} x0={PAD.left} x1={W - PAD.right} />
          <AxisY scale={y} x={PAD.left} label="observed quantile (calibrated z)" format={(v) => fmt(v, 0)} />
          <AxisX scale={x} y={H - PAD.bottom} label="quantile a standard normal would give" format={(v) => fmt(v, 0)} />

          {/* The reference is the claim, so it is drawn as an assertion: solid, labelled,
              and underneath the data rather than fitted to it. */}
          <line x1={x(-lim)} y1={y(-lim)} x2={x(lim)} y2={y(lim)}
                stroke="var(--text-muted)" strokeWidth={2} strokeDasharray="6 4" />
          <text x={x(lim) - 6} y={y(lim) + 16} textAnchor="end" fontSize={11}
                fill="var(--text-muted)">a correct null lies here</text>

          {fig.series.map((s) => (
            <g key={s.id}>
              <polyline
                points={s.sample.map((v, i) => `${x(fig.theoretical[i])},${y(v)}`).join(" ")}
                fill="none" stroke={COLORS[s.id]} strokeWidth={2} strokeLinejoin="round"
                opacity={0.55}
              />
              {s.sample.map((v, i) =>
                i % 8 ? null : (
                  <circle key={i} cx={x(fig.theoretical[i])} cy={y(v)} r={3.2}
                          fill={COLORS[s.id]}
                          onMouseEnter={(ev) => setTip({
                            x: ev.clientX + 14, y: ev.clientY - 10,
                            content: (
                              <>
                                <strong>{s.label}</strong>
                                <dl>
                                  <dt>expected</dt><dd className="num">{fmt(fig.theoretical[i], 2)}</dd>
                                  <dt>observed</dt><dd className="num">{fmt(v, 2)}</dd>
                                  <dt>departure</dt>
                                  <dd className="num">{fmt(v - fig.theoretical[i], 2)}</dd>
                                </dl>
                              </>
                            ),
                          })}
                          onMouseLeave={() => setTip(null)} />
                )
              )}
            </g>
          ))}
          {cursor >= 0 && fig.series[0] && (
            <g aria-hidden="true">
              <line
                x1={x(fig.theoretical[cursor])} x2={x(fig.theoretical[cursor])}
                y1={PAD.top} y2={H - PAD.bottom}
                stroke="var(--r-brand)" strokeWidth={1.5} opacity={0.65}
              />
              {fig.series.map((s2) => (
                <circle key={s2.id} cx={x(fig.theoretical[cursor])} cy={y(s2.sample[cursor])}
                        r={5} fill={COLORS[s2.id]} stroke="var(--surface-1)" strokeWidth={2} />
              ))}
            </g>
          )}
        </svg>
        {node}
      </div>

      <Sonifier
        label="Hear whether the null is in tune"
        onEnd={() => setCursor(-1)}
        play={() =>
          playQQ(fig.theoretical, fig.series.find((s2) => s2.id === "blocked")!.sample, {
            seconds: 7,
            onProgress: setCursor,
          })
        }
        legend={
          <>
            Two voices sweep the quantiles together: one at the pitch a <strong>correct
            null</strong> would give, one at the pitch actually <strong>observed</strong>.
            Perfect calibration is a <strong>unison</strong> — one note. A departure opens
            an interval, and you hear the beating in the tails long before the dots
            visibly leave the line.
          </>
        }
      />

      {dens && (
        <p className="aside num">
          {dens.panels.map((p) => `${p.label}: mean ${p.mean > 0 ? "+" : ""}${p.mean}, sd ${p.sd}`).join("   ·   ")}
        </p>
      )}
    </Figure>
  );
}
