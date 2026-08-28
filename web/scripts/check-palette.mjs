/**
 * Palette gate: are two colours a reader must tell apart actually distinguishable —
 * including for the ~8 % of men with a red-green colour vision deficiency.
 *
 * WHY THIS FILE EXISTS, AND WHAT IT REPLACES. `src/lib/palette.ts` carried this claim:
 *
 *     "VALIDATED. The categorical scale passes the six checks against both grounds
 *      (`scripts/validate_palette.js`, adjacent pairlist): worst adjacent normal-vision
 *      dE 29.9 light / 28.4 dark."
 *
 * **`scripts/validate_palette.js` was not in the repository.** The numbers could not be
 * reproduced, re-run, or checked after any edit — a claim of validation resting on a
 * validator nobody could execute. Same class of defect as a threshold with no manifest.
 *
 * And the gap had already been exploited: the `identityHue` scale added for the cancer
 * section spreads 24+ lineages around the hue circle and had **never been checked at all**,
 * in any vision model. A 24-hue scale is exactly where confusable pairs hide.
 *
 * WHAT IS CHECKED. Two scales, three vision models, both grounds:
 *
 *   categorical  6 hues, every pair — they appear together as series and any two may be
 *                compared directly.
 *   identity     the 24 lineages and 37 subtypes actually rendered, ADJACENT pairs in the
 *                sorted order the UI assigns. Not every pair: with 37 marks some collisions
 *                are unavoidable and the design does not rely on telling any two apart —
 *                every mark is directly labelled (see the note in palette.ts). What must
 *                hold is that neighbours in a list are separable, since those are the ones a
 *                reader scans against each other.
 *
 * Distance is CIEDE2000. Deficiency is simulated with Brettel/Viénot-style projection onto
 * the dichromat plane in linear RGB.
 *
 *     node scripts/check-palette.mjs
 */

/* --- colour space ------------------------------------------------------------------ */

function oklchToLinear(L, C, H) {
  const h = (H * Math.PI) / 180;
  const a = C * Math.cos(h), b = C * Math.sin(h);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ].map((v) => Math.min(1, Math.max(0, v)));
}

const toLab = (rgb) => {
  const [X, Y, Z] = [
    0.4124564 * rgb[0] + 0.3575761 * rgb[1] + 0.1804375 * rgb[2],
    0.2126729 * rgb[0] + 0.7151522 * rgb[1] + 0.0721750 * rgb[2],
    0.0193339 * rgb[0] + 0.1191920 * rgb[1] + 0.9503041 * rgb[2],
  ];
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const fx = f(X / 0.95047), fy = f(Y), fz = f(Z / 1.08883);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
};

/** CIEDE2000. Long, standard, and the reason the numbers below mean something. */
function deltaE(lab1, lab2) {
  const [L1, a1, b1] = lab1, [L2, a2, b2] = lab2;
  const avgL = (L1 + L2) / 2;
  const C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2);
  const avgC = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(avgC ** 7 / (avgC ** 7 + 25 ** 7)));
  const a1p = a1 * (1 + G), a2p = a2 * (1 + G);
  const C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
  const avgCp = (C1p + C2p) / 2;
  const deg = (r) => ((r * 180) / Math.PI + 360) % 360;
  const h1p = C1p === 0 ? 0 : deg(Math.atan2(b1, a1p));
  const h2p = C2p === 0 ? 0 : deg(Math.atan2(b2, a2p));
  let dhp = h2p - h1p;
  if (Math.abs(dhp) > 180) dhp -= Math.sign(dhp) * 360;
  const dLp = L2 - L1, dCp = C2p - C1p;
  const dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin((dhp * Math.PI) / 360);
  let avghp = (h1p + h2p) / 2;
  if (Math.abs(h1p - h2p) > 180) avghp += 180;
  const T = 1 - 0.17 * Math.cos(((avghp - 30) * Math.PI) / 180)
    + 0.24 * Math.cos((2 * avghp * Math.PI) / 180)
    + 0.32 * Math.cos(((3 * avghp + 6) * Math.PI) / 180)
    - 0.20 * Math.cos(((4 * avghp - 63) * Math.PI) / 180);
  const SL = 1 + (0.015 * (avgL - 50) ** 2) / Math.sqrt(20 + (avgL - 50) ** 2);
  const SC = 1 + 0.045 * avgCp;
  const SH = 1 + 0.015 * avgCp * T;
  const RT = -2 * Math.sqrt(avgCp ** 7 / (avgCp ** 7 + 25 ** 7))
    * Math.sin((60 * Math.exp(-(((avghp - 275) / 25) ** 2)) * Math.PI) / 180);
  return Math.sqrt(
    (dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH));
}

