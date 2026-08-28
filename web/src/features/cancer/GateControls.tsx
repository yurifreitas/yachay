import { useCallback } from "react";
import { useHashParam } from "../../lib/useHashParam";
import { binding, type GateInput } from "../../lib/cancerModel";
import g from "./GateControls.module.css";

/** The gates, as controls rather than as decisions already taken.
 *
 *  WHY THIS EXISTS, AND WHY IT CARRIES A WARNING. Every shortlist in this section is the
 *  output of three thresholds. A reader who can only see the answer at one setting cannot
 *  tell a robust finding from one balanced on the cut — and this library's entire argument is
 *  that the cut is where the mistakes live. So the thresholds move, and the shortlist moves
 *  with them, live.
 *
 *  That is also the danger. `manifests/thresholds.yaml` (ADR 0006) exists to record one thing
 *  about every threshold: whether the data had been seen when the number was chosen. A reader
 *  dragging a slider **has seen the data**. Anything they produce is calibrated to it, not
 *  pre-registered — which is a weaker object, and the difference is exactly what the manifest
 *  refuses to let blur. So the moment any control leaves its registered value the panel says
 *  so, in the same place as the result, and stays saying it until reset.
 *
 *  Settings live in the URL, so a re-gated view is a link someone can send — and so the
 *  warning travels with it rather than being lost on the way.
 */

export type Gates = { q: number; d: number; floor: number };

export type Registered = {
  q: number; d: number; dependencyFloor: number; burdenProxyD?: number;
};

export function useGates(reg: Registered): [Gates, (patch: Partial<Gates>) => void, boolean, () => void] {
  const [qs, setQs] = useHashParam("gq", String(reg.q));
  const [ds, setDs] = useHashParam("gd", String(reg.d));
  const [fs, setFs] = useHashParam("gf", String(reg.dependencyFloor));

  const gates: Gates = {
    q: safe(qs, reg.q), d: safe(ds, reg.d), floor: safe(fs, reg.dependencyFloor),
  };
  const dirty = gates.q !== reg.q || gates.d !== reg.d || gates.floor !== reg.dependencyFloor;

  const set = useCallback((patch: Partial<Gates>) => {
    if (patch.q !== undefined) setQs(String(patch.q));
    if (patch.d !== undefined) setDs(String(patch.d));
    if (patch.floor !== undefined) setFs(String(patch.floor));
  }, [setQs, setDs, setFs]);

  const reset = useCallback(() => {
    setQs(String(reg.q)); setDs(String(reg.d)); setFs(String(reg.dependencyFloor));
  }, [reg, setQs, setDs, setFs]);

  return [gates, set, dirty, reset];
}

function safe(raw: string, fallback: number): number {
  const n = Number(raw);
  return Number.isFinite(n) ? n : fallback;
}

const Q_STEPS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.25];

