/** The two languages this site is published in.
 *
 *  WHY BILINGUAL AND NOT TRANSLATED. The repository's own documentation standard
 *  (`.claude/skills/sieve-doc` §7) says repository prose is English — the audience for a
 *  methods repository is international and the bibliography it argues with is in English.
 *  The site's audience is not the same audience. Publishing one language would either put
 *  the method out of reach of Portuguese readers or put the argument out of step with the
 *  papers it cites. So both, from one source, with the choice in the URL and in the
 *  reader's browser.
 */
export type Lang = "en" | "pt";

/** A string that exists in both languages. Nothing may be added in one and not the other:
 *  the type is what stops a half-translated release from compiling. */
export type Bi = Record<Lang, string>;

/** Either a translated pair or a bare string.
 *
 *  The bare-string case is not laziness — it is for text that comes from the DATA rather
 *  than from this application: a run's title, a gene symbol, a disease name written by
 *  Orphanet. Those have one form, and inventing a Portuguese translation of a catalogue's
 *  own label would be fabricating a record. `t()` passes them through untouched. */
export type Text = string | Bi;

export const LANGS: { id: Lang; label: string; long: string }[] = [
  { id: "en", label: "EN", long: "English" },
  { id: "pt", label: "PT", long: "Português" },
];

/** Substitute `{name}` placeholders in a resolved string.
 *
 *  Interpolation has to survive translation, and the two languages do not put the numbers in
 *  the same place — "90th percentile 5, largest 254" against "percentil 90 5, maior 254", and
 *  worse where a clause order flips. Concatenating fragments would force one language's word
 *  order onto the other; a named placeholder lets each sentence put the value where its own
 *  grammar wants it.
 */
export function fill(s: string, vars: Record<string, string | number>): string {
  return s.replace(/\{(\w+)\}/g, (m, k) =>
    k in vars ? String(vars[k]) : m);
}
