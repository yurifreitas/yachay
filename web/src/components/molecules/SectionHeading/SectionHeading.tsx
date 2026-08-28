import { useNavHeading } from "../../../lib/nav";
import { useT } from "../../../i18n";
import css from "./SectionHeading.module.css";

/** The published position, printed. Reads the same tree the rail reads, so the two can
 *  never disagree — there is one source and two renderings of it. */
export function SectionHeading() {
  const { group, question, section } = useNavHeading();
  const t = useT();
  if (!group && !section) return null;
  return (
    <div className={css.head}>
      <div className={css.crumbs}>
        {group && <span>{t(group)}</span>}
        {group && section && <span className={css.sep} aria-hidden="true">/</span>}
        {section && <span className={css.here}>{t(section)}</span>}
      </div>
      {question && <p className={css.question}>{t(question)}</p>}
    </div>
  );
}
