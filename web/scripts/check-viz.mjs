/** Checks the viz arithmetic against answers that are known independently.
 *
 *  A bandwidth, a hex lattice and a quantile axis are statistical choices, and this
 *  repository's whole position is that a statistical choice which cannot be checked is an
 *  opinion. These run in the build, beside the contrast and palette gates, so a figure
 *  cannot ship on maths nobody re-derived.
 *
 *  Run with `node --experimental-strip-types` so the TypeScript modules the app imports are
 *  the exact modules under test — a re-implementation in JS would only prove itself.
 */
import { symlog, quantile, percentileOf } from "../src/lib/viz/scales.ts";
import { quantiles, silverman, kde1d, hexbin, beeswarm } from "../src/lib/viz/density.ts";
import { upset } from "../src/lib/viz/sets.ts";
import { intervalDomain, clears } from "../src/lib/viz/intervals.ts";

let failures = 0;
const near = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol;

function check(name, ok, detail = "") {
  if (ok) console.log(`  ok    ${name}`);
  else { failures++; console.log(`  FAIL  ${name}${detail ? ` - ${detail}` : ""}`); }
}

/* ---------------------------------------------------------------- symlog */
{
  const s = symlog([-100, 100], [0, 200], 1);
  check("symlog is symmetric about zero", near(s(0), 100) && near(s(-10), 200 - s(10)));
  check("symlog crosses zero without a discontinuity", s(-0.5) < s(0) && s(0) < s(0.5));
  // The property that matters is the one a linear axis fails: the region around zero, which
  // is 1% of the domain, must still get a readable share of the page. (Decades do NOT get
  // equal width near the threshold — that is symlog's linear region, and it is the point.)
  const half = s(100) - s(0);
  check("symlog gives the near-zero region a readable share of the axis",
        (s(1) - s(0)) / half > 0.1,
        `units 0-1 are 1% of the domain and take ${(((s(1) - s(0)) / half) * 100).toFixed(0)}% of the half-axis`);
  check("symlog decades approach equal width away from the threshold",
        Math.abs((s(1000) - s(100)) - (s(100) - s(10))) < Math.abs((s(100) - s(10)) - (s(10) - s(1))),
        "decade widths converge as |v| leaves the linear region");
  const ticks = s.ticks();
  check("symlog ticks are decades and zero, never an even step",
        ticks.includes(0) && ticks.includes(10) && ticks.includes(-10) && !ticks.includes(25),
        ticks.join(" "));
}

/* -------------------------------------------------------------- quantile */
{
  // Ninety points in [0,1] and ten in [9,10]: a bulk and a far tail.
  const sample = [...Array(90)].map((_, i) => i / 90).concat([...Array(10)].map((_, i) => 9 + i / 10));
  const q = quantile(sample, [0, 100]);
  check("quantile spends screen space in proportion to data, not to units",
        q(1) - q(0) > 85, `the bulk (units 0-1) takes ${(q(1) - q(0)).toFixed(0)} of 100px`);
  check("quantile is monotone", q(0) <= q(0.5) && q(0.5) <= q(9) && q(9) <= q(10));
  check("percentileOf agrees with the scale", near(percentileOf(sample, 0.9), q(0.9) / 100, 1e-9));
}

/* ------------------------------------------------------------- quantiles */
{
  // numpy.percentile([1,2,3,4], [0,25,50,75,100]) -> 1, 1.75, 2.5, 3.25, 4
  const got = quantiles([1, 2, 3, 4], [0, 0.25, 0.5, 0.75, 1]);
  check("quantiles match numpy's default (type 7)",
        [1, 1.75, 2.5, 3.25, 4].every((want, i) => near(got[i], want)), got.join(" "));
}