/** Dichromat simulation in linear RGB (Viénot/Brettel projection). */
const DICHROMAT = {
  deuteranopia: [[0.625, 0.375, 0], [0.7, 0.3, 0], [0, 0.3, 0.7]],
  protanopia: [[0.567, 0.433, 0], [0.558, 0.442, 0], [0, 0.242, 0.758]],
};
const simulate = (rgb, kind) => {
  if (kind === "normal") return rgb;
  const M = DICHROMAT[kind];
  return M.map((row) => Math.min(1, Math.max(0,
    row[0] * rgb[0] + row[1] * rgb[1] + row[2] * rgb[2])));
};

/* --- the scales, mirrored from src/lib/palette.ts ---------------------------------- */

const CAT_LIGHT = [
  [0.34, 0.17, 264], [0.40, 0.15, 85], [0.60, 0.15, 310],
  [0.45, 0.15, 165], [0.50, 0.17, 15], [0.55, 0.12, 205],
];
const CAT_DARK = [
  [0.52, 0.17, 264], [0.58, 0.15, 85], [0.84, 0.15, 310],
  [0.64, 0.15, 165], [0.70, 0.17, 15], [0.76, 0.12, 205],
];
const GOLDEN_ANGLE = 137.508;
const identity = (i, dark) =>
  [dark ? 0.7 : 0.63, 0.135, (i * GOLDEN_ANGLE + 25) % 360];

/** How far apart two colours must be. Categorical series are compared directly against each
 *  other, so they carry the higher bar; identity marks are labelled and only need a
 *  neighbour in a list to look different. Both are floors, not targets. */
const MIN_CATEGORICAL = 12;
const MIN_IDENTITY = 6;

/** A series must also be visible AGAINST ITS GROUND. Separability from the other series and
 *  visibility on the page are different requirements, and a search that optimises only the
 *  first will happily return a colour that vanishes into the background. 3:1 is the WCAG
 *  non-text contrast minimum, which is what a chart mark is. */
const GROUND = { light: [0.986, 0.004, 258], dark: [0.17, 0.013, 258] };
const MIN_GROUND = 3;

const relLum = (rgb) => 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
const contrast = (a, b) => {
  const [x, y] = [relLum(a), relLum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};

let failures = 0;
const report = [];

function checkGround(name, set, dark) {
  const ground = oklchToLinear(...GROUND[dark ? "dark" : "light"]);
  let worst = { c: Infinity, i: null };
  set.forEach((c, i) => {
    const r = contrast(oklchToLinear(...c), ground);
    if (r < worst.c) worst = { c: r, i };
  });
  const ok = worst.c >= MIN_GROUND;
  if (!ok) failures++;
  report.push(`  ${ok ? "ok  " : "FAIL"}  ${name} ${dark ? "dark " : "light"} `
    + `on-ground      worst ${worst.c.toFixed(2)}:1 (floor ${MIN_GROUND}) at #${worst.i}`);
}

function check(name, pairs, floor, dark) {
  for (const vision of ["normal", "deuteranopia", "protanopia"]) {
    let worst = { d: Infinity, a: null, b: null };
    for (const [i, j, ci, cj] of pairs) {
      const d = deltaE(
        toLab(simulate(oklchToLinear(...ci), vision)),
        toLab(simulate(oklchToLinear(...cj), vision)));
      if (d < worst.d) worst = { d, a: i, b: j };
    }
    const ok = worst.d >= floor;
    if (!ok) failures++;
    report.push(
      `  ${ok ? "ok  " : "FAIL"}  ${name} ${dark ? "dark " : "light"} `
      + `${vision.padEnd(13)} worst dE ${worst.d.toFixed(1)} `
      + `(floor ${floor}) between #${worst.a} and #${worst.b}`);
  }
}

for (const dark of [false, true]) {
  const cat = dark ? CAT_DARK : CAT_LIGHT;
  const catPairs = [];
  for (let i = 0; i < cat.length; i++)
    for (let j = i + 1; j < cat.length; j++) catPairs.push([i, j, cat[i], cat[j]]);
  check("categorical (all pairs)", catPairs, MIN_CATEGORICAL, dark);
  checkGround("categorical", cat, dark);

  // The counts the cancer section actually renders.
  for (const n of [24, 37]) {
    const adj = [];
    for (let i = 0; i + 1 < n; i++)
      adj.push([i, i + 1, identity(i, dark), identity(i + 1, dark)]);
    check(`identity n=${n} (adjacent)`, adj, MIN_IDENTITY, dark);
  }
}

console.log(report.join("\n"));
if (failures) {
  console.error(`\npalette: ${failures} check(s) failed.`);
  process.exit(1);
}
console.log("\npalette: all scales separable in both grounds and all three vision models.");
