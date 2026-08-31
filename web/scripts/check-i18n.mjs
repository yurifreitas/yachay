/** Prose that only exists in one language, counted.
 *
 *  WHY. This site has a language switch, and the switch is a promise. A reader who picks PT
 *  gets Portuguese chrome, Portuguese navigation and Portuguese section headings — and then
 *  hits a four-line figure caption in English. That is worse than an English-only site,
 *  because the switch said it had been handled.
 *
 *  WHAT COUNTS AS A VIOLATION. A run of prose written as a literal in a feature component
 *  rather than routed through `tt(...)`. Two kinds are deliberately NOT violations:
 *
 *    artefact prose   `{d.says}`, `{d.method}` — these come from the Python artefacts, which
 *                     are English by repository convention (sieve-doc §7: repository prose is
 *                     English). Translating them would mean translating the analysis layer,
 *                     which is a different and much larger decision than this check.
 *    short labels     under MIN_WORDS. "mutation", "drug", "z" are column headers, and a
 *                     table header in English inside a Portuguese page is a far smaller
 *                     failure than a paragraph.
 *
 *  So this counts PARAGRAPHS a reader has to read in the wrong language, which is the thing
 *  the switch actually broke.
 *
 *  It reports rather than fails, for now, because the count is the point: an unmeasured
 *  "the UI feels mixed" cannot be paid down, and a gate that fails on thirty pre-existing
 *  violations is a gate somebody disables.
 */
import { readFileSync } from "node:fs";
import { globSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");

/** Below this, a literal is a label rather than prose. */
const MIN_WORDS = 8;

const files = globSync("features/**/*.tsx", { cwd: SRC }).map((f) => join(SRC, f));

let total = 0;
const byFile = new Map();

for (const file of files) {
  const text = readFileSync(file, "utf8");
  // JSX text runs: between > and <, excluding anything holding an interpolation, a tag, or
  // an obvious identifier. Crude by design — this is a counter, not a parser, and it says so.
  const runs = text.match(/>[^<>{}]{40,}</g) ?? [];
  const hits = [];
  for (const run of runs) {
    const s = run.slice(1, -1).replace(/\s+/g, " ").trim();
    if (!s || s.startsWith("//") || s.startsWith("*")) continue;
    if (s.split(/\s+/).length < MIN_WORDS) continue;
    // ⚠️ THE FIRST VERSION OF THIS CHECK COUNTED CODE AS PROSE. JavaScript uses `<` and `>`
    // as operators, so a run between them catches `d.driver === pick) ?? drivers[0]` just as
    // happily as a sentence. It reported 358 violations, and the number was wrong in a way
    // that would have been quoted. A counter that counts the wrong things is worse than no
    // counter, because it produces a number somebody trusts.
    //
    // Prose does not contain these. A sentence with a semicolon in it also has letters
    // around the semicolon, and the ratio test below catches what this does not.
    if (/[;=(){}[\]]|=>|\?\?|\.\w+\(/.test(s)) continue;
    // At least four fifths letters, spaces and ordinary punctuation. Identifiers and
    // expressions fail this; sentences pass it comfortably.
    const proseChars = (s.match(/[\p{L}\s.,:;'"’—–-]/gu) ?? []).length;
    if (proseChars / s.length < 0.92) continue;
    // A sentence starts with a word, not with an operator or a fragment of one.
    if (!/^[\p{Lu}\p{Ll}"'“]/u.test(s)) continue;
    // Portuguese markers: if the run already carries them it is not an English-only literal.
    if (/[ãõçáéíóúâêô]|\b(que|não|uma|para|com|dos|das|pelo|pela)\b/i.test(s)) continue;
    hits.push(s.slice(0, 70));
  }
  if (hits.length) {
    byFile.set(relative(SRC, file).replace(/\\/g, "/"), hits);
    total += hits.length;
  }
}

const sorted = [...byFile.entries()].sort((a, b) => b[1].length - a[1].length);
console.log(`i18n: ${total} single-language prose runs in ${byFile.size} feature files\n`);
for (const [file, hits] of sorted.slice(0, 12)) {
  console.log(`  ${String(hits.length).padStart(3)}  ${file}`);
  console.log(`       e.g. "${hits[0]}…"`);
}
if (sorted.length > 12) console.log(`  … and ${sorted.length - 12} more files`);
console.log(
  "\n  These are paragraphs a reader who chose Portuguese has to read in English. Artefact\n"
  + "  prose is excluded: it is English by repository convention. Reported, not failed —\n"
  + "  a gate that fails on every pre-existing violation is a gate somebody disables.",
);
