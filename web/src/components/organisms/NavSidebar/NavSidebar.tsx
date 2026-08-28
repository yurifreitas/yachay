import { Fragment, useEffect, useState } from "react";
import { useNavTree } from "../../../lib/nav";
import { useT } from "../../../i18n";
import { S } from "../../../i18n/strings";
import { LangSwitch } from "../../atoms/LangSwitch";
import type { NavSidebarProps } from "./NavSidebar.types";
import css from "./NavSidebar.module.css";

/** The one navigation in the application.
 *
 *  WHY A RAIL, AND WHY THREE LEVELS. The site had a flat row of four buttons at the top and
 *  then, inside three of those four, a second pair of rows nobody could see from outside.
 *  Forty-odd panels were reachable and none of them was visible until you had already chosen
 *  the page holding it: the navigation described the file layout rather than the material.
 *
 *  Vertically there is room to show all three levels at once — which view, which question,
 *  which panel — so the reader can see the whole of what this repository measured without
 *  clicking to find out what a tab contains. Horizontally there was not; that is why the old
 *  top row kept wrapping onto two lines and turning into a list to be scanned.
 *
 *  The rail knows nothing about runs, cancers or documents. Level 1 is handed to it as props
 *  and levels 2 and 3 are published by whichever page is mounted, so a new page appears in
 *  the tree without this component learning its name.
 */
export function NavSidebar({ families, views, activeView, onView }: NavSidebarProps) {
  const tree = useNavTree();
  const t = useT();

  /* ON A PHONE THE RAIL WAS A WALL.
   *
   *  Below 1100px the rail laid itself down as rows of chips: five views, then four
   *  questions, then up to sixteen panels — a full screen of navigation before a reader
   *  reached one number. On a 430px phone that is three swipes of chrome to get to the
   *  content, every time.
   *
   *  So on small screens it becomes a drawer: a 56px bar saying where you are, and the same
   *  three-level tree behind a button. Nothing is removed — the tree a phone gets is the
   *  tree a desktop gets, which is the whole reason it was worth building once. */
  const [open, setOpen] = useState(false);

  // Escape closes, and the body does not scroll behind an open drawer — a drawer whose
  // backdrop scrolls is a drawer people close by accident.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  const here = views.find((v) => v.id === activeView);
  const section = tree?.sections.find((x) => x.id === tree.section);

  return (
    <>
      {/* The mobile bar. Sticky, 56px, and it says WHERE YOU ARE rather than only offering
          a menu — a bare hamburger makes the reader open the drawer to find that out. */}
      <div className={css.bar}>
        <button type="button" className={css.burger} onClick={() => setOpen(true)}
                aria-expanded={open} aria-label={t(S.navLabel)}>
          <span className={css.burgerIcon} aria-hidden="true" />
        </button>
        <span className={css.barWhere}>
          <span className={css.barView}>{here ? t(here.label) : "yachay"}</span>
          {section && <span className={css.barSection}>{t(section.label)}</span>}
        </span>
        <button
          type="button"
          className={css.find}
          aria-label={t(S.findGene)}
          onClick={() => window.dispatchEvent(new CustomEvent("yachay:find-gene"))}
        >
          {/* A magnifier drawn rather than imported: one circle and one line is less code
              than an icon dependency, and it inherits the token colour. */}
          <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
            <circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
            <line x1="13" y1="13" x2="17" y2="17" stroke="currentColor" strokeWidth="1.8"
                  strokeLinecap="round" />
          </svg>
        </button>
        <LangSwitch />
      </div>

      {open && (
        <div className={css.scrim} onPointerDown={() => setOpen(false)} role="presentation" />
      )}

      <aside className={open ? css.railOpen : css.rail}>
      <div className={css.brand}>
        <span className={css.mark} aria-hidden="true" />
        <div>
          <h1>yachay</h1>
          <p>{t(S.tagline)}</p>
        </div>
        <button
          type="button"
          className={css.find}
          aria-label={t(S.findGene)}
          onClick={() => window.dispatchEvent(new CustomEvent("yachay:find-gene"))}
        >
          {/* A magnifier drawn rather than imported: one circle and one line is less code
              than an icon dependency, and it inherits the token colour. */}
          <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
            <circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
            <line x1="13" y1="13" x2="17" y2="17" stroke="currentColor" strokeWidth="1.8"
                  strokeLinecap="round" />
          </svg>
        </button>
        <LangSwitch />
      </div>

      <nav className={css.tree} aria-label={t(S.navLabel)}>
        {families.map((f) => {
          const inFamily = views.filter((v) => v.family === f.id);
          if (!inFamily.length) return null;
          return (
            <div key={f.id} className={css.family}>
              <span className={css.familyLabel}>{t(f.label)}</span>
              {inFamily.map((v) => {
                const on = v.id === activeView;
                return (
                  <Fragment key={v.id}>
                    <button
                      type="button"
                      className={on ? css.viewOn : css.view}
                      aria-current={on ? "page" : undefined}
                      onClick={() => { onView(v.id); setOpen(false); }}
                    >
                      {t(v.label)}
                      {/* The blurb prints only under the open view. Under all of them it is
                          a paragraph of small grey text; under one it is an answer to
                          "where am I". */}
                      {on && <span className={css.blurb}>{t(v.blurb)}</span>}
                    </button>

                    {on && tree && (
                      <div className={css.groups} role="group"
                           aria-label={`${t(S.questionsIn)} ${t(v.label)}`}>
                        {tree.groups.map((g) => {
                          const openGroup = g.id === tree.group;
                          const sections = tree.sections.filter((s) => s.group === g.id);
                          return (
                            <Fragment key={g.id}>
                              <button
                                type="button"
                                className={openGroup ? css.groupOn : css.group}
                                aria-expanded={openGroup}
                                onClick={() => tree.onGroup(g.id)}
                              >
                                <span className={css.groupLabel}>{t(g.label)}</span>
                                <span className={css.count} aria-hidden="true">{g.count}</span>
                              </button>

                              {openGroup && (
                                <>
                                  <p className={css.question}>{t(g.question)}</p>
                                  <div className={css.sections} role="tablist"
                                       aria-label={`${t(S.panelsIn)} ${t(g.label)}`}>
                                    {sections.map((s) => (
                                      <button
                                        key={s.id}
                                        type="button"
                                        role="tab"
                                        aria-selected={s.id === tree.section}
                                        className={s.id === tree.section
                                          ? css.sectionOn : css.section}
                                        onClick={() => { tree.onSection(s.id); setOpen(false); }}
                                      >
                                        <span>{t(s.label)}</span>
                                        {s.badge && <span className={css.badge}>{s.badge}</span>}
                                      </button>
                                    ))}
                                  </div>
                                </>
                              )}
                            </Fragment>
                          );
                        })}
                      </div>
                    )}
                  </Fragment>
                );
              })}
            </div>
          );
        })}
      </nav>
      </aside>
    </>
  );
}
