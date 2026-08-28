import { createContext, useCallback, useContext, useEffect, useMemo, useState,
         type ReactNode } from "react";
import type { Lang, Text } from "./types";

/** The reader's language, chosen once and carried everywhere.
 *
 *  WHERE IT LIVES, IN ORDER OF AUTHORITY:
 *    1. `?lang=` in the URL hash — so a link carries the language it was read in. Someone
 *       sending a colleague a figure should not send them the other language.
 *    2. `localStorage` — the choice, remembered on this browser.
 *    3. `navigator.language` — a Portuguese browser opens in Portuguese without asking.
 *    4. English.
 *
 *  Every one of those can throw or be absent (a private window blocks storage, a headless
 *  render has no navigator), so each is attempted and none is required.
 */

type Ctx = { lang: Lang; setLang: (l: Lang) => void };
const LangCtx = createContext<Ctx>({ lang: "en", setLang: () => {} });

const KEY = "sieve.lang";
const valid = (v: unknown): v is Lang => v === "en" || v === "pt";

function readParam(): Lang | null {
  const q = window.location.hash.split("?")[1] ?? "";
  const v = new URLSearchParams(q).get("lang");
  return valid(v) ? v : null;
}

function initial(): Lang {
  try {
    const fromUrl = readParam();
    if (fromUrl) return fromUrl;
    const stored = window.localStorage.getItem(KEY);
    if (valid(stored)) return stored;
  } catch {
    // A browser set to block site data throws on read. Not a reason to fail to render.
  }
  try {
    if (navigator.language?.toLowerCase().startsWith("pt")) return "pt";
  } catch {
    /* no navigator */
  }
  return "en";
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initial);

  // The language is a document-level fact, not a component-level one: `lang` on <html> is
  // what a screen reader switches voice on and what a browser offers to translate.
  useEffect(() => {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  }, [lang]);

  useEffect(() => {
    const on = () => {
      const fromUrl = readParam();
      if (fromUrl && fromUrl !== lang) setLangState(fromUrl);
    };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try { window.localStorage.setItem(KEY, next); } catch { /* blocked, and fine */ }
    // Written into the hash so the current view stays linkable IN THIS LANGUAGE.
    const [view, q = ""] = window.location.hash.replace("#", "").split("?");
    const params = new URLSearchParams(q);
    // English is the default, so it is absent from the URL rather than stated — a link
    // should carry a choice, not a restatement of the default.
    if (next === "en") params.delete("lang");
    else params.set("lang", next);
    const qs = params.toString();
    window.location.hash = qs ? `${view}?${qs}` : view;
  }, []);

  const value = useMemo(() => ({ lang, setLang }), [lang, setLang]);
  return <LangCtx.Provider value={value}>{children}</LangCtx.Provider>;
}

export function useLang(): Ctx {
  return useContext(LangCtx);
}

/** Resolve a bilingual string. The whole API surface for text: `const t = useT(); t(S.title)`.
 *
 *  Deliberately NOT a key lookup like `t("nav.title")`. A key indirection means a typo
 *  renders a raw key to the reader and compiles fine; a `Bi` object means a missing
 *  translation is a type error at the point it is missing.
 *  A bare string passes through, which is how data-derived text (a gene symbol, a
 *  catalogue's own disease name) reaches the page without being pretend-translated.
 */
export function useT(): (s: Text) => string {
  const { lang } = useLang();
  return useCallback(
    (s: Text) => (typeof s === "string" ? s : s[lang] ?? s.en),
    [lang],
  );
}
