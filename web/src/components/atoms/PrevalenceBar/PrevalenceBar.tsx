import css from "./PrevalenceBar.module.css";
import type { PrevalenceBarProps } from "./PrevalenceBar.types";

/** Five ordered steps. The last is hatched rather than coloured, because "never measured"
 *  is not the last step of a scale — it is off the scale, and a solid fifth colour would
 *  read as "rarest of all". */
export function PrevalenceBar({ rank, label }: PrevalenceBarProps) {
  return (
    <div className={css.root}>
      <div className={css.track} role="img" aria-label={`prevalence: ${label}`}>
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className={[css.step, i <= rank ? css[`s${rank}`] : "", rank === 4 && i === 4 ? css.s4 : ""]
              .filter(Boolean)
              .join(" ")}
          />
        ))}
      </div>
      <span className={css.label}>{label}</span>
    </div>
  );
}
