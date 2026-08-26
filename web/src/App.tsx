import { useEffect, useState } from "react";
import RunView from "./features/run/RunView";
import Docs from "./features/docs/Docs";
import { runs } from "./lib/data";

/** Views are registered here, so adding one is a single entry — the navigation, the
 *  routing and the document title all follow from this list. */
const VIEWS = [
  ...runs.map((r) => ({ id: r.id, label: r.title.split("—")[0].trim(), el: <RunView run={r} /> })),
  { id: "docs", label: "Method", el: <Docs /> },
];

type ViewId = string;

function useTheme() {
  const [theme, setTheme] = useState<"system" | "light" | "dark">("system");
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
  }, [theme]);
  return { theme, setTheme };
}

/** Hash routing: no router dependency, and every view is linkable. */
function useHashView(): [ViewId, (v: ViewId) => void] {
  const read = (): ViewId => {
    const id = window.location.hash.replace("#", "");
    return VIEWS.some((v) => v.id === id) ? id : VIEWS[0].id;
  };
  const [view, setView] = useState<ViewId>(read);
  useEffect(() => {
    const on = () => setView(read());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const go = (v: ViewId) => {
    window.location.hash = v;
    setView(v);
  };
  return [view, go];
}

export default function App() {
  const [view, go] = useHashView();
  const { theme, setTheme } = useTheme();
  const current = VIEWS.find((v) => v.id === view)!;

  useEffect(() => {
    document.title = `${current.label} — sieve`;
  }, [current]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="mark" aria-hidden="true" />
          <div>
            <h1>sieve</h1>
            <p>screen &rarr; defensible shortlist</p>
          </div>
        </div>

        <nav aria-label="Views">
          {VIEWS.map((v) => (
            <button
              key={v.id}
              className={v.id === view ? "active" : ""}
              aria-current={v.id === view ? "page" : undefined}
              onClick={() => go(v.id)}
            >
              {v.label}
            </button>
          ))}
        </nav>

        <label className="theme">
          <span className="visually-hidden">Theme</span>
          <select value={theme} onChange={(e) => setTheme(e.target.value as typeof theme)}>
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </header>

      <main>{current.el}</main>

      <footer>
        <p>
          Adapter-driven: every number and document comes from a manifest written by an
          analysis run, converted by <code>npm run data</code>. A new adapter appears here
          without the UI knowing its name, and nothing in this app is hand-typed.
        </p>
      </footer>
    </div>
  );
}
