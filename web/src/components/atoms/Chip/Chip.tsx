import css from "./Chip.module.css";
import type { ChipProps } from "./Chip.types";

export function Chip({ children, tone, code, title }: ChipProps) {
  return (
    <span
      className={[css.root, tone ? css[tone] : "", code ? css.code : ""].filter(Boolean).join(" ")}
      title={title}
    >
      {children}
    </span>
  );
}
