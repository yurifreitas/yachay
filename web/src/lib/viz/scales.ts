/** Non-linear scales, as first-class objects rather than as a `Math.log` sprinkled into a
 *  chart body.
 *
 *  WHY THIS FILE EXISTS. Every quantity this repository plots is skewed: scores produced by
 *  a max-order statistic, prevalences spanning six orders of magnitude, rank moves whose
 *  median is 3 and whose maximum is 254. A linear axis spends nine tenths of its length on
 *  the empty part of those distributions and crushes the part being argued about into a few
 *  pixels. Log fixes that but cannot cross zero, and half of these quantities do.
 *
 *  So: `symlog` for signed heavy tails, `quantile` for "I do not care about the units, I
 *  care about who is where". Both satisfy the same `Scale` contract as `linear` and `log`,
 *  so an axis component never learns which one it was handed.
 */
import type { Scale } from "../scale";

function make(fwd: (v: number) => number, domain: [number, number], tick: (n: number) => number[]): Scale {
  const s = fwd as Scale;
  s.domain = domain;
  s.ticks = (n = 5) => tick(n);
  return s;
}

const niceStep = (raw: number): number => {
  const e = 10 ** Math.floor(Math.log10(Math.abs(raw) || 1));
  const f = raw / e;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e;
};

/** Symmetric log: linear inside ±`c`, logarithmic outside, and defined at and across zero.
 *
 *  The constant `c` is where the scale changes character. It is an argument and not a
 *  constant because it is a claim about the data — "below this, differences do not matter" —
 *  and a chart that hides that claim inside a default is asserting something it never says.
 */
export function symlog(
  domain: [number, number], range: [number, number], c = 1,
): Scale {
  const f = (v: number) => Math.sign(v) * Math.log10(1 + Math.abs(v) / c);
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const f0 = f(d0);
  const span = f(d1) - f0 || 1;
  return make(
    (v) => r0 + ((f(v) - f0) / span) * (r1 - r0),
    domain,
    () => {
      // Decades either side of zero, plus zero itself, clipped to the domain. Never a
      // "nice" linear step: on a symlog axis evenly spaced labels are evenly spaced lies.
      const out: number[] = [0];
      const top = Math.max(Math.abs(d0), Math.abs(d1));
      for (let e = Math.floor(Math.log10(c)); 10 ** e <= top * 1.0001; e++) {
        out.push(10 ** e, -(10 ** e));
      }
      return out
        .filter((t) => t >= Math.min(d0, d1) && t <= Math.max(d0, d1))
        .sort((a, b) => a - b)
        .filter((t, i, a) => i === 0 || t !== a[i - 1]);
    },
  );
}

/** A rank scale: a value maps to its position in the sample, not to its magnitude.
 *
 *  This is the honest axis for "the interesting region is a sparse corner of a cloud whose
 *  bulk is one blob". It spends screen space in proportion to how many points are there,
 *  which is exactly what a density question wants and exactly what a magnitude question does
 *  not — so the axis MUST be labelled with percentiles, and the component that draws it
 *  refuses to print raw units. Ties share a position, as ranks should.
 */
export function quantile(sample: readonly number[], range: [number, number]): Scale {
  const sorted = Float64Array.from(sample).sort();
  const n = sorted.length;
  const [r0, r1] = range;

  /** Fraction of the sample at or below v, by binary search. */
  const frac = (v: number) => {
    if (!n) return 0;
    let lo = 0, hi = n;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (sorted[mid] <= v) lo = mid + 1;
      else hi = mid;
    }
    return lo / n;
  };

  const domain: [number, number] = n ? [sorted[0], sorted[n - 1]] : [0, 1];
  return make(
    (v) => r0 + frac(v) * (r1 - r0),
    domain,
    (count = 5) => {
      // Ticks are the sample's own quantiles, so a label always sits where that share of
      // the data actually is.
      const out: number[] = [];
      for (let i = 0; i <= count; i++) {
        const at = Math.min(n - 1, Math.max(0, Math.round((i / count) * (n - 1))));
        if (n) out.push(sorted[at]);
      }
      return out.filter((t, i, a) => i === 0 || t !== a[i - 1]);
    },
  );
}

/** The percentile a value sits at, for labelling a quantile axis. Exposed separately
 *  because the axis prints percentiles while the tooltip prints units, and both are true. */
export function percentileOf(sample: readonly number[], v: number): number {
  const sorted = Float64Array.from(sample).sort();
  let lo = 0, hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (sorted[mid] <= v) lo = mid + 1;
    else hi = mid;
  }
  return sorted.length ? lo / sorted.length : 0;
}

export { niceStep };
