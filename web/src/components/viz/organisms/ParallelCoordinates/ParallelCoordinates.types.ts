import type { ReactNode } from "react";

export type PCAxis = {
  key: string;
  label: string;
  /** What the top and bottom of this axis MEAN. On a rank axis the reader cannot infer the
   *  direction, and an unlabelled one inverts every crossing they think they see. */
  top: string;
  bottom: string;
  format?: (v: number) => string;
};

export type PCRow = {
  id: string;
  /** A missing value is null, not zero. The line breaks there rather than being drawn
   *  through an absence. */
  values: Record<string, number | null | undefined>;
  /** Which rules fired for this row — the highlight selects on these. */
  classes?: string[];
};

export type ParallelCoordinatesProps = {
  axes: PCAxis[];
  rows: PCRow[];
  width?: number;
  height?: number;
  /** The class to draw bright over the faint ground. */
  highlight?: string;
  ariaLabel: string;
  readAloud?: ReactNode;
  onPick?: (id: string) => void;
  labels: {
    order: string;
    moveLeft: string;
    moveRight: string;
    /** "{n} genes drawn" */
    count: string;
    /** "{n} highlighted" */
    lit: string;
  };
};
