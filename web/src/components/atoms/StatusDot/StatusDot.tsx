import css from "./StatusDot.module.css";
import type { StatusDotProps } from "./StatusDot.types";

/** A state mark plus its label. Indivisible, no domain knowledge, no data access. */
export function StatusDot({ state, label, size = "md" }: StatusDotProps) {
  return (
    <span className={`${css.root} ${size === "sm" ? css.sm : ""}`}>
      <span className={`${css.mark} ${css[state]}`} aria-hidden="true" />
      {label}
    </span>
  );
}
