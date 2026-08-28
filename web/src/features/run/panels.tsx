/** The three panels that were local to RunView.
 *
 *  Moved out unchanged so the dashboard can place each one behind its own nav entry.
 *  They were local functions inside the page component, which was fine while the page was
 *  a single scroll and wrong the moment the panels became switchable sections.
 */
import { useMemo, useState } from "react";
import type { Run } from "../../lib/dataTypes";
import { rankBy } from "../../lib/dataTypes";
import { linear, log, fmt, fmtInt } from "../../lib/scale";
import { AxisX, AxisY, Figure, Grid, Legend, PAD, useTooltip } from "../../components/chart";
import CanvasScatter, { decodePoints } from "../../components/canvas-scatter";
import { pointsFor } from "../../lib/data/points";

/* The chart viewport. Lived at the top of RunView and came along with the panels that use it. */
const W = 880;
const H = 420;

/** Turn manifest keys into readable labels without hardcoding any adapter's vocabulary. */
const label = (k: string) => k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export function Headline({ run }: { run: Run }) {
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

export function NoiseFloor({ run }: { run: Run }) {
  const { setTip, node } = useTooltip();
  const [onlyClearing, setOnlyClearing] = useState(false);

  // The dense layer decodes three Float32Arrays once. Filtering is a predicate handed to
  // the painter, not a new array — re-slicing 17,916 rows on every checkbox click is the
  // kind of thing that makes an explorer feel slow for no reason.
  const cloud = useMemo(() => {
    const raw = pointsFor(run.id);
    return raw ? decodePoints(raw) : null;
  }, [run.id]);

  if (!run.null.length) return null;

  // The x domain comes from the OBSERVED counts, not from 1. DepMap screens almost every
  // gene in every line, so a [1, max] axis crushes 18,000 points into two columns at the
  // right edge and shows nothing. Fitting the axis to the data is also what makes the
  // amount of count variation legible — which is itself a finding worth reading off.
  // Domains come from the cloud, which is the whole distribution. Deriving them from the
  // trimmed `run.entities` would fit the axes to the extremes only and quietly clip
  // everything the sampled middle contains.
  const src = cloud ?? {
    n: Float32Array.from(run.entities.map((e) => e.n)),
    score: Float32Array.from(run.entities.map((e) => e.score)),
  };
  let nMin = Infinity, nMax = -Infinity, sMin = Infinity, sMax = -Infinity;
  for (let i = 0; i < src.n.length; i++) {
    if (src.n[i] < nMin) nMin = src.n[i];
    if (src.n[i] > nMax) nMax = src.n[i];
    if (src.score[i] < sMin) sMin = src.score[i];
    if (src.score[i] > sMax) sMax = src.score[i];
  }
  nMin = Math.max(1, nMin);
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
          {cloud && cloud.shown < cloud.total && (
            <>
              {" "}<strong>Plotted: {fmtInt(cloud.shown)} of {fmtInt(cloud.total)}</strong>{" "}
              — every entity in the top and bottom {fmtInt(1500)} by calibrated score, plus
              every {Math.round(1 / cloud.sampleRate)}
              <sup>nd</sup> entity of the middle. The bulk is <em>sampled</em>, not dropped,
              so the density you see is the real one at a known rate.
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
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img"
             aria-label="Observed scores against the metric's noise floor, by observation count">
          <Grid y={y} x0={PAD.left} x1={W - PAD.right} />
          <AxisY scale={y} x={PAD.left} label={run.statistic} format={(v) => fmt(v, 2)} />
          <AxisX scale={x} y={H - PAD.bottom} label="observations behind the score (log)"
                 format={(v) => fmtInt(v)} />
          <polygon points={band} fill="var(--series-1)" opacity={0.14} />
          <path d={path("p99")} fill="none" stroke="var(--series-1)" strokeWidth={1}
                strokeDasharray="4 3" opacity={0.8} />
          <path d={path("null_mean")} fill="none" stroke="var(--series-1)" strokeWidth={2} />

        </svg>

        {cloud && (
          <CanvasScatter
            pts={cloud}
            x={x}
            y={y}
            yOf={(p, i) => p.score[i]}
            width={W}
            height={H}
            colors={["var(--series-3)", "var(--series-1)", "var(--series-2)"]}
            filter={onlyClearing ? (p, i) => p.z[i] > 2.326 : undefined}
            onHover={(i, ev) => {
              if (i === null || !ev) return setTip(null);
              setTip({
                x: ev.clientX + 14,
                y: ev.clientY - 10,
                content: (
                  <>
                    <strong>{cloud.names[i]}</strong>
                    <dl>
                      <dt>observations</dt><dd className="num">{fmtInt(cloud.n[i])}</dd>
                      <dt>raw score</dt><dd className="num">{fmt(cloud.score[i], 4)}</dd>
                      <dt>calibrated z</dt><dd className="num">{fmt(cloud.z[i], 2)}</dd>
                    </dl>
                    <p className="verdict">
                      {cloud.z[i] > 2.326 ? "clears the noise p99" : "within the noise floor"}
                    </p>
                  </>
                ),
              });
            }}
          />
        )}
        {node}
      </div>
    </Figure>
  );
}

/** What calibration actually changed — the entities that moved the most, either way. */
export function Movers({ run }: { run: Run }) {
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
        // Prefer the ranks the analysis computed over the full table. Falling back to
        // ranks derived here is only correct when nothing was trimmed.
        raw: (e.rank_raw as number) ?? byScore.get(e.entity)!,
        cal: (e.rank_cal as number) ?? byZ.get(e.entity)!,
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
      note={<>Entities are ordered by the size of the move, not by rank, so both directions are visible. Ranks are the ones the analysis computed over <strong>all</strong> entities, not over the rows shipped to this page.</>}
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