export default function GateControls(
  { gates, set, dirty, reset, reg, kept, total, rows }:
  {
    gates: Gates; set: (p: Partial<Gates>) => void; dirty: boolean; reset: () => void;
    reg: Registered; kept: number; total: number; rows: GateInput[];
  },
) {
  const solo = binding(rows, gates);
  const worst = (["floor", "d", "q"] as const)
    .reduce((a, b) => (solo[b] > solo[a] ? b : a), "floor" as "floor" | "d" | "q");
  const GATE_NAME = { q: "false-discovery rate", d: "minimum effect",
                      floor: "dependency floor" } as const;
  return (
    <section className={g.wrap} aria-label="Shortlist gates">
      <div className={g.head}>
        <div>
          <h3 className={g.title}>The gates, as controls</h3>
          <p className={g.sub}>
            Move a threshold and the shortlist below moves with it. What survives a wide range
            is a finding; what appears and vanishes within one step of the registered value is
            balanced on the cut.
          </p>
        </div>
        <div className={g.countBlock}>
          <span className={g.count}>{kept}</span>
          <span className={g.countLabel}>of {total} candidates kept</span>
        </div>
      </div>

      <div className={g.controls}>
        <Control
          id="gate-q" label="false-discovery rate" hint="Benjamini–Hochberg q, within subgroup"
          value={gates.q} registered={reg.q}
          display={gates.q < 0.01 ? gates.q.toExponential(0) : gates.q.toString()}
          min={0} max={Q_STEPS.length - 1} step={1}
          sliderValue={nearest(Q_STEPS, gates.q)}
          onSlider={(i) => set({ q: Q_STEPS[i] })}
          // The q control is backed by an INDEX into a non-linear list of steps, so without
          // this a screen reader announces "3 of 5" — the position, not the threshold. The
          // number a reader is setting is 0.05, and that is what must be spoken.
          valueText={`q ${gates.q}`}
        />
        <Control
          id="gate-d" label="minimum effect" hint="Cohen's d against the comparison set"
          value={gates.d} registered={reg.d} display={gates.d.toFixed(2)}
          min={0.2} max={1.5} step={0.05}
          sliderValue={gates.d} onSlider={(v) => set({ d: v })}
        />
        <Control
          id="gate-f" label="dependency floor"
          hint="Stage 0 — the gene must actually be depended on, not merely differ"
          value={gates.floor} registered={reg.dependencyFloor}
          display={gates.floor.toFixed(2)}
          min={0} max={1.2} step={0.05}
          sliderValue={gates.floor} onSlider={(v) => set({ floor: v })}
        />
      </div>

      <p className={g.binding}>
        {solo[worst] === 0 ? (
          <>No single gate is excluding anything on its own here — every candidate that fails
          fails on more than one condition at once.</>
        ) : (
          <>
            <strong>{GATE_NAME[worst]}</strong> is where this shortlist is actually decided:{" "}
            <strong>{solo[worst]}</strong> of {total} candidates fail on it and on nothing
            else. The other two exclude {solo.q + solo.d + solo.floor - solo[worst]} between
            them. A gate that excludes nothing exclusively is doing no work, whatever its
            value looks like.
          </>
        )}
      </p>

      {dirty ? (
        <div className={g.warn} role="status">
          <p>
            <strong>This is no longer the registered shortlist.</strong> The values in{" "}
            <code>manifests/thresholds.yaml</code> were fixed with a record of whether the data
            had been seen when they were chosen. You have seen the data. What is below is
            calibrated to it, which is a weaker object than a pre-registered result and must
            not be reported as one.
          </p>
          <button className={g.reset} onClick={reset}>Restore registered gates</button>
        </div>
      ) : (
        <p className={g.ok} role="status">
          At the registered gates — q&nbsp;{reg.q}, d&nbsp;{reg.d}, floor&nbsp;
          {reg.dependencyFloor}, all fixed before this data was seen.
        </p>
      )}
    </section>
  );
}

function Control(
  { id, label, hint, registered, display, min, max, step, sliderValue, onSlider, value,
    valueText }:
  {
    id: string; label: string; hint: string; value: number; registered: number;
    display: string; min: number; max: number; step: number;
    sliderValue: number; onSlider: (v: number) => void; valueText?: string;
  },
) {
  const moved = value !== registered;
  return (
    <div className={g.control}>
      <label htmlFor={id} className={g.label}>
        {label}
        <span className={moved ? g.valueMoved : g.value}>{display}</span>
      </label>
      <input
        id={id} type="range" className={g.range}
        min={min} max={max} step={step} value={sliderValue}
        onChange={(e) => onSlider(Number(e.target.value))}
        aria-describedby={`${id}-hint`}
        aria-valuetext={valueText ?? display}
      />
      <p id={`${id}-hint`} className={g.hint}>
        {hint}
        {moved && <span className={g.moved}> · registered: {registered}</span>}
      </p>
    </div>
  );
}

function nearest(steps: number[], v: number): number {
  let best = 0;
  for (let i = 1; i < steps.length; i++) {
    if (Math.abs(steps[i] - v) < Math.abs(steps[best] - v)) best = i;
  }
  return best;
}
