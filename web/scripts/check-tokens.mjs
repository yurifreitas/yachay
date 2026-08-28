/** Every custom property a stylesheet uses must be one a stylesheet defines.
 *
 *  WHY THIS EXISTS. `padding: var(--sp-5)` appeared in eleven places across five components.
 *  There is no `--sp-5` — the scale is 4·8·12·16·24·32·48·64·96 and 20px is deliberately off
 *  it — so every one of those declarations was invalid at computed-value time and the
 *  padding fell back to zero. Cards had been rendering with their text against the border
 *  for days.
 *
 *  NOTHING FAILS WHEN THIS HAPPENS. No build error, no console warning, no visual break
 *  loud enough to notice: an element with no padding still looks like an element. It is the
 *  exact shape of defect this repository keeps finding elsewhere — a wrong answer that
 *  arrives looking like an answer — and the fix is the same one: a gate that reads the files
 *  rather than a person who remembers the scale.
 *
 *  Run in `npm run check`, beside contrast, palette, viz and shards.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const SRC = join(import.meta.dirname, "..", "src");

/** Every .css file under src/. */
function sheets(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) out.push(...sheets(path));
    else if (entry.endsWith(".css")) out.push(path);
  }
  return out;
}

const files = sheets(SRC);

/** Properties set from a component at runtime — `style={{ ["--cols"]: n }}`.
 *
 *  These are legitimately absent from every stylesheet: the value arrives from the data, and
 *  a bar whose width is a percentage cannot be a static token. Without this pass the gate
 *  fails on every runtime-driven value, which is the fastest way to get a gate switched off.
 */
function runtimeTokens(dir) {
  const out = new Set();
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      for (const t of runtimeTokens(path)) out.add(t);
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      const text = readFileSync(path, "utf8");
      for (const m of text.matchAll(/\[\s*["'`](--[\w-]+)["'`]/g)) out.add(m[1]);
    }
  }
  return out;
}

// Definitions: `--name:` anywhere. Collected across every sheet, because a token defined in
// tokens.css is legitimately used in a component's module.
const defined = new Set();
// Uses: `var(--name)` or `var(--name, fallback)`.
const used = new Map();

for (const t of runtimeTokens(SRC)) defined.add(t);

for (const path of files) {
  const text = readFileSync(path, "utf8");
  for (const m of text.matchAll(/(--[\w-]+)\s*:/g)) defined.add(m[1]);
  for (const m of text.matchAll(/var\(\s*(--[\w-]+)\s*([,)])/g)) {
    // A var() with a fallback still renders something, so it is not a silent failure.
    if (m[2] === ",") continue;
    if (!used.has(m[1])) used.set(m[1], []);
    used.get(m[1]).push(relative(SRC, path));
  }
}

const missing = [...used.entries()].filter(([name]) => !defined.has(name));

if (missing.length) {
  console.log("tokens: undefined custom properties, each one silently zero:\n");
  for (const [name, where] of missing.sort((a, b) => b[1].length - a[1].length)) {
    const files = [...new Set(where)];
    console.log(`  ${name}  ${where.length} use(s) in ${files.length} file(s)`);
    for (const f of files.slice(0, 6)) console.log(`      ${f}`);
  }
  const scale = [...defined].filter((d) => d.startsWith("--sp-")).sort(
    (a, b) => Number(a.slice(5)) - Number(b.slice(5)));
  console.log(`\n  the spacing scale is: ${scale.join(" ")}`);
  process.exit(1);
}

console.log(`tokens: ${used.size} custom properties used, all defined `
  + `(${defined.size} declared across ${files.length} sheets).`);
