import type { ReactNode } from "react";

export type ScatterSet = { x: number[]; y: number[] };

export type ScatterPairProps = {
  a: ScatterSet;
  b: ScatterSet;
  /** Panel captions, in order. */
  labels: [string, string];
  /** Cluster per point, shared by both panels — the same gene keeps its colour across the
   *  two maps, which is what makes a moved point visible. Negative means unclustered. */
  cluster?: number[];
  /** CSS custom-property names to colour clusters by, so the palette stays in the sheet. */
  palette: string[];
  width?: number;
  height?: number;
  ariaLabel: string;
  readAloud: ReactNode;
  source?: string;
};
