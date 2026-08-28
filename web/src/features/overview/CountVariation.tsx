/** Does the observation count vary at all? — the gate every other view depends on.
 *
 * WHY THIS IS FIRST. The correction reorders a ranking only when counts differ. If they
 * do not, calibration is one common monotone transform, and a monotone transform cannot
 * reorder anything. So this is not context, it is the precondition: read it and you know
 * whether the rest of the dashboard can say anything about ranking.
 *
 * FORM: a bar chart of share-by-count, plus a single derived number — the spread ratio.
 * Bars because the comparison is magnitude along a common scale, which is the most
 * accurately decoded encoding available (Cleveland & McGill 1984); a pie or a treemap
 * would spend the same data on area, which is decoded far worse and cannot show the
 * log-spaced x that this variable actually lives on.
 *
 * INTERDISCIPLINARY NOTE. Ecology asks this question first too, and answers it
 * differently: a rarefaction curve (Hurlbert 1971) subsamples every unit down to a
 * COMMON count rather than standardising against the count. Equalise-n and
 * standardise-against-n are the two available strategies, and which is right depends on
 * exactly the distribution this chart shows. When 95% of entities share one count,
 * rarefaction is nearly free and calibration is nearly pointless.
 */
import { useMemo } from "react";
import { figures } from "../../lib/data/figures";
import { linear, log, fmt, fmtInt, pct } from "../../lib/scale";
import { AxisX, AxisY, Figure, Grid, PAD, useTooltip } from "../../components/chart";

const W = 880;
const H = 300;

export default function CountVariation({ runId }: { runId: string }) {
  const fig = figures[runId]?.count_distribution;
  const { setTip, node } = useTooltip();

  const geom = useMemo(() => {
    if (!fig) return null;
    const ns = fig.bars.map((b) => b.n);
    const lo = Math.min(...ns);
    const hi = Math.max(...ns);
    return {
      x: log([lo / 1.08, hi * 1.08], [PAD.left, W - PAD.right]),
      y: linear([0, 1], [H - PAD.bottom, PAD.top]),
      lo, hi,
    };
  }, [fig]);

  if (!fig || !geom) return null;
  const { x, y, lo, hi } = geom;
  const spread = hi / lo;
  const tail = fig.total - Math.round(fig.modal_share * fig.total);

  return (
    <Figure
      title="How much does the observation count actually vary?"
      subtitle="Read this before anything else on the page: it decides whether calibration can change a ranking at all."
      note={
        <>
          Counts here span <span className="num">{fmt(spread, 1)}x</span> and{" "}
          <strong>{pct(fig.modal_share)} of entities share a single count</strong>, so the
          whole count effect rests on {fmtInt(tail)} of {fmtInt(fig.total)}. Calibration is
          therefore very nearly one common monotone transform on this screen — and a
          monotone transform cannot reorder anything.
          <br />
          <br />
          That is not a defect in the data; it is a fact about what this dataset can test.
          It is a strong test of whether the <em>null</em> is right and a weak test of the
          <em> ranking</em> claim. A screen whose counts run 1 to 4,494 is the opposite.
        </>
      }
      table={
        <table className="data">
          <thead><tr><th>observations</th><th>entities</th><th>share</th></tr></thead>
          <tbody>
            {fig.bars.map((b) => (
              <tr key={b.n}>
                <td className="num">{fmtInt(b.n)}</td>
                <td className="num">{fmtInt(b.genes)}</td>
                <td className="num">{pct(b.share, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="tiles tiles-tight">
        <article className="tile card">
          <h3>Distinct counts</h3>
          <p className="value num">{fig.distinct}</p>
        </article>
        <article className="tile card">
          <h3>Spread (max / min)</h3>
          <p className="value num">{fmt(spread, 1)}x</p>
        </article>
        <article className="tile card">
          <h3>Share on one count</h3>
          <p className="value num">{pct(fig.modal_share)}</p>
        </article>
        <article className="tile card">
          <h3>Entities carrying the variation</h3>
          <p className="value num">{fmtInt(tail)}</p>
        </article>
      </div>

      <div className="plot-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img"
             aria-label="Share of entities at each observation count">
          <Grid y={y} x0={PAD.left} x1={W - PAD.right} />
          <AxisY scale={y} x={PAD.left} label="share of entities" format={(v) => pct(v, 0)} />
          <AxisX scale={x} y={H - PAD.bottom} label="observations behind the score (log)"
                 format={(v) => fmtInt(v)} />
          {fig.bars.map((b) => {
            // The modal bar is the finding, so it gets the one attention-carrying colour
            // and the direct label. Everything else stays recessive.
            const dominant = b.share > 0.5;
            const w = dominant ? 11 : 5;
            const top = y(b.share);
            return (
              <rect
                key={b.n}
                x={x(b.n) - w / 2}
                y={top}
                width={w}
                height={Math.max(H - PAD.bottom - top, 1.5)}
                rx={2}
                fill={dominant ? "var(--series-2)" : "var(--series-1)"}
                onMouseEnter={(ev) => setTip({
                  x: ev.clientX + 14, y: ev.clientY - 10,
                  content: (
                    <>
                      <strong>{fmtInt(b.genes)} entities</strong>
                      <dl>
                        <dt>observations each</dt><dd className="num">{fmtInt(b.n)}</dd>
                        <dt>share</dt><dd className="num">{pct(b.share, 2)}</dd>
                      </dl>
                    </>
                  ),
                })}
                onMouseLeave={() => setTip(null)}
              />
            );
          })}
          <text x={x(fig.modal_n) - 12} y={y(fig.modal_share) - 10} textAnchor="end"
                fontSize={12} fill="var(--text-primary)">
            {pct(fig.modal_share)} share one count
          </text>
        </svg>
        {node}
      </div>
    </Figure>
  );
}
