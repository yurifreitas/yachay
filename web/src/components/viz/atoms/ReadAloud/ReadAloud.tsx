import type { ReactNode } from "react";
import css from "./ReadAloud.module.css";

/** The sentence that says how to read the figure, made into a component so that shipping an
 *  unfamiliar form without one takes effort.
 *
 *  THE RULE IT ENFORCES. Every exotic form in this repository — ridgeline, slopegraph,
 *  hexbin, raincloud, UpSet — trades a little positional precision for density or for
 *  narrative, and the trade is only fair if the reader is told what the marks mean. "Each
 *  ridge is one observation count" costs one line and is the difference between a figure and
 *  a decoration.
 *
 *  `form` names the form, so a reader who has met it before can skip the sentence, and one
 *  who has not has something to look up.
 */
export function ReadAloud(
  { form, children, source }:
  { form: string; children: ReactNode; source?: string },
) {
  return (
    <p className={css.read}>
      <span className={css.form}>{form}</span>
      <span className={css.body}>{children}</span>
      {source && <span className={css.source}>{source}</span>}
    </p>
  );
}
