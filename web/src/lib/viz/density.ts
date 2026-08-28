/** Density estimation and point layout — the arithmetic behind every form in this repository
 *  that is not a bar.
 *
 *  Pure functions over plain arrays, in their own module and not inside a component, for one
 *  reason: a kernel bandwidth or a hex radius is a STATISTICAL choice, and a statistical
 *  choice that lives inside a render function cannot be checked. `scripts/check-viz.mjs`
 *  exercises everything here against known answers.
 */

/** Quantiles by linear interpolation between order statistics (the R type-7 definition,
 *  which is what numpy and pandas use — so the site and the Python that produced its data
 *  cannot report different medians for the same array). */
export function quantiles(values: readonly number[], ps: readonly number[]): number[] {
  const v = Float64Array.from(values).sort();
  const n = v.length;
  if (!n) return ps.map(() => NaN);
  return ps.map((p) => {
    const h = (n - 1) * Math.min(1, Math.max(0, p));
    const lo = Math.floor(h);
    const hi = Math.ceil(h);
    return v[lo] + (h - lo) * (v[hi] - v[lo]);
  });
}

/** Silverman's rule of thumb, with the IQR term that makes it survive a heavy tail.
 *  Returned rather than applied, so a caller can print the bandwidth it drew at — a density
 *  curve without its bandwidth is an opinion about smoothness presented as a measurement. */
export function silverman(values: readonly number[]): number {
  const n = values.length;
  if (n < 2) return 1;
  const mean = values.reduce((s, x) => s + x, 0) / n;
  const sd = Math.sqrt(values.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1));
  const [q1, q3] = quantiles(values, [0.25, 0.75]);
  const spread = Math.min(sd || Infinity, (q3 - q1) / 1.349 || Infinity);
  const h = 0.9 * (Number.isFinite(spread) ? spread : sd || 1) * n ** (-1 / 5);
  return h > 0 ? h : 1;
}

export type DensityPoint = { x: number; y: number };

/** Gaussian kernel density on a regular grid.
 *
 *  O(grid x n) and deliberately so: at the sizes here (hundreds to low thousands) it is
 *  microseconds, and the obvious fast alternatives — binning first, or an FFT — each add a
 *  second smoothing whose width nobody would then be able to state.
 */
export function kde1d(
  values: readonly number[],
  opts: { bandwidth?: number; grid?: number; domain?: [number, number] } = {},
): { points: DensityPoint[]; bandwidth: number } {
  const n = values.length;
  const bandwidth = opts.bandwidth ?? silverman(values);
  const grid = opts.grid ?? 96;
  if (!n) return { points: [], bandwidth };

  const [lo, hi] = opts.domain ?? [
    Math.min(...values) - 3 * bandwidth,
    Math.max(...values) + 3 * bandwidth,
  ];
  const step = (hi - lo) / Math.max(1, grid - 1);
  const norm = 1 / (n * bandwidth * Math.sqrt(2 * Math.PI));

  const points: DensityPoint[] = [];
  for (let g = 0; g < grid; g++) {
    const x = lo + g * step;
    let acc = 0;
    for (let i = 0; i < n; i++) {
      const u = (x - values[i]) / bandwidth;
      // Beyond four bandwidths the gaussian contributes less than 1e-4 of its peak; the
      // cutoff is what keeps this linear enough to run on every render.
      if (u > -4 && u < 4) acc += Math.exp(-0.5 * u * u);
    }
    points.push({ x, y: acc * norm });
  }
  return { points, bandwidth };
}

export type HexBin = { x: number; y: number; count: number; indices: number[] };

/** Hexagonal binning in SCREEN space.
 *
 *  WHY HEXAGONS AND NOT SQUARES. A hexagon's centre is equidistant from all six neighbours,
 *  so a point's assignment does not depend on which axis it drifted along; square bins
 *  produce visible horizontal and vertical banding in exactly the dense regions the plot
 *  exists to show. It is the standard answer for over-plotted clouds above a few thousand
 *  marks (Carr et al., 1987).
 *
 *  Binning happens after the scales have been applied, because the bins have to be regular
 *  on the page — on a log or symlog axis, bins regular in data units are not.
 */
