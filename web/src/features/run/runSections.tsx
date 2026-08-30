import { lazy } from "react";
import type { Run } from "../../lib/dataTypes";
import type { SectionRegistry } from "../../lib/sectionRegistry";
import CountVariation from "../overview/CountVariation";
import ControlCalibration from "../nullfloor/ControlCalibration";
import RankShift from "../ranking/RankShift";
import NullRidgeline from "../nullfloor/NullRidgeline";
import { NoiseFloor, Movers, Headline } from "./panels";
import { Shortlist, Populations, Selectivity, Base, FlagOverlap } from "./Substance";
import Multiplicity from "./Multiplicity";
import TailCalibration from "./TailCalibration";

const ScreenEvent = lazy(() => import("./ScreenEvent").then((m) => ({ default: m.ScreenEvent })));
const CalibrationField = lazy(() => import("./CrisprViews").then((m) => ({ default: m.CalibrationField })));
const RankBump = lazy(() => import("./CrisprViews").then((m) => ({ default: m.RankBump })));
const LineageMatrix = lazy(() => import("./CrisprViews").then((m) => ({ default: m.LineageMatrix })));

/** THE RUN DASHBOARD'S SECTIONS, DECLARED.
 *
 *  This file replaced a seventeen-branch render chain. The point is not brevity — it is that
 *  adding a measurement is now ONE ENTRY rather than an edit in a nav array, a render chain
 *  and an import block, which is exactly the drift `tools/index_check.py` exists to catch in
 *  prose and `web/scripts/check-sections.mjs` now catches here.
 *
 *  Every entry carries a `sub`, and that is required rather than optional: in this project a
 *  figure's sentence is where it states what it does NOT show, and a section that cannot be
 *  described in one is a section nobody can argue with.
 */
export type RunCtx = { run: Run };

export const RUN_SECTIONS: SectionRegistry<RunCtx> = [
  {
    id: "event",
    title: "Where the controls sit is what the calibration is judged on",
    sub:
      "A screen contains three populations: common-essential genes, which are the confound "
      + "Stage 3 removes; nonessential controls, designed to be inert; and everything else, "
      + "the candidate pool a shortlist comes from. All three against the null's own "
      + "percentiles, ordered by median. This replaced a figure that could not be drawn, and "
      + "the panel says why rather than deleting the attempt.",
    bare: true,
    view: () => (
      <><ScreenEvent /></>
    ),
  },
  {
    id: "shortlist",
    title: "The deliverable, and the rule that produced it",
    sub:
      "Ranked by calibrated z with the common-essential genes removed, because a gene every line needs is a real dependency and a useless selective one. The rule sits above the table rather than in a footnote: a shortlist whose inclusion rule is invisible is an opinion with a table around it.",
    view: (ctx) => <Shortlist run={ctx.run} />,
  },
  {
    id: "overlap",
    title: "The flags are sets, and they overlap",
    sub:
      "Everywhere else on this site a gene gets one class, because a legend wants three colours. Here the flags are counted as the overlapping sets they actually are — including the raw and calibrated top hundreds, whose intersection with common-essential is the whole argument for calibrating, stated as a number.",
    view: (ctx) => <FlagOverlap run={ctx.run} />,
  },
  {
    id: "selectivity",
    title: "The two axes that define the word selective",
    sub:
      "How strong the dependency is where it exists, against how few lines carry it. Both columns were already in the data and neither had ever been plotted.",
    view: (ctx) => <Selectivity run={ctx.run} />,
  },
  {
    id: "populations",
    title: "Three populations that should not look alike",
    sub:
      "Controls should sit at zero with unit spread; common essentials should sit far above it; candidates should be somewhere a person has to think about. If the three collapse together, the calibration has flattened the screen rather than corrected it.",
    view: (ctx) => <Populations run={ctx.run} />,
  },
  {
    id: "multiplicity",
    title: "Ranking 17,916 genes is itself a selection operator",
    sub:
      "Calibrating each gene against a null of the right shape fixes half the problem. The other half is that the top of seventeen thousand numbers is extreme for free. This panel converts z to a p-value, tests the assumption that conversion rests on, and reports what a false-discovery-rate cut actually buys over the threshold the shortlist was using.",
    view: () => <Multiplicity />,
  },
  {
    id: "tail",
    title: "The normality test failed. This is by how much, and where",
    sub:
      "A goodness-of-fit p-value says a distribution is wrong and nothing about where. At this many observations almost anything fails a normality test, so the only question that matters is whether the failure lives in the middle, where nobody looks, or in the tail, where the entire shortlist lives.",
    view: () => <TailCalibration />,
  },
  {
    id: "counts",
    title: "If the counts do not vary, nothing downstream can",
    sub:
      "Calibration divides by a null that depends on n. Where n is constant the correction is a constant, and every ranking claim collapses to the raw one. This panel is first because it can end the argument.",
    view: (ctx) => <CountVariation runId={ctx.run.id} />,
  },
  {
    id: "floor",
    title: "The floor every score is measured against",
    sub:
      "A maximum over many observations rises with the number of observations even when nothing is happening. The null says how much, at each n.",
    view: (ctx) => <NoiseFloor run={ctx.run} />,
  },
  {
    id: "ridge",
    title: "The null, by observation count",
    sub:
      "One distribution per n. If these overlap, calibration is cosmetic; if they march, the raw score was measuring the count.",
    view: (ctx) => <NullRidgeline runId={ctx.run.id} />,
  },
  {
    id: "control",
    title: "The control, which is where this was caught being wrong",
    sub:
      "Entities that should score at zero. A control that comes back at −4 is not a finding, it is a broken null — and that is exactly what a pooled resample produced before the null was drawn block-shaped.",
    view: (ctx) => <ControlCalibration runId={ctx.run.id} />,
  },
  {
    id: "field",
    title: "The same score is a different result at a different n",
    sub:
      "The library's claim as a surface rather than as a sentence: raw score on one axis, how many cell lines produced it on the other, and where the pan-essential genes concentrate marked on top.",
    view: () => <CalibrationField />,
  },
  {
    id: "bump",
    title: "Where the raw top sixty went",
    sub:
      "A reordering cannot be drawn as a bar chart of either ranking. The lines that fall are the genes the raw metric over-rewarded, and the marked ones are known pan-essential.",
    view: () => <RankBump />,
  },
  {
    id: "lineages",
    title: "One lineage, or all of them",
    sub:
      "Rows are cancer lineages, columns the genes they nominated. A column with one mark is a lineage-specific dependency; a column with many is a gene the metric likes everywhere, which is the failure mode Stage 7 exists for.",
    view: () => <LineageMatrix />,
  },
  {
    id: "shift",
    title: "What the calibration moves",
    sub:
      "Raw rank against calibrated rank. A diagonal means the correction changed nothing; the departures from it are the entire result.",
    view: (ctx) => <RankShift runId={ctx.run.id} />,
  },
  {
    id: "movers",
    title: "Who moved, and by how much",
    sub:
      "The table behind the shift, with both ranks and the distance between them.",
    view: (ctx) => <Movers run={ctx.run} />,
  },
  {
    id: "base",
    title: "What every number on this page rests on",
    sub:
      "The dataset, the statistic and why its shape is the problem, the sampling model of the null, the controls — and, at the end, what would show the whole thing is wrong.",
    view: (ctx) => <Base run={ctx.run} />,
  },
  {
    id: "provenance",
    title: "Where these numbers came from",
    sub:
      "The manifest the analysis wrote. Nothing on this page is typed by hand; a new adapter appears here without the interface knowing its name.",
    view: (ctx) => <Headline run={ctx.run} />,
  },
];
