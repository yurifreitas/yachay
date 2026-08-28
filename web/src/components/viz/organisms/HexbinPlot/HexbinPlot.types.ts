import type { ReactNode } from "react";
import type { Scale } from "../../../../lib/scale";
import type { PlotBox } from "../../atoms/PlotFrame";

export type HexbinPlotProps = {
  /** Parallel arrays, in DATA units. Typed arrays are welcome — nothing here copies them. */
  xs: ArrayLike<number>;
  ys: ArrayLike<number>;
  /** Scale FACTORIES, not scales.
   *
   *  The plot area's size is decided by `PlotFrame`, so a scale built outside would have to
   *  guess the range and then be silently wrong when a margin changed. Handing in
   *  `(range) => symlog(domain, range, 0.2)` keeps the choice of scale with the caller (it is
   *  a claim about the data) and the choice of geometry with the frame. Any scale works:
   *  linear, log, symlog, quantile — the plot never asks which. */
  x: (range: [number, number]) => Scale;
  y: (range: [number, number]) => Scale;
  width?: number;
  height?: number;
  /** Hexagon radius in screen units. Bigger = smoother density, fewer individuals. */
  radius?: number;
  /** Cells at or below this count give their points back as individual marks. */
  pointThreshold?: number;
  xLabel: string;
  yLabel: string;
  /** Where a non-linear scale confesses to being one. */
  xNote?: string;
  yNote?: string;
  xFormat?: (v: number) => string;
  yFormat?: (v: number) => string;
  ariaLabel: string;
  /** The how-to-read sentence. Omitting it is allowed only when the caller prints its own. */
  readAloud?: ReactNode;
  /** Colour for an individually drawn point — class, flag, whatever the caller means. */
  colorOf?: (i: number) => string;
  /** Name of a point, for the readout when a cell holds few enough to list. */
  labelOf?: (i: number) => string;
  /** Predicate applied during binning, so a filter costs no array copy. */
  keep?: (i: number) => boolean;
  /** Reference lines, quadrant labels, callouts — drawn over the marks. Handed the box and
   *  the resolved scales, so an annotation lands in data coordinates. */
  annotations?: (box: PlotBox, x: Scale, y: Scale) => ReactNode;
  /** Unique within the page; used for the clip path id. */
  id: string;
};
