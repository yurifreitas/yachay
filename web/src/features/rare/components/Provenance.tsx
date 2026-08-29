import { useState } from "react";
import { useT } from "../../../i18n";
import { MEAS } from "../../../i18n/measured";
import css from "./MeasuredPanels.module.css";

/** THE EPISTEMIC FOOTER — provenance, method, and what the measurement does NOT say.
 *
 *  Every artefact under ADR 0007 carries four fields that the rest of this site had no way
 *  to show: `provenance` (which files were read), the method block, `says` (the limit of the
 *  claim, written by the analysis rather than by the interface), and `limits`. They are the
 *  most important text in the payload and they were rendered nowhere.
 *
 *  COLLAPSED BY DEFAULT, and that is a judgement worth stating. A reader scanning the page
 *  should meet the finding first; a reader who wants to argue with it needs every one of
 *  these fields and should not have to open a JSON file to get them. The summary line names
 *  what is inside, so the disclosure is not a mystery box.
 *
 *  It is deliberately NOT a tooltip. Provenance that vanishes when the pointer moves is
 *  provenance nobody can read on a phone, and this is the half of the page a sceptic needs.
 */
export function Provenance({
  generated, provenance, method, says, limits, governedBy,
}: {
  generated?: string;
  provenance?: string;
  method?: Record<string, unknown>;
  says?: string;
  limits?: string[];
  governedBy?: string;
}) {
  const tt = useT();
  const [open, setOpen] = useState(false);

  return (
    <div className={css.prov}>
      <button
        type="button"
        className={css.provToggle}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className={css.provChevron} data-open={open || undefined} aria-hidden>›</span>
        {tt(MEAS.prov)}
      </button>

      {open && (
        <div className={css.provBody}>
          {provenance && (
            <div className={css.provRow}>
              <span className={css.provK}>{tt(MEAS.provRead)}</span>
              <p className={css.provV}>{provenance}</p>
            </div>
          )}

          {method && (
            <div className={css.provRow}>
              <span className={css.provK}>{tt(MEAS.provMethod)}</span>
              <dl className={css.provDl}>
                {Object.entries(method).map(([k, v]) => (
                  <div key={k} className={css.provDlRow}>
                    <dt>{k.replace(/_/g, " ")}</dt>
                    <dd>{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {says && (
            <div className={css.provRow}>
              <span className={css.provK}>{tt(MEAS.provSays)}</span>
              <p className={css.provV}>{says}</p>
            </div>
          )}

          {limits && limits.length > 0 && (
            <div className={css.provRow}>
              <span className={css.provK}>{tt(MEAS.provLimits)}</span>
              <ul className={css.provList}>
                {limits.map((l) => <li key={l}>{l}</li>)}
              </ul>
            </div>
          )}

          <div className={css.provFoot}>
            {governedBy && <code>{governedBy}</code>}
            {generated && <span>{tt(MEAS.provGenerated)} {generated}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
