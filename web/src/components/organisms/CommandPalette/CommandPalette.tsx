import { useEffect, useMemo, useRef, useState } from "react";
import { useRemoteData } from "../../../lib/useRemoteData";
import { useT } from "../../../i18n";
import { CMD } from "../../../i18n/command";
import { fmtInt } from "../../../lib/scale";
import css from "./CommandPalette.module.css";

/** Ctrl-K, from anywhere on the site.
 *
 *  WHY. Reaching a gene took four actions from any other page: find the rail, find the gene
 *  navigator, find the search field, type. That is a navigation cost paid on every lookup,
 *  and the people this site is for look things up constantly — a curator checks fifty
 *  symbols in an afternoon.
 *
 *  KEYBOARD FIRST, AND THAT IS THE POINT. The search field on the gene page was mouse-only:
 *  a reader could type but not choose without reaching for the pointer. Here the arrows move,
 *  Enter opens, Escape closes, and the active row is scrolled into view — which is the part
 *  most hand-rolled palettes forget, so the selection walks off the bottom of the list and
 *  the reader is choosing something they cannot see.
 *
 *  IT LOADS ONLY THE INDEX. 186 kB of symbols and one integer each, fetched once and shared
 *  with the gene page through the browser cache — never the 41 MB of records.
 */

type SearchIndex = { genes: Record<string, number>; scope: { genes: number } };

const LAYERS = 7;

export function CommandPalette({ onPick }: { onPick: (symbol: string) => void }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Only fetched once the palette has been opened. A reader who never presses the shortcut
  // never pays for it.
  const [armed, setArmed] = useState(false);
  const idx = useRemoteData<SearchIndex>(armed ? "data/gene/idx.json" : "");

  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setArmed(true);
        setOpen((v) => !v);
        return;
      }
      // "/" is the other convention, and it must not fire while someone is typing into a
      // field somewhere else on the page.
      const el = document.activeElement;
      const typing = el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement;
      if (e.key === "/" && !typing && !mod) {
        e.preventDefault();
        setArmed(true);
        setOpen(true);
      }
    };
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  }, []);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    /* FOCUS, AND THEN CHECK. One requestAnimationFrame was not enough: the palette opened
       without the caret in it, so the shortcut delivered a box the reader still had to
       click — which is the whole cost the shortcut exists to remove.
       Two attempts, a frame apart, and the second only runs if the first did not take. */
    const grab = () => inputRef.current?.focus({ preventScroll: true });
    grab();
    const frame = requestAnimationFrame(() => {
      if (document.activeElement !== inputRef.current) grab();
    });
    return () => cancelAnimationFrame(frame);
  }, [open]);

  const symbols = useMemo(
    () => (idx.state === "ready" ? Object.keys(idx.data.genes) : []),
    [idx],
  );

  const matches = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (!q) return [];
    const exact: string[] = [];
    const prefix: string[] = [];
    const inside: string[] = [];
    for (const s of symbols) {
      if (s === q) exact.push(s);
      else if (s.startsWith(q)) prefix.push(s);
      else if (s.includes(q)) inside.push(s);
      if (exact.length + prefix.length >= 30 && q.length > 2) break;
    }
    return [...exact, ...prefix, ...inside].slice(0, 30);
  }, [symbols, query]);

  useEffect(() => setActive(0), [query]);

  // The row must be visible, not merely selected. A palette whose selection walks off the
  // bottom is asking the reader to choose something they cannot see.
  useEffect(() => {
    const el = listRef.current?.children[active] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [active]);

  if (!open) return null;

  const choose = (symbol: string) => {
    onPick(symbol);
    setOpen(false);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { setOpen(false); return; }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && matches[active]) {
      e.preventDefault();
      choose(matches[active]);
    }
  };

  return (
    <div className={css.veil} onPointerDown={() => setOpen(false)} role="presentation">
      <div
        className={css.panel}
        role="dialog"
        aria-modal="true"
        aria-label={t(CMD.label)}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          className={css.input}
          type="text"
          value={query}
          placeholder={t(CMD.placeholder)}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKey}
          autoComplete="off"
          spellCheck={false}
          // eslint-disable-next-line jsx-a11y/no-autofocus -- a dialog the reader opened on
          // purpose, with a single field: focusing anything else would be the surprise.
          autoFocus
          aria-controls="cmd-results"
          aria-activedescendant={matches[active] ? `cmd-${matches[active]}` : undefined}
        />

        {idx.state === "loading" && <p className={css.hint}>{t(CMD.loading)}</p>}

        {idx.state === "ready" && (
          <>
            <ul className={css.list} id="cmd-results" role="listbox" ref={listRef}>
              {matches.map((s, i) => (
                <li
                  key={s}
                  id={`cmd-${s}`}
                  role="option"
                  aria-selected={i === active}
                  className={i === active ? css.rowOn : css.row}
                  onPointerEnter={() => setActive(i)}
                  onPointerDown={() => choose(s)}
                >
                  <span className={css.sym}>{s}</span>
                  <span className={css.pips} aria-hidden="true">
                    {Array.from({ length: LAYERS }, (_, k) => (
                      <i key={k} className={k < (idx.data.genes[s] ?? 0) ? css.pipOn : css.pip} />
                    ))}
                  </span>
                </li>
              ))}
            </ul>

            <p className={css.foot}>
              {query.trim()
                ? `${matches.length}${matches.length === 30 ? "+" : ""} ${t(CMD.results)}`
                : `${fmtInt(idx.data.scope.genes)} ${t(CMD.indexed)}`}
              <span className={css.keys}>
                <kbd>↑</kbd><kbd>↓</kbd> {t(CMD.move)} · <kbd>↵</kbd> {t(CMD.open)} ·{" "}
                <kbd>esc</kbd> {t(CMD.close)}
              </span>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
