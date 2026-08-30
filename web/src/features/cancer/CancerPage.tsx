import { Suspense } from "react";
import { useHashParam } from "../../lib/useHashParam";
import { useRemoteData } from "../../lib/useRemoteData";
import {
  DEFAULT_REGISTERED, LEVELS, LEVEL_LABEL, LEVEL_BLURB, cancellation, ordered,
  type CancerLevel,
} from "../../lib/cancerModel";
import { renderSection } from "../../lib/sectionRegistry";
import { CANCER_SECTIONS } from "./cancerSections";
import ChoiceGroup from "../../components/atoms/ChoiceGroup";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { CANCER } from "../../i18n/strings";
import { useT } from "../../i18n";
import s from "./CancerPage.module.css";

/** Grouped thousands, pinned to the page's own language rather than the reader's browser.
 *  `toLocaleString()` with no argument rendered 1242 as "1.242" under a pt-BR browser, which
 *  inside an English sentence reads as a decimal — a number that is wrong by a factor of a
 *  thousand and looks deliberate. The prose here is English; so is its number formatting. */
const fmt = (n: number) => n.toLocaleString("en-US");

/** Cancer, by subgroup — the section this repository should have had first.
 *
 *  DepMap is `sieve`'s reference application and the source of every calibration result it
 *  publishes, and until now the interface showed it scored as ONE POOL: 17,916 genes across
 *  1,178 cell lines with no regard for what cancer those lines are. That answers "what is
 *  broadly essential", which is the question whose top is 60 % pan-essential genes.
 *
 *  Everything here answers the other question — which gene does *this* cancer depend on that
 *  others do not — at three nested levels of subgroup that were sitting unread in Model.csv.
 *
 *  ON COLOUR. There are 24 lineages and 37 subtypes, and none of these panels asks the reader
 *  to rank 24 colours against each other. Colour is identity: find the subgroup you chose,
 *  recognise it in the next panel. Every mark is directly labelled and the hue only confirms
 *  — see `identityScale` in lib/palette.ts for why that permits a scale the six-hue
 *  categorical cap would not.
 */
/** THE PANELS WERE A SCROLL, AND A SCROLL IS NOT A STRUCTURE.
 *
 *  Every other page on this site states the questions it answers and lets a reader open one.
 *  This one stacked seven panels under a two-way switch, so the fifth panel was reachable
 *  only by scrolling past four others, could not be linked to, and announced nothing about
 *  itself from outside. The panels were already answering four distinct questions — how big
 *  the contrast is, what could have been detected at all, what one subgroup needs, and
 *  whether the positive controls came back — so those are the groups, and each panel is a
 *  section with its own URL.
 *
 *  The catalogue/genotype split becomes the top level rather than a control above the
 *  panels: they are two questions, not two views of one. "Melanoma" is a label someone
 *  assigned; "carries a damaging mutation in SMARCA4" is a property of the cell.
 */
const GROUPS: NavGroupDef[] = [
  { id: "catalogue", label: CANCER.gCatalogue, question: CANCER.qCatalogue },
  { id: "genotype", label: CANCER.gGenotype, question: CANCER.qGenotype },
];

const SECTIONS: NavSectionDef[] = [
  { id: "scale", label: CANCER.sScale, group: "catalogue" },
  { id: "power", label: CANCER.sPower, group: "catalogue" },
  { id: "subgroup", label: CANCER.sSubgroup, group: "catalogue" },
  { id: "shared", label: CANCER.sShared, group: "catalogue" },
  { id: "controls", label: CANCER.sControls, group: "catalogue" },
  { id: "genotype", label: CANCER.sGenotype, group: "genotype" },
];

