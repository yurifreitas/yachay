import type { ReactNode } from "react";

export type UpSetPlotProps = {
  /** How many items there are. Predicates are asked about indices 0..count-1, so nothing is
   *  copied and a typed array or a 17,916-row table costs nothing to pass. */
  count: number;
  /** Declaration order is display order: the caller decides what "first" means. */
  sets: { name: string; has: (i: number) => boolean }[];
  /** What one item is called, in prose. "genes", "diseases", "documents". */
  itemLabel?: string;
  labelOf?: (i: number) => string;
  ariaLabel: string;
  readAloud?: ReactNode;
  maxCombinations?: number;
  height?: number;
};
