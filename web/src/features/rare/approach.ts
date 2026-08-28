/** A parameterised model for choosing a therapeutic approach in rare disease.
 *
 *  WHAT THIS IS. Given the constraints a specific programme actually has — the variant,
 *  the target tissue, how many patients exist, how long there is — it scores the candidate
 *  modalities and, crucially, **shows the contribution of every criterion**. A ranking
 *  without its decomposition is an opinion with a number attached.
 *
 *  WHAT THIS IS NOT. It is not clinical guidance, not a recommendation engine, and not
 *  validated against outcomes. It is a structured way to make assumptions explicit and
 *  disagree with them: every weight is exposed, every rule is one line, and changing a
 *  parameter changes the visible reason rather than just the answer.
 *
 *  DESIGN, borrowed from the rest of this repository:
 *   - a candidate can be RULED OUT by a hard constraint, which is different from scoring
 *     low — the same distinction as UNKNOWN vs NONE_APPROVED in the lexicon;
 *   - the score is reported with the criteria that produced it, in both directions;
 *   - the weights are the user's, not the model's.
 */

export type VariantClass =
  | "transition_snv"     /* C>T / A>G — the base-editing sweet spot */
  | "transversion_snv"   /* C>A, C>G etc — needs prime editing or another route */
  | "small_indel"
  | "large_deletion"
  | "repeat_expansion"
  | "splice"
  | "whole_gene_loss";

export type Tissue = "liver" | "cns" | "muscle" | "eye" | "haematopoietic" | "systemic";

export type Params = {
  variant: VariantClass;
  tissue: Tissue;
  /** Coding sequence length in kb — decides whether a gene fits in an AAV capsid. */
  cdsKb: number;
  /** How many patients are known to exist worldwide. Drives everything downstream. */
  patients: number;
  /** Months until intervention must begin to be useful (progressive disease). */
  monthsToAct: number;
  /** Does correcting the sequence require gain of function, or is silencing enough? */
  mechanism: "loss_of_function" | "gain_of_function" | "dominant_negative";
};

export type Weights = {
  precision: number;    /* how exactly the lesion can be addressed */
  delivery: number;     /* can it reach the tissue */
  speed: number;        /* time to a treatable construct */
  evidence: number;     /* how much prior human data exists */
  reusability: number;  /* does the work carry to the next patient (the platform thesis) */
};

export const DEFAULT_WEIGHTS: Weights = {
  precision: 1, delivery: 1, speed: 0.8, evidence: 0.7, reusability: 0.9,
};

export type Approach = {
  id: string;
  name: string;
  note: string;
};

export const APPROACHES: Approach[] = [
  { id: "base", name: "Base editing", note: "Chemically converts one base without a double-strand break." },
  { id: "prime", name: "Prime editing", note: "Writes a short new sequence at a targeted site." },
  { id: "aso", name: "Antisense oligonucleotide", note: "Redirects splicing or lowers transcript; repeat dosing." },
  { id: "replace", name: "Gene replacement (AAV)", note: "Delivers a working copy; capsid-limited in size." },
  { id: "sirna", name: "siRNA / knockdown", note: "Lowers a toxic product rather than restoring a missing one." },
  { id: "smallmol", name: "Small molecule", note: "Targets the pathway rather than the lesion." },
];

export type Criterion = {
  key: keyof Weights;
  label: string;
  /** −1 … +1 before weighting. Signed, so the bar chart can show both directions. */
  raw: number;
  why: string;
};

export type Verdict = {
  approach: Approach;
  /** null when a hard constraint rules it out — not the same as scoring zero. */
  score: number | null;
  ruledOutBy?: string;
  criteria: Criterion[];
};

const AAV_CAPACITY_KB = 4.7;

