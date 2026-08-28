import type { Scale } from "../../../../lib/scale";
import type { PlotBox } from "../PlotFrame";
import css from "./Axis.module.css";

export type AxisProps = {
  scale: Scale;
  box: PlotBox;
  label: string;
  /** How a tick value is printed. Defaults to the value itself. */
  format?: (v: number) => string;
  ticks?: number;
  /** Draw gridlines across the plot from each tick. Off by default: a grid is a reading aid
   *  for lookups, and most figures here are comparisons. */
  grid?: boolean;
  /** Printed under the label in small type. This is where a non-linear axis states that it
   *  IS one — the single most common way a chart misleads is an unannounced scale. */
  note?: string;
};

/** One axis, for any scale.
 *
 *  It takes a `Scale` and never asks which kind. That is what makes swapping a linear axis
 *  for a symlog or a quantile one a one-word change at the call site — and it is why the
 *  scales in `lib/viz/scales.ts` were written to the same contract as `linear` rather than
 *  as bespoke helpers.
 *
 *  THE `note` IS NOT DECORATION. A reader who does not notice an axis is logarithmic reads
 *  every distance on it wrong, and nothing in the drawing announces it. So the components
 *  that build non-linear axes below pass a note, and the ones that do not are linear.
 */
export function AxisY({ scale, box, label, format = String, ticks = 5, grid, note }: AxisProps) {
  return (
    <g>
      {scale.ticks(ticks).map((t) => (
        <g key={t}>
          {grid && (
            <line x1={box.x0} x2={box.x1} y1={scale(t)} y2={scale(t)} className={css.grid} />
          )}
          <text x={box.x0 - 10} y={scale(t)} textAnchor="end" dominantBaseline="middle"
                className={css.tick}>
            {format(t)}
          </text>
        </g>
      ))}
      <text transform={`translate(14, ${(box.y0 + box.y1) / 2}) rotate(-90)`}
            textAnchor="middle" className={css.label}>
        {label}
        {note && <tspan className={css.note}> · {note}</tspan>}
      </text>
    </g>
  );
}

export function AxisX({ scale, box, label, format = String, ticks = 5, grid, note }: AxisProps) {
  return (
    <g>
      {scale.ticks(ticks).map((t) => (
        <g key={t}>
          {grid && (
            <line x1={scale(t)} x2={scale(t)} y1={box.y0} y2={box.y1} className={css.grid} />
          )}
          <text x={scale(t)} y={box.y0 + 18} textAnchor="middle" className={css.tick}>
            {format(t)}
          </text>
        </g>
      ))}
      <text x={(box.x0 + box.x1) / 2} y={box.y0 + 38} textAnchor="middle" className={css.label}>
        {label}
        {note && <tspan className={css.note}> · {note}</tspan>}
      </text>
    </g>
  );
}

/** A reference line with its own label — the value a figure is arguing against: zero, a
 *  noise floor, a registered threshold. Drawn as an annotation rather than as a series,
 *  because it is not data. */
export function RuleY(
  { at, box, label, tone = "axis" }:
  { at: number; box: PlotBox; label?: string; tone?: "axis" | "warn" },
) {
  return (
    <g>
      <line x1={box.x0} x2={box.x1} y1={at} y2={at} className={css.rule} data-tone={tone} />
      {label && (
        <text x={box.x1 - 4} y={at - 5} textAnchor="end" className={css.ruleLabel} data-tone={tone}>
          {label}
        </text>
      )}
    </g>
  );
}

export function RuleX(
  { at, box, label, tone = "axis" }:
  { at: number; box: PlotBox; label?: string; tone?: "axis" | "warn" },
) {
  return (
    <g>
      <line x1={at} x2={at} y1={box.y0} y2={box.y1} className={css.rule} data-tone={tone} />
      {label && (
        <text x={at + 5} y={box.y1 + 12} className={css.ruleLabel} data-tone={tone}>{label}</text>
      )}
    </g>
  );
}
