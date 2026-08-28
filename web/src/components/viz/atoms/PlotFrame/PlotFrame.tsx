import type { ReactNode } from "react";
import css from "./PlotFrame.module.css";
import type { PlotBox, PlotFrameProps } from "./PlotFrame.types";

/** The box every figure is drawn in, and the only place margins are decided.
 *
 *  WHY. Four charts in this repository each declared their own `PAD`/`M`/`PADX` constant and
 *  then computed `PLOT_H - M.b` inline, which is how one of them ended up with an axis label
 *  clipped and another with a plot area that did not match its own grid. Margins are not a
 *  per-chart preference; they are the space the axes need, and the axes are shared.
 *
 *  The children are a FUNCTION of the resulting box, so a caller builds its scales against
 *  the real inner rectangle instead of re-deriving it. That is the whole contract: this
 *  component owns the geometry, the caller owns the marks.
 */
export function PlotFrame({
  width, height, margin, ariaLabel, children, scrollAtWidth,
}: PlotFrameProps) {
  const m = { top: 16, right: 20, bottom: 44, left: 60, ...margin };
  const box: PlotBox = {
    x0: m.left,
    x1: width - m.right,
    y0: height - m.bottom,
    y1: m.top,
    width: width - m.left - m.right,
    height: height - m.top - m.bottom,
  };

  const svg = (
    <svg viewBox={`0 0 ${width} ${height}`} className={css.svg}
         role="img" aria-label={ariaLabel} preserveAspectRatio="xMidYMid meet">
      {children(box)}
    </svg>
  );

  // A figure that must not be squeezed says so with a minimum width and scrolls instead.
  // Silently shrinking a hexbin changes the bin size, and a bin size that depends on the
  // reader's window is not a measurement.
  return scrollAtWidth
    ? <div className={css.scroll}><div style={{ minWidth: scrollAtWidth }}>{svg}</div></div>
    : svg;
}

/** A plot-area clip, for marks that must not paint over the axes — a density curve whose
 *  tail runs past the domain, a hexbin at the edge. Declared once because every use needs a
 *  unique id and hand-rolled ids collide the moment two figures share a page. */
export function PlotClip({ id, box, children }: { id: string; box: PlotBox; children: ReactNode }) {
  return (
    <>
      <defs>
        <clipPath id={id}>
          <rect x={box.x0} y={box.y1} width={box.width} height={box.height} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id})`}>{children}</g>
    </>
  );
}
