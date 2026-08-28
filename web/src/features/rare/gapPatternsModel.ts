/** The gap-pattern measurement, typed.
 *
 *  Written by `tools/gap_patterns.py` over the whole HPO annotation file. Nothing is derived
 *  here — the counts are the ones Python wrote, because a chart that recomputes its own
 *  statistic is a second implementation of the analysis and the two will disagree.
 */
import raw from "../../data/generated/gap_patterns.json";

export type GapPatterns = {
  generated: string;
  inputs: string[];
  question: string;
  fields: string[];
  total: number;
  unjoinable: number;
  population: string;
  complete: number;
  totals: { field: string; missing: number }[];
  combinations: { missing: string[]; size: number }[];
  caveat: string;
};

export const gapPatterns = raw as unknown as GapPatterns;

/** How much of the emptiness is CO-occurring rather than isolated.
 *
 *  The number the figure exists to produce: if gaps were independent events, most diseases
 *  with a gap would have exactly one. The share carrying three or more is the measure of how
 *  wrong that assumption is.
 */
export function coOccurrence(g: GapPatterns) {
  const withGaps = g.combinations.reduce((s, c) => s + c.size, 0);
  const three = g.combinations
    .filter((c) => c.missing.length >= 3)
    .reduce((s, c) => s + c.size, 0);
  const biggest = g.combinations[0];
  return {
    withGaps,
    three,
    shareOfGapped: withGaps ? three / withGaps : 0,
    biggest,
    biggestShare: withGaps && biggest ? biggest.size / withGaps : 0,
  };
}
