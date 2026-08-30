/** Every section the rail offers must have something registered to draw it.
 *
 *  WHY. A page's nav array and its render chain used to be two lists that nothing connected,
 *  and 59 branches across three pages is exactly the shape where they drift. When they drift
 *  the reader gets a blank panel — no error, no log, nothing to notice.
 *
 *  This is the interface's version of `tools/index_check.py`, which found sixteen of eighteen
 *  ingested sources named in no index on its first run. Same failure, same remedy: make the
 *  list checkable, and check it in the build rather than in a review.
 *
 *  WHAT IT CHECKS, and each is a real way this has broken:
 *    1. every id in a page's SECTIONS array is registered in that page's registry
 *    2. every registered id appears in the SECTIONS array — a section nobody can reach
 *    3. every registry entry has a non-empty `sub`, because in this project a figure's
 *       sentence is where it states what it does not show
 *
 *  Read as text rather than imported: these are .tsx modules with JSX, and a checker that
 *  needs a bundler to run is a checker that gets skipped.
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");

/** Pages that have been migrated to a registry. A page not listed here still uses a render
 *  chain and is not checked — which is itself worth seeing, so it is printed. */
const MIGRATED = [
  {
    name: "run",
    page: join(SRC, "features/run/RunDash.tsx"),
    registry: join(SRC, "features/run/runSections.tsx"),
  },
];

const LEGACY = [
  join(SRC, "features/rare/RarePage.tsx"),
  join(SRC, "features/gene/GenePage.tsx"),
];

let failures = 0;

for (const { name, page, registry } of MIGRATED) {
  if (!existsSync(page) || !existsSync(registry)) {
    console.error(`sections: ${name} — file missing`);
    failures++;
    continue;
  }
  const pageSrc = readFileSync(page, "utf8");
  const regSrc = readFileSync(registry, "utf8");

  // A SECTION carries `group:`; a GROUP carries `question:`. The first version of this
  // check matched both and reported five groups as undrawn sections — a checker that cries
  // wolf is a checker somebody deletes.
  const navIds = [...pageSrc.matchAll(/\{\s*id:\s*"([a-z_]+)",\s*label:[^}]*?group:/g)]
    .map((m) => m[1]);
  const regIds = [...regSrc.matchAll(/^\s{2}\{\s*$\n\s*id:\s*"([a-z_]+)"/gm)].map((m) => m[1]);

  const missing = navIds.filter((id) => !regIds.includes(id));
  const orphan = regIds.filter((id) => !navIds.includes(id));

  // Every entry must carry a sentence.
  const entries = regSrc.split(/^\s{2}\{$/m).slice(1);
  const noSub = entries
    .filter((e) => !/sub:\s*\n?\s*"[^"]{20,}"/.test(e))
    .map((e) => (e.match(/id:\s*"([a-z_]+)"/) || [, "?"])[1]);

  if (missing.length || orphan.length || noSub.length) {
    failures++;
    console.error(`sections: ${name}`);
    for (const id of missing) console.error(`  the rail offers "${id}" and nothing draws it`);
    for (const id of orphan) console.error(`  "${id}" is registered and unreachable from the rail`);
    for (const id of noSub) console.error(`  "${id}" has no sentence saying what it shows`);
  } else {
    console.log(`sections: ${name} — ${regIds.length} sections, every one reachable and described.`);
  }
}

for (const page of LEGACY) {
  if (!existsSync(page)) continue;
  const n = (readFileSync(page, "utf8").match(/section === "/g) || []).length;
  if (n > 0) {
    console.log(`sections: ${page.split(/[\\/]/).pop()} — ${n} branches still in a render `
      + `chain, unchecked. Migrating it to a registry brings it under this check.`);
  }
}

if (failures) {
  console.error(`\n${failures} page(s) with a section defect. `
    + `A blank panel is not an error a reader can report.`);
  process.exit(1);
}
