import type { NavGroupDef, NavSectionDef } from "../../lib/nav";
import { RARE } from "../../i18n/strings";
import { MEAS } from "../../i18n/measured";
import { MORE } from "../../i18n/more";
import { DEEP } from "../../i18n/deep";
import { SAMP } from "../../i18n/sampled";
import { TROP } from "../../i18n/tropical";

/** FOUR VIEWS WHERE THERE WAS ONE PAGE OF FORTY SECTIONS.
 *
 *  The rare atlas had grown to forty sections in twelve groups. Grouping them helped, and
 *  banding the groups helped again, but a reader still arrived at one page that answers four
 *  different questions and had to scroll past three of them.
 *
 *  The bands were already the seam. They named the KIND of question a run of groups answers —
 *  what the catalogue holds, where in the organism it sits, how well any of it is
 *  established, what the whole thing argues — so each band becomes a view, and the top-level
 *  navigation gains four entries that are four questions instead of one entry that is a
 *  corpus.
 *
 *  ONE DECLARATION, FOUR VIEWS. The sections and their groups live here once. The pages read
 *  from this file, `check-sections.mjs` reads from it, and nothing restates which section
 *  belongs where — the failure that ADR 0009 exists to prevent, one level up.
 *
 *  SECTION IDS ARE UNCHANGED, so `?s=world` still names the same panel. The route in front of
 *  it changes, and `#rare?s=…` is redirected to whichever view now holds that section rather
 *  than dropped — a link somebody sent is a promise.
 */

export type RareView = {
  id: string;
  groups: NavGroupDef[];
  sections: NavSectionDef[];
  initial: string;
};

/* ------------------------------------------------------------------ 1. the catalogue */

const CATALOGUE: RareView = {
  id: "catalogue",
  initial: "world",
  groups: [
    { id: "known", label: RARE.gKnown, question: RARE.qKnown },
    { id: "naming", label: RARE.gNaming, question: RARE.qNaming },
  ],
  sections: [
    // The catalogue and what its numbers are really measuring. First, because a reader who
    // meets one disease before meeting the denominator has no way to weigh it.
    { id: "world", label: RARE.sWorld, group: "known" },
    { id: "bias", label: RARE.sBias, group: "known" },
    { id: "population", label: RARE.sPopulation, group: "known" },
    { id: "patients", label: RARE.sPatients, group: "known" },
    { id: "names", label: RARE.sNames, group: "naming" },
    { id: "atlas", label: RARE.sAtlas, group: "naming" },
    { id: "gaps", label: RARE.sGaps, group: "naming" },
    { id: "tropical", label: TROP.section, group: "naming" },
  ],
};

/* ------------------------------------------------------------------ 2. the ladder */

const LADDER: RareView = {
  id: "ladder",
  initial: "cell",
  groups: [
    { id: "micro", label: MEAS.gMicro, question: MEAS.qMicro },
    { id: "signal", label: MEAS.gSignal, question: MEAS.qSignal },
    { id: "nano", label: MEAS.gNano, question: MEAS.qNano },
    { id: "case", label: RARE.gCase, question: RARE.qCase },
  ],
  sections: [
    { id: "cell", label: RARE.sCell, group: "micro" },
    { id: "sparse", label: RARE.sSparse, group: "micro" },
    { id: "cells", label: DEEP.sCells, group: "micro" },

    { id: "network", label: RARE.sNetwork, group: "signal" },
    { id: "twin", label: DEEP.sTwin, group: "signal" },
    { id: "scale", label: MEAS.sScale, group: "signal" },
    { id: "autism", label: MORE.sAut, group: "signal" },
    { id: "signalenergy", label: SAMP.sSignal, group: "signal" },

    { id: "nongene", label: RARE.sNongene, group: "nano" },
    { id: "genopheno", label: DEEP.sGeno, group: "nano" },
    { id: "gapkinds", label: MORE.sGaps, group: "nano" },
    { id: "constraint", label: DEEP.sConstraint, group: "nano" },

    { id: "disease", label: RARE.sDisease, group: "case" },
    { id: "capability", label: RARE.sCapability, group: "case" },
  ],
};

/* ------------------------------------------------------------------ 3. how well established */

const ESTABLISHED: RareView = {
  id: "established",
  initial: "shape",
  groups: [
    { id: "knownshape", label: MEAS.gShape, question: MEAS.qShape },
    { id: "sampled", label: SAMP.group, question: SAMP.question },
    { id: "register", label: MEAS.gRegister, question: MEAS.qRegister },
    { id: "decide", label: RARE.gDecide, question: RARE.qDecide },
  ],
  sections: [
    { id: "shape", label: MEAS.sShape, group: "knownshape" },
    { id: "voidcells", label: MORE.sVoid, group: "knownshape" },

    { id: "ancestrygwas", label: SAMP.sAncestry, group: "sampled" },
    { id: "disorders", label: SAMP.sDisorders, group: "sampled" },
    { id: "axes", label: SAMP.sAxes, group: "sampled" },
    { id: "grid", label: SAMP.sMatrix, group: "sampled" },
    { id: "joins", label: SAMP.sJoins, group: "sampled" },

    { id: "language", label: MEAS.sLang, group: "register" },
    { id: "conflict", label: MEAS.sConflict, group: "register" },
    { id: "attention", label: MORE.sAtt, group: "register" },

    { id: "evidence", label: RARE.sEvidence, group: "decide" },
    { id: "choose", label: RARE.sChoose, group: "decide" },
    { id: "dims", label: RARE.sDims, group: "decide" },
  ],
};

/* ------------------------------------------------------------------ 4. the argument */

const ARGUMENT: RareView = {
  id: "argument",
  initial: "thesis",
  groups: [
    { id: "argument", label: RARE.gArgument, question: RARE.qArgument },
    { id: "beyond", label: DEEP.gBeyond, question: DEEP.qBeyond },
  ],
  sections: [
    { id: "thesis", label: RARE.sThesis, group: "argument" },
    { id: "selfaudit", label: RARE.sSelfAudit, group: "argument" },
    { id: "zaudit", label: DEEP.sZAudit, group: "argument" },
    { id: "cluster", label: DEEP.sCluster, group: "argument" },
    { id: "refmap", label: RARE.sRefmap, group: "argument" },
    { id: "sources", label: RARE.sSources, group: "argument" },
    { id: "hiv", label: DEEP.sHiv, group: "beyond" },
  ],
};

export const RARE_VIEWS: RareView[] = [CATALOGUE, LADDER, ESTABLISHED, ARGUMENT];

/** Which view holds a section, so `#rare?s=…` can be forwarded rather than dropped. */
export function viewHolding(sectionId: string): string | null {
  for (const v of RARE_VIEWS) {
    if (v.sections.some((s) => s.id === sectionId)) return v.id;
  }
  return null;
}