export function hexbin(
  xs: ArrayLike<number>, ys: ArrayLike<number>, radius: number,
  keep?: (i: number) => boolean,
): HexBin[] {
  const dx = radius * Math.sqrt(3);
  const dy = radius * 1.5;
  const bins = new Map<string, HexBin>();

  for (let i = 0; i < xs.length; i++) {
    if (keep && !keep(i)) continue;
    const px = xs[i], py = ys[i];
    if (!Number.isFinite(px) || !Number.isFinite(py)) continue;

    // Candidate row/column, then the nearer of the two staggered centres — the standard
    // two-candidate test, which is exact for a hex lattice.
    const row = Math.round(py / dy);
    const shift = row & 1 ? dx / 2 : 0;
    const col = Math.round((px - shift) / dx);
    const cx = col * dx + shift;
    const cy = row * dy;

    const rowAlt = row + (py > cy ? 1 : -1);
    const shiftAlt = rowAlt & 1 ? dx / 2 : 0;
    const colAlt = Math.round((px - shiftAlt) / dx);
    const cxAlt = colAlt * dx + shiftAlt;
    const cyAlt = rowAlt * dy;

    const near = (px - cx) ** 2 + (py - cy) ** 2 <= (px - cxAlt) ** 2 + (py - cyAlt) ** 2;
    const [kx, ky, kc, kr] = near ? [cx, cy, col, row] : [cxAlt, cyAlt, colAlt, rowAlt];

    const key = `${kc},${kr}`;
    const bin = bins.get(key);
    if (bin) { bin.count++; bin.indices.push(i); }
    else bins.set(key, { x: kx, y: ky, count: 1, indices: [i] });
  }
  // Sparse bins last, so the densest cells paint on top and a single outlier cannot hide
  // the core of the distribution behind it.
  return [...bins.values()].sort((a, b) => a.count - b.count);
}

/** The path of one hexagon of the given radius, centred on the origin. Flat-top orientation,
 *  matching the lattice `hexbin` lays out. */
export function hexPath(radius: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i + Math.PI / 6;
    pts.push(`${(radius * Math.cos(a)).toFixed(3)},${(radius * Math.sin(a)).toFixed(3)}`);
  }
  return `M${pts.join("L")}Z`;
}

/** Beeswarm: one-dimensional dodge, so every observation keeps its exact position on the
 *  measured axis and is displaced only on the axis that means nothing.
 *
 *  This is the honest alternative to jitter, which displaces on BOTH axes and therefore
 *  moves points away from the value they represent. Values arrive in screen units; the
 *  returned offset is in screen units too.
 */
export function beeswarm(positions: readonly number[], diameter: number): number[] {
  const order = positions.map((p, i) => [p, i] as const).sort((a, b) => a[0] - b[0]);
  const offsets = new Array<number>(positions.length).fill(0);
  const placed: { p: number; o: number }[] = [];

  for (const [p, i] of order) {
    // Only neighbours within one diameter can collide, and the list is sorted, so the scan
    // is bounded by the local density rather than by n.
    const near = placed.filter((q) => Math.abs(q.p - p) < diameter);
    let o = 0;
    if (near.length) {
      // Try alternating offsets outward from the centre line until one is free. The result
      // is the familiar symmetrical swarm rather than a one-sided pile.
      for (let k = 0; k < 400; k++) {
        const cand = (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (diameter * 0.85);
        if (near.every((q) => Math.hypot(q.p - p, q.o - cand) >= diameter * 0.98)) { o = cand; break; }
        o = cand;
      }
    }
    offsets[i] = o;
    placed.push({ p, o });
  }
  return offsets;
}
