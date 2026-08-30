/** A grid track that cannot shrink is a horizontal scrollbar waiting for a wide table.
 *
 *  WHY. `grid-template-columns: 1fr` does not mean "one flexible column". `1fr` is
 *  `minmax(auto, 1fr)`, and that `auto` minimum is the item's MIN-CONTENT — so a six-column
 *  table inside it refuses to shrink, the track grows past the viewport, and the whole
 *  document scrolls sideways. `overflow-x: auto` on the table's own wrapper cannot help,
 *  because the wrapper is not allowed to be narrower than the table it wraps.
 *
 *  This shipped. `RarePage.module.css` collapsed to `1fr` below 1200px — every laptop and
 *  every phone — and on the sections carrying wide tables the breadcrumb was clipped off the
 *  right edge three screens above the table that caused it. Thirty-seven declarations across
 *  the site had the same shape, all of them in the narrow-viewport media queries where the
 *  failure is most likely.
 *
 *  The fix is `minmax(0, 1fr)`, which behaves identically except that the item may shrink.
 *  There is no case in this codebase that wants the other behaviour, so the check is total.
 */
import { readFileSync } from "node:fs";
import { globSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");

const files = globSync("**/*.css", { cwd: SRC });
const hits = [];

for (const rel of files) {
  const text = readFileSync(join(SRC, rel), "utf8");
  text.split("\n").forEach((line, i) => {
    // `1fr` as a whole track, anywhere in the list. `minmax(...)`, `auto`, fixed widths and
    // `repeat(n, minmax(0, 1fr))` are all fine; a bare `1fr` track is not.
    const m = line.match(/grid-template-columns:\s*([^;}]+)/);
    if (!m) return;
    const tracks = m[1].trim();
    // Split on top-level whitespace, ignoring the inside of minmax()/repeat().
    const top = tracks.replace(/\([^)]*\)/g, "()").split(/\s+/);
    if (top.some((t) => t === "1fr")) {
      hits.push({ file: rel, line: i + 1, decl: tracks.slice(0, 72) });
    }
  });
}

if (hits.length) {
  console.error("layout: grid tracks that cannot shrink below their content");
  for (const h of hits) {
    console.error(`  ${h.file}:${h.line}  ${h.decl}`);
  }
  console.error(
    `\n${hits.length} bare \`1fr\` track(s). Use \`minmax(0, 1fr)\`: identical layout, but the`
    + ` item is allowed to be narrower than its widest child. A bare 1fr scrolls the whole`
    + ` document sideways the first time a wide table lands in it.`);
  process.exit(1);
}

console.log(`layout: ${files.length} sheets, no grid track that refuses to shrink.`);
