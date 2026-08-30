/** The domain an interval figure has to cover, and why it is not the domain of its points.
 *
 *  THE BUG THIS EXISTS TO PREVENT, which was shipped once already: a track built from the
 *  point estimates and clamped at zero. Every band whose lower bound was negative began at
 *  the left edge, so a propagation z of 1825 with an interval of [-1753, +5403] — an estimate
 *  that does not exclude no effect at all — drew identically to one bounded well above zero.
 *  The figure asserted the opposite of what the number said.
 *
 *  So the domain covers every BOUND, every reference the caller draws, and zero. Zero is
 *  always included because these figures exist to answer "does this interval clear the line",
 *  and a domain that excludes the line cannot show the answer.
 */
export type Bounded = { point: number; lo?: number | null; hi?: number | null };

export function intervalDomain(
  rows: readonly Bounded[],
  refs: readonly number[] = [],
  padFraction = 0.04,
): [number, number] {
  const vals: number[] = [0, ...refs];
  for (const r of rows) {
    vals.push(r.point);
    if (r.lo != null) vals.push(r.lo);
    if (r.hi != null) vals.push(r.hi);
  }
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);
  // A band ending exactly on the domain edge loses its cap to the plot boundary, so the
  // domain is padded rather than tight. Never padded to a "nice" round number: rounding a
  // domain outward moves the reference lines relative to the data.
  const pad = (hi - lo) * padFraction || 1;
  return [lo - pad, hi + pad];
}

/** Whether an interval clears a bar, with the two ways of asking kept apart.
 *
 *  `point` is what every ranking in this repository used before intervals existed. `interval`
 *  is the honest version. They disagree on 25 of 41 perturbations in the obesity screen and
 *  on the whole of the propagation artefact's top ten, which is the reason both are named
 *  rather than one being called "clears".
 */
export function clears(
  row: Bounded, bar: number,
): { point: boolean; interval: boolean } {
  return {
    point: row.point > bar,
    interval: row.lo != null && row.lo > bar,
  };
}
