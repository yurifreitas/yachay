import { useNavTree } from "../../../lib/nav";
import { useT } from "../../../i18n";
import { WALK } from "../../../i18n/walk";
import css from "./SectionWalk.module.css";

/** THE ORDER WAS AN ARGUMENT AND NOTHING LET A READER FOLLOW IT.
 *
 *  Every page here declares its sections in a deliberate sequence. The rare atlas says so in
 *  its own comment — *look at one disease, then at what stops it, then at what it would
 *  physically take* — and then offered twenty-nine labels in a rail and no way to walk them
 *  in the order that comment describes. A reader who wanted the next step had to know its
 *  name, find it, and notice on their own that it sat under a different question.
 *
 *  So: one control, at the foot of every panel, carrying the sequence. It reads the published
 *  tree rather than taking props, so it cannot disagree with the rail — same source, third
 *  rendering, alongside the rail and `SectionHeading`.
 *
 *  IT NAMES THE GROUP CROSSING. Moving from the last section of one question to the first of
 *  the next is the only move in this interface that changes what is being asked, and a plain
 *  "next" would hide exactly that. When the step crosses a boundary the control prints the
 *  question being entered, so the reader is told the subject changed rather than discovering
 *  it from a chart that no longer matches.
 *
 *  Keyboard is `[` and `]`, bound in `useSectionNav` — arrows scroll, and a page that eats
 *  them from a reader halfway down a table has broken more than it fixed.
 */
export function SectionWalk() {
  const tree = useNavTree();
  const t = useT();
  if (!tree) return null;

  const { sections, groups, section, onSection } = tree;
  const i = sections.findIndex((s) => s.id === section);
  if (i < 0) return null;

  const prev = i > 0 ? sections[i - 1] : null;
  const next = i < sections.length - 1 ? sections[i + 1] : null;
  const groupQuestion = (id?: string) => groups.find((g) => g.id === id)?.label;

  const step = (
    dir: "prev" | "next",
    entry: typeof prev,
  ) => {
    if (!entry) {
      // Not a disabled button. An end is a fact about the sequence, and saying it is shorter
      // than a greyed control the reader has to test by clicking.
      return (
        <span className={`${css.step} ${css.end}`}>
          <span className={css.dir}>
            {t(dir === "prev" ? WALK.atStart : WALK.atEnd)}
          </span>
        </span>
      );
    }
    const crossing = entry.group !== sections[i].group ? groupQuestion(entry.group) : null;
    return (
      <button
        type="button"
        className={`${css.step} ${dir === "next" ? css.next : css.prev}`}
        onClick={() => onSection(entry.id)}
      >
        <span className={css.dir}>
          <span className={css.arrow} aria-hidden="true">{dir === "prev" ? "←" : "→"}</span>
          {t(dir === "prev" ? WALK.prev : WALK.next)}
          <kbd className={css.kbd}>{dir === "prev" ? "[" : "]"}</kbd>
        </span>
        <span className={css.label}>{t(entry.label)}</span>
        {crossing && (
          <span className={css.crossing}>
            {t(WALK.enters)} <strong>{t(crossing)}</strong>
          </span>
        )}
      </button>
    );
  };

  return (
    <nav className={css.walk} aria-label={t(WALK.aria)}>
      {step("prev", prev)}
      <span className={css.count} aria-label={`section ${i + 1} of ${sections.length}`}>
        {i + 1} <span className={css.of}>/ {sections.length}</span>
      </span>
      {step("next", next)}
    </nav>
  );
}
