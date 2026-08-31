/** Every measurement on disk is published, or says in writing why it is not.
 *
 *  WHY THIS EXISTS. Audit A29 — *a dashboard that publishes twenty aggregate layers while
 *  its strongest result sits in a JSON file is publishing that result nowhere* — has now
 *  been written three times in three different comment blocks, and found a fourth time by
 *  hand. A failure that recurs after being named is not a mistake; it is a missing check.
 *
 *  The cost asymmetry is what makes it recur. Producing a measurement is a day's work and
 *  ends with a green test. Publishing it is four more steps and ends with nothing failing if
 *  you skip them. So the unpublished state has to be the one that breaks the build.
 *
 *  WHAT COUNTS AS PUBLISHED. Two delivery paths, and both count:
 *    - bundled: written to src/data/generated and imported by some module under src/
 *    - fetched: written to public/data and named by a fetch() somewhere under src/
 *  An artefact that is emitted but imported by nothing is NOT published — it is bundle
 *  weight the reader pays for and never sees, which is the same defect facing the other way.
 *
 *  WHAT IS NOT A MEASUREMENT. Inputs, manifests, shards and intermediates are listed in
 *  NOT_PUBLISHED below, each with the reason. The reason is the point: an entry with no
 *  reason is how this list becomes a place to hide things, so a bare filename fails too.
 */
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const WEB = join(HERE, "..");
const REPO = join(WEB, "..");
const SRC = join(WEB, "src");

/** Artefacts under out/ that are deliberately not published, and why.
 *  A reason is required. "Not ready" is a reason; an empty string is not. */
const NOT_PUBLISHED = {
  // The demonstration record of a method that FAILED, and the failure is published — inside
  // twin_propagation, under `three_statistics.moderated_z`, on the screen where the ranking it
  // could not fix is drawn. Rendering the standalone artefact too would put the same negative
  // result on two screens and invite a reader to think they are two findings.
  moderated_calibration:
    "a method demonstration whose finding is published in twin_propagation's "
    + "`three_statistics` block, beside the ranking it failed to fix",
  "depmap.manifest": "a run manifest, read by the pipeline rather than by a reader",
  "nf2.manifest": "a run manifest, read by the pipeline rather than by a reader",
  "interactome_string_700": "an ingested input, not a measurement; the graph it feeds is published",
  "interactome_string_900": "an ingested input, not a measurement; the graph it feeds is published",
  "interactome_sparse": "the sparse form of the same input, consumed by the network views",
  "status": "written for docs/status.md and read by tools/status.py, not by the explorer",
  "lexicon": "the seed lexicon; the explorer reads the checked form, lexicon_check",
  "pipeline": "the stage list, rendered by the run dashboard from its own copy",
  "ecosystem": "read by the run dashboard through the manifest path, not by name",
};

/** Prefixes whose members are sharded or fetched per-item rather than named once. */
const SHARDED = [
  { prefix: "gene_", why: "sharded into public/data/gene/*.json and fetched per symbol" },
  { prefix: "cancer_", why: "fetched one level at a time by the cancer sections" },
];

const artefacts = [];
for (const dir of [join(REPO, "out"), join(REPO, "out", "rare")]) {
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".json")) continue;
    const p = join(dir, f);
    if (statSync(p).isDirectory()) continue;
    artefacts.push({ name: basename(f, ".json"), path: p, size: statSync(p).size });
  }
}

/** Every source file, read once. */
const sources = [];
(function walk(dir) {
  for (const f of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, f.name);
    if (f.isDirectory()) walk(p);
    else if (/\.(tsx?|mjs)$/.test(f.name)) sources.push(readFileSync(p, "utf8"));
  }
})(SRC);
const allSource = sources.join("\n");

const bundledDir = join(SRC, "data", "generated");
const publicDir = join(WEB, "public", "data");
const bundled = existsSync(bundledDir)
  ? new Set(readdirSync(bundledDir).filter((f) => f.endsWith(".json")).map((f) => basename(f, ".json")))
  : new Set();
const published = existsSync(publicDir)
  ? new Set(readdirSync(publicDir).filter((f) => f.endsWith(".json")).map((f) => basename(f, ".json")))
  : new Set();

const importedByName = (name) =>
  allSource.includes(`generated/${name}.json`) || allSource.includes(`generated/${name}"`);
const fetchedByName = (name) =>
  allSource.includes(`${name}.json`) || allSource.includes(`"${name}"`);

const unpublished = [];
const deadWeight = [];

for (const a of artefacts) {
  const shard = SHARDED.find((s) => a.name.startsWith(s.prefix));
  if (shard || NOT_PUBLISHED[a.name] !== undefined) {
    if (!shard && !NOT_PUBLISHED[a.name]) {
      unpublished.push({ ...a, why: "listed in NOT_PUBLISHED with an empty reason" });
    }
    continue;
  }
  const isBundled = bundled.has(a.name) && importedByName(a.name);
  const isFetched = published.has(a.name) && fetchedByName(a.name);
  if (!isBundled && !isFetched) {
    unpublished.push({
      ...a,
      why: bundled.has(a.name) || published.has(a.name)
        ? "emitted, and read by no module — the reader downloads it and never sees it"
        : "measured, and reaches no delivery path at all",
    });
  }
}

// The same defect facing the other way: shipped, and drawn by nothing.
for (const name of bundled) {
  if (!importedByName(name) && !artefacts.some((a) => a.name === name && NOT_PUBLISHED[name])) {
    if (!unpublished.some((u) => u.name === name)) deadWeight.push(name);
  }
}

let failed = false;

if (unpublished.length) {
  failed = true;
  console.error("artefacts: measured and published nowhere");
  for (const u of unpublished) {
    console.error(`  ${u.name}  (${Math.round(u.size / 1024)} kB) — ${u.why}`);
  }
  console.error(
    "\nPublish it, or add it to NOT_PUBLISHED in this file with the reason. A measurement"
    + " nobody can see is a measurement nobody can argue with.");
}

if (deadWeight.length) {
  failed = true;
  console.error("\nartefacts: bundled and drawn by nothing");
  for (const n of deadWeight) console.error(`  ${n}`);
  console.error("\nEvery reader downloads and parses these. Either draw them or stop emitting them.");
}

if (failed) process.exit(1);

console.log(
  `artefacts: ${artefacts.length} on disk — every one published or exempt with a stated reason.`);