/** One rule per line, each returning a signed contribution and the sentence behind it. */
function criteriaFor(id: string, p: Params): Criterion[] {
  const c: Criterion[] = [];
  const push = (key: keyof Weights, label: string, raw: number, why: string) =>
    c.push({ key, label, raw, why });

  const smallCohort = p.patients <= 12;
  const urgent = p.monthsToAct <= 12;

  if (id === "base") {
    push("precision", "Lesion class",
      p.variant === "transition_snv" ? 1 : p.variant === "transversion_snv" ? -0.7 : -1,
      p.variant === "transition_snv"
        ? "A transition SNV is exactly what a base editor installs."
        : "Base editors install transitions; this lesion is not one.");
    push("delivery", "Target tissue",
      p.tissue === "liver" ? 1 : p.tissue === "haematopoietic" ? 0.6 : p.tissue === "cns" ? -0.1 : -0.4,
      p.tissue === "liver"
        ? "Liver is the best-served tissue for LNP delivery."
        : "Delivery outside liver and blood remains the binding constraint.");
    push("speed", "Time to a construct", urgent ? 0.5 : 0.7,
      "A guide can be designed and screened quickly once the variant is known.");
    push("evidence", "Prior human data", 0.8,
      "Patient-specific base editing has reached the clinic.");
    push("reusability", "Carries to the next patient", 0.9,
      "The platform — delivery, manufacturing, safety package — is shared; only the guide changes.");
  }

  if (id === "prime") {
    push("precision", "Lesion class",
      ["transition_snv", "transversion_snv", "small_indel"].includes(p.variant) ? 0.9 : -0.6,
      "Prime editing writes arbitrary short edits, so it covers lesions base editing cannot.");
    push("delivery", "Target tissue",
      p.tissue === "liver" ? 0.8 : p.tissue === "cns" ? -0.2 : -0.5,
      "Larger cargo than a base editor, which makes delivery harder, not easier.");
    push("speed", "Time to a construct", -0.2,
      "pegRNA optimisation is slower and less predictable than guide selection.");
    push("evidence", "Prior human data", 0.2, "Earlier in clinical translation than base editing.");
    push("reusability", "Carries to the next patient", 0.9, "Same platform argument as base editing.");
  }

  if (id === "aso") {
    push("precision", "Lesion class",
      p.variant === "splice" ? 1 : p.mechanism === "gain_of_function" ? 0.6 : -0.5,
      p.variant === "splice"
        ? "Splice-modulating ASOs address splice lesions directly."
        : "An ASO lowers or reshapes a transcript; it cannot restore a missing function.");
    push("delivery", "Target tissue",
      p.tissue === "cns" ? 0.8 : p.tissue === "liver" ? 0.6 : p.tissue === "muscle" ? -0.3 : 0,
      "Intrathecal delivery makes CNS unusually tractable for ASOs.");
    push("speed", "Time to a construct", 1,
      "The fastest route from variant to a treatable construct — the n-of-1 precedent is an ASO.");
    push("evidence", "Prior human data", 0.9, "The largest body of individualised human experience.");
    push("reusability", "Carries to the next patient", 0.4,
      "Chemistry is shared, but each sequence is a new product and dosing is lifelong.");
  }

  if (id === "replace") {
    push("precision", "Lesion class",
      p.mechanism === "loss_of_function" ? 0.8 : -0.9,
      p.mechanism === "loss_of_function"
        ? "Replacing a lost function is what gene replacement does."
        : "Adding a copy does nothing about a toxic or dominant-negative product.");
    push("delivery", "Target tissue",
      p.tissue === "eye" ? 1 : p.tissue === "liver" ? 0.7 : p.tissue === "muscle" ? -0.2 : -0.3,
      "Contained compartments like the eye are the strongest case.");
    push("speed", "Time to a construct", -0.4, "Vector production and release testing dominate the timeline.");
    push("evidence", "Prior human data", 0.7, "Several approved products.");
    push("reusability", "Carries to the next patient", -0.3,
      "Each gene is a new vector; little carries across diseases.");
  }

  if (id === "sirna") {
    push("precision", "Lesion class",
      p.mechanism === "gain_of_function" || p.mechanism === "dominant_negative" ? 0.9 : -1,
      "Knockdown helps only when the problem is a product that should not be there.");
    push("delivery", "Target tissue",
      p.tissue === "liver" ? 1 : p.tissue === "cns" ? -0.2 : -0.5, "Liver is the solved case for siRNA.");
    push("speed", "Time to a construct", 0.6, "Sequence design is fast.");
    push("evidence", "Prior human data", 0.7, "Approved products in liver indications.");
    push("reusability", "Carries to the next patient", 0.5, "Shared chemistry and delivery.");
  }

  if (id === "smallmol") {
    push("precision", "Lesion class", -0.6,
      "A small molecule addresses the pathway, not the variant, so it is rarely mutation-specific.");
    push("delivery", "Target tissue", p.tissue === "cns" ? 0.2 : 0.7,
      "Oral bioavailability is the advantage; the blood-brain barrier is the exception.");
    push("speed", "Time to a construct", -0.8, "Discovery timelines do not fit a progressive rare disease.");
    push("evidence", "Prior human data", 0.5, "Well-understood development path when a target exists.");
    push("reusability", "Carries to the next patient", -0.6,
      "A molecule for one target says little about the next disease.");
  }

  // Cohort size is a criterion for every approach, not a property of one: it decides
  // whether the economics and the evidence base can exist at all.
  push(
    "evidence", "Cohort size",
    smallCohort ? (id === "aso" || id === "base" || id === "prime" ? 0.5 : -0.8) : 0.3,
    smallCohort
      ? `${p.patients} known patients: only approaches with an n-of-1 regulatory path are realistic.`
      : `${p.patients} patients is enough for a conventional development route.`
  );

  return c;
}

