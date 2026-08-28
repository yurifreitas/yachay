import { LANGS, useLang, useT } from "../../../i18n";
import { S } from "../../../i18n/strings";
import css from "./LangSwitch.module.css";

/** Two buttons, not a dropdown.
 *
 *  There are exactly two languages, so a select would hide one behind a click and a chevron
 *  to save eleven pixels. The current choice is shown pressed rather than merely coloured,
 *  because a reader who cannot tell which of two states is active has been given a toggle
 *  with no state.
 */
export function LangSwitch() {
  const { lang, setLang } = useLang();
  const t = useT();
  return (
    <div className={css.wrap} role="group" aria-label={t(S.language)}>
      {LANGS.map((l) => (
        <button
          key={l.id}
          type="button"
          className={l.id === lang ? css.on : css.off}
          aria-pressed={l.id === lang}
          // The long name is what a screen reader says; the two letters are what the eye
          // needs. "EN" read aloud is a spelling, not a language.
          aria-label={l.long}
          lang={l.id === "pt" ? "pt-BR" : "en"}
          onClick={() => setLang(l.id)}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
