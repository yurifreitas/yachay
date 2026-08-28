import { Suspense, lazy, useEffect, useState } from "react";
import { runsIndex } from "./lib/data/runsIndex";
import { NavProvider } from "./lib/nav";
import { LangProvider, useT } from "./i18n";
import { S } from "./i18n/strings";
import { NavSidebar, type NavFamily, type NavView } from "./components/organisms/NavSidebar";

/** Lazy, and stored as a RENDER FUNCTION rather than an element below: building the
 *  element eagerly is what put all three pages in the entry chunk. A visitor who opens
 *  the explorer should not download the rare-disease dashboard to do it. */
const RunView = lazy(() => import("./features/run/RunView"));
const Docs = lazy(() => import("./features/docs/Docs"));
const RarePage = lazy(() => import("./features/rare/RarePage"));
const CancerPage = lazy(() => import("./features/cancer/CancerPage"));

/** THE VIEWS ARE FAMILIES NOW, not a row.
 *
 *  Four buttons in a line said the four things were alternatives of one kind. They are not:
 *  one is a screen that produced a shortlist, two are domains the method was carried into,
 *  and one is the method itself. The families say which is which before anything is clicked,
 *  and they are the level the rail groups on. */
const FAMILIES: NavFamily[] = [
  { id: "screens", label: S.famScreens },
  { id: "domains", label: S.famDomains },
  { id: "method", label: S.famMethod },
];

/** Views are registered here, so adding one is a single entry — the navigation, the
 *  routing and the document title all follow from this list. */
const VIEWS: (NavView & { render: () => JSX.Element })[] = [
  /* THE NF2 RUN IS NOT LISTED. Its outputs were produced before the block-shaped null was
     fixed, so the pipeline reports the stage as stale, and a stale finding on a permanent
     navigation bar is worse than an absent one. It comes back when the stage is re-run; the
     route still resolves for anyone holding the link. */
  ...runsIndex
    .filter((r) => !/nf2/i.test(r.id))
    .map((r) => ({
      id: r.id,
      label: r.title.split("—")[0].trim(),
      blurb: r.subtitle,
      family: "screens",
      render: () => <RunView runId={r.id} />,
    })),
  { id: "cancer", label: S.viewCancer, family: "domains",
    blurb: S.viewCancerBlurb, render: () => <CancerPage /> },
  { id: "rare", label: S.viewRare, family: "domains",
    blurb: S.viewRareBlurb, render: () => <RarePage /> },
  { id: "docs", label: S.viewDocs, family: "method",
    blurb: S.viewDocsBlurb, render: () => <Docs /> },
];

type ViewId = string;

/* THE THEME CONTROL IS GONE. It sat in the top-right of every page offering three options
   nobody had asked a question about, and a control that is always visible should be one people
   use. The stylesheets still define both palettes and still switch on `prefers-color-scheme`,
   so the app follows the reader's own system setting — which is the setting they already made,
   somewhere they expected to make it. */

/** Hash routing: no router dependency, and every view is linkable. */
function useHashView(): [ViewId, (v: ViewId) => void] {
  const read = (): ViewId => {
    // View state is carried after a "?" in the hash (see lib/useHashParam), so the route
    // is only the part before it.
    const id = window.location.hash.replace("#", "").split("?")[0];
    // A run hidden from the nav is still reachable by its link — hiding it from the bar is a
    // display decision, not a deletion.
    const known = VIEWS.some((v) => v.id === id) || runsIndex.some((r) => r.id === id);
    return known ? id : VIEWS[0].id;
  };
  const [view, setView] = useState<ViewId>(read);
  useEffect(() => {
    const on = () => setView(read());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const go = (v: ViewId) => {
    // Switching view drops the previous view's parameters rather than carrying them into
    // a page where they mean something else.
    window.location.hash = v;
    setView(v);
  };
  return [view, go];
}

export default function App() {
  return (
    <LangProvider>
      <NavProvider>
        <Shell />
      </NavProvider>
    </LangProvider>
  );
}

function Shell() {
  const [view, go] = useHashView();
  const t = useT();
  const hidden = runsIndex.find((r) => r.id === view && !VIEWS.some((v) => v.id === r.id));
  const current = VIEWS.find((v) => v.id === view)
    ?? { id: view, label: hidden?.title.split("—")[0].trim() ?? view,
         blurb: hidden?.subtitle ?? "", family: "screens",
         render: () => <RunView runId={view} /> };

  useEffect(() => {
    document.title = `${t(current.label)} — sieve`;
  }, [current, t]);

  /* An unlisted run still needs a row in the rail while it is open, or the rail would show
     no current position at all — worse than showing one the reader arrived at by link. */
  const views = VIEWS.some((v) => v.id === view) ? VIEWS : [...VIEWS, current];

  return (
    <div className="app">
      <a className="skip" href="#content">{t(S.skip)}</a>

      <NavSidebar families={FAMILIES} views={views} activeView={view} onView={go} />

      <div className="column">
        <main id="content">
          <Suspense key={view} fallback={<ViewSkeleton />}>{current.render()}</Suspense>
        </main>

        <footer>
          <p>{t(S.footer)}</p>
        </footer>
      </div>
    </div>
  );
}

/** Route-level loading: a reserved block, not a spinner. */
function ViewSkeleton() {
  return (
    <div className="view-skeleton" role="status" aria-live="polite">
      <span className="visually-hidden">…</span>
    </div>
  );
}
