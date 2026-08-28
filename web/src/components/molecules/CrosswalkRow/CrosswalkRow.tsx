import { Chip } from "../../atoms/Chip";
import css from "./CrosswalkRow.module.css";
import type { CrosswalkRowProps } from "./CrosswalkRow.types";

/** The identifiers one disease carries across ontologies, with the missing ones shown as
 *  missing rather than omitted. A crosswalk that hides its holes is why records fail to
 *  join in the first place. */
export function CrosswalkRow({ entries }: CrosswalkRowProps) {
  return (
    <div className={css.root}>
      {entries.map((e) => (
        <span key={e.ontology} className={css.slot}>
          <span className={css.ont}>{e.ontology}</span>
          {e.id ? (
            <Chip code title={e.role}>{e.id}</Chip>
          ) : (
            <Chip code tone="unknown" title={`no ${e.ontology} identifier — ${e.role}`}>
              not indexed
            </Chip>
          )}
        </span>
      ))}
    </div>
  );
}
