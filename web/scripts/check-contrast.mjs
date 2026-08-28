/**
 * Contrast gate for the design tokens, in BOTH themes.
 *
 * WHY THIS EXISTS. The cancer section shipped with `--r-text-3` — the token carrying the
 * lede, every panel subtitle, every axis note and every KPI caption — at **3.44:1 in light
 * mode**, against a 4.5:1 requirement. `--unknown`, which carries the warning states and the
 * "moved off the registered value" marker, was at **3.05:1**. Both are the colours a reader
 * is most likely to need and least likely to be able to guess from context.
 *
 * Nothing caught it because nothing looked: the work was done in a dark-mode browser and the
 * light palette was never rendered. A theme that is never opened is a theme that is never
 * tested, and "I checked it by eye" does not survive a second theme, a second developer, or a
 * token edit six months later.
 *
 * So the check is arithmetic and runs in CI. It reads the token files, resolves every
 * text-bearing token against every surface it can legally sit on, and fails the build on a
 * pair below its WCAG 2.1 threshold. It deliberately checks the TOKENS rather than a rendered
 * page: a page test needs a browser and only covers the routes someone remembered to visit,
 * while the token pairs are the whole space.
 *
 *     node scripts/check-contrast.mjs
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const TOKENS = join(HERE, "..", "src", "design", "rare-tokens.css");

/* --- colour ------------------------------------------------------------------------ */

/** OKLCH -> linear sRGB (Ottosson's oklab), clamped. Mirrors lib/palette.ts. */
function oklchToRgb(L, C, H) {
  const h = (H * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ].map((v) => Math.min(1, Math.max(0, v)));
}

/** Relative luminance from LINEAR rgb — no gamma round-trip, so no rounding drift. */
const luminance = ([r, g, b]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

const contrast = (a, b) => {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};

/* --- parsing --------------------------------------------------------------------- */

const css = readFileSync(TOKENS, "utf8");

/** Tokens declared inside the light `:root {` block and inside the dark override. */
function parseTheme(source, { dark }) {
  // The dark block is the one guarded by prefers-color-scheme; light is everything before it.
  const cut = source.indexOf("@media (prefers-color-scheme: dark)");
  const region = dark ? source.slice(cut) : source.slice(0, cut);
  const out = {};
  for (const m of region.matchAll(/--([a-z0-9-]+):\s*oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\s*\)/g)) {
    out[m[1]] = oklchToRgb(Number(m[2]) / 100, Number(m[3]), Number(m[4]));
  }
  return out;
}

/* --- the pairs that must hold ------------------------------------------------------ */

/** Every surface a token may legally sit on. A token is checked against ALL of them,
 *  because a component author picks the surface, not the token author. */
const SURFACES = ["r-bg", "r-surface", "r-surface-2"];

/** token -> the smallest text it is used at, which sets the threshold.
 *  4.5 is body text; 3.0 applies only to text at 24px, or 18.66px bold. */
const TEXT_TOKENS = {
  "r-text": 4.5,
  "r-text-2": 4.5,
  "r-text-3": 4.5,     // lede, panel subtitles, axis notes, KPI captions — all small
  "r-brand": 4.5,      // hit counts, links, the active tab label
  known: 4.5,          // "survives" pills and the controls table's recovered ranks
  unknown: 4.5,        // warning text, the burden-proxy badge, a moved gate value
  partial: 4.5,
};

let failures = 0;
let checked = 0;

for (const dark of [false, true]) {
  const theme = parseTheme(css, { dark });
  const label = dark ? "dark " : "light";
  for (const [token, need] of Object.entries(TEXT_TOKENS)) {
    const fg = theme[token];
    if (!fg) {
      console.error(`  ${label}  ${token}: not defined`);
      failures++;
      continue;
    }
    for (const surfaceName of SURFACES) {
      const bg = theme[surfaceName];
      if (!bg) continue;
      checked++;
      const ratio = contrast(fg, bg);
      if (ratio < need) {
        failures++;
        console.error(
          `  ${label}  --${token} on --${surfaceName}: ${ratio.toFixed(2)}:1 `
          + `(needs ${need}:1)`);
      }
    }
  }
}

if (failures) {
  console.error(`\ncontrast: ${failures} failing pair(s) of ${checked} checked.`);
  console.error("A token below its threshold is unreadable for some readers on every page "
    + "that uses it. Adjust the LIGHTNESS in src/design/rare-tokens.css — hue and chroma can "
    + "usually stay.");
  process.exit(1);
}

console.log(`contrast: ${checked} token/surface pairs checked in both themes, all pass.`);
