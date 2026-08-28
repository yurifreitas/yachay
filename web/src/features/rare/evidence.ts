/** What a case series of n can and cannot support.
 *
 *  THE PROBLEM THIS SOLVES. Ultra-rare disease literature is written in percentages
 *  derived from single-digit case series: "seizures in 75% of patients" is 3 of 4. The
 *  percentage is not wrong, it is *unqualified* — and a reader who plans a trial, a
 *  registry, or an n-of-1 protocol against it is planning against a number whose 95%
 *  interval runs from roughly 30% to 99%.
 *
 *  Nothing here is novel statistics. It is the standard small-sample toolkit, applied at
 *  the sample sizes ultra-rare disease actually has, and reported as an interval rather
 *  than a point — which is the same discipline this repository applies to a screen.
 *
 *  Pure functions, no React, no formatting.
 */

/** Wilson score interval for a binomial proportion.
 *
 *  Chosen over the textbook normal approximation deliberately: at n = 4, k = 4 the normal
 *  interval is [1, 1] — it claims certainty from four observations. Wilson does not
 *  degenerate at the boundaries, which is the entire situation here.
 */
export function wilson(k: number, n: number, z = 1.959963985): [number, number] {
  if (n <= 0) return [0, 1];
  const p = k / n;
  const d = 1 + (z * z) / n;
  const centre = (p + (z * z) / (2 * n)) / d;
  const half = (z / d) * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n));
  return [Math.max(0, centre - half), Math.min(1, centre + half)];
}

/** The rule of three: with 0 events in n observations, the 95% upper bound is ~3/n.
 *
 *  The number that most often surprises people working at these sample sizes. A case
 *  series of 5 patients with no serious adverse event is consistent with a true rate as
 *  high as 60%. "None observed" is not "does not happen", and at n < 20 it is barely
 *  even evidence.
 */
export function ruleOfThree(n: number): number {
  return n > 0 ? Math.min(1, 3 / n) : 1;
}

/** How many observations to bound a rate below `target` when none are observed. */
export function nForUpperBound(target: number): number {
  return target > 0 ? Math.ceil(3 / target) : Infinity;
}

/** The width of the 95% interval on a proportion observed at k/n — the quantity that
 *  actually decides whether a reported percentage means anything. */
export function intervalWidth(k: number, n: number): number {
  const [lo, hi] = wilson(k, n);
  return hi - lo;
}

export type Inference = {
  claim: string;
  /** What the series supports, honestly. */
  verdict: "supported" | "underpowered" | "uninformative";
  detail: string;
};

/** Turn a case series into the set of claims it does and does not support.
 *
 *  The thresholds are conventions, and stated as such: an interval wider than 50 points
 *  cannot separate "most patients" from "a minority", which is the distinction almost
 *  every clinical sentence turns on.
 */
export function inferences(k: number, n: number): Inference[] {
  const [lo, hi] = wilson(k, n);
  const width = hi - lo;
  const pct = (v: number) => `${Math.round(v * 100)}%`;

  const out: Inference[] = [];

  out.push({
    claim: `the feature occurs in ${n ? Math.round((k / n) * 100) : 0}% of patients`,
    verdict: width > 0.5 ? "uninformative" : width > 0.3 ? "underpowered" : "supported",
    detail: `95% interval ${pct(lo)}–${pct(hi)}, ${Math.round(width * 100)} points wide.` +
      (width > 0.5
        ? " Too wide to separate a majority from a minority — the point estimate carries almost no information."
        : width > 0.3
        ? " Wide enough that the direction is suggestive but the magnitude is not."
        : " Narrow enough to plan against."),
  });

  out.push({
    claim: "the feature is present in more than half of patients",
    verdict: lo > 0.5 ? "supported" : hi < 0.5 ? "supported" : "underpowered",
    detail:
      lo > 0.5
        ? `The lower bound is ${pct(lo)}, so yes.`
        : hi < 0.5
        ? `The upper bound is ${pct(hi)}, so no — it is a minority feature.`
        : `The interval straddles 50% (${pct(lo)}–${pct(hi)}). This series cannot answer it.`,
  });

  const r3 = ruleOfThree(n);
  out.push({
    claim: "an unobserved complication is rare",
    verdict: r3 > 0.3 ? "uninformative" : r3 > 0.1 ? "underpowered" : "supported",
    detail:
      `Nothing observed in ${n} patients bounds the true rate at ${pct(r3)} (rule of three), ` +
      `not at zero. To bound it below 10% you would need ${nForUpperBound(0.1)} patients; ` +
      `below 1%, ${nForUpperBound(0.01)}.`,
  });

  return out;
}

/** The sample sizes an ultra-rare programme actually meets, for the scale annotation. */
export const LANDMARKS = [
  { n: 1, label: "n-of-1", note: "a single treated patient" },
  { n: 4, label: "first case series", note: "the modal ultra-rare publication" },
  { n: 12, label: "a registry cohort", note: "years of recruitment" },
  { n: 30, label: "a small trial arm", note: "rarely reachable for an ultra-rare disease" },
  { n: 100, label: "a rare-disease trial", note: "out of reach below ~1 / 1 000 000" },
];
