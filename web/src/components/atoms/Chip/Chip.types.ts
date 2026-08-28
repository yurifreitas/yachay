import type { Epistemic } from "../StatusDot";

export type ChipProps = {
  children: React.ReactNode;
  /** Tints the chip. Omit for a neutral chip. */
  tone?: Epistemic;
  /** Renders the identifier in a monospaced face — for ontology codes. */
  code?: boolean;
  title?: string;
};
