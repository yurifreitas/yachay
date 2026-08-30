import type { ReactNode } from "react";

export type RaincloudGroup = {
  label: string;
  values: number[];
  /** One colour per group, used identically by cloud, box and rain — three encodings of the
   *  same group must never differ in hue, or they read as three groups. */
  color: string;
  /** A value to mark inside THIS group's row, with its label. Used for the observed value a
   *  null was built to calibrate: the whole reading of the figure is where that one number
   *  falls in the cloud beneath it, and a single figure-wide rule cannot carry four of them.
   */
  marker?: { at: number; label: string };
};

export type RaincloudPlotProps = {
  groups: RaincloudGroup[];
  /** Force a shared domain (e.g. to include a reference value the data does not reach). */
  domain?: [number, number];
  width?: number;
  rowHeight?: number;
  xLabel: string;
  xNote?: string;
  xFormat?: (v: number) => string;
  ariaLabel: string;
  readAloud?: ReactNode;
  /** A value to mark with a rule — usually zero, or a null mean. */
  zeroLine?: number;
  /** Above this many observations the rain is thinned, and the thinning is printed. */
  maxRain?: number;
};