/* ------------------------------------------------------------------- kde */
{
  // A standard normal, sampled deterministically through the inverse CDF, so this is a
  // fixed input and not a flaky random one. Acklam's rational approximation.
  const n = 400;
  const inv = (p) => {
    const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
               1.383577518672690e2, -3.066479806614716e1, 2.506628277459239];
    const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
               6.680131188771972e1, -1.328068155288572e1];
    const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
               -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
    const pl = 0.02425;
    if (p < pl) {
      const q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
    }
    if (p > 1 - pl) {
      const q = Math.sqrt(-2 * Math.log(1 - p));
      return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
    }
    const q = p - 0.5, r = q * q;
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q /
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
  };
  const normal = [...Array(n)].map((_, i) => inv((i + 0.5) / n));

  const { points, bandwidth } = kde1d(normal, { grid: 201 });
  const area = points.slice(1).reduce(
    (s, p, i) => s + ((p.y + points[i].y) / 2) * (p.x - points[i].x), 0);
  check("kde integrates to one", near(area, 1, 0.02), `area ${area.toFixed(4)}`);

  const peak = points.reduce((m, p) => (p.y > m.y ? p : m), points[0]);
  check("kde peaks at the mode", Math.abs(peak.x) < 0.15, `peak at x=${peak.x.toFixed(3)}`);
  check("kde peak height is near the normal's 0.399", Math.abs(peak.y - 0.3989) < 0.05,
        `peak y=${peak.y.toFixed(4)}`);
  // Every tenth value: a SUBSAMPLE of the same distribution. Taking the first forty would
  // have taken the left tail, whose spread is smaller for a reason that has nothing to do
  // with n — the exact confound this repository exists to catch.
  const thinned = normal.filter((_, i) => i % 10 === 0);
  check("silverman shrinks with n, holding the distribution fixed",
        silverman(normal) < silverman(thinned),
        `n=400 -> ${silverman(normal).toFixed(3)}, n=40 -> ${silverman(thinned).toFixed(3)}`);
  check("kde reports the bandwidth it drew at", bandwidth > 0);
}

/* ---------------------------------------------------------------- hexbin */
{
  const N = 5000;
  const xs = new Float64Array(N), ys = new Float64Array(N);
  let seed = 7;
  const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  for (let i = 0; i < N; i++) { xs[i] = rnd() * 400; ys[i] = rnd() * 300; }

  const bins = hexbin(xs, ys, 8);
  const counted = bins.reduce((s, b) => s + b.count, 0);
  check("hexbin loses no points", counted === N, `${counted} of ${N}`);
  check("hexbin assigns each point once", new Set(bins.flatMap((b) => b.indices)).size === N);
  check("hexbin is sorted sparse-first so dense cells paint last",
        bins.every((b, i) => i === 0 || bins[i - 1].count <= b.count));

  // Every point must land in the hexagon it is nearest to: the defining property, and the
  // one a naive single-candidate rounding gets wrong along the staggered rows.
  const r = 8, dx = r * Math.sqrt(3), dy = r * 1.5;
  let misassigned = 0;
  for (const b of bins) {
    for (const i of b.indices) {
      const d = Math.hypot(xs[i] - b.x, ys[i] - b.y);
      for (let rr = -2; rr <= 2; rr++) {
        const row = Math.round(b.y / dy) + rr;
        const shift = row & 1 ? dx / 2 : 0;
        for (let cc = -2; cc <= 2; cc++) {
          const cx = (Math.round((b.x - shift) / dx) + cc) * dx + shift;
          if (Math.hypot(xs[i] - cx, ys[i] - row * dy) < d - 1e-9) misassigned++;
        }
      }
    }
  }
  check("hexbin assigns every point to its nearest centre", misassigned === 0,
        `${misassigned} misassigned`);

  const filtered = hexbin(xs, ys, 8, (i) => i % 2 === 0);
  check("hexbin honours the filter without copying the arrays",
        filtered.reduce((s, b) => s + b.count, 0) === N / 2);
}

