import type { ReactNode } from "react";

export type AlluvialBand = {
  id: number;
  genes: number;
  /** What the band is, when it could be named. `#id` is printed otherwise, rather than a
   *  made-up label — a band with no established identity says so. */
  name?: string | null;
};

export type AlluvialAxis = { algorithm: string; bands: AlluvialBand[] };

export type AlluvialFlow = {
  /** "algorithm:community", matching the band keys. */
  from: string;
  to: string;
  genes: number;
  /** Whether the two communities were paired by the assignment solution. Unmatched ribbons
   *  are the disagreement, and they carry the emphasis. */
  matched?: boolean;
};

export type AlluvialPlotProps = {
  axes: AlluvialAxis[];
  flows: AlluvialFlow[];
  /** Band order per axis, solved in Python by barycentre sweeps. Passing it in rather than
   *  computing it here is ADR 0008: a layout recomputed per render can differ between two
   *  readers looking at the same figure. */
  order: Record<string, number[]>;
  width?: number;
  height?: number;
  ariaLabel: string;
  readAloud: ReactNode;
  source?: string;
};
