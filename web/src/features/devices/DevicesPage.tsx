import { Suspense } from "react";
import { renderSection } from "../../lib/sectionRegistry";
import { DEVICE_SECTIONS } from "./devicesSections";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { SectionWalk } from "../../components/molecules/SectionWalk";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { DEV } from "../../i18n/devices";
import { useT } from "../../i18n";
import raw from "../../data/generated/cleared_devices.json";
import css from "./DevicesPage.module.css";

/** PREDICTIVE TECHNOLOGIES — the third pillar, and the one most likely to go wrong.
 *
 *  The design this page came from asks for a card per technology: model, input, output,
 *  clinical role, model class, dataset, population, AUROC, sensitivity, specificity, PPV,
 *  NPV, calibration, external validation, prospective validation, clinical trial, regulatory
 *  status, limitations. It is a good schema. It is also, filled in by hand from papers,
 *  precisely what ADR 0007 forbids: a page of numbers that no tool computed and no reader can
 *  trace, in a project whose one claim is that every figure leads back to its artefact.
 *
 *  So this page begins where the schema can be OBSERVED rather than typed. Of the eighteen
 *  fields that schema asks for, exactly one is published by a party with no interest in the
 *  answer and a date attached: regulatory status. The FDA maintains the list. Everything on
 *  these screens is a count over it, with its denominator.
 *
 *  WHAT IS DELIBERATELY MISSING, and it is most of the schema. There is no AUROC here, no
 *  sensitivity, no population breakdown, no skin-phototype coverage. Those need a source per
 *  field — ISIC metadata for population, ClinicalTrials.gov for the prospective rung — and
 *  each one is a separate ingest with its own limitations. Publishing the schema with those
 *  cells empty would advertise a completeness this has not earned. The taxonomy section says
 *  what the layer is FOR; the counts say what it can currently support. The gap between them
 *  is stated rather than filled with plausible numbers.
 */

const GROUPS: NavGroupDef[] = [
  { id: "deployed", label: DEV.gWhat, question: DEV.qWhat },
  { id: "reading", label: DEV.gCheck, question: DEV.qCheck },
];

const SECTIONS: NavSectionDef[] = [
  // What a regulator permitted, and when, and by whom.
  { id: "panels", label: DEV.sPanels, group: "deployed" },
  { id: "years", label: DEV.sYears, group: "deployed" },
  { id: "companies", label: DEV.sWho, group: "deployed" },

  // The two sections about how to read the counts. The correction is a section rather than a
  // footnote because a site that publishes findings owes its corrections the same size.
  { id: "expected", label: DEV.sExpected, group: "reading" },
  { id: "correction", label: DEV.sSkin, group: "reading" },
];

export default function DevicesPage() {
  const t = useT();
  const { section } = useSectionNav({
    owner: "devices", groups: GROUPS, sections: SECTIONS, initial: "panels",
  });
  const d = raw as any;

  return (
    <section className={css.page}>
      <header className={css.head}>
        <p className={css.eyebrow}>
          Predictive technologies · regulatory record · {d.scale?.first_decision}–
          {d.scale?.last_decision}
        </p>
        <h2>Most clinical AI has never been authorised for use on anybody</h2>
        <p className={css.lede}>
          An atlas of clinical AI is usually a table of accuracies copied out of papers. This
          one starts from the only field in that table which is published, dated and not
          self-reported: whether a regulator has permitted the thing.{" "}
          <strong>{(d.scale?.devices ?? 0).toLocaleString("en-US")}</strong> AI-enabled devices
          have been authorised for clinical use in the United States, and{" "}
          <strong>
            {Math.round(100 * (d.concentration?.largest_panel_share ?? 0))} %
          </strong>{" "}
          of them are radiology. Nothing here says a model is good — only that someone is
          allowed to use it.
        </p>
      </header>

      <SectionHeading />

      <Suspense fallback={<div className={css.skel} />}>
        {renderSection(DEVICE_SECTIONS, section, { tt: t }, {
          className: css.block, headingClass: css.h3, subClass: css.sub,
        })}
      </Suspense>

      <SectionWalk />
    </section>
  );
}
