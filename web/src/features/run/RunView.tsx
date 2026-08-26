/** One adapter run: the headline numbers, the noise floor, and what calibration moved.
 *
 * Deliberately generic. It knows a run has entities with (score, n, z) and a fitted
 * null — nothing about genes, prompts, or cell lines — so a new adapter renders here
 * with no UI change.
 */
import { useMemo, useState } from "react";
import type { Run } from "../../lib/data";
import { rankBy } from "../../lib/data";
import { linear, log, fmt, fmtInt } from "../../lib/scale";
import { AxisX, AxisY, Figure, Grid, Legend, PAD, useTooltip } from "../../components/chart";

const W = 880;
const H = 420;

export default function RunView({ run }: { run: Run }) {
  return (
    <section className="stack">
      <header className="lede">
        <h2>{run.title}</h2>
        <p>{run.subtitle}</p>
      </header>
      <Headline run={run} />
      <NoiseFloor run={run} />
      <Movers run={run} />
    </section>
  );
}

/** Turn manifest keys into readable labels without hardcoding any adapter's vocabulary. */
const label = (k: string) => k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function Headline({ run }: { run: Run }) {
  const entries = Object.entries(run.headline);
  return (
    <div className="tiles">
      {entries.map(([k, v]) => (
        <article key={k} className="tile card">
          <h3>{label(k)}</h3>
          <p className="value num">
            {typeof v === "number" ? (Number.isInteger(v) ? fmtInt(v) : fmt(v, 3)) : v}
          </p>
        </article>
      ))}
    </div>
  );
}

