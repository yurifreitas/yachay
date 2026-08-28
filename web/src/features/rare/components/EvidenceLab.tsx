/** An instrument, not a report: what a case series of n patients can and cannot support.
 *
 *  WHY THIS IS THE CENTRE OF THE ATLAS. Ultra-rare disease literature is written in
 *  percentages drawn from single-digit series — "seizures in 75% of patients" is three of
 *  four — and those percentages are then used to plan registries, endpoints and n-of-1
 *  protocols. The number is not wrong. It is *unqualified*, and at n = 4 its 95% interval
 *  spans most of the possible answers.
 *
 *  The researcher sets the two numbers that actually exist in the paper (k of n) and reads
 *  off three things the paper does not print: the interval, what claims survive it, and
 *  how many more patients would be needed to reach a given precision.
 */
import { useMemo, useState } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { chartInk, categorical, type Mode } from "../../../lib/palette";
import {
  LANDMARKS, inferences, intervalWidth, nForUpperBound, ruleOfThree, wilson,
} from "../evidence";
import { Sonifier } from "../../../components/molecules/Sonifier";
import { playUncertainty } from "../../../lib/sonify";
import css from "./EvidenceLab.module.css";

const pct = (v: number) => `${Math.round(v * 100)}%`;

export function EvidenceLab() {
  const [n, setN] = useState(4);
  const [k, setK] = useState(3);
  const kk = Math.min(k, n);

  const [lo, hi] = wilson(kk, n);
  const claims = useMemo(() => inferences(kk, n), [kk, n]);
  const r3 = ruleOfThree(n);

  // How the interval narrows with n, at the same observed proportion. The shape is the
  // point: evidence at these sample sizes accumulates far more slowly than intuition.
  const build = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const [c1, , , , cRed] = categorical(mode);
      const p = n ? kk / n : 0;
      const pts: [number, number][] = [];
      for (let m = 1; m <= 120; m++) pts.push([m, intervalWidth(Math.round(p * m), m) * 100]);
      return {
        animation: false,
        grid: { left: 54, right: 96, top: 20, bottom: 42 },
        tooltip: {
          trigger: "axis",
          valueFormatter: (v: number) => `${Math.round(v)} points wide`,
        },
        xAxis: {
          type: "log",
          name: "patients reported",
          nameLocation: "middle",
          nameGap: 26,
          nameTextStyle: { color: ink.muted, fontSize: 12 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "value",
          max: 100,
          name: "width of the 95% interval",
          nameLocation: "middle",
          nameGap: 38,
          nameTextStyle: { color: ink.muted, fontSize: 12 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11, formatter: "{value}" },
        },
        series: [
          {
            type: "line",
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 2.5, color: c1 },
            areaStyle: { color: c1, opacity: 0.12 },
            data: pts,
            markLine: {
              silent: true,
              symbol: "none",
              label: {
                formatter: "cannot separate majority from minority",
                color: ink.muted,
                fontSize: 11,
                position: "insideEndTop",
              },
              lineStyle: { color: cRed, type: "dashed", width: 1.5 },
              data: [{ yAxis: 50 }],
            },
          },
          {
            type: "scatter",
            symbolSize: 11,
            itemStyle: { color: cRed, borderColor: ink.surface, borderWidth: 2 },
            z: 10,
            data: [[n, intervalWidth(kk, n) * 100]],
            label: {
              show: true,
              formatter: `n=${n}`,
              position: "right",
              color: ink.text,
              fontSize: 12,
            },
          },
        ],
      };
    },
    [n, kk]
  );

  return (
    <div className={css.lab}>
      <div className={css.controls}>
        <label className={css.field}>
          <span className={css.label}>Patients reported</span>
          <input
            className={css.range}
            type="range" min={1} max={60} value={n}
            onChange={(e) => setN(Number(e.target.value))}
            aria-describedby="n-help"
          />
          <output className={css.value}>{n}</output>
        </label>
        <label className={css.field}>
          <span className={css.label}>With the feature</span>
          <input
            className={css.range}
            type="range" min={0} max={n} value={kk}
            onChange={(e) => setK(Number(e.target.value))}
          />
          <output className={css.value}>{kk}</output>
        </label>
        <div className={css.landmarks} id="n-help">
          {LANDMARKS.map((l) => (
            <button
              key={l.n} type="button"
              className={n === l.n ? css.lmOn : css.lm}
              onClick={() => setN(l.n)}
              title={l.note}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div className={css.readout}>
        <div className={css.headline}>
          <span className={css.reported}>{n ? Math.round((kk / n) * 100) : 0}%</span>
          <span className={css.reportedNote}>is what the paper prints</span>
        </div>
        <div className={css.intervalRow}>
          <span className={css.intervalLabel}>what it actually supports</span>
          <div className={css.bar}>
            <span
              className={css.barSpan}
              style={{ left: `${lo * 100}%`, width: `${Math.max((hi - lo) * 100, 1.5)}%` }}
            />
            <span className={css.barTick} style={{ left: `${(kk / Math.max(n, 1)) * 100}%` }} />
            <span className={css.barMid} />
          </div>
          <span className={css.intervalValue}>
            {pct(lo)} – {pct(hi)}
          </span>
        </div>
        <p className={css.width}>
          <strong>{Math.round((hi - lo) * 100)} points wide.</strong>{" "}
          {hi - lo > 0.5
            ? "Wider than half the scale — this cannot distinguish a majority from a minority."
            : hi - lo > 0.3
            ? "The direction is suggestive; the magnitude is not."
            : "Narrow enough to plan against."}
        </p>
      </div>

      <div className={css.sonify}>
        <Sonifier
          label="Hear how much is known"
          play={() => playUncertainty(n ? kk / n : 0, lo, hi, { seconds: 2.4 })}
          legend={
            <>
              The <strong>pitch</strong> is the estimate; the <strong>noise around it</strong>
              is the interval. A narrow interval is a clean tone; a wide one is a band of
              hiss you can locate but not pin down. Move the sliders and play it again —
              uncertainty sounds uncertain, which is the whole mapping.
            </>
          }
        />
      </div>

      <ul className={css.claims}>
        {claims.map((c) => (
          <li key={c.claim} className={css[c.verdict]}>
            <span className={css.verdict}>
              {c.verdict === "supported" ? "supported" :
               c.verdict === "underpowered" ? "underpowered" : "uninformative"}
            </span>
            <span className={css.claim}>{c.claim}</span>
            <span className={css.detail}>{c.detail}</span>
          </li>
        ))}
      </ul>

      <div className={css.chart}>
        <p className={css.chartTitle}>
          Evidence accumulates far more slowly than the sample sizes available
        </p>
        <p className={css.chartSub}>
          Width of the 95% interval at the same observed proportion, as patients accumulate.
          The dot is where this series sits.
        </p>
        <EChart
          build={build}
          height={260}
          deps={[n, kk]}
          ariaLabel={`The 95% interval is ${Math.round((hi - lo) * 100)} points wide at ${n} patients and narrows slowly; it crosses 50 points near n=${nForUpperBound(0.1)}.`}
        />
        <p className={css.footnote}>
          With <strong>none</strong> of a complication observed in {n} patients, the rule of
          three still allows a true rate up to <strong>{pct(r3)}</strong> — "not observed" is
          not "does not happen". Bounding it below 10% needs{" "}
          <strong>{nForUpperBound(0.1)}</strong> patients; below 1%,{" "}
          <strong>{nForUpperBound(0.01)}</strong>. For a disease with a dozen patients alive,
          those are not sample sizes — they are the reason ultra-rare evidence has to be
          built differently.
        </p>
      </div>
    </div>
  );
}
