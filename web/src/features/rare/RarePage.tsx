/** The rare-disease atlas — a page whose subject is what is NOT known.
 *
 *  It exists because the fit assessment in `docs/references/broad-institute-fit.md` kept
 *  running into the same wall: the shape of a rare-disease problem is not "rank these
 *  candidates" but "most of the fields are empty, and the emptiness is patterned". A
 *  dashboard that renders empty fields as blanks under-reports that, so here every gap is
 *  a typed value with its own mark.
 *
 *  Composition only: the page picks the data, holds the two pieces of view state, and
 *  hands slots to organisms. Nothing below an organism knows what a disease is.
 */
import { Suspense, useEffect, useMemo, useState } from "react";
import { lexicon } from "./data/lexicon";
import { atlas } from "./data/atlas";
import { nongeneMeasured } from "./data/nongeneMeasured";
import { sortDiseases, type SortKey } from "./model";



import { renderSection } from "../../lib/sectionRegistry";
import { RARE_SECTIONS } from "./rareSections";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { SectionWalk } from "../../components/molecules/SectionWalk";
import { useSectionNav } from "../../lib/nav";
import type { RareView } from "./rareViews";
import { useT } from "../../i18n";


import css from "./RarePage.module.css";

/** Sections are mutually exclusive, so they are the natural code-split boundary: the
 *  network, the charts and the capability tables are not downloaded until the reader
 *  opens the question that needs them. Each is named so the chunk is legible in a build
 *  report rather than appearing as a hash. */



















// The ADR 0007 layer. Lazy like the rest: a reader who never opens the group pays nothing.
// Prefetch the solved layouts the moment a reader shows intent toward this group, so the
// 46 kB is in flight before the section mounts rather than after. Fire-and-forget: the views
// render a shaped skeleton if it has not landed.
const prefetchMeasured = () => {
  import("./components/HyperViews").then((m) => m.prefetchViewModels()).catch(() => {});
};








/** TWO LEVELS, BECAUSE THIRTEEN FLAT TABS STOPPED BEING A MAP.
 *
 *  The nav wrapped onto two lines and turned into a list to be scanned rather than a set of
 *  questions to be chosen between, and nothing announced what was inside a tab before it was
 *  clicked. So the sections are grouped by the QUESTION they answer, the group row states
 *  those questions and how many sections each holds, and the section row underneath is short
 *  enough to read in one pass.
 *
 *  The order inside a group is still a workflow and not a table of contents: look at one
 *  disease, then at what stops it, then at what it would physically take.
 *
 *  Both levels are URL state, so every view in the dashboard is a link someone can send.
 */




/** ONE COMPONENT, FOUR ROUTES.
 *
 *  The atlas was a single page of forty sections answering four different questions, so a
 *  reader arriving for one of them scrolled past three. The bands over the groups were
 *  already the seam — they named the KIND of question a run of groups answers — so each band
 *  is now a view of its own, declared once in `rareViews.ts`.
 *
 *  The body is unchanged and shared: same registry, same hero, same walker. What differs per
 *  route is which sections the rail offers, which is data rather than markup. */
