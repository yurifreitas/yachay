import { Fragment } from "react";
import { StatusDot } from "../../../components/atoms/StatusDot";
import { PrevalenceBar } from "../../../components/atoms/PrevalenceBar";
import { AXES, axisState, bandOf, type Disease, type Lexicon } from "../model";
import css from "./GapMatrix.module.css";

/** The atlas's central view: one row per disease, one column per axis of knowledge.
 *
 *  This is a heatmap whose cells are epistemic states rather than magnitudes, so the
 *  encoding is a labelled mark, not a colour fill — a filled colour grid would invite the
 *  reader to compare "how unknown" two cells are, which is not a quantity that exists.
 */
export function GapMatrix({ lexicon, diseases }: { lexicon: Lexicon; diseases: Disease[] }) {
  return (
    <div className={css.wrap}>
      <div className={css.grid} role="table" aria-label="What is known about each disease">
        <div className={`${css.cell} ${css.head}`} role="columnheader">Disease</div>
        {AXES.map((a) => (
          <div key={a.key} className={`${css.cell} ${css.head}`} role="columnheader">{a.label}</div>
        ))}
        <div className={`${css.cell} ${css.head}`} role="columnheader">Prevalence</div>

        {diseases.map((d) => {
          const band = bandOf(lexicon, d);
          return (
            <Fragment key={d.name}>
              <div className={`${css.cell} ${css.name}`} role="cell">
                <span className={css.title}>{d.name}</span>
                <span className={css.syn}>{d.synonyms.slice(0, 2).join(" · ")}</span>
              </div>
              {AXES.map((a) => {
                const state = axisState(d, a.key);
                const label =
                  a.key === "gene" ? (state === "known" ? d.gene : "not found")
                  : a.key === "mechanism" ? (state === "known" ? "described" : "not described")
                  : a.key === "therapy" ? (state === "known" ? "approved" : state === "partial" ? "off-label" : "none")
                  : state === "known" ? "indexed" : state === "partial" ? "partial" : "none";
                return (
                  <div key={a.key} className={css.cell} role="cell">
                    <StatusDot state={state} label={label} size="sm" />
                  </div>
                );
              })}
              <div className={css.cell} role="cell">
                <PrevalenceBar rank={band.rank as 0 | 1 | 2 | 3 | 4} label={band.label} />
              </div>
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