/** Hard constraints. Being ruled out is a different state from scoring low, and the UI
 *  must not blur them — see the typed-unknown argument in the lexicon. */
function hardConstraint(id: string, p: Params): string | undefined {
  if (id === "replace" && p.cdsKb > AAV_CAPACITY_KB)
    return `The coding sequence is ${p.cdsKb} kb; a single AAV carries about ${AAV_CAPACITY_KB} kb.`;
  if (id === "base" && p.variant === "large_deletion")
    return "A base editor changes single bases; it cannot restore a large deletion.";
  if (id === "sirna" && p.mechanism === "loss_of_function")
    return "Knockdown cannot restore a function that is already absent.";
  if (id === "smallmol" && p.monthsToAct <= 6)
    return `Discovery cannot deliver within ${p.monthsToAct} months.`;
  return undefined;
}

export function evaluate(p: Params, w: Weights): Verdict[] {
  const out = APPROACHES.map((approach) => {
    const ruledOutBy = hardConstraint(approach.id, p);
    const criteria = criteriaFor(approach.id, p);
    if (ruledOutBy) return { approach, score: null, ruledOutBy, criteria };
    const total = criteria.reduce((s, c) => s + c.raw * (w[c.key] ?? 1), 0);
    const maxima = criteria.reduce((s, c) => s + Math.abs(w[c.key] ?? 1), 0);
    // Normalised to −100…+100 so the number is comparable across parameter sets rather
    // than only within one.
    return { approach, score: maxima ? (total / maxima) * 100 : 0, ruledOutBy, criteria };
  });
  return out.sort((a, b) => (b.score ?? -Infinity) - (a.score ?? -Infinity));
}

/** Sensitivity: how much does the leader change if one weight is moved?
 *  A recommendation that flips when a weight moves 10% is not a recommendation. */
export function leaderStability(p: Params, w: Weights): { stable: boolean; flips: string[] } {
  const base = evaluate(p, w).find((v) => v.score !== null);
  const flips: string[] = [];
  (Object.keys(w) as (keyof Weights)[]).forEach((k) => {
    for (const delta of [-0.5, 0.5]) {
      const alt = { ...w, [k]: Math.max(0, w[k] + delta) };
      const top = evaluate(p, alt).find((v) => v.score !== null);
      if (top && base && top.approach.id !== base.approach.id) flips.push(`${k} ${delta > 0 ? "+" : ""}${delta}`);
    }
  });
  return { stable: flips.length === 0, flips: [...new Set(flips)] };
}