export default function RarePage({ view }: { view: RareView }) {
  const [sort, setSort] = useState<SortKey>("gaps");
  const [selected, setSelected] = useState<string | null>(null);
  // Both nav levels live in the URL and are drawn by the rail, not by this page.
  const tt = useT();
  const { section } = useSectionNav({
    owner: view.id, groups: view.groups, sections: view.sections, initial: view.initial,
  });

  // Intent, not arrival: the moment the reader is inside the measured group, the solved
  // layouts start loading. Idempotent, so re-renders cost nothing and two sections racing
  // share one request.
  useEffect(() => {
    // DERIVED, NOT LISTED. This was a hand-written array of four ids, and four sections were
    // added to the group the same day without touching it — the same list-drifts-from-the-
    // thing failure ADR 0009 exists to stop, one file away from where it was stopped.
    // The solved layouts back four panels — scale, language, conflict and shape — which now
    // sit in three different groups. Named by the groups that contain them rather than by a
    // list of section ids, because a list of ids is the thing that went stale last time.
    const g = view.sections.find((s) => s.id === section)?.group;
    if (g === "measured" || g === "register" || g === "knownshape") prefetchMeasured();
  }, [section]);

  const ordered = useMemo(
    () => sortDiseases(lexicon, lexicon.diseases, sort),
    [sort]
  );
  const focus = ordered.find((d) => d.name === selected) ?? ordered[0];

  /** The section a bare link opens on. Only there does the reader need the introduction. */
  // The full hero belongs on the first panel of the first view only; every other route
  // is somewhere a reader arrived deliberately.
  const entry = view.id === "catalogue" && section === "world";

  // The lexicon is a build artifact and can legitimately be missing. Say so, and say how
  // to produce it, rather than rendering an atlas of nothing.
  if (!lexicon.diseases.length) {
    return (
      <section className={css.page}>
        <div className={css.empty}>
          <span className={css.emptyTitle}>No lexicon has been generated yet</span>
          <p className={css.sub}>
            The atlas reads a build artifact. Generate it, then rebuild the explorer's data.
          </p>
          <code className={css.emptyHint}>python tools/rare_disease_seed.py</code>
        </div>
      </section>
    );
  }

  return (
    <section className={css.page}>
      {/* THE SAME 700 PIXELS, TWENTY-NINE TIMES.
          The headline, the lede and the four counters are how a reader is introduced to the
          atlas — and they sat above every one of the twenty-nine panels, so a reader who
          changed section scrolled past the whole introduction again to reach the thing they
          had just asked for. An introduction repeated on arrival is an introduction; repeated
          on the twelfth panel it is an obstacle.

          So it is full on the section a bare link opens, and a strip everywhere else. Derived
          from the section rather than stored, so it cannot disagree with where the reader is,
          and a deep link to a panel opens with the panel near the top where it belongs. The
          counters survive the collapse, in place and in order — nothing appears from nowhere
          when the reader walks back. */}
      <header className={entry ? css.hero : `${css.hero} ${css.heroLean}`}>
        <div className={css.heroTop}>
        <div className={css.heroText}>
          <p className={css.eyebrow}>Rare and ultra-rare disease · decision support</p>
          <h2 className={css.title}>Most of what there is to know about a rare disease is a field nobody has filled in</h2>
        </div>
        <div className={css.heroSide}>
          <p className={css.lede}>
            The join across HPO, Orphanet and the Human Protein Atlas reaches{" "}
            <strong>{atlas.scale.diseases.toLocaleString("en-US")}</strong> catalogue entries
            — more than the <strong>7,000–8,000</strong> distinct diseases usually quoted,
            because OMIM, Orphanet and DECIPHER each describe the same conditions at
            different grain. The counters are measured on that join, not asserted: each one
            is a place the data stops.
          </p>
        </div>
        </div>
        {/* MEASURED ON THE ATLAS, NOT ON THE SEED. These counters used to read "3 of 12" —
            the denominators of the twelve-disease demonstration lexicon — under a headline
            that speaks for the whole field. The seed is still on the page and still labelled
            as a demonstration; it just no longer supplies the hero's statistics.
            "No approved therapy" is gone rather than rescaled: none of the ingested sources
            records approved therapies, so there was no honest denominator at any size. */}
        <div className={css.counters}>
          <Counter n={atlas.scale.diseases - atlas.scale.diseasesWithGene}
                   of={atlas.scale.diseases} label="no causal gene found" tone="unknown" />
          <Counter n={atlas.scale.diseases - atlas.scale.diseasesPlaceableOnCellAxis}
                   of={atlas.scale.diseases} label="cannot be placed on the cell axis" tone="unknown" />
          <Counter n={atlas.scale.ultraRare - atlas.scale.ultraRareWithGene}
                   of={atlas.scale.ultraRare} label="ultra-rare, and no gene" tone="absent" />
          <Counter n={nongeneMeasured.geneLessBreakdown.withNoInheritanceAnnotation}
                   of={nongeneMeasured.geneLessBreakdown.total}
                   label="gene-less, and no inheritance recorded either" tone="unknown" />
        </div>
      </header>

      <SectionHeading />

      <Suspense key={section} fallback={<SectionSkeleton />}>

      {/* ONE CALL. The twenty-five branches that were here are declared in rareSections.tsx.
          A nav array and a render chain are two lists nothing connects, and when they drift
          the reader gets a blank panel with no error to report — ADR 0009. */}
      {renderSection(RARE_SECTIONS, section,
        { tt, lexicon, ordered, focus, sort, setSort, setSelected }, {
          className: css.block, headingClass: css.h3, subClass: css.sub,
          fallback: <SectionSkeleton />,
        })}
      </Suspense>

      {/* The order these sections are declared in is an argument, and until now the only way
          to follow it was to hunt the next label in the rail by name. */}
      <SectionWalk />
    </section>
  );
}

function Counter({
  n, of, label, tone,
}: { n: number; of: number; label: string; tone: "unknown" | "absent" }) {
  const share = of ? n / of : 0;
  return (
    <article className={css.counter}>
      <span className={css.counterL}>{label}</span>
      <div className={css.counterRow}>
        <span className={css.counterN}>{n.toLocaleString("en-US")}</span>
        <span className={`${css.counterShare} ${tone === "unknown" ? css.shareUnknown : css.shareAbsent}`}>
          {Math.round(share * 100)}% of {of.toLocaleString("en-US")}
        </span>
      </div>
      <span className={css.counterBar}>
        <span
          className={`${css.counterFill} ${tone === "unknown" ? css.fillUnknown : ""}`}
          style={{ width: `${Math.round(share * 100)}%` }}
        />
      </span>
    </article>
  );
}

/** Loading state with the shape of the content, not a spinner in the middle of nothing.
 *  The height is reserved so arriving content does not shove the page. */
function SectionSkeleton() {
  return (
    <div className={css.skeleton} role="status" aria-live="polite">
      <span className={css.srOnly}>Loading this section</span>
      <div className={css.skelBar} style={{ width: "38%" }} />
      <div className={css.skelBar} style={{ width: "62%" }} />
      <div className={css.skelPanel} />
    </div>
  );
}
