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

  /* OPENING A MENU MOVED THE READER.
   *
   *  Clicking a group called `onGroup`, which selects that group's FIRST section — so
   *  looking at what a question contains navigated away from the panel being read, and
   *  reaching a section two groups over cost two navigations, the first of them somewhere
   *  nobody asked to go. With six groups that was annoying; at ten it is the reason the rail
   *  stopped being usable.
   *
   *  Disclosure and position are different things, so they are different state. `peek` is
   *  which group is expanded; the tree still owns where the reader is. Expanding shows the
   *  sections and moves nothing; only a section click navigates.
   *
   *  `peek` is null until the reader opens something, and null means "follow the tree" —
   *  so arriving anywhere, by link or by the [ and ] keys, expands the group you are in
   *  without this component having to synchronise a copy of it. */
  /* EVERY GROUP OPEN, ALL THE TIME.
   *
   *  The rail was an accordion: one group expanded, the other ten collapsed to a label and a
   *  count. That hides the thing a reader came to the rail FOR. A count says a group holds
   *  four panels; it does not say that one of them is the language coverage and another is
   *  the attention bias, so finding a panel meant opening groups one at a time and reading
   *  what fell out. Thirty-two panels behind eleven doors is a worse map than thirty-two
   *  labels in a column, because a column can be scanned in one pass and doors cannot.
   *
   *  So the whole tree is drawn. The rail scrolls, which it already did, and the density is
   *  paid for in the CSS: the section rows lost their padding and the questions moved out of
   *  the always-on path — a paragraph under each of eleven groups is what would actually
   *  make this unreadable, so the question prints only under the group the reader is in.
   *
   *  `collapsed` exists for a reader who wants a shorter rail; nothing starts in it. */
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const toggle = (id: string) => setCollapsed((prev) => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

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
          const familyIsHere = inFamily.some((v) => v.id === activeView);
          return (
            <div key={f.id} className={css.family}>
              <span className={css.familyLabel}>{t(f.label)}</span>
              {/* The question prints under the family the reader is standing in — the same
                  rule the groups follow, for the same reason: six at once is a paragraph of
                  grey text nobody reads, one is an answer to "am I in the right place". */}
              {familyIsHere && f.question && (
                <p className={css.familyQ}>{t(f.question)}</p>
              )}
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
                          const openGroup = !collapsed.has(g.id);
                          // The group the reader is actually IN, which may not be the one
                          // they are peeking at. Marked, so peeking never loses the anchor.
                          const isHere = g.id === tree.group;
                          const sections = tree.sections.filter((s) => s.group === g.id);
                          return (
                            <Fragment key={g.id}>
                              <button
                                type="button"
                                className={isHere ? css.groupOn : openGroup ? css.groupPeek : css.group}
                                aria-expanded={openGroup}
                                onClick={() => toggle(g.id)}
                              >
                                <span className={openGroup ? css.caret : `${css.caret} ${css.caretOff}`}
                                      aria-hidden="true">▾</span>
                                <span className={css.groupLabel}>{t(g.label)}</span>
                                <span className={css.count} aria-hidden="true">{g.count}</span>
                              </button>

                              {openGroup && (
                                <>
                                  {/* Eleven questions at once is a wall of grey prose. The
                                      one you are standing in is context; the other ten are
                                      noise until you are standing in them. */}
                                  {isHere && <p className={css.question}>{t(g.question)}</p>}
                                  {/* A LIST, NOT A TABLIST — and this one is the clearest
                                      case of the seven. These buttons change the whole page
                                      beneath the rail; a tab swaps a labelled panel that
                                      keeps its place in the reading order. Declaring
                                      `role="tab"` with no `tabpanel` anywhere told a screen
                                      reader "tab, 4 of 8" and offered a panel that does not
                                      exist. A navigation list with `aria-current` says the
                                      true thing: these are destinations, and this is the one
                                      you are at. */}
                                  <ul className={css.sections}
                                      aria-label={`${t(S.panelsIn)} ${t(g.label)}`}>
                                    {sections.map((s) => (
                                      <li key={s.id}>
                                      <button
                                        type="button"
                                        aria-current={s.id === tree.section ? "true" : undefined}
                                        className={s.id === tree.section
                                          ? css.sectionOn : css.section}
                                        onClick={() => { tree.onSection(s.id); setOpen(false); }}
                                      >
                                        <span>{t(s.label)}</span>
                                        {s.badge && <span className={css.badge}>{s.badge}</span>}
                                      </button>
                                      </li>
                                    ))}
                                  </ul>
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
