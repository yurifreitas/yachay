import { Suspense } from "react";
import { renderSection } from "../../lib/sectionRegistry";
import { DISCOVERY_SECTIONS } from "./discoverySections";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { SectionWalk } from "../../components/molecules/SectionWalk";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { DISC } from "../../i18n/discovery";
import { useT } from "../../i18n";
import raw from "../../data/generated/obesity_thermogenesis.json";
import css from "./DiscoveryPage.module.css";

/** DISCOVERY — the method turned on work that was not this repository's own.
 *
 *  Every other page here measures a catalogue somebody else curated. This one measures a
 *  SCREEN: the Broad / Eric and Wendy Schmidt Center obesity challenge, which asked which
 *  gene perturbations promote thermogenesis in adipocytes over a space of 4,474,413 candidate
 *  pairs.
 *
 *  IT IS HERE BECAUSE OF THE CONTROL POOL. `.claude/skills/sieve-new-adapter` ranks three
 *  ways to calibrate: designed controls in the same harness, a matched inert set, or label
 *  permutation. Every adapter in this repository until now used the third or the second, and
 *  `hiv_resistance` says out loud that it used the weakest. This screen carries a
 *  non-targeting control measured in the same experiment on 2,242 cells — so for the first
 *  time the null is RESAMPLED from cells that were perturbed with nothing, rather than
 *  assumed.
 *
 *  WHAT IT IS NOT. Not a nomination, not a claim about gene pairs, and not a statement about
 *  what would work in a person. It asks one question about the layer under all of those: how
 *  much of a top-3 ranking over unequally sampled perturbations is thermogenesis, and how
 *  much is the floor of the statistic.
 */

const GROUPS: NavGroupDef[] = [
  { id: "gate", label: DISC.gGate, question: DISC.qGate, tier: DISC.tScreen },
  { id: "floor", label: DISC.gFloor, question: DISC.qFloor, tier: DISC.tScreen },
  { id: "rank", label: DISC.gRank, question: DISC.qRank, tier: DISC.tResult },
];

const SECTIONS: NavSectionDef[] = [
  { id: "fit", label: DISC.sFit, group: "gate" },
  { id: "control", label: DISC.sControl, group: "gate" },
  { id: "nullfloor", label: DISC.sFloor, group: "floor" },
  { id: "rerank", label: DISC.sRerank, group: "rank" },
];

export default function DiscoveryPage() {
  const t = useT();
  const { section } = useSectionNav({
    owner: "discovery", groups: GROUPS, sections: SECTIONS, initial: "fit",
  });
  const d = raw as any;
  const sc = d.scale ?? {};

  return (
    <section className={css.page}>
      <header className={css.head}>
        <p className={css.eyebrow}>
          Discovery · Broad / Schmidt Center obesity challenge · {d.generated}
        </p>
        <h2>A perturbation with eight cells can outrank the winner by noise alone</h2>
        <p className={css.lede}>
          The challenge ranks gene perturbations by the mean of their top three thermogenic
          signatures — a top-k over correlated scores, computed on between{" "}
          <strong>{sc.cells_min}</strong> and <strong>{sc.cells_max}</strong> cells depending
          on the perturbation. Resampling the{" "}
          <strong>{(sc.control_cells ?? 0).toLocaleString("en-US")}</strong>-cell non-targeting
          control gives that statistic's floor at each cell count, and the floor moves by more
          than tenfold across the range. Nothing here is a nomination; it is a calibration of
          the layer every nomination sits on.
        </p>
      </header>

      <SectionHeading />

      <Suspense fallback={<div className={css.skel} />}>
        {renderSection(DISCOVERY_SECTIONS, section, { tt: t }, {
          className: css.block, headingClass: css.h3, subClass: css.sub,
        })}
      </Suspense>

      <SectionWalk />
    </section>
  );
}
