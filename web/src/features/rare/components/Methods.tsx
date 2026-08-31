import { useT } from "../../../i18n";
import { DEEP } from "../../../i18n/deep";
import raw from "../../../data/generated/methods.json";
import css from "./MeasuredPanels.module.css";

/** Five constructs of the author's, each with the falsifier he wrote for it.
 *
 *  WHAT MAKES THIS PUBLISHABLE RATHER THAN A MANIFESTO. Every entry carries the number that
 *  would have killed it, written before any number existed — and a status saying whether that
 *  number has been computed. Two of the five are measured against a null with an interval. Two
 *  are specified and not run. One has a half that no public dataset can kill.
 *
 *  THAT LAST CATEGORY IS THE REASON THE LIST IS WORTH READING. A framework which presents its
 *  untested parts in the same voice as its tested ones is advertising, and the verdict on the
 *  untestable half is the author's own: without an operational definition of intention, the
 *  quantity "pode ser ajustado retrospectivamente para explicar qualquer coisa". A theory that
 *  survives because it cannot be tested has not survived anything, and the list says which is
 *  which rather than leaving a reader to work it out.
 */
export function Methods() {
  const tt = useT();
  const d = raw as any;
  const methods: any[] = d.methods ?? [];
  const c = d.counts ?? {};

  const STATUS: Record<string, { label: string; cls: string }> = {
    measured: { label: "measured — null and interval", cls: css.badgeKnown },
    testable_not_yet_run: { label: "specified, not run", cls: css.badgeCensored },
    no_public_falsifier: { label: "no public falsifier", cls: css.badgeCensored },
  };

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{c.measured}/{c.total}</span>
        <p>
          <span className={css.answersK}>{tt(DEEP.mtHeading)}</span>
          {d.why_the_status_field}
        </p>
      </div>

      {methods.map((m) => {
        const st = STATUS[m.status] ?? STATUS.testable_not_yet_run;
        return (
          <div key={m.id} className={css.block}>
            <span className={css.blockK}>
              {m.name} <span className={st.cls}>{st.label}</span>
            </span>
            <p className={css.blockSub}>
              <strong>{m.subtitle}</strong> — {m.statement}
            </p>

            <div className={css.pair}>
              <div className={css.stat}>
                <span className={css.statK}>
                  <strong>Nearest precedent.</strong> {m.precedent}
                </span>
              </div>
              <div className={css.stat}>
                <span className={css.statK}>
                  <strong>What is his.</strong> {m.what_is_his}
                </span>
              </div>
            </div>

            <p className={css.note}>
              <strong>How it would be measured.</strong> {m.measurement}
            </p>
            {/* The falsifier is the caveat style deliberately: it is the sentence that can end
                the idea, and it should read as the sharpest thing in the card. */}
            <p className={css.caveat}>
              <strong>What would kill it.</strong> {m.falsifier}
            </p>
            {m.result && (
              <p className={css.blockSub}>
                <strong>Result.</strong> {m.result}
                {m.measured_by && <span className={css.rowNote}> · {m.measured_by}</span>}
              </p>
            )}
            {m.blocked_on && (
              <p className={css.note}>
                <strong>Not measured because.</strong> {m.blocked_on}
              </p>
            )}
          </div>
        );
      })}

      <div className={css.block}>
        <span className={css.blockK}>{tt(DEEP.mtProvenance)}</span>
        <p className={css.note}>{d.whose}</p>
        <p className={css.caveat}>{d.governed_by}</p>
      </div>
    </div>
  );
}
