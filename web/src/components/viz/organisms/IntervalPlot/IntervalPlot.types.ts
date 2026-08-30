/** One row of an interval plot: an estimate, and what it is worth. */
export type IntervalRow = {
  /** Printed at the left. Kept short; the caller truncates rather than the component. */
  label: string;
  /** The point estimate. Always drawn, even when there is no interval. */
  point: number;
  /** The interval. `null` when the estimate has none, which is a state the plot DRAWS
   *  rather than skips — see `noInterval`. */
  lo?: number | null;
  hi?: number | null;
  /** Whether this row clears whatever bar the caller set. Decides the mark's weight: the
   *  ones that survive carry the accent, the rest go grey. Colour is never the only signal —
   *  a row that does not survive is also hollow. */
  ok?: boolean;
  /** Why there is no interval, when there is none. Printed in place of the band, so an
   *  absent interval reads as a statement instead of as a rendering failure. */
  noInterval?: string | null;
  /** Small text after the label. Counts, degrees, drug names. */
  note?: string;
};

/** A vertical reference: zero, a threshold, an assay ceiling. */
export type IntervalRef = {
  at: number;
  label: string;
  /** Dashed marks a decision threshold; solid marks a structural value like zero. */
  dashed?: boolean;
};

export type IntervalPlotProps = {
  rows: readonly IntervalRow[];
  /** The x axis label, with its unit. */
  xLabel: string;
  /** `symlog` when the values span decades and cross zero — which is the situation this
   *  plot was built for. The axis prints a note saying so; an unannounced non-linear axis
   *  is the most common way a figure misleads. */
  scale?: "linear" | "symlog";
  refs?: readonly IntervalRef[];
  width?: number;
  height?: number;
  /** Row height. Below about 18px the labels collide; the caller usually leaves this. */
  rowH?: number;
  ariaLabel: string;
  readAloud: React.ReactNode;
  source?: string;
  format?: (v: number) => string;
};
