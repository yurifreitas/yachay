import { memo, useMemo, useState } from "react";
import { PlotFrame } from "../../atoms/PlotFrame";
import { ReadAloud } from "../../atoms/ReadAloud";
import { fmtInt } from "../../../../lib/scale";
import css from "./ParallelCoordinates.module.css";
import type { ParallelCoordinatesProps, PCRow } from "./ParallelCoordinates.types";

/** A gene as a LINE THROUGH THE MEASUREMENT SPACE.
 *
 *  THE FORM. Parallel coordinates (Inselberg, 1985): one vertical axis per variable, side by
 *  side, and each observation is a polyline crossing all of them. It is the standard answer
 *  to a question no scatter can take — "these five measurements disagree; which ones, and
 *  for whom" — because a scatter shows two variables and a matrix of scatters shows pairs
 *  while hiding the individual that is extreme in one and ordinary in four.
 *
 *  WHY IT IS THE RIGHT FORM HERE AND NOT A FLOURISH. This site's own finding engine is built
 *  entirely on disagreements between layers: constrained in people and dispensable in
 *  culture, needed by every line and broken freely in populations, clearly important and
 *  unreadable. Every one of those is a CROSSING between two axes. On parallel coordinates the
 *  crossing is the visible object — a rule firing is a shape, not a lookup.
 *
 *  THE TRADE, STATED. Order matters and is arbitrary: two axes only show their relationship
 *  when adjacent, so a five-axis plot shows four of the ten pairwise relationships. Which four
 *  is a decision, so the axis order is shown under the plot and the reader can move any axis
 *  with the arrows beside its name.
 *
 *  Overplotting at 18,000 lines is handled by drawing everything faint and one class bright:
 *  the question is never "where is gene X" — the navigator answers that — but "does this
 *  class of gene run differently through the space than the rest".
 */
