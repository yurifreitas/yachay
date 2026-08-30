import type { ReactNode } from "react";

export type SweepPanel = {
  /** Printed as the panel's y-axis label. It is also the key `marks` refer to. */
  label: string;
  /** One value per x, in the same order. */
  values: number[];
  format?: (v: number) => string;
  /** A panel that is context rather than subject. Drawn grey so the reader knows which
   *  line the sentence above is about — contrast, not saturation, carries emphasis. */
  muted?: boolean;
};

export type SweepPlotProps = {
  /** The swept parameter. Shared by every panel, which is the whole point of the form. */
  x: number[];
  panels: readonly SweepPanel[];
  xLabel: string;
  /** A horizontal reference inside one named panel — a resolution limit, a null's level. */
  marks?: readonly { panel: string; y: number | null; label: string }[];
  width?: number;
  panelHeight?: number;
  ariaLabel: string;
  readAloud: ReactNode;
  source?: string;
};
