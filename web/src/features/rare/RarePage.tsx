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
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { RARE } from "../../i18n/strings";
import { TROP } from "../../i18n/tropical";
import { MEAS } from "../../i18n/measured";
import { MORE } from "../../i18n/more";
import { DEEP } from "../../i18n/deep";
import { SAMP } from "../../i18n/sampled";
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
const GROUPS: NavGroupDef[] = [
  { id: "known", label: RARE.gKnown, question: RARE.qKnown },
  { id: "naming", label: RARE.gNaming, question: RARE.qNaming },
  { id: "cause", label: RARE.gCause, question: RARE.qCause },
  { id: "case", label: RARE.gCase, question: RARE.qCase },
  { id: "decide", label: RARE.gDecide, question: RARE.qDecide },
  { id: "measured", label: MEAS.group, question: MEAS.question },
  { id: "register", label: MEAS.gRegister, question: MEAS.qRegister },
  { id: "knownshape", label: MEAS.gShape, question: MEAS.qShape },
  { id: "converge", label: MEAS.gConverge, question: MEAS.qConverge },
  { id: "sampled", label: SAMP.group, question: SAMP.question },
  { id: "beyond", label: DEEP.gBeyond, question: DEEP.qBeyond },
  { id: "argument", label: RARE.gArgument, question: RARE.qArgument },
];

const SECTIONS: NavSectionDef[] = [
  // 1. The catalogue, and what its numbers are really measuring. First, because a reader who
  //    meets one disease before meeting the denominator has no way to weigh it.
  { id: "world", label: RARE.sWorld, group: "known" },
  { id: "bias", label: RARE.sBias, group: "known" },
  { id: "population", label: RARE.sPopulation, group: "known" },
  { id: "patients", label: RARE.sPatients, group: "known" },
  { id: "names", label: RARE.sNames, group: "naming" },
  { id: "atlas", label: RARE.sAtlas, group: "naming" },
  { id: "gaps", label: RARE.sGaps, group: "naming" },
  { id: "tropical", label: TROP.section, group: "naming" },

  // 2. What a disease is OF — the ladder's middle rungs, in order of scale.
  { id: "cell", label: RARE.sCell, group: "cause" },
  { id: "network", label: RARE.sNetwork, group: "cause" },
  { id: "sparse", label: RARE.sSparse, group: "cause" },
  { id: "nongene", label: RARE.sNongene, group: "cause" },
  { id: "twin", label: DEEP.sTwin, group: "cause" },

  // 3. One record in full, then the physics and the payroll a therapy would need.
  { id: "disease", label: RARE.sDisease, group: "case" },
  { id: "capability", label: RARE.sCapability, group: "case" },

  // 4. Deciding: what the evidence carries, then choosing under constraint.
  { id: "evidence", label: RARE.sEvidence, group: "decide" },
  { id: "choose", label: RARE.sChoose, group: "decide" },
  { id: "dims", label: RARE.sDims, group: "decide" },
  { id: "genopheno", label: DEEP.sGeno, group: "decide" },

  // 5. What was measured under ADR 0007 — eight results, each with a null and an interval,
  //    and one of them negative. These carry a governing decision record the catalogue layers
  //    do not, and a reader is entitled to know which is which.
  //
  //    THEY ARE FOUR QUESTIONS, NOT ONE. Held under a single heading they were a list of
  //    eight labels whose only shared property was the ADR that governs them. What a coarser
  //    alphabet costs, what biases the register, what shape the known region has, and where
  //    many disorders meet are four different questions with four different answers, and the
  //    rail is where a reader is supposed to be able to see that before clicking.
  //
  //    Contiguous by group, deliberately: the walker steps through this array in order, so a
  //    sequence that zig-zags between groups would announce a boundary crossing every step.
  { id: "scale", label: MEAS.sScale, group: "measured" },
  { id: "language", label: MEAS.sLang, group: "measured" },

  { id: "conflict", label: MEAS.sConflict, group: "register" },
  { id: "attention", label: MORE.sAtt, group: "register" },

  { id: "shape", label: MEAS.sShape, group: "knownshape" },
  { id: "gapkinds", label: MORE.sGaps, group: "knownshape" },
  { id: "voidcells", label: MORE.sVoid, group: "knownshape" },

  { id: "cells", label: DEEP.sCells, group: "knownshape" },
  { id: "constraint", label: DEEP.sConstraint, group: "converge" },
  { id: "autism", label: MORE.sAut, group: "converge" },
  { id: "signalenergy", label: SAMP.sSignal, group: "converge" },

  // 5a. Who was in the sample. Beside the constraint result rather than in a pillar of its
  //     own: gene_constraint states in prose that gnomAD's panel is majority European, and
  //     this turns that sentence into a count. Separated, it is a silo; here, it is an
  //     argument about the result above it.
  { id: "ancestrygwas", label: SAMP.sAncestry, group: "sampled" },
  { id: "disorders", label: SAMP.sDisorders, group: "sampled" },
  { id: "axes", label: SAMP.sAxes, group: "sampled" },
  { id: "grid", label: SAMP.sMatrix, group: "sampled" },
  { id: "joins", label: SAMP.sJoins, group: "sampled" },

  // 5b. The method on a domain that did not produce it. Its own group, because the standing
  //     is different again: this is not a fact about rare disease, it is evidence that the
  //     instrument works where the instrument was not built.
  { id: "hiv", label: DEEP.sHiv, group: "beyond" },

  // 6. The argument and its provenance — a thesis and its bibliography are one thing.
  { id: "thesis", label: RARE.sThesis, group: "argument" },
  { id: "selfaudit", label: RARE.sSelfAudit, group: "argument" },
  { id: "refmap", label: RARE.sRefmap, group: "argument" },
  { id: "sources", label: RARE.sSources, group: "argument" },
];



export default function RarePage() {
  const [sort, setSort] = useState<SortKey>("gaps");
  const [selected, setSelected] = useState<string | null>(null);
  // Both nav levels live in the URL and are drawn by the rail, not by this page.
  const tt = useT();
  const { section } = useSectionNav({
    owner: "rare", groups: GROUPS, sections: SECTIONS, initial: "world",
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
    const g = SECTIONS.find((s) => s.id === section)?.group;
    if (g === "measured" || g === "register" || g === "knownshape") prefetchMeasured();
  }, [section]);

  const ordered = useMemo(
    () => sortDiseases(lexicon, lexicon.diseases, sort),
    [sort]
  );
  const focus = ordered.find((d) => d.name === selected) ?? ordered[0];

  /** The section a bare link opens on. Only there does the reader need the introduction. */
  const entry = section === "world";

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