export function ParallelCoordinates({
  axes, rows, width = 900, height = 420, highlight, labels, readAloud,
  ariaLabel, onPick,
}: ParallelCoordinatesProps) {
  const [hover, setHover] = useState<number | null>(null);
  const [order, setOrder] = useState<number[]>(() => axes.map((_, i) => i));

  const ordered = useMemo(() => order.map((i) => axes[i]), [order, axes]);

  // Every axis is drawn on its own RANK scale, not its own linear range. The variables here
  // span six orders of magnitude (papers) and a bounded ratio (VUS share); on linear axes the
  // papers axis is one line at the bottom and 17,900 at the top, which shows nothing. Rank
  // makes every axis uniform by construction, and the caption says so.
  const ranks = useMemo(() => {
    return ordered.map((ax) => {
      const vals = rows
        .map((r) => r.values[ax.key])
        .filter((v): v is number => v != null && Number.isFinite(v));
      const sorted = Float64Array.from(vals).sort();
      return (v: number | null | undefined) => {
        if (v == null || !Number.isFinite(v)) return null;
        let lo = 0, hi = sorted.length;
        while (lo < hi) {
          const mid = (lo + hi) >> 1;
          if (sorted[mid] <= v) lo = mid + 1; else hi = mid;
        }
        return sorted.length ? lo / sorted.length : 0;
      };
    });
  }, [ordered, rows]);

  const lit = useMemo(
    () => (highlight ? rows.filter((r) => r.classes?.includes(highlight)) : []),
    [rows, highlight],
  );

  const move = (from: number, dir: -1 | 1) => {
    const to = from + dir;
    if (to < 0 || to >= order.length) return;
    const next = [...order];
    [next[from], next[to]] = [next[to], next[from]];
    setOrder(next);
  };

  return (
    <div className={css.wrap}>
      {readAloud && (
        <ReadAloud form="Parallel coordinates" source="Inselberg (1985), The Visual Computer.">
          {readAloud}
        </ReadAloud>
      )}

      <PlotFrame width={width} height={height} scrollAtWidth={680} ariaLabel={ariaLabel}
                 margin={{ top: 44, right: 30, bottom: 56, left: 30 }}>
        {(box) => {
          const step = ordered.length > 1 ? box.width / (ordered.length - 1) : 0;
          const x = (i: number) => box.x0 + i * step;
          const y = (rank: number) => box.y0 - rank * box.height;

          const path = (r: (typeof rows)[number]) => {
            const pts: string[] = [];
            ordered.forEach((ax, i) => {
              const rank = ranks[i](r.values[ax.key]);
              // A missing measurement BREAKS the line rather than being interpolated. A
              // polyline drawn through an absence is a claim nobody made.
              if (rank == null) { pts.push(""); return; }
              pts.push(`${pts.length && pts[pts.length - 1] ? "L" : "M"}${x(i)},${y(rank)}`);
            });
            return pts.filter(Boolean).join(" ");
          };

          return (
            <>
              {/* The ground: everything, faint. The question is never "where is one gene" —
                  it is "does this class run differently from the rest".

                  MEMOISED, AND THAT IS NOT AN OPTIMISATION. Hover lives in this component's
                  state, so every pointer move re-rendered all three thousand ground paths and
                  recomputed each one's `d` string — three thousand binary searches per mouse
                  move, which wedges the tab rather than slowing it. The ground does not
                  depend on hover, so it is cut out of the hover render entirely. */}
              <Ground rows={rows} path={path} orderKey={order.join(",")} />

              {lit.length > 0 && (
                <g className={css.lit}>
                  {lit.map((r, i) => (
                    <path
                      key={i} d={path(r)}
                      onPointerEnter={() => setHover(rows.indexOf(r))}
                      onPointerLeave={() => setHover(null)}
                      onClick={() => onPick?.(r.id)}
                    />
                  ))}
                </g>
              )}

              {hover != null && rows[hover] && (
                <path d={path(rows[hover])} className={css.hovered} />
              )}

              {ordered.map((ax, i) => (
                <g key={ax.key}>
                  <line x1={x(i)} x2={x(i)} y1={box.y0} y2={box.y1} className={css.axis} />
                  <text x={x(i)} y={box.y1 - 22} textAnchor="middle" className={css.axisName}>
                    {ax.label}
                  </text>
                  {/* Which end is which. On a rank axis the reader cannot infer it, and an
                      unlabelled direction inverts every crossing they think they see. */}
                  <text x={x(i)} y={box.y1 - 8} textAnchor="middle" className={css.axisEnd}>
                    {ax.top}
                  </text>
                  <text x={x(i)} y={box.y0 + 16} textAnchor="middle" className={css.axisEnd}>
                    {ax.bottom}
                  </text>
                </g>
              ))}
            </>
          );
        }}
      </PlotFrame>

      {/* AXIS ORDER IS A CHOICE AND THE READER GETS IT. Two variables only show their
          relationship when adjacent, so a five-axis plot shows four of ten pairs; which four
          is a decision, and hiding it would be the plot's biggest lie. */}
      <div className={css.reorder}>
        <span className={css.reorderLabel}>{labels.order}</span>
        {ordered.map((ax, i) => (
          <span key={ax.key} className={css.chip}>
            {ax.label}
            <button type="button" onClick={() => move(i, -1)} disabled={i === 0}
                    aria-label={`${labels.moveLeft} ${ax.label}`}>←</button>
            <button type="button" onClick={() => move(i, 1)} disabled={i === ordered.length - 1}
                    aria-label={`${labels.moveRight} ${ax.label}`}>→</button>
          </span>
        ))}
      </div>

      <p className={css.readout} role="status" aria-live="polite">
        {hover != null && rows[hover] ? (
          <>
            <strong className={css.sym}>{rows[hover].id}</strong>
            {ordered.map((ax) => {
              const v = rows[hover].values[ax.key];
              return (
                <span key={ax.key} className={css.pair}>
                  {ax.label} <b>{v == null ? "—" : ax.format ? ax.format(v) : fmtInt(v)}</b>
                </span>
              );
            })}
          </>
        ) : (
          <span className={css.hint}>
            {labels.count.replace("{n}", fmtInt(rows.length))}
            {highlight ? ` · ${labels.lit.replace("{n}", fmtInt(lit.length))}` : ""}
          </span>
        )}
      </p>
    </div>
  );
}

/** The faint layer, cut out of the hover render.
 *
 *  `path` is rebuilt on every render of the parent, so a plain memo on props would never hit.
 *  The comparator ignores it deliberately and keys on the two things that actually change the
 *  drawing: which rows there are, and what order the axes are in.
 */
const Ground = memo(
  function Ground(
    { rows, path }:
    { rows: PCRow[]; path: (r: PCRow) => string; orderKey: string },
  ) {
    return (
      <g className={css.ground}>
        {rows.map((r, i) => <path key={i} d={path(r)} />)}
      </g>
    );
  },
  // ORDER IS PART OF THE KEY. Comparing only on `rows` left the ground drawn in the previous
  // axis order after a reorder — the bright lines moved and the faint ones did not, which is
  // a plot showing two different arrangements at once.
  (a, b) => a.rows === b.rows && a.orderKey === b.orderKey,
);
