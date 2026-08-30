import { useState } from "react";
import { useT } from "../../i18n";
import { CRISPR } from "../../i18n/crispr";
import { useViewModels } from "../rare/components/HyperViews";
import css from "./CrisprViews.module.css";
import own from "./ScreenEvent.module.css";

/** THE THREE POPULATIONS OF A SCREEN, AND THE THRESHOLD MEANT TO SEPARATE THEM.
 *
 *  This replaced a figure that did not work, and the failure is drawn here rather than
 *  deleted. The obvious picture for a library whose thesis is "the threshold bends with n"
 *  is every gene over an (n, score) plane with the fitted null across it. Built, it came out
 *  as twenty hex cells: 95.4 % of this screen was scored on exactly the same number of cell
 *  lines, so there is no second dimension to plot. The surface `CalibrationField` draws is
 *  real and its rule is right — but it is fitted across a range where almost no gene in this
 *  screen sits, and that had never been said.
 *
 *  What the data does support is a comparison of distributions, so that is what this is: a
 *  ridgeline, ordered by median rather than alphabetically, with the null's own mean, 95th
 *  and 99th percentile ruled across all three. The nonessential controls are drawn as
 *  individual marks — 726 of them, below the smearing point — because where the controls sit
 *  IS the calibration, and a smoothed curve would hide the seven that clear p99.
 *
 *  Positions solved in `tools/view_models.py` (ADR 0008). This file draws.
 */
export function ScreenEvent() {
  const tt = useT();
  const models = useViewModels();
  const m = models?.screen_event;
  const [rule, setRule] = useState<string | null>("null p99");

  if (!models) return <div className={css.skeleton} style={{ height: 420 }} aria-hidden />;
  if (!m) return null;

  const bins = m.curves[0]?.density.length ?? 1;
  /** A closed polygon per group: baseline, the density, baseline again. Drawn as an area
   *  rather than a line because three overlapping outlines are three outlines, and the
   *  comparison is of masses. */
  const area = (density: number[]) =>
    ["0,100",
     ...density.map((v: number, i: number) =>
       `${((i / (bins - 1)) * 100).toFixed(3)},${(100 - v * 100).toFixed(3)}`),
     "100,100"].join(" ");

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(CRISPR.eventTitle)}</strong> {m.reading}
      </figcaption>

      {/* The failure that produced this figure, stated above it rather than in a footnote. */}
      <p className={own.degenerate}>{m.degenerate_axis?.reading}</p>

      <div className={own.rules} role="group" aria-label={tt(CRISPR.eventRules)}>
        {m.rules.map((r: any) => (
          <button key={r.label} type="button"
                  className={rule === r.label ? own.ruleOn : own.rule}
                  aria-pressed={rule === r.label}
                  onClick={() => setRule(rule === r.label ? null : r.label)}>
            {r.label} <span className={own.ruleV}>{r.raw}</span>
          </button>
        ))}
      </div>

      <div className={own.stack}>
        {m.curves.map((c: any) => (
          <div key={c.group} className={own.lane}>
            <div className={own.laneHead}>
              <span className={own.laneName}>{c.group}</span>
              <span className={own.laneN}>{c.members.toLocaleString("en-US")} genes</span>
              <span className={own.laneNote}>{c.note}</span>
            </div>

            <div className={own.plot}>
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className={own.svg}
                   role="img" aria-label={`${c.group}: ${c.members} genes, median ${c.median}`}>
                <polygon points={area(c.density)} className={own.area} />
                {/* The median, on the curve it belongs to. */}
                <line x1={c.median_at * 100} y1="0" x2={c.median_at * 100} y2="100"
                      className={own.median} vectorEffect="non-scaling-stroke" />
                {m.rules.map((r: any) => (
                  <line key={r.label}
                        x1={r.at * 100} y1="0" x2={r.at * 100} y2="100"
                        className={rule === r.label ? own.ruleLineOn : own.ruleLine}
                        vectorEffect="non-scaling-stroke" />
                ))}
              </svg>

              {/* Raw marks, only where there are few enough for them to mean anything. */}
              {c.points.length > 0 && (
                <div className={own.rug}>
                  {c.points.map((p: any) => (
                    <span key={p.entity} className={own.tick}
                          style={{ left: `${p.at * 100}%` }}
                          title={`${p.entity}: ${p.score}`} />
                  ))}
                </div>
              )}
            </div>

            <span className={own.medianLabel} style={{ left: `${c.median_at * 100}%` }}>
              median {c.median}
            </span>
          </div>
        ))}

        {/* One axis for all three lanes, because they share it — repeating it per lane would
            imply three scales. */}
        <div className={own.axis}>
          {m.axis.ticks.map((t: any) => (
            <span key={t.raw} className={own.tickLabel} style={{ left: `${t.at * 100}%` }}>
              {t.raw}
            </span>
          ))}
          <span className={own.axisName}>
            {m.axis.label} · {m.axis.scale}
          </span>
        </div>
      </div>

      <div className={own.counts}>
        <span>
          <strong>{m.counts.above_p99.toLocaleString("en-US")}</strong> clear the 99th
          percentile
        </span>
        <span>
          <strong>{m.counts.essential_above_p99.toLocaleString("en-US")}</strong> of those are
          common-essential — the confound, not the finding
        </span>
        <span>
          <strong>{m.counts.controls_above_p99}</strong> of{" "}
          {m.curves.find((c: any) => c.group === "nonessential control")?.members} controls
          clear it, which is what a 99th percentile is supposed to let through
        </span>
      </div>
    </figure>
  );
}
