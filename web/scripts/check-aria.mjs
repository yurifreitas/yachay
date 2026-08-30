/** A declared role is a promise about behaviour. This checks the promises that were broken.
 *
 *  WHY. Seven components here shipped `role="tab"` inside a `role="tablist"` with no
 *  `role="tabpanel"` anywhere in the application, no `aria-controls`, no ids and no keyboard
 *  handling. A screen reader announces "tab, 3 of 5" and offers to move to a panel that does
 *  not exist; a tablist promises arrow-key navigation, and the arrows did nothing. That is
 *  worse than using plain buttons, because plain buttons make no promise to break.
 *
 *  None of them were tabs. A tab swaps a labelled panel that keeps its place in the reading
 *  order; every one of these chose which question was being asked and re-rendered the content
 *  beneath — a radio group, which `ChoiceGroup` and `lib/useRovingRadio.ts` now implement
 *  with the keyboard model the role requires.
 *
 *  WHAT IT CHECKS, and each is a way this actually broke:
 *    1. `role="tablist"` with no `role="tabpanel"` in the same file — the promise with no
 *       destination.
 *    2. `role="tab"` with no `aria-controls` — a tab that names no panel.
 *    3. `role="radiogroup"` with no `aria-label` or `aria-labelledby` — a group of options
 *       announced with no statement of what is being chosen.
 *    4. `aria-selected` outside a tab/option context — it means nothing on a plain button and
 *       is the attribute people reach for when they mean `aria-current` or `aria-pressed`.
 *
 *  It is deliberately narrow. A general accessibility audit needs a browser and a real
 *  assistive-technology pass; this catches the one class of defect this codebase has already
 *  made seven times, at build time, for free.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");

const files = [];
(function walk(dir) {
  for (const f of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, f.name);
    if (f.isDirectory()) walk(p);
    else if (f.name.endsWith(".tsx")) files.push(p);
  }
})(SRC);

const problems = [];

for (const path of files) {
  const src = readFileSync(path, "utf8");
  const rel = relative(SRC, path).replace(/\\/g, "/");

  // Comments describe the defect in several of these files on purpose. Strip them so the
  // checker reads code rather than the prose explaining why the code no longer does this.
  const code = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

  const has = (re) => re.test(code);

  if (has(/role="tablist"/) && !has(/role="tabpanel"/)) {
    problems.push([rel, 'role="tablist" with no role="tabpanel" in the same file — '
      + "a tab that offers a panel the reader cannot reach"]);
  }
  const tabs = code.match(/role="tab"/g) || [];
  const controls = code.match(/aria-controls=/g) || [];
  if (tabs.length > controls.length) {
    problems.push([rel, `${tabs.length} role="tab" and ${controls.length} aria-controls — `
      + "a tab must name the panel it shows"]);
  }
  for (const m of code.matchAll(/role="radiogroup"([\s\S]{0,220}?)>/g)) {
    if (!/aria-label(ledby)?[=\s]/.test(m[1])) {
      problems.push([rel, 'role="radiogroup" with no aria-label — a group of options with '
        + "no statement of what is being chosen"]);
      break;
    }
  }
  if (has(/aria-selected/) && !has(/role="(tab|option|row|gridcell|treeitem)"/)) {
    problems.push([rel, "aria-selected with no tab/option role — it means nothing on a "
      + "plain button; aria-current or aria-pressed is almost always what was meant"]);
  }
}

if (problems.length) {
  console.error("aria: declared roles whose contract is not kept");
  for (const [file, why] of problems) console.error(`  ${file} — ${why}`);
  console.error("\nA role is a promise about behaviour. Use ChoiceGroup or "
    + "lib/useRovingRadio.ts for a set of options that re-renders the content beneath, and "
    + "aria-current for navigation.");
  process.exit(1);
}

console.log(`aria: ${files.length} components, no role declaring a contract it does not keep.`);
