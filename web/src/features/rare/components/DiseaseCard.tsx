import { Chip } from "../../../components/atoms/Chip";
import { StatusDot } from "../../../components/atoms/StatusDot";
import { CrosswalkRow } from "../../../components/molecules/CrosswalkRow";
import { AXES, axisState, scriptOf, type Disease } from "../model";
import css from "./DiseaseCard.module.css";

/** One disease in full: the crosswalk, the four states, and the synonym set.
 *
 *  The synonyms are not decoration. A literature search keyed on one language misses the
 *  corpus written in the others, and for a rare disease the corpus may be a handful of
 *  papers — so the language coverage IS the searchability of the disease.
 */
export function DiseaseCard({ d }: { d: Disease }) {
  return (
    <article className={css.card}>
      <header className={css.head}>
        <h3 className={css.name}>{d.name}</h3>
        <p className={css.note}>{d.note}</p>
      </header>

      <div>
        <div className={css.section}>Identifiers</div>
        <CrosswalkRow
          entries={[
            { ontology: "MONDO", id: d.mondo, role: "the merge target" },
            { ontology: "ORPHA", id: d.orpha, role: "European rare-disease reference" },
            { ontology: "OMIM", id: d.omim, role: "the genetics literature's index" },
          ]}
        />
      </div>

      <div>
        <div className={css.section}>What is known</div>
        <div className={css.states}>
          {AXES.map((a) => (
            <StatusDot key={a.key} state={axisState(d, a.key)} label={a.label} size="sm" />
          ))}
        </div>
      </div>

      <div>
        <div className={css.section}>Names it is searched by ({d.synonyms.length})</div>
        <div className={css.syns}>
          {d.synonyms.map((s) => (
            <Chip key={s} tone={scriptOf(s) === "latin" ? undefined : "partial"}>{s}</Chip>
          ))}
        </div>
      </div>
    </article>
  );
}
