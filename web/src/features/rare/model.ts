/** Types and pure rules for the rare-disease atlas. No React, no fetch, no formatting.
 *
 *  The domain rule that shapes everything: a gap is a VALUE, not an absence. The seed
 *  encodes that with sentinel tokens, and every derivation here treats them as data.
 */
import type { Epistemic } from "../../components/atoms/StatusDot";

export const UNKNOWN_GENE = "UNKNOWN_GENE";
export const UNKNOWN_PREVALENCE = "UNKNOWN_PREVALENCE";
export const UNKNOWN_MECHANISM = "UNKNOWN_MECHANISM";
export const NONE_APPROVED = "NONE_APPROVED";

export type Disease = {
  name: string;
  mondo: string | null;
  orpha: string | null;
  omim: string | null;
  gene: string;
  inherit: string;
  onset: string;
  prevalence: string;
  mechanism: string;
  therapy: string;
  system: string;
  confidence: "high" | "medium" | "low" | "none";
  synonyms: string[];
  note: string;
  unknowns: number;
  orphan_of_ontologies: boolean;
};

export type PrevalenceBand = { id: string; label: string; note: string; rank: number };
export type Ontology = { id: string; name: string; role: string; pattern: string; scope: string };
export type Definition = { where: string; rule: string; basis: string; source: string };
export type FieldFact = { claim: string; verify: string; confidence: string };

export type Lexicon = {
  generated: string;
  provenance: string;
  definitions: Definition[];
  prevalenceBands: PrevalenceBand[];
  ontologies: Ontology[];
  fieldFacts: FieldFact[];
  diseases: Disease[];
  summary: {
    entries: number;
    withoutGene: number;
    withoutMechanism: number;
    withoutTherapy: number;
    withoutAnyOntologyId: number;
    bySystem: Record<string, number>;
    byConfidence: Record<string, number>;
  };
};

/** The four axes an entry can be known or unknown along. Order is the reading order of a
 *  translational pipeline: you need the gene before the mechanism before the therapy. */
export const AXES = [
  { key: "gene", label: "causal gene" },
  { key: "mechanism", label: "mechanism" },
  { key: "therapy", label: "approved therapy" },
  { key: "id", label: "ontology identifier" },
] as const;

export type AxisKey = (typeof AXES)[number]["key"];

/** What is known about one disease along one axis. Pure. */
export function axisState(d: Disease, axis: AxisKey): Epistemic {
  switch (axis) {
    case "gene":
      return d.gene === UNKNOWN_GENE ? "unknown" : "known";
    case "mechanism":
      return d.mechanism === UNKNOWN_MECHANISM ? "unknown" : "known";
    case "therapy":
      if (d.therapy === NONE_APPROVED) return "absent";
      return d.therapy === "APPROVED" ? "known" : "partial";
    case "id":
      if (d.orphan_of_ontologies) return "unknown";
      return d.mondo && d.orpha && d.omim ? "known" : "partial";
  }
}

export function bandOf(l: Lexicon, d: Disease): PrevalenceBand {
  return (
    l.prevalenceBands.find((b) => b.id === d.prevalence) ??
    l.prevalenceBands[l.prevalenceBands.length - 1]
  );
}

/** How complete the record is, 0..1 — used only for ordering, never shown as a score.
 *  A single number about knowledge would be exactly the false-confidence this page is
 *  about; it earns its place as a sort key and nothing else. */
export function completeness(d: Disease): number {
  return AXES.filter((a) => axisState(d, a.key) === "known").length / AXES.length;
}

export type SortKey = "gaps" | "rarity" | "name";

export function sortDiseases(l: Lexicon, ds: Disease[], by: SortKey): Disease[] {
  const copy = [...ds];
  if (by === "name") return copy.sort((a, b) => a.name.localeCompare(b.name));
  if (by === "rarity")
    return copy.sort((a, b) => bandOf(l, a).rank - bandOf(l, b).rank || a.name.localeCompare(b.name));
  return copy.sort((a, b) => completeness(a) - completeness(b) || a.name.localeCompare(b.name));
}

/** Every language a synonym is written in is a language the literature is written in.
 *  Detecting script rather than language, which is all that is knowable from the string. */
export function scriptOf(s: string): "latin" | "cjk" | "other" {
  if (/[\u3040-\u30ff\u4e00-\u9fff]/.test(s)) return "cjk";
  if (/^[\u0000-\u024f\s'()\-.,]+$/.test(s)) return "latin";
  return "other";
}
