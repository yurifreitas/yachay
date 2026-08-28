/** The colour system, in OKLCH, resolved to hex for chart libraries.
 *
 * ECharts cannot read CSS custom properties — it needs literal colours — so the scales
 * live here as OKLCH triples and are converted on demand. Keeping the definitions in
 * OKLCH rather than as hex constants is what makes the dark variants a *re-step* rather
 * than an inversion: lightness is perceptual, so "same colour, one band lighter" is a
 * number you can write down.
 *
 * THREE SCALES, THREE JOBS. Using one where another belongs is the most common charting
 * error there is, so they are separated by type rather than by convention:
 *
 *   categorical  identity, no order          6 hues, staggered lightness
 *   sequential   magnitude, one direction    one hue, monotone lightness
 *   diverging    polarity around a midpoint  two hues, NEUTRAL at the middle
 *
 * A calibrated z-score is genuinely diverging — zero is "the null", above is real signal,
 * below is less than nothing — which is why the diverging scale exists here at all and is
 * not decoration.
 *
 * VALIDATED, and this time by a validator that exists. The previous note here cited
 * `scripts/validate_palette.js` — **a file that was not in the repository**, so its numbers
 * could not be reproduced or re-checked after an edit. `scripts/check-palette.mjs` replaces
 * it and runs in the build.
 *
 * Its first run failed the scale it was written to confirm. Under a deuteranopia model,
 * series 1 (yellow) and 4 (red) sat at **dE 1.4 in dark** and 3.8 in light — the same
 * colour, for roughly 8 % of men, in a scale documented as validated. The lightness values
 * below are the assignment that clears CIEDE2000 >= 12 for EVERY pair under normal,
 * deuteranopic and protanopic vision, while each series still holds 3:1 against its own
 * ground. Measured worst pair: **15.0 light / 16.0 dark**.
 *
 * THE COST IS DELIBERATE AND WORTH NAMING. Lightness is no longer near-uniform across the
 * six, so the series do not carry identical visual weight — which a categorical scale
 * normally wants. Red-green deficiency collapses exactly the channel that six well-spread
 * hues rely on, so lightness is the only axis left to separate them on. The alternative was
 * a scale that is provably unreadable for some readers, and weight balance does not outrank
 * that. Where the difference between two series matters, they must still be directly
 * labelled: colour is never the only carrier.
 */

export type Oklch = [L: number, C: number, H: number];

/** OKLCH -> sRGB hex (Ottosson's oklab). Clamped, so out-of-gamut steps degrade to the
 *  nearest displayable colour rather than throwing. */
