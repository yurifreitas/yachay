/** The four epistemic states this atlas encodes. Not a severity scale: `unknown` is not
 *  worse than `absent`, it is a different kind of gap. */
export type Epistemic = "known" | "partial" | "unknown" | "absent";

export type StatusDotProps = {
  state: Epistemic;
  /** Rendered next to the mark. Required: colour never carries the meaning alone. */
  label: string;
  size?: "sm" | "md";
};