function NoiseFloor({ run }: { run: Run }) {
  const { setTip, node } = useTooltip();
  const [onlyClearing, setOnlyClearing] = useState(false);

  const pts = useMemo(() => {
    const rows = run.entities.filter((e) => Number.isFinite(e.score) && e.n >= 1);
    return onlyClearing ? rows.filter((e) => (e.z as number) > 2.326) : rows;
  }, [run, onlyClearing]);

  if (!run.null.length) return null;

  // The x domain comes from the OBSERVED counts, not from 1. DepMap screens almost every
  // gene in every line, so a [1, max] axis crushes 18,000 points into two columns at the
  // right edge and shows nothing. Fitting the axis to the data is also what makes the
  // amount of count variation legible — which is itself a finding worth reading off.
  const nMin = Math.max(1, Math.min(...run.entities.map((e) => e.n)));
  const nMax = Math.max(...run.entities.map((e) => e.n));
  const sMin = Math.min(...run.entities.map((e) => e.score));
  const sMax = Math.max(...run.entities.map((e) => e.score));
  const pad = (sMax - sMin) * 0.08;
  const spread = nMax / nMin;

  const x = log([nMin / 1.15, nMax * 1.15], [PAD.left, W - PAD.right]);
  const y = linear([sMin - pad, sMax + pad], [H - PAD.bottom, PAD.top]);

  const path = (key: "null_mean" | "p99") =>
    run.null
      .filter((d) => d[key] !== undefined)
      .map((d, i) => `${i ? "L" : "M"}${x(d.n)},${y(d[key] as number)}`)
      .join(" ");

  const band = [
    ...run.null.map((d) => `${x(d.n)},${y((d.p99 ?? d.null_mean) as number)}`),
    ...[...run.null].reverse().map((d) => `${x(d.n)},${y(d.null_mean)}`),
  ].join(" ");

  return (
    <Figure
      title="What the score reads when nothing is happening"
      subtitle={`Statistic: ${run.statistic} (reduce=${run.reduce}). The band is pure noise, measured by resampling real control observations — no effect present.`}
      note={
        <>
          Every point inside the band is indistinguishable from noise at that observation
          count. Ranking on the raw score ranks partly on how much each entity was
          measured; the calibrated <span className="num">z</span> is what is comparable.
          {run.entities.length < run.entitiesTotal && (
            <>
              {" "}<strong>Plotted: {fmtInt(run.entities.length)} of{" "}
              {fmtInt(run.entitiesTotal)} entities</strong> — the highest and lowest by
              calibrated score. The middle is omitted for rendering, not because it is
              uninteresting; the full table is in <code>out/</code>.
            </>
          )}
          {spread < 5 && (
            <>
              {" "}Here observation counts span only <span className="num">{fmt(spread, 1)}x</span>
              {" "}({fmtInt(nMin)}–{fmtInt(nMax)}), so the count artifact is small and the
              calibration is doing something else: separating real effects from the floor,
              not undoing a count bias.
            </>
          )}
        </>
      }
      table={
        <table className="data">
          <thead>
            <tr><th>n</th><th>null mean</th><th>null sd</th><th>p99</th></tr>
          </thead>
          <tbody>
            {run.null.map((d) => (
              <tr key={d.n}>
                <td className="num">{fmtInt(d.n)}</td>
                <td className="num">{fmt(d.null_mean, 4)}</td>
                <td className="num">{fmt(d.null_sd, 4)}</td>
                <td className="num">{d.p99 !== undefined ? fmt(d.p99, 4) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="controls">
        <label className="check">
          <input type="checkbox" checked={onlyClearing}
                 onChange={(e) => setOnlyClearing(e.target.checked)} />
          Only entities clearing the noise 99th percentile
        </label>
        <Legend items={[
          { color: "var(--series-1)", label: "null mean (no effect)" },
          { color: "var(--series-2)", label: "clears the noise p99" },
          { color: "transparent", label: "within the noise floor", hollow: true },
        ]} />
      </div>

      <div className="plot-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
             aria-label="Observed scores against the metric's noise floor, by observation count">
          <Grid y={y} x0={PAD.left} x1={W - PAD.right} />
          <AxisY scale={y} x={PAD.left} label={run.statistic} format={(v) => fmt(v, 2)} />
          <AxisX scale={x} y={H - PAD.bottom} label="observations behind the score (log)"
                 format={(v) => fmtInt(v)} />
          <polygon points={band} fill="var(--series-1)" opacity={0.14} />
          <path d={path("p99")} fill="none" stroke="var(--series-1)" strokeWidth={1}
                strokeDasharray="4 3" opacity={0.8} />
          <path d={path("null_mean")} fill="none" stroke="var(--series-1)" strokeWidth={2} />

          {pts.map((e) => {
            const clears = (e.z as number) > 2.326;
            return (
              <circle
                key={e.entity}
                cx={x(e.n)} cy={y(e.score)} r={3.6}
                fill={clears ? "var(--series-2)" : "var(--surface-1)"}
                stroke="var(--series-2)" strokeWidth={1.6}
                opacity={clears ? 0.9 : 0.35}
                onMouseEnter={(ev) => setTip({
                  x: ev.clientX + 14, y: ev.clientY - 10,
                  content: (
                    <>
                      <strong>{e.entity}</strong>
                      <dl>
                        <dt>observations</dt><dd className="num">{fmtInt(e.n)}</dd>
                        <dt>raw score</dt><dd className="num">{fmt(e.score, 4)}</dd>
                        <dt>calibrated z</dt><dd className="num">{fmt(e.z as number, 2)}</dd>
                      </dl>
                      <p className="verdict">
                        {clears ? "clears the noise p99" : "within the noise floor"}
                      </p>
                    </>
                  ),
                })}
                onMouseLeave={() => setTip(null)}
              />
            );
          })}
        </svg>
        {node}
      </div>
    </Figure>
  );
}

/** What calibration actually changed — the entities that moved the most, either way. */
function Movers({ run }: { run: Run }) {
  const [n, setN] = useState(15);
  const rows = useMemo(() => {
    const byScore = rankBy(run.entities, "score");
    const byZ = rankBy(run.entities, "z");
    return run.entities
      .map((e) => ({
        entity: e.entity,
        n: e.n,
        score: e.score,
        z: e.z as number,
        raw: byScore.get(e.entity)!,
        cal: byZ.get(e.entity)!,
      }))
      .map((r) => ({ ...r, move: r.raw - r.cal }))
      .sort((a, b) => Math.abs(b.move) - Math.abs(a.move))
      .slice(0, n);
  }, [run, n]);

  const maxMove = Math.max(...rows.map((r) => Math.abs(r.move)), 1);

  return (
    <Figure
      title="What calibration moved"
      subtitle="Rank by raw score versus rank by calibrated z. A large promotion means the entity was well measured and under-credited; a large demotion means its raw score was mostly noise."
      note="Entities are ordered by the size of the move, not by rank, so both directions are visible."
    >
      <div className="controls">
        <label className="check">
          Show
          <select value={n} onChange={(e) => setN(Number(e.target.value))}>
            {[10, 15, 25, 40].map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
          biggest moves of {fmtInt(run.entitiesTotal)}
        </label>
        <Legend items={[
          { color: "var(--series-3)", label: "promoted by calibration" },
          { color: "var(--series-2)", label: "demoted by calibration" },
        ]} />
      </div>
      <div className="scroll-x">
        <table className="data movers">
          <thead>
            <tr>
              <th>entity</th><th>obs</th><th>raw</th><th>raw rank</th>
              <th>z</th><th>cal rank</th><th style={{ width: "34%" }}>move</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const up = r.move > 0;
              const w = (Math.abs(r.move) / maxMove) * 100;
              return (
                <tr key={r.entity}>
                  <td>{r.entity}</td>
                  <td className="num">{fmtInt(r.n)}</td>
                  <td className="num">{fmt(r.score, 3)}</td>
                  <td className="num">#{r.raw}</td>
                  <td className="num">{fmt(r.z, 1)}</td>
                  <td className="num">#{r.cal}</td>
                  <td>
                    <div className="bar-cell">
                      <span
                        className="bar"
                        style={{
                          width: `${w}%`,
                          background: up ? "var(--series-3)" : "var(--series-2)",
                        }}
                      />
                      <span className="bar-label num">{up ? "+" : ""}{r.move}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Figure>
  );
}
