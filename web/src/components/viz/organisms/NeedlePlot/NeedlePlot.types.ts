import type { ReactNode } from "react";

export type NeedleSeries = Partial<
  Record<"pathogenic" | "uncertain" | "benign" | "conflicting", number[]>
>;

export type NeedlePlotProps = {
  /** One array per significance class, each `bins` long, already counted by Python. */
  series: NeedleSeries;
  /** Residues. The axis is the molecule, so this must be the protein length and not the
   *  furthest observed variant — otherwise the axis is a picture of the sequencing. */
  span: number;
  bins: number;
  width?: number;
  height?: number;
  /** Individually recurrent residues, labelled in place. */
  recurrent?: { pos: number; n: number }[];
  /** The parts of the protein, drawn as a track under the needles. Without them a reader
   *  sees a cluster at residue 340 and cannot know whether 340 is a folded domain, a
   *  membrane pass, or a stretch nobody has characterised. */
  features?: {
    kind: "domain" | "membrane" | "motif" | "active" | "binding";
    start: number;
    end: number;
    label: string;
  }[];
  /** Where the length came from, printed on the axis: a length inferred from the variants
   *  themselves is a weaker axis and the reader is entitled to know. */
  lengthFrom?: string;
  ariaLabel: string;
  readAloud?: ReactNode;
  /** Every visible word, resolved by the caller — this organism holds no English. */
  labels: {
    axis: string;
    residues: string;
    placed: string;
    pathogenic: string;
    uncertain: string;
    benign: string;
    conflicting: string;
    /** One per feature kind, for the track's own legend. */
    domain?: string;
    membrane?: string;
    motif?: string;
    active?: string;
    binding?: string;
  };
};
