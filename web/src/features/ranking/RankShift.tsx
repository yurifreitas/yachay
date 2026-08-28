/** Did the ordering actually change? — the figure that tests the library's only claim.
 *
 * FORM: a slopegraph (Tufte, *The Visual Display of Quantitative Information*, 1983).
 * Two ranked positions and a line between them; the reader decodes the change as SLOPE,
 * which is a length-and-position judgement rather than a colour or area one. For "did
 * this move, and which way" it beats both a grouped bar chart (which forces two separate
 * position comparisons) and a scatter of rank-versus-rank (which shows the joint
 * distribution but buries the direction of individual moves).
 *
 * WHY CLASS MEDIANS AND NOT 17,916 LINES. A slopegraph of every entity is a hairball, and
 * the question is not "where did each gene go" — the table below answers that — but "did
 * the classes we can check move the way the method predicts". The confound should be
 * visible; the controls should sit low. Aggregating to a median is a deliberate loss of
 * detail in exchange for an answerable question (Munzner's abstraction step: pick the
 * task, then the encoding).
 *
 * The axis is INVERTED because rank 1 is the top. Getting this wrong inverts the meaning
 * of every line on the chart, which is the sort of error a chart cannot signal.
 */
import { useMemo } from "react";
import { figures } from "../../lib/data/figures";
import { linear, fmtInt } from "../../lib/scale";
import { Figure, useTooltip } from "../../components/chart";

const W = 880;
const H = 320;
const PADX = 210;

export default function RankShift({ runId }: { runId: string }) {
  const fig = figures[runId]?.rank_shift;
  const { setTip, node } = useTooltip();

  const y = useMemo(
    // Rank 1 at the top: the range is inverted, not the domain, so the tick labels stay
    // in reading order.
    () => (fig ? linear([1, fig.total], [34, H - 34]) : null),
    [fig]
  );

  if (!fig || !y) return null;
  const xa = PADX;
  const xb = W - PADX;
  const COLOR: Record<string, string> = {
    "pan-essential": "var(--series-2)",
    "nonessential control": "var(--series-3)",
  };

  const moved = fig.classes.some((c) => Math.abs(c.raw - c.cal) > fig.total * 0.02);

  return (
    <Figure
      title="What calibration did to the ordering"
      subtitle="Median rank of each checkable class, before and after. The library's only claim is about ordering, so this is the figure that can falsify it."
      note={
        moved ? (
          <>The classes moved, which is what the method predicts when counts vary.</>
        ) : (
          <>
            <strong>Almost nothing moved — and that is the honest result.</strong> On this
            screen the observation counts barely vary, so calibration is nearly a common
            monotone transform and cannot reorder much. Read together with the count
            figure, the two say: the null here was <em>wrong</em> and is now right, and
            fixing it barely changed <em>this</em> ranking. Both are true. A dataset can be
            the right test of a null and the wrong test of a ranking claim.
          </>
        )
      }
      table={
        <table className="data">
          <thead>
            <tr><th>class</th><th>entities</th><th>median raw rank</th><th>median calibrated rank</th><th>move</th></tr>
          </thead>
          <tbody>
            {fig.classes.map((c) => (
              <tr key={c.id}>
                <td>{c.id} <span className="muted">— {c.note}</span></td>
                <td className="num">{fmtInt(c.n)}</td>
                <td className="num">{fmtInt(c.raw)}</td>
                <td className="num">{fmtInt(c.cal)}</td>
                <td className="num">{c.raw - c.cal > 0 ? "+" : ""}{fmtInt(c.raw - c.cal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="plot-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img"
             aria-label="Median rank of each class before and after calibration">
          {[[xa, "ranked on the raw score"], [xb, "ranked on the calibrated z"]].map(([px, lab]) => (
            <g key={lab as string}>
              <line x1={px as number} x2={px as number} y1={30} y2={H - 30}
                    stroke="var(--gridline)" strokeWidth={2} />
              <text x={px as number} y={18} textAnchor="middle" fontSize={11.5}
                    fill="var(--text-secondary)">{lab as string}</text>
            </g>
          ))}

          {fig.classes.map((c) => {
            const col = COLOR[c.id] ?? "var(--series-1)";
            return (
              <g key={c.id}
                 onMouseEnter={(ev) => setTip({
                   x: ev.clientX + 14, y: ev.clientY - 10,
                   content: (
                     <>
                       <strong>{c.id}</strong>
                       <dl>
                         <dt>entities</dt><dd className="num">{fmtInt(c.n)}</dd>
                         <dt>median raw rank</dt><dd className="num">{fmtInt(c.raw)}</dd>
                         <dt>median calibrated</dt><dd className="num">{fmtInt(c.cal)}</dd>
                       </dl>
                       <p className="verdict">{c.note}</p>
                     </>
                   ),
                 })}
                 onMouseLeave={() => setTip(null)}>
                <line x1={xa} y1={y(c.raw)} x2={xb} y2={y(c.cal)} stroke={col} strokeWidth={2.5} />
                <circle cx={xa} cy={y(c.raw)} r={5} fill={col}
                        stroke="var(--surface-1)" strokeWidth={2} />
                <circle cx={xb} cy={y(c.cal)} r={5} fill={col}
                        stroke="var(--surface-1)" strokeWidth={2} />
                {/* Direct labels on both ends: a legend would force a colour lookup for a
                    chart with only two series, and identity should never be colour alone. */}
                <text x={xa - 12} y={y(c.raw)} textAnchor="end" dominantBaseline="middle"
                      fontSize={11.5} fill="var(--text-primary)">
                  {c.id} · #{fmtInt(c.raw)}
                </text>
                <text x={xb + 12} y={y(c.cal)} dominantBaseline="middle"
                      fontSize={11.5} fill="var(--text-primary)" className="num">
                  #{fmtInt(c.cal)}
                </text>
              </g>
            );
          })}

          <text x={W / 2} y={H - 8} textAnchor="middle" fontSize={11}
                fill="var(--text-muted)">
            of {fmtInt(fig.total)} entities · rank 1 is the top
          </text>
        </svg>
        {node}
      </div>
    </Figure>
  );
}
