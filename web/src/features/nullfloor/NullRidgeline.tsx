/** The null's SHAPE at each observation count — a ridgeline (joyplot).
 *
 *  WHY THIS FORM. Everything else in this repository reports the null as a mean and a
 *  spread. Two moments describe a normal distribution, and nothing ever promised this one
 *  was normal — a top-k operator produces a *skewed* null by construction, because it
 *  selects the upper end of whatever it is given. Skew and tail weight are the properties
 *  that decide where a calibrated cutoff lands, and a mean±sd band shows neither.
 *
 *  A ridgeline is the form for "many distributions, one ordered axis": each ridge is one
 *  observation count, and the reader compares shapes down the stack rather than reading
 *  two numbers per row. The trade is Cleveland–McGill's: overlapping ridges swap a little
 *  positional precision for the ability to see seven distributions at once. That is the
 *  right trade here, because the question is comparative, not a lookup.
 *
 *  READ IT ALOUD: each ridge is the score you would get from pure noise at that number of
 *  cell lines; the ridge slides right as the count grows, and the tail on its right is how
 *  far noise alone can reach.
 */
import { useMemo } from "react";
import { EChart } from "../../components/organisms/EChart";
import { figures } from "../../lib/data/figures";
import { sequential, chartInk, type Mode } from "../../lib/palette";
import { Figure } from "../../components/chart";
import { fmt, fmtInt } from "../../lib/scale";

type Ridge = {
  n: number; lo: number; hi: number; mean: number; p99: number;
  density: { x: number; density: number }[];
};

const OVERLAP = 2.6; // ridge height in row units. >1 overlaps, which is the point.

export default function NullRidgeline({ runId }: { runId: string }) {
  const fig = figures[runId]?.null_ridgeline;
  const rows = (fig?.series?.blocked ?? []) as Ridge[];

  const build = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const ramp = sequential(mode);
      const maxD = Math.max(...rows.flatMap((r) => r.density.map((d) => d.density)), 1);

      // Ridges are drawn back to front so a nearer ridge occludes the one behind it —
      // the occlusion is what makes the stack readable as depth.
      const series = rows
        .map((r, i) => {
          const colour = ramp[Math.min(ramp.length - 1, Math.round((i / (rows.length - 1)) * (ramp.length - 1)))];
          const base = rows.length - 1 - i;
          return {
            type: "line" as const,
            name: `${r.n} lines`,
            z: i,
            silent: true,
            showSymbol: false,
            smooth: 0.25,
            lineStyle: { width: 1.5, color: colour },
            areaStyle: { color: colour, opacity: mode === "dark" ? 0.5 : 0.42, origin: "start" },
            data: r.density.map((d) => [d.x, base + (d.density / maxD) * OVERLAP]),
          };
        })
        .reverse();

      // p99 marks: where noise alone still reaches once in a hundred draws.
      const marks = rows.map((r, i) => ({
        type: "scatter" as const,
        z: 100,
        silent: true,
        symbolSize: 6,
        itemStyle: { color: ink.text },
        data: [[r.p99, rows.length - 1 - i]],
      }));

      return {
        animation: false,
        grid: { left: 78, right: 30, top: 16, bottom: 46 },
        xAxis: {
          type: "value",
          name: "score under no effect",
          nameLocation: "middle",
          nameGap: 28,
          nameTextStyle: { color: ink.muted, fontSize: 12 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: rows.map((r) => `${fmtInt(r.n)}`).reverse(),
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { color: ink.muted, fontSize: 11 },
          name: "cell lines",
          nameTextStyle: { color: ink.muted, fontSize: 11, align: "right" },
        },
        series: [...series, ...marks],
      };
    },
    [rows]
  );

  if (!rows.length) return null;
  const first = rows[0];
  const last = rows[rows.length - 1];

  return (
    <Figure
      title="The null is not a mean and a spread — it has a shape"
      subtitle="Each ridge is the distribution of the score under no effect, at that many screened cell lines. The dot marks the 99th percentile: how far pure noise still reaches."
      note={
        <>
          A top-<span className="num">k</span> operator selects the upper end of whatever it
          is given, so its null is <strong>skewed</strong> — the right tail is long and the
          left is short. That is invisible in a mean ± sd band, and it is exactly what
          decides where a calibrated cutoff falls. Between{" "}
          <span className="num">{fmtInt(first.n)}</span> and{" "}
          <span className="num">{fmtInt(last.n)}</span> lines the whole ridge slides right,
          from a 99th percentile of <span className="num">{fmt(first.p99, 3)}</span> to{" "}
          <span className="num">{fmt(last.p99, 3)}</span> — a gene screened in more lines
          must clear a higher bar to mean the same thing.
        </>
      }
      table={
        <table className="data">
          <thead>
            <tr><th>cell lines</th><th>null mean</th><th>p99</th><th>range (0.1–99.9%)</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.n}>
                <td className="num">{fmtInt(r.n)}</td>
                <td className="num">{fmt(r.mean, 4)}</td>
                <td className="num">{fmt(r.p99, 4)}</td>
                <td className="num">{fmt(r.lo, 3)} … {fmt(r.hi, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <EChart
        build={build}
        height={380}
        deps={[rows]}
        ariaLabel="Ridgeline: the distribution of the score under no effect at seven observation counts. Each ridge slides right as the count grows, and every ridge is right-skewed."
      />
    </Figure>
  );
}
