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
 *    4. every section names a group the page declares, and every declared group holds at
 *       least one section. A section whose group does not exist is drawn by nothing and
 *       listed under nothing — invisible in the rail with no error; an empty group is a
 *       heading with nothing under it. Splitting six groups into ten made both one typo away.
 *    5. no id appears twice, in either list. `renderSection` resolves with `.find`, so a
 *       duplicate id does not fail — the FIRST entry wins and the second is unreachable
 *       while the rail still offers it. That shipped once: a section added on 2026-08-29
 *       reused `gaps`, and the rail carried two tabs that drew the same old panel. Checks
 *       1 and 2 both passed, because a duplicate is a member of both sets.
 *
 *  Read as text rather than imported: these are .tsx modules with JSX, and a checker that
 *  needs a bundler to run is a checker that gets skipped.
 */
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");

/** Pages that have been migrated to a registry. A page not listed here still uses a render
 *  chain and is not checked — which is itself worth seeing, so it is printed. */
const MIGRATED = [
  {
    name: "rare",
    page: join(SRC, "features/rare/RarePage.tsx"),
    registry: join(SRC, "features/rare/rareSections.tsx"),
  },
  {
    name: "gene",
    page: join(SRC, "features/gene/GenePage.tsx"),
    registry: join(SRC, "features/gene/geneSections.tsx"),
  },
  {
    name: "cancer",
    page: join(SRC, "features/cancer/CancerPage.tsx"),
    registry: join(SRC, "features/cancer/cancerSections.tsx"),
  },
  {
    name: "run",
    page: join(SRC, "features/run/RunDash.tsx"),
    registry: join(SRC, "features/run/runSections.tsx"),
  },
];

/** Pages still using a render chain.
 *
 *  Empty is the goal, and it was empty while the cancer page sat in NEITHER list — using
 *  `useSectionNav` like the others, unmigrated, and therefore unchecked AND unreported. An
 *  empty LEGACY list is only meaningful if every page is in MIGRATED, so the scan below now
 *  finds pages that call `useSectionNav` and appear in neither, rather than trusting that
 *  somebody remembered to add them. */
const LEGACY = [
  {
    page: join(SRC, "features/docs/Docs.tsx"),
    why: "its sections are DERIVED from the documents on disk — DOC_GROUPS filtered and "
      + "mapped — so there are no literal ids for a registry to key on or for this checker "
      + "to read. A registry of computed entries would still be one list, just one this "
      + "check cannot verify, which is worse than an honest exemption.",
  },
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

  // Set membership cannot see a duplicate: the id is present in both lists, twice. Only a
  // count can, and the second entry is dead code the rail advertises.
  const dupes = (ids) => [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
  const dupNav = dupes(navIds);
  const dupReg = dupes(regIds);

  // The third list on the page: the groups. A section carries `group: "x"`; a group is
  // declared with `question:`. Nothing connected those two either.
  const groupIds = [...pageSrc.matchAll(/\{\s*id:\s*"([a-z_]+)",\s*label:[^}]*?question:/g)]
    .map((m) => m[1]);
  const sectionGroups = [...pageSrc.matchAll(/\{\s*id:\s*"[a-z_]+",\s*label:[^}]*?group:\s*"([a-z_]+)"/g)]
    .map((m) => m[1]);
  const strayGroup = [...new Set(sectionGroups.filter((g) => !groupIds.includes(g)))];
  const emptyGroup = groupIds.filter((g) => !sectionGroups.includes(g));

  // Every entry must carry a sentence — and the check is on the TEXT, not the syntax.
  // Its first version demanded a quoted string and failed twenty-three entries whose
  // sentences are JSX carrying inline emphasis. That is the checker being wrong about form
  // rather than about substance, the same mistake verify_claims made about the typographic
  // minus: a check that fails on notation teaches people to disable it.
  const entries = regSrc.split(/^\s{2}\{$/m).slice(1);
  const noSub = entries
    .filter((e) => {
      const m = e.match(/\n\s*sub:([\s\S]*?)\n\s*(?:bare|view):/);
      if (!m) return true;
      // A sentence that lives in the i18n module counts. `tt(MEAS.scaleSub)` cannot compile
      // unless the key exists and the key cannot exist without both languages, so TypeScript
      // has already made the guarantee this check was written to make. Re-deriving it here
      // would mean parsing the i18n modules to prove something the compiler proves.
      if (/\btt\(\s*[A-Z][A-Za-z]*\.[A-Za-z]/.test(m[1])) return false;
      const text = m[1]
        .replace(/<[^>]*>/g, " ")
        .replace(/\{[^}]*\}/g, " ")
        .replace(/["'`(),]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      return text.length < 20;
    })
    .map((e) => (e.match(/id:\s*"([a-z_]+)"/) || [, "?"])[1]);

  if (missing.length || orphan.length || noSub.length || dupNav.length || dupReg.length
      || strayGroup.length || emptyGroup.length) {
    failures++;
    console.error(`sections: ${name}`);
    for (const id of missing) console.error(`  the rail offers "${id}" and nothing draws it`);
    for (const id of orphan) console.error(`  "${id}" is registered and unreachable from the rail`);
    for (const id of noSub) console.error(`  "${id}" has no sentence saying what it shows`);
    for (const id of dupNav) console.error(`  the rail offers "${id}" twice — two tabs, one view`);
    for (const g of strayGroup) console.error(
      `  a section names group "${g}", which the page does not declare — invisible in the rail`);
    for (const g of emptyGroup) console.error(`  group "${g}" holds no section`);
    for (const id of dupReg) console.error(
      `  "${id}" is registered twice; \`.find\` takes the first and the second never draws`);
  } else {
    console.log(`sections: ${name} — ${regIds.length} sections, every one reachable, `
      + `uniquely addressed and described, in ${groupIds.length} groups.`);
  }
}

/** A page that navigates but is in neither list is the gap that hid the cancer page: the
 *  check reported three pages clean and said nothing at all about the fourth. */
const known = new Set([...MIGRATED.map((m) => m.page), ...LEGACY.map((l) => l.page)]);
(function scan(dir) {
  for (const f of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, f.name);
    if (f.isDirectory()) scan(p);
    else if (f.name.endsWith(".tsx") && !known.has(p)) {
      if (readFileSync(p, "utf8").includes("useSectionNav(")) {
        failures++;
        console.error(`sections: ${f.name} publishes a nav tree and is in neither list — `
          + `not checked, and not reported as unchecked. Add it to MIGRATED or LEGACY.`);
      }
    }
  }
})(SRC);

for (const { page, why } of LEGACY) {
  if (!existsSync(page)) continue;
  // A reason is required, for the same purpose it is required in check-artefacts.mjs: an
  // exemption list without reasons is where things get put to stop the build complaining.
  if (!why || why.length < 40) {
    failures++;
    console.error(`sections: ${page.split(/[\/]/).pop()} is exempt with no stated reason`);
    continue;
  }
  console.log(`sections: ${page.split(/[\/]/).pop()} — exempt. ${why}`);
}

if (failures) {
  console.error(`\n${failures} page(s) with a section defect. `
    + `A blank panel is not an error a reader can report.`);
  process.exit(1);
}
