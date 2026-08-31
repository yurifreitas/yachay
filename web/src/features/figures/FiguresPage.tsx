import { useMemo, useState } from "react";
import { useT } from "../../i18n";
import { FIG } from "../../i18n/figures";
import index from "../../data/generated/figure_index.json";
import css from "./FiguresPage.module.css";

/** An index of every figure on the site, by form.
 *
 *  WHY THIS EXISTS. Forty-six sections across five families, four levels deep, labelled with
 *  questions — "Quanto vale um z aqui?", "Os grupos são reais?". A question is the right label
 *  for a section and the wrong one for finding a picture. A reader who remembers seeing a
 *  reordered matrix, or who wants to know whether this site has an alluvial anywhere, had no
 *  way in but to open sections until one appeared.
 *
 *  IT IS GENERATED, NOT WRITTEN. `web/scripts/build-figure-index.mjs` scans the feature source
 *  for uses of the viz organisms and reads each one's `ariaLabel` — which by construction is a
 *  sentence saying what the figure shows. A figure added without touching anything here
 *  appears; one deleted leaves. A hand-maintained index of forty-six sections is an index that
 *  is wrong within a week, which is the failure `tools/index_check.py` exists to catch in
 *  prose.
 *
 *  AND IT SAYS WHAT IT CANNOT SEE. Thirty-four marks on this site are drawn with CSS bars
 *  rather than a viz organism, and they are counted here without being listed. An index
 *  claiming to be complete while missing a third of the pictures would be worse than none.
 */
export function FiguresPage() {
  const tt = useT();
  const d = index as any;
  const all: any[] = d.figures ?? [];
  const [form, setForm] = useState<string>("all");
  const [q, setQ] = useState("");

  const forms = useMemo(
    () => Object.entries(d.by_form ?? {}).sort((a: any, b: any) => b[1] - a[1]),
    [d],
  );

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return all.filter((f) => {
      if (form !== "all" && f.form !== form) return false;
      if (!needle) return true;
      return [f.form, f.label, f.answers, f.section, f.area, f.component]
        .filter(Boolean)
        .some((s: string) => s.toLowerCase().includes(needle));
    });
  }, [all, form, q]);

  return (
    <div className={css.page}>
      <header className={css.head}>
        <h1>{tt(FIG.title)}</h1>
        <p className={css.sub}>{tt(FIG.sub)}</p>
        <p className={css.counts}>
          {d.counts?.indexed} {tt(FIG.indexed)} · {d.counts?.forms} {tt(FIG.forms)} ·{" "}
          {d.counts?.on_a_page_rather_than_in_a_section} {tt(FIG.onOwnPage)} ·{" "}
          {d.counts?.css_marks_not_indexed} {tt(FIG.cssNotIndexed)}
        </p>
      </header>

      <div className={css.controls}>
        <input
          type="search"
          className={css.search}
          placeholder={tt(FIG.searchPlaceholder)}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label={tt(FIG.searchPlaceholder)}
        />
        {/* Form is a filter, not a tab strip: the counts are what tell a reader which forms
            this site actually uses, and a tab that hides its own size is a tab that gets
            clicked once. */}
        <div className={css.forms} role="group" aria-label={tt(FIG.byForm)}>
          <button
            className={form === "all" ? css.formOn : css.form}
            onClick={() => setForm("all")}
          >
            {tt(FIG.allForms)} <span className={css.n}>{all.length}</span>
          </button>
          {forms.map(([name, n]: any) => (
            <button
              key={name}
              className={form === name ? css.formOn : css.form}
              onClick={() => setForm(name)}
            >
              {name} <span className={css.n}>{n}</span>
            </button>
          ))}
        </div>
      </div>

      <ul className={css.list}>
        {shown.map((f, i) => (
          <li key={`${f.component}-${f.form}-${i}`} className={css.item}>
            <div className={css.itemHead}>
              <span className={css.formTag}>{f.form}</span>
              {/* A figure lives either in a section of a multi-section area, or on a route
                  of its own. Both are linkable and they are linked differently; a figure that
                  is neither says so rather than being pointed somewhere plausible. */}
              {f.section ? (
                <a className={css.go} href={`#${f.area ?? "rare"}?s=${f.section}`}>
                  {tt(FIG.open)}
                </a>
              ) : f.route ? (
                <a className={css.go} href={`#${f.route}`}>{tt(FIG.open)}</a>
              ) : (
                <span className={css.unplaced}>{tt(FIG.unplaced)}</span>
              )}
            </div>
            <p className={css.label}>{f.label ?? tt(FIG.noLabel)}</p>
            <p className={css.answers}>{f.answers}</p>
            {f.source && <p className={css.source}>{f.source}</p>}
          </li>
        ))}
      </ul>

      {!shown.length && <p className={css.empty}>{tt(FIG.none)}</p>}

      <p className={css.note}>{d.says}</p>
    </div>
  );
}
