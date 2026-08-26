/** Chart primitives.
 *
 * Deliberately not a chart library: four charts, each with a specific job, built from
 * shared axis/tooltip pieces. Marks follow the method's specs — 2px lines, >= 8px
 * markers, recessive grid and axes, text in ink tokens rather than the series color.
 */
import { useState, type ReactNode } from "react";
import type { Scale } from "../lib/scale";

export const PAD = { top: 16, right: 20, bottom: 42, left: 60 };

export function Grid({ y, x0, x1 }: { y: Scale; x0: number; x1: number }) {
  return (
    <g aria-hidden="true">
      {y.ticks(5).map((t) => (
        <line key={t} x1={x0} x2={x1} y1={y(t)} y2={y(t)} stroke="var(--gridline)" strokeWidth={1} />
      ))}
    </g>
  );
}

export function AxisY({
  scale,
  x,
  label,
  format = (v: number) => String(v),
}: {
  scale: Scale;
  x: number;
  label: string;
  format?: (v: number) => string;
}) {
  return (
    <g>
      {scale.ticks(5).map((t) => (
        <text
          key={t}
          x={x - 10}
          y={scale(t)}
          textAnchor="end"
          dominantBaseline="middle"
          fontSize={11}
          fill="var(--text-muted)"
          className="num"
        >
          {format(t)}
        </text>
      ))}
      <text
        transform={`translate(14, ${(scale(scale.domain[0]) + scale(scale.domain[1])) / 2}) rotate(-90)`}
        textAnchor="middle"
        fontSize={11}
        fill="var(--text-secondary)"
      >
        {label}
      </text>
    </g>
  );
}

export function AxisX({
  scale,
  y,
  label,
  format = (v: number) => String(v),
}: {
  scale: Scale;
  y: number;
  label: string;
  format?: (v: number) => string;
}) {
  return (
    <g>
      <line
        x1={scale(scale.domain[0])}
        x2={scale(scale.domain[1])}
        y1={y}
        y2={y}
        stroke="var(--axis)"
        strokeWidth={1}
      />
      {scale.ticks(6).map((t) => (
        <text
          key={t}
          x={scale(t)}
          y={y + 18}
          textAnchor="middle"
          fontSize={11}
          fill="var(--text-muted)"
          className="num"
        >
          {format(t)}
        </text>
      ))}
      <text
        x={(scale(scale.domain[0]) + scale(scale.domain[1])) / 2}
        y={y + 36}
        textAnchor="middle"
        fontSize={11}
        fill="var(--text-secondary)"
      >
        {label}
      </text>
    </g>
  );
}

export function Legend({
  items,
}: {
  items: { color: string; label: string; hollow?: boolean }[];
}) {
  return (
    <ul className="legend">
      {items.map((i) => (
        <li key={i.label}>
          <span
            className={`swatch${i.hollow ? " hollow" : ""}`}
            style={i.hollow ? undefined : { background: i.color }}
            aria-hidden="true"
          />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

export interface TipState {
  x: number;
  y: number;
  content: ReactNode;
}

export function useTooltip() {
  const [tip, setTip] = useState<TipState | null>(null);
  const node = tip ? (
    <div
      className="tooltip"
      style={{ left: tip.x, top: tip.y }}
      role="status"
      aria-live="polite"
    >
      {tip.content}
    </div>
  ) : null;
  return { tip, setTip, node };
}

export function Figure({
  title,
  subtitle,
  children,
  note,
  table,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  note?: ReactNode;
  table?: ReactNode;
}) {
  const [showTable, setShowTable] = useState(false);
  return (
    <figure className="figure card">
      <figcaption>
        <div>
          <h3>{title}</h3>
          {subtitle && <p className="sub">{subtitle}</p>}
        </div>
        {table && (
          <button className="ghost" onClick={() => setShowTable((v) => !v)}>
            {showTable ? "Show chart" : "Show table"}
          </button>
        )}
      </figcaption>
      <div className="plot scroll-x">{showTable && table ? table : children}</div>
      {note && <p className="note">{note}</p>}
    </figure>
  );
}
