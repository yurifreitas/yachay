import type { ReactNode } from "react";

export type MatrixOrdering = {
  /** Which gene sits at each slot. The inverse of a rank, decoded from the payload. */
  index: Int32Array;
  /** What this ordering claims, printed under the figure. An ordering is an argument
   *  (ADR 0008) and an unlabelled one is an argument nobody can check. */
  says: string;
};

export type MatrixPlotProps = {
  n: number;
  edges: { i: Int32Array; j: Int32Array };
  /** Keyed by name; the FIRST key is treated as the one that asserts the communities, and is
   *  the only ordering the block rules are drawn over. */
  orderings: Record<string, MatrixOrdering>;
  /** [start, end, community] in slot space, from the first ordering. */
  blocks?: readonly (readonly number[])[];
  /** Per gene, in gene-id space; negative means unscored. */
  confidence?: Float32Array;
  labelFor?: (gene: number) => string;
  /** Called with the community id of the block under the pointer, or null outside one. Only
   *  fires under the first ordering: the blocks are only contiguous there, so a click under
   *  `spectral` would select a range that is not a community. */
  onPickBlock?: (community: number | null) => void;
  /** The community drawn emphasised. Kept outside the component because the card that shows
   *  it lives outside too, and two sources of truth for a selection is how a highlight ends
   *  up describing a different block from the panel beside it. */
  picked?: number | null;
  size?: number;
  ariaLabel: string;
  readAloud: ReactNode;
  source?: string;
};
