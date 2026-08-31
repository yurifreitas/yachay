import { Suspense, lazy, useEffect, useState } from "react";
import { runsIndex } from "./lib/data/runsIndex";
import { NavProvider } from "./lib/nav";
import { LangProvider, useT } from "./i18n";
import { S } from "./i18n/strings";
import { DEV } from "./i18n/devices";
import { ADD } from "./i18n/addiction";
import { CRISPR } from "./i18n/crispr";
import { FIG } from "./i18n/figures";
import { DISC } from "./i18n/discovery";
import { RARE_VIEWS, viewHolding } from "./features/rare/rareViews";
import { RARE_VIEW_LABEL } from "./i18n/rareviews";
import { NavSidebar, type NavFamily, type NavView } from "./components/organisms/NavSidebar";
import { CommandPalette } from "./components/organisms/CommandPalette";

/** Lazy, and stored as a RENDER FUNCTION rather than an element below: building the
 *  element eagerly is what put all three pages in the entry chunk. A visitor who opens
 *  the explorer should not download the rare-disease dashboard to do it. */
const RunView = lazy(() => import("./features/run/RunView"));
const AddictionPage = lazy(() => import("./features/addiction/AddictionPage").then((m) => ({ default: m.AddictionPage })));
const CrisprMatrixPage = lazy(() => import("./features/crispr/CrisprMatrixPage").then((m) => ({ default: m.CrisprMatrixPage })));
const FiguresPage = lazy(() => import("./features/figures/FiguresPage").then((m) => ({ default: m.FiguresPage })));
const Docs = lazy(() => import("./features/docs/Docs"));
const RarePage = lazy(() => import("./features/rare/RarePage"));
const CancerPage = lazy(() => import("./features/cancer/CancerPage"));
const DevicesPage = lazy(() => import("./features/devices/DevicesPage"));
const DiscoveryPage = lazy(() => import("./features/discovery/DiscoveryPage"));
const GenePage = lazy(() => import("./features/gene/GenePage"));

/** THE VIEWS ARE FAMILIES NOW, not a row.
 *
 *  Four buttons in a line said the four things were alternatives of one kind. They are not:
 *  one is a screen that produced a shortlist, two are domains the method was carried into,
 *  and one is the method itself. The families say which is which before anything is clicked,
 *  and they are the level the rail groups on. */
