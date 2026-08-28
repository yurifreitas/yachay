/** Types for the dimensional transforms. Written by tools/dimensions.py.
 *
 *  `result` is intentionally loose: each transform returns its own shape, because forcing
 *  seven different computations into one schema would flatten exactly what makes them
 *  different views.
 */
export type Dimension = {
  id: string; person: string; contribution: string; transform: string;
  result: Record<string, unknown> & Record<string, any>;
};
export type Dimensions = {
  generated: string;
  rule: string;
  omitted: { person: string; why: string }[];
  dimensions: Dimension[];
};

export type DimensionsTwo = {
  generated: string;
  why: string;
  rule: string;
  dimensions: (Dimension & { years: string })[];
};
