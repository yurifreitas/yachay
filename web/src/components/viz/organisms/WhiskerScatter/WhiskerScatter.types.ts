/** One observation: a known x, and a y that carries an interval. */
export type WhiskerPoint = {
  label: string;
  x: number;
  y: number;
  lo?: number | null;
  hi?: number | null;
  /** Whether the interval clears whatever bar the caller set. Drives weight and fill. */
  ok?: boolean;
};

export type WhiskerScatterProps = {
  points: readonly WhiskerPoint[];
  xLabel: string;
  yLabel: string;
  refs?: readonly { at: number; label: string }[];
  /** A reference CURVE in data space — a calibration line, a null's 95th percentile against
   *  observation count. Drawn as a stepped path and labelled at its right end, because the
   *  thing a reader must compare each point against is often a function of x rather than a
   *  constant. */
  curve?: readonly { x: number; y: number }[];
  curveLabel?: string;
  /** symlog by default, because the figure this component was built for spans decades and
   *  crosses zero. A caller whose y is a bounded score in [0, 1] passes "linear": symlog on
   *  a narrow positive range compresses the whole figure into one band and reads as a bug. */
  yScale?: "symlog" | "linear";
  /** Tick formatting. The defaults round to whole numbers, which is right for a z of 1825
   *  and destroys a score of 0.548. */
  yFormat?: (v: number) => string;
  xFormat?: (v: number) => string;
  width?: number;
  height?: number;
  ariaLabel: string;
  readAloud: React.ReactNode;
  source?: string;
};
