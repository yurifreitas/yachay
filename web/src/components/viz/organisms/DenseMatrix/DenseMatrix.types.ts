import type { ReactNode } from "react";

export type DenseMatrixProps = {
  /** rows × cols bytes, row-major. Every cell is a measurement, not a count. */
  bytes: Uint8Array;
  rows: number;
  cols: number;
  rowLabels?: string[];
  /** A grouping per row — lineage, tissue, cohort. Drives the strip beside the matrix, which
   *  is what makes "this block is a lineage block" checkable rather than asserted. */
  rowGroups?: string[];
  colLabels?: string[];
  /** Per column, a share in [0,1] drawn as a strip under the matrix. */
  colMargin?: number[];
  marginLabel?: string;
  height?: number;
  /** The byte scale, so the component can place zero and format a value. */
  orderings?: {
    lo: number;
    hi: number;
    options: Record<string, { says?: string }>;
  };
  ordering?: string;
  onOrdering?: (k: string) => void;
  ariaLabel: string;
  readAloud: ReactNode;
  source?: string;
};