export default function CancerPage() {
  const t = useT();
  const { section, group: mode } = useSectionNav({
    owner: "cancer", groups: GROUPS, sections: SECTIONS, initial: "scale",
  });
  const [level, setLevel] = useHashParam("level", "lineage");
  const [pick, setPick] = useHashParam("group", "");

  const lin = useRemoteData<CancerLevel>("data/cancer_subgroups_lineage.json");
  // keepPrevious: changing the level is a filter on the same question, not a new page.
  const cur = useRemoteData<CancerLevel>(`data/cancer_subgroups_${level}.json`,
                                         { keepPrevious: true });
  const sub = useRemoteData<CancerLevel>("data/cancer_subgroups_subtype.json");

  if (cur.state === "loading") return <Skeleton />;
  if (cur.state === "error") {
    return (
      <section className={s.page}>
        <p className={s.error}>
          Could not load the subgroup analysis ({cur.message}). It is written by{" "}
          <code>python tools/cancer_subgroups.py</code> and converted by{" "}
          <code>npm run data</code>.
        </p>
      </section>
    );
  }

  const data = cur.data;
  const registered = (data as { gates?: { registered?: typeof DEFAULT_REGISTERED } })
    .gates?.registered ?? DEFAULT_REGISTERED;
  const groups = ordered(data);
  const stale = cur.state === "ready" && cur.stale === true;
  const chosen = groups.find((g) => g.subgroup === pick) ?? groups[0];
  const split =
    lin.state === "ready" && sub.state === "ready" ? cancellation(lin.data, sub.data) : null;

  return (
    <section className={s.page} aria-busy={stale || undefined}>
      {/* The header follows the mode. Leaving the catalogue title and premise standing over
          the genotype answer would have described one analysis while showing another. */}
      <header className={s.head}>
        <p className={s.eyebrow}>
          {mode === "genotype"
            ? "Stage 0 · Stage 2 · Stage 3 · DepMap 24Q2"
            : "Stage 2 · Stage 3 · DepMap 24Q2"}
        </p>
        <h2>
          {mode === "genotype"
            ? "What a mutation makes a cell need"
            : "What each cancer needs that the others do not"}
        </h2>
        <p className={s.lede}>
          {mode === "genotype"
            ? "A catalogue label is a name someone assigned; a damaging mutation is a "
              + "property of the cell, and it is the grouping a target programme acts on. "
              + "Two confounds sit between that question and its answer — lineage and "
              + "mutational burden — and both are measured here rather than disclaimed."
            : data.premise}
        </p>
      </header>

      <SectionHeading />

      {/* The level is the SCOPE of every catalogue panel, not a control belonging to one of
          them, so it stays put while the sections change underneath it. It does not apply to
          the genotype answer, which groups by mutation rather than by subgroup. */}
      {mode !== "genotype" && (
        <LevelSwitch level={level} setLevel={setLevel} scale={data.scale} stale={stale} />
      )}

      {/* ONE CALL. The six branches that were here are declared in cancerSections.tsx —
          and this page was in neither the checked list nor the unchecked one, so the drift
          the check exists to catch could not have been caught here. ADR 0009. */}
      <Suspense fallback={<div className={s.skelPanel} />}>
        {renderSection(CANCER_SECTIONS, section,
          { tt: t, data, groups, chosen, onPick: setPick, level, registered, split }, {})}
      </Suspense>

    </section>
  );
}

/* ------------------------------------------------------------------ level switch */

function LevelSwitch(
  { level, setLevel, scale, stale }:
  { level: string; setLevel: (v: string) => void; scale: CancerLevel["scale"];
    stale: boolean },
) {
  return (
    <div className={s.levels}>
      <ChoiceGroup
        label="Subgroup level"
        value={level}
        onChange={setLevel}
        choices={LEVELS.map((l) => ({ id: l, label: LEVEL_LABEL[l] }))}
      />
      {/* Busy, not blank: the previous level stays readable and is marked as such. */}
      <p className={s.staleNote} role="status" aria-live="polite">
        {stale ? `Loading the ${LEVEL_LABEL[level].toLowerCase()} level — the figures below
          are still the previous one.` : ""}
      </p>
      <p className={s.levelNote}>
        {LEVEL_BLURB[level]} Each level re-runs the whole contrast — {fmt(scale.genesAfterStage3)} genes against {fmt(scale.lines)} lines — because a
        subgroup&rsquo;s comparison set is every line outside it, and that set changes when the
        grouping does.
      </p>
    </div>
  );
}

/* A list, not a chart: 24 lineages need a control that stays one line tall above a panel
   whose subject is a single one of them. */

function Skeleton() {
  return (
    <div className={s.page} role="status" aria-live="polite">
      <span className="visually-hidden">Loading the subgroup analysis</span>
      <div className={s.skelHead} />
      <div className={s.skelKpis}>{[0, 1, 2, 3].map((i) => <div key={i} />)}</div>
      <div className={s.skelPanel} />
    </div>
  );
}
