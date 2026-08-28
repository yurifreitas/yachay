/** Set intersections, counted.
 *
 *  WHY THIS EXISTS AT ALL. This repository keeps flagging entities — common-essential,
 *  non-essential control, clears the noise floor, survives multiplicity — and then reduces
 *  those flags to ONE class per entity so a legend can have three colours. That reduction is
 *  a lie whenever a gene carries two flags at once, and the site had no figure in which the
 *  overlap could even be seen.
 *
 *  A Venn diagram fails past three sets and is unreadable at four. The UpSet plot (Lex et
 *  al., 2014) is the form built for exactly this: sets as rows, INTERSECTIONS as columns, a
 *  bar for each combination's size and a dot matrix underneath saying which combination it
 *  is. It reads as a bar chart — a position judgement on a common scale, the top of
 *  Cleveland–McGill — and scales to a dozen sets.
 */

export type UpSetCombination = {
  /** Which sets this combination is IN, in the order the sets were declared. */
  members: string[];
  /** A stable key: the membership as a bit pattern. */
  key: string;
  size: number;
  /** Indices of the items in it, so a click can list them. */
  indices: number[];
};

export type UpSetResult = {
  /** Per-set totals, for the left-hand bars. */
  totals: { set: string; size: number }[];
  /** Non-empty combinations, largest first. An empty combination is not a fact about the
   *  data, it is the absence of one, and drawing it makes the plot say the opposite. */
  combinations: UpSetCombination[];
  /** Items carrying no flag at all — reported as a number rather than as a column, because
   *  it is usually the largest "combination" and would flatten every real one. */
  unflagged: number;
  total: number;
};

/** `sets` maps a set name to a predicate over item index. Declaration order is display
 *  order, so the caller decides what "first" means rather than inheriting an alphabet. */
export function upset(
  count: number, sets: { name: string; has: (i: number) => boolean }[],
): UpSetResult {
  const byKey = new Map<string, UpSetCombination>();
  const totals = sets.map((s) => ({ set: s.name, size: 0 }));
  let unflagged = 0;

  for (let i = 0; i < count; i++) {
    const members: string[] = [];
    let key = "";
    sets.forEach((s, si) => {
      const has = s.has(i);
      key += has ? "1" : "0";
      if (has) { members.push(s.name); totals[si].size++; }
    });
    if (!members.length) { unflagged++; continue; }

    const found = byKey.get(key);
    if (found) { found.size++; found.indices.push(i); }
    else byKey.set(key, { members, key, size: 1, indices: [i] });
  }

  const combinations = [...byKey.values()].sort(
    // Size first; ties broken by degree so that, among equals, the simpler statement about
    // the data comes first.
    (a, b) => b.size - a.size || a.members.length - b.members.length,
  );
  return { totals, combinations, unflagged, total: count };
}
