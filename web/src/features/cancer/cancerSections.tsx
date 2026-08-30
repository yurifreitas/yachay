import { lazy } from "react";
import type { SectionRegistry } from "../../lib/sectionRegistry";
import { CANCER } from "../../i18n/strings";
import type { Text } from "../../i18n";
import { Kpis, Cancellation, Power, SubgroupPicker, Gated, Shared, Controls,
         type Split } from "./panels";
import { type CancerLevel, type Subgroup, type DEFAULT_REGISTERED } from "../../lib/cancerModel";

/** Split out: the genotype view carries its own model, its own stylesheet and a 78 kB
 *  dataset, and a reader who only wants the lineage answer should not download it. */
const GenotypeView = lazy(() => import("./GenotypeView"));

/** THE SIXTH PAGE, AND THE ONE NOTHING WAS CHECKING.
 *
 *  `check-sections.mjs` holds three pages to the rule that every rail entry has something to
 *  draw it and every registered section has a sentence saying what it does not show. Cancer
 *  used `useSectionNav` like the others and appeared in neither list — not MIGRATED, so not
 *  checked; not LEGACY, so not even reported as unchecked. It was invisible to the check
 *  written to make this class of drift impossible, which is the most expensive kind of gap a
 *  poka-yoke can have: one that reads as compliance.
 *
 *  Migrating it costs the render chain and buys the check. Its six panels also gained the
 *  sentences they never had — the rail's label was the only thing telling a reader what they
 *  were looking at, and a label is a name, not a claim.
 *
 *  BARE THROUGHOUT. These panels draw their own headings and several carry controls above
 *  the figure, so wrapping them in the registry's heading-plus-view frame would have meant
 *  either rewriting working views or printing two headings. The sentence still lives in the
 *  entry, so the check still sees it.
 */
export type CancerCtx = {
  tt: (t: Text) => string;
  data: CancerLevel;
  groups: Subgroup[];
  chosen: Subgroup;
  onPick: (id: string) => void;
  level: string;
  /** The gates as REGISTERED, before any re-gating the reader does. */
  registered: typeof DEFAULT_REGISTERED;
  split: Split | null;
};

export const CANCER_SECTIONS: SectionRegistry<CancerCtx> = [
  {
    id: "scale",
    title: (ctx) => (<>{ctx.tt(CANCER.sScale)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subScale)}</>),
    bare: true,
    view: (ctx) => (
      <>
        <Kpis data={ctx.data} />
        {ctx.split && <Cancellation split={ctx.split} />}
      </>
    ),
  },
  {
    id: "power",
    title: (ctx) => (<>{ctx.tt(CANCER.sPower)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subPower)}</>),
    bare: true,
    view: (ctx) => (
      <><Power groups={ctx.groups} chosen={ctx.chosen} onPick={ctx.onPick} /></>
    ),
  },
  {
    id: "subgroup",
    title: (ctx) => (<>{ctx.tt(CANCER.sSubgroup)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subSubgroup)}</>),
    bare: true,
    view: (ctx) => (
      <>
        {/* The plane in "What could be detected at all" is where a subgroup is normally
            chosen. Arriving here by link, there was nothing to choose with and the panel
            showed whichever subgroup happened to sort first. */}
        <SubgroupPicker groups={ctx.groups} chosen={ctx.chosen} onPick={ctx.onPick} />
        <Gated group={ctx.chosen} level={ctx.level} registered={ctx.registered} />
      </>
    ),
  },
  {
    id: "shared",
    title: (ctx) => (<>{ctx.tt(CANCER.sShared)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subShared)}</>),
    bare: true,
    view: (ctx) => (<><Shared data={ctx.data} /></>),
  },
  {
    id: "controls",
    title: (ctx) => (<>{ctx.tt(CANCER.sControls)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subControls)}</>),
    bare: true,
    view: (ctx) => (<><Controls data={ctx.data} /></>),
  },
  {
    id: "genotype",
    title: (ctx) => (<>{ctx.tt(CANCER.sGenotype)}</>),
    sub: (ctx) => (<>{ctx.tt(CANCER.subGenotype)}</>),
    bare: true,
    view: () => (<><GenotypeView /></>),
  },
];
