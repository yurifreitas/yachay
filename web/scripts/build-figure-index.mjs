/** Every figure on the site, found by reading the source rather than by remembering.
 *
 *  THE PROBLEM THIS SOLVES. There are forty-six sections across five families, four view
 *  levels deep, and the labels are questions — "Quanto vale um z aqui?", "Os grupos são
 *  reais?". Questions are the right label for a section and the wrong one for finding a
 *  picture: a reader who remembers seeing a reordered matrix, or wants to know whether this
 *  site has an alluvial anywhere, has no way in but to open sections until one appears.
 *
 *  So this scans the feature source for uses of the viz organisms, pulls each one's
 *  `ariaLabel` — which by construction is a sentence saying what the figure shows — and maps
 *  it back to the section that renders it. The result is an index that cannot drift: a figure
 *  added without touching this file appears in it, and one deleted leaves it.
 *
 *  WHAT IT CANNOT SEE, and reports rather than hides: figures built from CSS bars and grids
 *  rather than from a viz organism. Those are the majority of the older panels. They are
 *  counted as `unindexed` so the number is honest — an index claiming to be complete while
 *  missing two thirds of the pictures would be worse than no index.
 */
import { readFileSync, writeFileSync, globSync, mkdirSync } from "node:fs";
import { join, dirname, relative, basename, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");
const OUT = join(SRC, "data", "generated");

/** The organisms, with the question each form is FOR. Written here rather than derived,
 *  because "what a form is good at" is an editorial claim and belongs somewhere a reader can
 *  argue with it — the viz-atlas rule that an exotic form must justify itself. */
const FORMS = {
  IntervalPlot: "an estimate against a threshold, with its interval",
  MatrixPlot: "a graph too dense to draw as nodes and links",
  RaincloudPlot: "a distribution, not its summary",
  AlluvialPlot: "flow between two or three categorisations",
  ScatterPair: "the same points twice, on one scale",
  SweepPlot: "several quantities against one swept parameter",
  WhiskerScatter: "two variables where one carries an interval",
  HexbinPlot: "density where individual points would overplot",
  NeedlePlot: "where along a molecule the damage falls",
  ParallelCoordinates: "many dimensions at once, per entity",
  UpSetPlot: "overlapping sets, beyond what a Venn can hold",
  DenseMatrix: "a matrix where every cell is a measurement, not a count",
};

const files = globSync("features/**/*.tsx", { cwd: SRC }).map((f) => join(SRC, f));

// ⚠️ A FORM MISSING FROM `FORMS` IS A FORM MISSING FROM THE INDEX, SILENTLY. DenseMatrix was
// built, used to draw 21 million CRISPR values, and appeared nowhere here — because the list
// above is hand-written and nobody added it. So the organisms on disk are read and any that
// this file does not know about are reported. An index whose omissions are invisible is the
// thing this index exists to replace.
const organisms = globSync("components/viz/organisms/*/index.ts", { cwd: SRC })
  // Windows returns backslashes here, so the separator is normalised before splitting
  // rather than matched — a character class with an escaped backslash inside a
  // generated file is exactly where this went wrong the first time.
  // Windows returns backslashes, so the separator is normalised with split/join
  // rather than a regex — an escaped backslash inside a generated file is exactly
  // where this went wrong twice.
  .map((f) => f.split(sep).at(-2) ?? f.split("/").at(-2));
const unknownForms = organisms.filter((o) => !(o in FORMS));

// ---- component -> section, read from the section registries -----------------------------
// A registry entry looks like `{ id: "x", title: …, view: () => (<><Comp /></>) }`. The scan
// is deliberately shallow: it pairs an id with the components named after it and before the
// next id, which is exactly the structure those files have and nothing more.
const sectionOf = new Map();
for (const file of files.filter((f) => /Sections\.tsx$/.test(f))) {
  const text = readFileSync(file, "utf8");
  const area = basename(file).replace(/Sections\.tsx$/, "");
  const parts = text.split(/\n\s*\{\s*\n?\s*id:\s*"/);
  for (const part of parts.slice(1)) {
    const id = part.slice(0, part.indexOf('"'));
    const upto = part.split(/\n\s*\{\s*id:/)[0];
    // ⚠️ THIS REQUIRED A SELF-CLOSING TAG WITH NO PROPS, and most section views pass one:
    // `<Shortlist run={ctx.run} />`. Six figures were reported as unplaced for that reason
    // alone — the scan could see `<Dossier />` and not `<Shortlist run={…} />`, which is a
    // property of the regex rather than of the site.
    for (const m of upto.matchAll(/<([A-Z][A-Za-z0-9]*)[\s/>]/g)) {
      if (!sectionOf.has(m[1])) sectionOf.set(m[1], { section: id, area });
    }
  }
}

// ---- component -> route, for the pages that are not section registries ------------------
// A standalone page — the addiction atlas, the CRISPR matrix, the discovery screen — is a
// whole route rather than a section inside one, so the registry scan above cannot see it. The
// view table in App.tsx names them: `{ id: "addiction", … render: () => <AddictionPage /> }`.
const routeOf = new Map();
{
  const app = readFileSync(join(SRC, "App.tsx"), "utf8");
  for (const m of app.matchAll(/id:\s*"([a-z_]+)"[^}]*?render:\s*\(\)\s*=>\s*<([A-Z][A-Za-z0-9]*)/g)) {
    routeOf.set(m[2], m[1]);
  }
}

// ---- the figures ------------------------------------------------------------------------
const figures = [];
let unindexed = 0;
for (const file of files) {
  const text = readFileSync(file, "utf8");
  const rel = relative(SRC, file).replace(/\\/g, "/");
  // Which component in this file renders? The default is the file's own exported component.
  const owner = (text.match(/export function ([A-Z][A-Za-z0-9]*)/) ?? [])[1] ?? basename(file, ".tsx");

  for (const form of Object.keys(FORMS)) {
    const uses = [...text.matchAll(new RegExp(`<${form}\\b`, "g"))];
    for (const use of uses) {
      // The aria label is the figure's own sentence about itself, taken from the nearest
      // `ariaLabel` after the tag opens.
      //
      // TEMPLATE INTERPOLATIONS ARE COLLAPSED, not kept. The first version reasoned that
      // leaving `${openPanel}` in the text was "ugly and honest". It is neither: a reader
      // sees "the top mutations of the ${openPanel} panel" and learns only that this index
      // prints source code at them. The value is not knowable here — it depends on what the
      // reader has clicked — and an ellipsis is what an unknown value looks like in a
      // sentence.
      // Nested braces defeat a `[^}]*` scan — `${d.counts.edges.toLocaleString()}` closes
      // early and leaves a fragment behind. Anything still carrying a brace after the pass is
      // DROPPED rather than printed: a missing source line costs a reader nothing, and a line
      // of JavaScript on the page costs them their trust in the rest of it.
      const clean = (v) => {
        if (!v) return null;
        const out = v.replace(/\$\{[^{}]*\}/g, "…").replace(/\s{2,}/g, " ").trim();
        if (/[${}]/.test(out)) return null;
        // A line that survived as "… genes … … features" is punctuation, not information.
        // Four real words is the floor for a caption that is worth the pixels.
        const words = out.split(/\s+/).filter((w) => /\p{L}{2,}/u.test(w));
        return words.length < 4 ? null : out;
      };
      const after = text.slice(use.index, use.index + 2600);
      const label = clean((after.match(/ariaLabel=\{?["'`]([^"'`]{10,200})["'`]\}?/) ?? [])[1]);
      const source = clean((after.match(/source=\{?["'`]([^"'`]{4,120})["'`]/) ?? [])[1]);
      if (!label) unindexed++;
      // THE COMPONENT THAT ACTUALLY CONTAINS THIS FIGURE, which is not always the file's
      // export. A registry file often defines its panels as module-local functions above the
      // array — `function Floor() { … <WhiskerScatter … /> … }` — and the registry then names
      // them. Taking the enclosing function is what connects the two.
      const enclosing =
        [...text.slice(0, use.index).matchAll(/function\s+([A-Z][A-Za-z0-9]*)\s*\(/g)]
          .map((m) => m[1]).at(-1) ?? owner;
      let home = sectionOf.get(enclosing) ?? sectionOf.get(owner) ?? null;
      // A figure written INLINE in a registry file belongs to the section it sits under, not
      // to the file's first export. Found by position: the last `id: "..."` before the tag.
      if (!home && /Sections[.]tsx$/.test(rel)) {
        const before = text.slice(0, use.index);
        const ids = [...before.matchAll(/id:\s*"([a-z_]+)"/g)];
        if (ids.length) {
          home = {
            section: ids[ids.length - 1][1],
            area: basename(file).replace(/Sections[.]tsx$/, ""),
          };
        }
      }
      const route = routeOf.get(owner) ?? null;
      figures.push({
        form,
        answers: FORMS[form],
        label,
        source,
        component: enclosing,
        file: rel,
        area: home?.area ?? null,
        section: home?.section ?? null,
        // A page-level figure has no section; it has a route, and that is enough to link to.
        route,
      });
    }
  }
}

// Figures drawn with CSS rather than an organism: counted so the index does not claim to be
// the whole picture. A `.track`/`.bar` pair is this repository's bar-chart idiom.
let cssFigures = 0;
for (const file of files) {
  const text = readFileSync(file, "utf8");
  cssFigures += (text.match(/css\.(track|corrTrack|floorTrack|bar)\b/g) ?? []).length;
}

const byForm = {};
for (const f of figures) byForm[f.form] = (byForm[f.form] ?? 0) + 1;

const payload = {
  generated: "web/scripts/build-figure-index.mjs",
  says:
    "Every figure built from a viz organism, found by scanning the source. Figures drawn "
    + "with CSS bars are counted but not indexed — an index claiming completeness while "
    + "missing them would be worse than none.",
  counts: {
    indexed: figures.length,
    forms: Object.keys(byForm).length,
    without_a_label: unindexed,
    css_marks_not_indexed: cssFigures,
    unplaced: figures.filter((f) => !f.section && !f.route).length,
    on_a_page_rather_than_in_a_section: figures.filter((f) => !f.section && f.route).length,
    organisms_on_disk: organisms.length,
    organisms_this_index_does_not_know: unknownForms,
  },
  by_form: byForm,
  figures: figures.sort((a, b) => (a.form + a.component).localeCompare(b.form + b.component)),
};

mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, "figure_index.json"), JSON.stringify(payload, null, 1));
console.log(
  `figures: ${figures.length} indexed across ${Object.keys(byForm).length} forms; `
  + `${payload.counts.on_a_page_rather_than_in_a_section} on a page rather than in a section; `
  + `${payload.counts.unplaced} unplaced; `
  + `${cssFigures} CSS marks not indexed.`,
);
if (unknownForms.length) {
  console.log(
    `  !! ${unknownForms.length} viz organism(s) on disk that this index does not know: `
    + unknownForms.join(", "),
  );
  console.log(
    "     Add them to FORMS with the question the form answers, or they draw nothing a "
    + "reader can find.",
  );
}