const FAMILIES: NavFamily[] = [
  /* FOUR QUESTIONS AND A METHOD, not a shelf of subjects.
   *
   *  These were domains — "rare disease", "cancer" — and a domain is not a question. Both are
   *  enormous bodies of work spanning different fields, so naming a family after one told a
   *  reader nothing about what was inside it.
   *
   *  The third family is the correction that matters. Cancer dependencies, the CRISPR runs
   *  and the obesity screen were three separate domains; they are one problem, and it is the
   *  problem this whole repository is about — a ranking produced by a selection operator from
   *  observations that are not equally many. Filing them apart hid the only claim they share.
   *
   *  The gene stays first. People do not arrive holding a method; they arrive holding a
   *  symbol. */
  { id: "entity", label: S.famEntity, question: S.qFamEntity },
  { id: "evidence", label: S.famEvidence, question: S.qFamEvidence },
  { id: "selection", label: S.famSelection, question: S.qFamSelection },
  { id: "tech", label: DEV.famTech, question: DEV.qFamTech },
  { id: "method", label: S.famMethod, question: S.qFamMethod },
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
      family: "selection",
      render: () => <RunView runId={r.id} />,
    })),
  { id: "gene", label: S.viewGene, family: "entity",
    blurb: S.viewGeneBlurb, render: () => <GenePage /> },
  { id: "cancer", label: S.viewCancer, family: "selection",
    blurb: S.viewCancerBlurb, render: () => <CancerPage /> },
  /* FOUR ROUTES OVER ONE COMPONENT. The atlas was one entry answering four questions; the
     bands that already grouped its sections are now the views themselves, declared once in
     features/rare/rareViews.ts. */
  ...RARE_VIEWS.map((v) => ({
    id: v.id,
    label: RARE_VIEW_LABEL[v.id].label,
    blurb: RARE_VIEW_LABEL[v.id].blurb,
    family: "evidence",
    render: () => <RarePage view={v} />,
  })),
  /* THE WHOLE DEPMAP MATRIX. Every other view of this data here is a ranked table or a
     sample, and both hide the three things that are structural: the common-essential band,
     the lineage blocks, and how little of the screen is either. */
  { id: "crispr", label: CRISPR.wholeTitle, family: "selection",
    blurb: CRISPR.wholeLoading, render: () => <CrisprMatrixPage /> },
  /* SUBSTANCE USE. A domain the site had not touched, entered through the question the
     field's own headings hide: what the genetics of "alcohol" was actually measured on. */
  { id: "addiction", label: ADD.title, family: "evidence",
    blurb: ADD.blurb, render: () => <AddictionPage /> },
  { id: "obesity", label: DISC.view, family: "selection",
    blurb: DISC.viewBlurb, render: () => <DiscoveryPage /> },
  { id: "devices", label: DEV.view, family: "tech",
    blurb: DEV.viewBlurb, render: () => <DevicesPage /> },
  /* THE FIGURE INDEX. Forty-six sections labelled with questions read well and search badly:
     a reader who remembers a picture has no way back to it. This route is generated from the
     source, so it cannot drift from what is actually drawn. */
  { id: "figures", label: FIG.title, family: "method",
    blurb: FIG.sub, render: () => <FiguresPage /> },
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
    if (known) return id;
    // THE ATLAS USED TO BE ONE ROUTE. Every link anyone sent says `#rare?s=<section>`, and
    // the sections still exist — they are spread across four views now. Forwarding to the
    // view that holds the section keeps those links working; dropping them to the first view
    // would silently answer a different question than the one that was asked.
    if (id === "rare") {
      const wanted = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("s");
      const holder = wanted ? viewHolding(wanted) : null;
      return holder ?? RARE_VIEWS[0].id;
    }
    return VIEWS[0].id;
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
         blurb: hidden?.subtitle ?? "", family: "selection",
         render: () => <RunView runId={view} /> };

  useEffect(() => {
    document.title = `${t(current.label)} — yachay`;
  }, [current, t]);

  /* An unlisted run still needs a row in the rail while it is open, or the rail would show
     no current position at all — worse than showing one the reader arrived at by link. */
  const views = VIEWS.some((v) => v.id === view) ? VIEWS : [...VIEWS, current];

  return (
    <div className="app">
      <a className="skip" href="#content">{t(S.skip)}</a>

      {/* Ctrl-K from anywhere. Reaching a gene used to take four actions from any other
          page, and the people this is for look things up constantly. */}
      <CommandPalette onPick={(symbol) => { window.location.hash = `gene?g=${symbol}`; }} />

      <NavSidebar families={FAMILIES} views={views} activeView={view} onView={go} />

      <div className="column">
        <main id="content">
          <Suspense key={view} fallback={<ViewSkeleton />}>{current.render()}</Suspense>
        </main>

        {/* ATTRIBUTION ON EVERY SCREEN, not only in the repository's LICENSE. Somebody who
            screenshots a figure or reuses a number takes it from here, and a licence they
            never see is a licence they cannot follow. The author's name and link travel with
            the work. */}
        <footer>
          <p>{t(S.footer)}</p>
          <p className="attribution">
            {t(S.author)}{" "}
            <a href="https://www.linkedin.com/in/yuribzfreitas/"
               target="_blank" rel="noopener noreferrer">Yuri Bezerra Freitas</a>
            {" · "}
            <a href="https://github.com/yurifreitas/yachay/blob/main/LICENSE"
               target="_blank" rel="noopener noreferrer">{t(S.licence)}</a>
          </p>
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
