/** Types for the two layers whose subject is this repository rather than any disease.
 *
 *  WHY THEY BELONG ON THE DASHBOARD AT ALL. `tools/consistency.py` and
 *  `tools/lexicon_check.py` are the only artefacts that audit the project itself, and until
 *  now they existed only as JSON on disk. A dashboard that renders twenty layers of findings
 *  while keeping its own contradictions in a file nobody opens is publishing them nowhere —
 *  which is the same failure as a provenance string that never reaches the screen
 *  (docs/audit.md A13).
 */

/** One claim two or more layers disagree about. */
export type Contradiction = {
  disease: string | null;
  field: string;
  byLayer: Record<string, { value: string | string[]; grade: string }>;
  severity: string;
  says: string;
  recordedByOrphanet?: string[];
};

export type Consistency = {
  generated: string;
  premise: string;
  caveat: string;
  scope: { layersIndexed: string[]; diseaseKeys: number; joinedOn: string };
  contradictions: Contradiction[];
  bySeverity: Record<string, number>;
  unjoinable: { disease: string | null; onlyIn: string; grade: string; says: string }[];
  coverage: { disease: string | null; layers: string[]; count: number }[];
  summary: {
    contradictions: number;
    diseasesInMoreThanOneLayer: number;
    diseasesInOnlyOneLayer: number;
    mostCrossReferenced: { disease: string | null; layers: string[]; count: number } | null;
  };
};

/** One identifier check. `verdict` is deliberately a string rather than a boolean: the
 *  interesting states are "unverifiable" and "declared unknown", and a boolean would have
 *  to lie about both. */
export type FieldCheck = {
  verdict: string;
  says: string;
  catalogueName?: string;
  recorded?: string[];
  claimed?: string;
};

export type LexiconCheck = {
  generated: string;
  premise: string;
  caveat: string;
  scope: {
    diseases: number;
    fieldsChecked: string[];
    unverifiableByDesign: string[];
    orphanetDisorders: number;
    annotatedDiseases: number;
    geneSymbols: number;
  };
  verdicts: Record<string, number>;
  rows: {
    name: string;
    confidence: string | null;
    checks: Record<string, FieldCheck>;
    flags: string[];
  }[];
  /** Whether the author's own confidence marks predicted the defects. They did. */
  calibration: {
    byConfidence: Record<string, { diseases: number; flagged: number; share: number }>;
    says: string;
    caveat: string;
  };
  clean: number;
  flagged: number;
};

/** Verdicts sorted into the three states the interface actually distinguishes. A verdict in
 *  SHOUTING CAPS is a defect; "unverifiable" and "declared unknown" are honest non-answers
 *  and must never be coloured like passes OR like failures. */
export function verdictTone(verdict: string): "ok" | "gap" | "bad" {
  if (verdict === verdict.toUpperCase() && /[A-Z]{3,}/.test(verdict)) return "bad";
  if (verdict.includes("differs") || verdict.includes("not found")) return "bad";
  if (verdict.startsWith("unverifiable") || verdict.startsWith("declared")
      || verdict === "absent") return "gap";
  return "ok";
}