export function oklchToHex([L, C, H]: Oklch): string {
  const h = (H * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ ** 3;
  const m = m_ ** 3;
  const s = s_ ** 3;
  const r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  const g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  const bl = -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s;
  const f = (v: number) => {
    const c = v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(Math.max(v, 0), 1 / 2.4) - 0.055;
    return Math.round(Math.min(1, Math.max(0, c)) * 255);
  };
  return "#" + [f(r), f(g), f(bl)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

/* --- categorical: identity. Hues far apart, lightness staggered so neighbours differ
       on two channels rather than one. Six is the cap: a seventh series folds into
       "other" or becomes small multiples. ------------------------------------------- */
const CAT_LIGHT: Oklch[] = [
  [0.34, 0.17, 264], [0.40, 0.15, 85], [0.60, 0.15, 310],
  [0.45, 0.15, 165], [0.50, 0.17, 15], [0.55, 0.12, 205],
];
const CAT_DARK: Oklch[] = [
  [0.52, 0.17, 264], [0.58, 0.15, 85], [0.84, 0.15, 310],
  [0.64, 0.15, 165], [0.70, 0.17, 15], [0.76, 0.12, 205],
];

/* --- sequential: magnitude. One hue, lightness falling monotonically. Never a rainbow:
       an ordered variable read through unordered hues is unreadable, however pretty. -- */
const SEQ_LIGHT: Oklch[] = [
  [0.93, 0.03, 300], [0.82, 0.09, 300], [0.70, 0.15, 300], [0.57, 0.19, 300], [0.44, 0.17, 300],
];
const SEQ_DARK: Oklch[] = [
  [0.32, 0.05, 300], [0.44, 0.12, 300], [0.56, 0.17, 300], [0.68, 0.16, 300], [0.82, 0.11, 300],
];

/* --- diverging: polarity. Two hues meeting at a NEUTRAL, never at a third hue, because a
       coloured midpoint reads as a category of its own and hides the zero. ------------ */
const DIV_LIGHT: Oklch[] = [
  [0.42, 0.15, 258], [0.58, 0.12, 258], [0.75, 0.07, 258],
  [0.94, 0.008, 258],
  [0.75, 0.09, 42], [0.58, 0.14, 42], [0.44, 0.15, 42],
];
const DIV_DARK: Oklch[] = [
  [0.72, 0.13, 258], [0.62, 0.14, 258], [0.50, 0.11, 258],
  [0.30, 0.008, 258],
  [0.50, 0.13, 42], [0.62, 0.15, 42], [0.72, 0.14, 42],
];

export type Mode = "light" | "dark";

export const categorical = (mode: Mode) => (mode === "dark" ? CAT_DARK : CAT_LIGHT).map(oklchToHex);
export const sequential = (mode: Mode) => (mode === "dark" ? SEQ_DARK : SEQ_LIGHT).map(oklchToHex);
export const diverging = (mode: Mode) => (mode === "dark" ? DIV_DARK : DIV_LIGHT).map(oklchToHex);

/** Chart ink, pulled from the page's own tokens so a chart never invents a grey. */
export function chartInk(mode: Mode) {
  return mode === "dark"
    ? { text: "#f1f2ef", muted: "#9aa1a8", grid: "rgba(255,255,255,0.07)", surface: "#1a1d20" }
    : { text: "#16181b", muted: "#6b727a", grid: "rgba(0,0,0,0.07)", surface: "#ffffff" };
}

/** The viewer's resolved mode: explicit stamp wins, otherwise the OS setting. */
export function resolveMode(): Mode {
  const stamped = document.documentElement.getAttribute("data-theme");
  if (stamped === "dark" || stamped === "light") return stamped;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/* --- identity: a LOOKUP scale, and explicitly not the categorical one above -----------

   The categorical scale is capped at six because six is where a reader stops being able to
   hold a legend in their head while comparing series. That cap is right and it stays.

   This scale exists for a different job. A cancer dashboard has 24 lineages and 37 subtypes,
   and they are never six competing series in one frame — they are the *identity* of a row, a
   dot, a small multiple. The reader is not asked "which of these 24 is largest"; they are
   asked "find the one I clicked, and recognise it again in the next panel". That is a lookup,
   and a lookup can carry far more hues than a comparison can, on two conditions:

     1. Every mark is DIRECTLY LABELLED. Colour is the confirmation, never the only carrier.
        Nothing here is legend-only — that is the failure mode this scale invites and the one
        the panels are built to avoid.
     2. Lightness and chroma are held CONSTANT and only hue turns. Varying all three is what
        makes a 24-colour scale read as a ranking it does not encode.

   Golden-angle hue stepping rather than an even division: consecutive indices land far apart
   on the hue circle, so a list read top to bottom never puts two near-hues adjacent, which is
   exactly what an even 360/n division does at every wrap. */

const IDENTITY_L_LIGHT = 0.63;
const IDENTITY_L_DARK = 0.7;
const IDENTITY_C = 0.135;
const GOLDEN_ANGLE = 137.508;

/** Stable colour for the i-th member of a named set. Stable in i, so a subgroup keeps its
 *  colour across panels and across a level switch that reorders the list. */
export function identityHue(i: number, dark = false): string {
  const h = (i * GOLDEN_ANGLE + 25) % 360;
  return oklchToHex([dark ? IDENTITY_L_DARK : IDENTITY_L_LIGHT, IDENTITY_C, h]);
}

/** Colours for a whole named set, keyed by name so the mapping survives re-sorting.
 *  Names are sorted before assignment for exactly that reason: index in a sorted list is
 *  stable, index in a display order is not. */
export function identityScale(names: string[], dark = false): Record<string, string> {
  const sorted = [...new Set(names)].sort();
  const out: Record<string, string> = {};
  sorted.forEach((n, i) => { out[n] = identityHue(i, dark); });
  return out;
}