/* -------------------------------------------------------------- beeswarm */
{
  const positions = [...Array(60)].map((_, i) => 100 + (i % 7));
  const off = beeswarm(positions, 4);
  check("beeswarm returns one offset per point", off.length === positions.length);
  check("beeswarm keeps the measured axis untouched", off.every(Number.isFinite));
  let overlaps = 0;
  for (let i = 0; i < positions.length; i++)
    for (let j = i + 1; j < positions.length; j++)
      if (Math.hypot(positions[i] - positions[j], off[i] - off[j]) < 4 * 0.9) overlaps++;
  check("beeswarm separates points that would collide", overlaps === 0, `${overlaps} overlaps`);
  check("beeswarm is roughly symmetric about the centre line",
        Math.abs(off.reduce((s, o) => s + o, 0)) < 4 * 3,
        `net offset ${off.reduce((s, o) => s + o, 0).toFixed(2)}`);
}

/* ----------------------------------------------------------------- upset */
{
  // 10 items. A: 0-4. B: 3-7. C: 6-9. So A only 0-2, A&B 3-4, B only 5, B&C 6-7, C only 8-9.
  const r = upset(10, [
    { name: "A", has: (i) => i < 5 },
    { name: "B", has: (i) => i >= 3 && i < 8 },
    { name: "C", has: (i) => i >= 6 },
  ]);
  check("upset totals match the sets", r.totals.map((t) => t.size).join(",") === "5,5,4");
  check("upset finds every non-empty combination", r.combinations.length === 5,
        r.combinations.map((c) => `${c.members.join("&")}=${c.size}`).join(" "));
  check("upset sorts largest first",
        r.combinations.every((c, i) => i === 0 || r.combinations[i - 1].size >= c.size));
  check("upset partitions the items",
        r.combinations.reduce((s, c) => s + c.size, 0) + r.unflagged === 10);
  check("upset reports the unflagged rather than drawing them", r.unflagged === 0);

  const none = upset(4, [{ name: "A", has: () => false }]);
  check("upset draws no empty combination", none.combinations.length === 0 && none.unflagged === 4);
}

/* ------------------------------------------------------- interval domains
   The regression these guard is a figure that was actually shipped: a track built from the
   point estimates and clamped at zero, which drew an interval spanning zero identically to
   one bounded well above it. */
{
  const rows = [{ point: 1825, lo: -1753, hi: 5403 }, { point: 3, lo: 2, hi: 4 }];
  const [d0, d1] = intervalDomain(rows);
  check("domain reaches below the lowest LOWER bound", d0 < -1753, `${d0}`);
  check("domain reaches above the highest UPPER bound", d1 > 5403, `${d1}`);

  // A figure whose estimates are all positive still has to show the line they are judged
  // against, or "does it clear zero" is a question the drawing cannot answer.
  const pos = intervalDomain([{ point: 5, lo: 4, hi: 6 }]);
  check("domain always contains zero", pos[0] <= 0 && pos[1] >= 6, pos.join(","));

  // A reference the caller draws must be inside the domain or it lands on the frame edge and
  // reads as the boundary of the plot rather than as a threshold.
  const withRef = intervalDomain([{ point: 0.1, lo: 0.05, hi: 0.2 }], [1.96]);
  check("domain contains a reference outside the data", withRef[1] > 1.96, withRef.join(","));

  // A point with no interval must not collapse the domain onto itself.
  const bare = intervalDomain([{ point: 7 }]);
  check("a point with no interval still gets a domain with width", bare[1] > bare[0]);

  const c = clears({ point: 0.55, lo: 0.41, hi: 0.69 }, 0.5);
  check("clears distinguishes the point from the interval", c.point && !c.interval);
  const c2 = clears({ point: 0.55, lo: 0.52, hi: 0.58 }, 0.5);
  check("an interval above the bar clears on both", c2.point && c2.interval);
  const c3 = clears({ point: 0.55 }, 0.5);
  check("no interval never clears on the interval", c3.point && !c3.interval);
}

console.log(failures
  ? `\nviz: ${failures} check(s) failed.`
  : "\nviz: scales, density, hexbin, beeswarm, set arithmetic and interval domains all check out.");
process.exit(failures ? 1 : 0);
