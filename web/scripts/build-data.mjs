/**
 * Build the explorer's data from whatever adapter last ran.
 *
 * The generalization over the predecessor's version: that one hardcoded one screen's
 * filenames. This reads a MANIFEST that each analysis writes, so a new adapter appears
 * in the UI without touching the UI. An adapter that does not write a manifest simply
 * does not show up — no silent partial rendering.
 *
 *   node scripts/build-data.mjs
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const OUT_DIRS = [join(REPO, "out")];
const DEST = join(HERE, "..", "src", "data", "generated");

mkdirSync(DEST, { recursive: true });

function readCsv(path) {
  const text = readFileSync(path, "utf8").trim();
  if (!text) return [];
  const [head, ...rows] = text.split(/\r?\n/);
  const cols = head.split(",");
  return rows.map((line) => {
    const cells = line.split(",");
    return Object.fromEntries(
      cols.map((c, i) => {
        const raw = cells[i];
        const num = Number(raw);
        return [c, raw !== "" && raw !== undefined && !Number.isNaN(num) ? num : raw];
      })
    );
  });
}

function emit(name, value) {
  writeFileSync(join(DEST, name + ".json"), JSON.stringify(value));
  const n = Array.isArray(value) ? value.length : Object.keys(value).length;
  console.log(`  ${name}.json (${n})`);
}

/** A run is one adapter's output: a manifest plus the frames it names. */
const runs = [];
for (const dir of OUT_DIRS) {
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".manifest.json")) continue;
    const manifest = JSON.parse(readFileSync(join(dir, f), "utf8"));
    const entities = manifest.entities ? readCsv(join(dir, manifest.entities)) : [];
    const nulls = manifest.null ? readCsv(join(dir, manifest.null)) : [];
    runs.push({
      id: manifest.id ?? basename(f, ".manifest.json"),
      title: manifest.title ?? manifest.id,
      subtitle: manifest.subtitle ?? "",
      statistic: manifest.statistic ?? "",
      reduce: manifest.reduce ?? "",
      headline: manifest.headline ?? {},
      // The explorer plots at most a few thousand points; a 18k-gene table is sent
      // whole only if small, otherwise trimmed to the extremes that matter visually.
      entities: entities.length > 4000
        ? [...entities.slice(0, 2000), ...entities.slice(-2000)]
        : entities,
      entitiesTotal: entities.length,
      null: nulls,
    });
  }
}
if (!runs.length) {
  console.error("no *.manifest.json found under out/ — run an analysis first "
    + "(python tasks.py depmap). Refusing to build an empty explorer.");
  process.exit(1);
}
emit("runs", runs);

/** Documents: methodology, expansion map, ADRs, findings. Shipped as raw Markdown. */
const docs = [];
function addDoc(path, group) {
  if (!existsSync(path)) return;
  const body = readFileSync(path, "utf8");
  const first = body.split(/\r?\n/).find((l) => l.startsWith("# "));
  docs.push({
    id: `${group}/${basename(path, ".md")}`,
    group,
    file: basename(path),
    title: first ? first.replace(/^#\s*/, "") : basename(path),
    words: body.split(/\s+/).length,
    body,
  });
}
const docsDir = join(REPO, "docs");
if (existsSync(docsDir)) {
  for (const f of readdirSync(docsDir).filter((f) => f.endsWith(".md"))) {
    addDoc(join(docsDir, f), "method");
  }
  const adr = join(docsDir, "adr");
  if (existsSync(adr)) {
    for (const f of readdirSync(adr).filter((f) => f.endsWith(".md"))) addDoc(join(adr, f), "adr");
  }
  const cases = join(docsDir, "case-studies");
  if (existsSync(cases)) {
    for (const f of readdirSync(cases).filter((f) => f.endsWith(".md"))) addDoc(join(cases, f), "case");
  }
}
for (const dir of OUT_DIRS) {
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".md"))) addDoc(join(dir, f), "findings");
}
addDoc(join(REPO, "README.md"), "method");
emit("docs", docs);

console.log("done");
