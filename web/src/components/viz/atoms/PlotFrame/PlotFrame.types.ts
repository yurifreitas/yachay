import type { ReactNode } from "react";

/** The rectangle marks are drawn in, in SVG user units.
 *  `y0` is the BOTTOM (largest y) and `y1` the top, matching the inverted screen axis, so a
 *  caller writes `linear(domain, [box.y0, box.y1])` and gets the orientation right by
 *  default rather than by remembering to flip it. */
export type PlotBox = {
  x0: number; x1: number; y0: number; y1: number;
  width: number; height: number;
};

export type PlotFrameProps = {
  width: number;
  height: number;
  margin?: Partial<{ top: number; right: number; bottom: number; left: number }>;
  /** One sentence, spoken aloud. Every unfamiliar form owes the reader this. */
  ariaLabel: string;
  children: (box: PlotBox) => ReactNode;
  /** Minimum width below which the figure scrolls horizontally instead of compressing. */
  scrollAtWidth?: number;
};
