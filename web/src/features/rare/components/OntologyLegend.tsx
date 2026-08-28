import type { Ontology } from "../model";
import css from "./OntologyLegend.module.css";

/** The systems a rare-disease record has to be joined across. Presented as cards rather
 *  than a table because each one needs a sentence to be useful, and a table of sentences
 *  is a table nobody reads. */
export function OntologyLegend({ ontologies }: { ontologies: Ontology[] }) {
  return (
    <div className={css.grid}>
      {ontologies.map((o) => (
        <article key={o.id} className={css.card}>
          <div>
            <div className={css.id}>{o.id}</div>
            <div className={css.name}>{o.name}</div>
          </div>
          <p className={css.role}>{o.role}</p>
          <span className={css.pattern}>{o.pattern} · {o.scope}</span>
        </article>
      ))}
    </div>
  );
}
