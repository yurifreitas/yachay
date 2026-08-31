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
// Written here instead of into the bundle; see FETCHED below.
const PUBLIC_DEST = join(HERE, "..", "public", "data");

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

/** THE BOUNDARY BETWEEN AN ANALYSIS ARTEFACT AND A VIEW MODEL.
 *
 *  These two are different objects and were the same file, which is how a 1.6 MB cohort
 *  lookup table for 6,728 disorders ended up in a bundle that renders five numbers from it.
 *  Each entry names the fields the interface actually reads; everything else stays on disk
 *  for the pipeline, where it belongs and where it costs nothing.
 *
 *  `drop` removes a field. `head` truncates an array. Anything not listed passes through
 *  whole, so adding a dataset does not require touching this table — only a dataset that
 *  grows a large analysis-only field does.
 */
const PROJECT = {
  prevalence_audit: {
    // The per-disorder cohort table is a pipeline lookup consumed by capability_math.py.
    // Nothing in the interface reads it, and it is 96% of the file.
    drop: ["cohorts"],
    head: { rows: 40 },
  },
  interactome_sparse: {
    // The full verdict and ordering tables are small; nothing to trim yet. Listed so the
    // next person sees where the knob is.
  },
  clinvar_evidence: {
    // 13,528 per-gene rows are read by sieve.stages.target from disk, never by the browser.
    drop: ["vusByGene.all"],
  },
  gap_taxonomy: {
    // The per-field example lists are for a person reading the artefact, not the page.
    drop: ["examples"],
  },
  attention_burden: {
    // Two ranked lists of fifteen are what the view shows; the arms carry the rest.
    head: { most_neglected: 15, most_attended: 15 },
  },
  community_identity: {
    // Six pathways and five diseases per community is what the card reads; the full test
    // list is 2,987 rows and belongs on disk with the analysis.
    head: { communities: 30 },
  },
  community_stability: {
    // One confidence per gene for 3,335 genes is the artefact's most useful output and the
    // page renders three summary numbers from it. It stays on disk, where the gene layer can
    // join it, and out of a bundle that would carry 58 kB to print "91%".
    drop: ["per_gene"],
  },
  knowledge_void: {
    // The ten faces are drawn from view_models, which already carries them.
    drop: ["faces"],
  },
  knowledge_shape: {
    // 12,994 per-disease vectors are the pipeline's output, not the interface's. The page
    // renders the headline, the correlation matrix and the depth table, all of which are
    // summaries already in the payload.
    drop: ["diseases"],
  },
  language_coverage: {
    // The per-organ-system map inside every language row is 23 keys x 14 languages and is
    // read only for the two extremes, which the payload already names.
  },
  ancestry_geography: {
    // NOTHING IS TRIMMED, deliberately, and the note is here so the next person does not
    // "optimise" it. The 386 discordant rows ARE the interface: it ranks, filters and
    // searches them. Shipping a truncated head would make the visible set a sample drawn
    // by rank from the population it claims to describe — the selection error this whole
    // repository exists to catch, committed in a build script. It is fetched instead.
  },
};

/** Datasets written to `public/` and fetched at runtime rather than bundled.
 *
 *  The rule is a size one, not a taste one: past roughly a quarter of a megabyte the parse
 *  cost of an inlined JSON module is paid before the page can paint, and the data is not
 *  needed to paint it. `runs.json` stays inlined for now because RunView cannot render
 *  without it; the gene network can, and does, render a loading state.
 */
const FETCHED = new Set([
  "gene_network", "ancestry_geography",
  // Solved layouts for the hyperdimensional views. Fetched rather than bundled: it is
  // needed only by one group of sections, and a reader who never opens them should not pay
  // its parse cost before first paint. The route prefetches it on intent.
  "view_models",
  // One gene from residue to organ system. Fetched: 220 kB read by one view.
  "gene_ladder",
  // The three cancer levels: fetched, and one at a time. Bundling all three would charge
  // every route in the shared chunk for two levels the reader is not looking at.
  "cancer_subgroups_lineage", "cancer_subgroups_disease", "cancer_subgroups_subtype",
  "cancer_genotype",
]);

function project(name, value) {
  const rule = PROJECT[name];
  if (!rule || value === null || typeof value !== "object") return value;
  const out = Array.isArray(value) ? [...value] : { ...value };
  for (const key of rule.drop ?? []) {
    // Dotted paths drop a nested field, which is what a large table inside a small
    // artefact needs — `clinvar_evidence` is 2.3 MB of which 13,528 per-gene rows are
    // read only from disk.
    if (key.includes(".")) {
      const [head, tail] = key.split(".");
      if (out[head] && typeof out[head] === "object") {
        out[head] = { ...out[head] };
        delete out[head][tail];
      }
    } else {
      delete out[key];
    }
  }
  for (const [key, n] of Object.entries(rule.head ?? {})) {
    if (Array.isArray(out[key])) out[key] = out[key].slice(0, n);
    // Nested one level, because the arrays worth truncating are usually inside a block.
    for (const k of Object.keys(out)) {
      if (out[k] && typeof out[k] === "object" && Array.isArray(out[k][key])) {
        out[k] = { ...out[k], [key]: out[k][key].slice(0, n) };
      }
    }
  }
  return out;
}

function emit(name, value) {
  const projected = project(name, value);
  const json = JSON.stringify(projected);
  const kb = Math.round(json.length / 1024);
  if (FETCHED.has(name)) {
    mkdirSync(PUBLIC_DEST, { recursive: true });
    writeFileSync(join(PUBLIC_DEST, name + ".json"), json);
    console.log(`  ${name}.json (${kb} kB)  -> public/data, fetched at runtime`);
    return;
  }
  writeFileSync(join(DEST, name + ".json"), json);
  // Printed because a bundle regression should be visible in the build log, not in a
  // profiler three weeks later. Anything over a quarter of a megabyte is called out.
  console.log(`  ${name}.json (${kb} kB)` + (kb > 256 ? "  <-- large, consider fetching it" : ""));
}

/** Reduced figure series, written by tools/figure_data.py. The renderer never computes
 *  a statistic; it only draws what the analysis already reduced. */
const figures = {};
{
  const dir = join(REPO, "out", "figures");
  if (existsSync(dir)) {
    for (const f of readdirSync(dir)) {
      if (f.endsWith(".json")) figures[basename(f, ".json")] = JSON.parse(readFileSync(join(dir, f), "utf8"));
    }
  }
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
      // TABLES ONLY. The dense charts read `points.json`, which carries a sampled but
      // density-preserving cloud; this array feeds the ranked tables, which never show
      // more than a few dozen rows. Trimming to the extremes is therefore correct here
      // and was wrong when this array also fed the scatter.
      //
      // Ranks must already be columns: a rank recomputed from a trimmed array is a rank
      // within the trim. `analyses/*.py` writes rank_raw / rank_cal for exactly this.
      entities: entities.length > 800
        ? [...entities.slice(0, 400), ...entities.slice(-400)]
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
  const mul = join(REPO, "out", "multiplicity.json");
  emit("multiplicity", existsSync(mul) ? JSON.parse(readFileSync(mul, "utf8"))
    : { generated: "", input: "", uses: [], premise: "not generated",
        scale: { genes: 0, controls: 0, commonEssential: 0, candidates: 0 },
        assumption: { claim: "", testedOn: "", controlMean: 0, controlSd: 0, ksStatistic: 0,
                      ksP: 1, shapiroP: null, cvmStatistic: 0, cvmP: 1, whyItMatters: "",
                      verdict: "not generated" },
        empiricalResolution: { controls: 0, smallestAttainableP: 0, says: "" },
        fdr: { parametric: {}, empirical: {} },
        naive: { zOver3: 0, zOver3Candidates: 0, says: "", expectedFalsePositives: 0 },
        finding: "" });

  const tcl = join(REPO, "out", "tail_calibration.json");
  emit("tail_calibration", existsSync(tcl) ? JSON.parse(readFileSync(tcl, "utf8"))
    : { generated: "", input: "", uses: [], premise: "not generated", controls: 0,
        shape: { skew: 0, skewSE: 0, skewInSEs: 0, excessKurtosis: 0, kurtosisSE: 0,
                 kurtosisInSEs: 0, says: "" },
        lambda: { value: 1, says: "" }, tail: [], tailVerdict: "",
        fits: {}, bestFit: "norm", consequence: {}, genesChangingStatus: 0,
        finding: "", lambdaTrap: "" });

  const eco = join(REPO, "out", "ecosystem.json");
  emit("ecosystem", existsSync(eco) ? JSON.parse(readFileSync(eco, "utf8"))
    : { generated: "", premise: "not generated", confession: "", libraries: [], resources: [],
        summary: { libraries: 0, byStatus: {}, installedUnused: [], resources: 0,
                   resourcesIngested: 0, resourcesNamed: 0 } });

  const pip = join(REPO, "out", "pipeline.json");
  emit("pipeline", existsSync(pip) ? JSON.parse(readFileSync(pip, "utf8"))
    : { generated: "", premise: "not generated", rule: "", stages: [],
        summary: { stages: 0, stale: 0, fresh: 0, blocked: 0, artifacts: 0,
                   artifactsPresent: 0, staleNames: [] } });

  emit("runs", runs);
  // The navigation needs three strings per run. Emitting them separately keeps the
  // entity tables out of the entry chunk.
  emit("runs_index", runs.map((r) => ({ id: r.id, title: r.title,
                                        subtitle: r.subtitle ?? "" })));

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
emit("figures", figures);

/** The rare-disease lexicon, written by tools/rare_disease_seed.py. Emitted even when
 *  absent, as an empty shell, so the page renders a stated "no data" rather than a crash. */
{
  const gnw = join(REPO, "out", "rare", "gene_network.json");
  emit("gene_network", existsSync(gnw) ? JSON.parse(readFileSync(gnw, "utf8"))
    : { generated: "", premise: "not generated", nodes: [], degree: [], community: [],
        diseaseCount: [], indptr: [0], indices: [], weights: [], communities: 0,
        modularity: 0,
        stats: { nodes: 0, edges: 0, isolated: 0, maxDegree: 0, medianDegreeConnected: 0 },
        seedSuggestions: [] });

  const isp = join(REPO, "out", "interactome_sparse.json");
  emit("interactome_sparse", existsSync(isp) ? JSON.parse(readFileSync(isp, "utf8"))
    : { generated: "", input: "", uses: [], premise: "not generated", hypothesis: "",
        graph: {}, real: {}, null: {}, nullFidelity: {}, verdict: [],
        versusClassical: {}, finding: "", summary: {} });

  const rfj = join(REPO, "out", "rare", "references.json");
  emit("references", existsSync(rfj) ? JSON.parse(readFileSync(rfj, "utf8"))
    : { generated: "", premise: "not generated", provenanceNote: "", communities: [],
        references: [], bridges: [], communityPairs: [], neverMeet: [], confined: [],
        authorFormula: "", finding: "", theGap: "",
        summary: { references: 0, byCommunity: {}, byKind: {}, byProvenance: {}, byRung: {},
                   countries: 0, topCountries: {}, bridgedRungs: 0, singleCommunityRungs: 0,
                   communityPairs: 0, neverMeet: 0, confinedCommunities: [],
                   authorSupplied: 0 } });

  const thj = join(REPO, "out", "rare", "thesis.json");
  emit("thesis", existsSync(thj) ? JSON.parse(readFileSync(thj, "utf8"))
    : { generated: "", premise: "not generated", provenance: "", thesisScientific: "",
        thesisComputational: "", oneLine: "", deepest: "", scales: [], insights: [],
        register: { founded: [], hypothesis: [], metaphor: [] }, supplied: [],
        architecture: [], loop: [],
        summary: { scales: 0, scalesByStatus: {}, insights: 0, insightsByRegister: {},
                   insightsByStatus: {}, foundedClaims: 0, openHypotheses: 0,
                   metaphorsRetired: 0, suppliedUnverified: 0 } });

  // The population axis: which population each prevalence is about. Fetched, not bundled —
  // ~440 kB, and no part of it is needed to paint the page.
  const ang = join(REPO, "out", "rare", "ancestry_geography.json");
  emit("ancestry_geography", existsSync(ang) ? JSON.parse(readFileSync(ang, "utf8"))
    : { generated: "", input: "", premise: "not generated", caveat: "",
        authoredConstants: { populationTable: 0, regionTable: 0, note: "" },
        classOrder: [],
        shape: { records: 0, withGeographyTag: 0, worldwide: 0, supranational: 0,
                 specificPopulation: 0, namedCountry: 0, distinctCountries: 0,
                 worldwideShare: 0, namedCountryShare: 0 },
        perCapita: [], countriesWithoutPopulation: [],
        disparity: null, regions: [],
        concentration: { disordersWithAnyPlacedRecord: 0, disordersPlacedInExactlyOneCountry: 0,
                         disordersPlacedInMoreThanOneCountry: 0, disordersWithNoPlacedRecord: 0,
                         topCountriesForSinglePlaceDisorders: [], confound: "" },
        discordance: { comparableDisorders: 0, discordant: 0, share: null, rows: [], says: "" },
        specificPopulationTag: { records: 0, disorders: 0, examples: [], says: "" } });

  // The catalogue-wide evidence profile. Small, and it is what lets one disease's panel
  // say how it compares to the field instead of floating free.
  const eva = join(REPO, "out", "rare", "evidence_atlas.json");
  emit("evidence_atlas", existsSync(eva) ? JSON.parse(readFileSync(eva, "utf8"))
    : { generated: "", premise: "not generated", caveat: "", grades: {},
        profile: { diseasesWithPhenotypeAnnotations: 0, annotations: 0,
                   diseasesWithAQuantifiedSign: 0, shareWithAQuantifiedSign: 0,
                   diseasesWithAnyFraction: 0, diseasesWithNoFractionAtAll: 0,
                   shareWithNoFractionAtAll: 0, diseasesWithNoFrequencyAnywhere: 0,
                   annotationsByGrade: {}, denominators: {} },
        bySystem: [], byPrevalenceBand: {}, byPrevalenceBandNote: null,
        attention: { medianAnnotationsWhenQuantified: null,
                     medianAnnotationsWhenNot: null, says: "" } });

  // THE SELF-AUDIT LAYERS. Both are measured, both are about this repository rather than
  // about disease, and neither had ever been rendered - a dashboard that publishes its own
  // contradictions only in a JSON file on disk is publishing them nowhere.
  for (const [name, fallback] of [
    ["consistency", { generated: "", premise: "not generated", caveat: "",
                      scope: { layersIndexed: [], diseaseKeys: 0, joinedOn: "" },
                      contradictions: [], bySeverity: {}, unjoinable: [], coverage: [],
                      summary: { contradictions: 0, diseasesInMoreThanOneLayer: 0,
                                 diseasesInOnlyOneLayer: 0, mostCrossReferenced: null } }],
    ["lexicon_check", { generated: "", premise: "not generated", caveat: "",
                        scope: { diseases: 0, fieldsChecked: [], unverifiableByDesign: [],
                                 orphanetDisorders: 0, annotatedDiseases: 0, geneSymbols: 0 },
                        verdicts: {}, rows: [], clean: 0, flagged: 0 }],
  ]) {
    const f = join(REPO, "out", "rare", `${name}.json`);
    emit(name, existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : fallback);
  }

  // THE PATIENT LAYER AND THE INTERVALS. Five measured artefacts existed on disk and were
  // rendered nowhere — the whole patient-level body of work plus the confidence intervals.
  // A dashboard that publishes twenty aggregate layers while its strongest result sits in a
  // JSON file is publishing that result nowhere (audit A29).
  // gap_patterns: the co-occurrence measurement behind the UpSet, written by
  // tools/gap_patterns.py. It is the answer to visualization-canon.md §7b's third row.
  // THE ADR 0007 LAYER. Four constructs promoted from docs/references/theory-atlas.md, each
  // with a null and an interval, and none of them rendered anywhere until now — which is the
  // same failure the comment above names, committed again on newer work.
  for (const name of ["scale_information", "language_coverage", "evidence_conflict",
                      "conflict_decomposition", "knowledge_shape", "view_models",
                      "gene_ladder",
                      // Measured today and rendered nowhere until now — the A29 failure,
                      // committed again on the newest work.
                      "gap_taxonomy", "attention_burden", "autism_convergence",
                      "knowledge_void",
                      // The published partition, held to a null and an interval at last.
                      "community_stability",
                      // What each of those blocks IS, from a source outside the
                      // loop that built the graph.
                      "community_identity",
                      // Where the algorithms disagree, gene by gene.
                      "partition_flow",
                      // Is there anything to cluster in the first place.
                      "clusterability",
                      // The author's own hypothesis, against his own falsifier.
                      "nonreciprocal",
                      // The author's own constructs, with their falsifiers.
                      "relational_primacy", "methods"]) {
    const f = join(REPO, "out", "rare", `${name}.json`);
    emit(name, existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // TWO MORE THAT WERE MEASURED AND PUBLISHED NOWHERE — found by scripts/check-artefacts.mjs,
  // which exists because this comment block has now been written three times.
  //
  // twin_propagation: network propagation with a degree-stratified null, the rung
  // tools/thesis_seed.py grades as the one this repository actually built.
  // hiv_resistance: the method outside rare disease entirely — an adapter that passed the
  // four-question gate, whose positive controls were named before the run, and which breaks
  // an assumption the core smuggles in. That last part is why it is worth a screen.
  // Who was actually in the sample, on the psychiatric consortia's own findings. Lives in
  // out/psychiatric/ because the disorders are not rare, but it is emitted with the rare
  // bundle: it joins on MONDO and its whole point is to sit beside gene_constraint, whose
  // ancestry caveat it turns into a count.
  {
    const f = join(REPO, "out", "psychiatric", "psychiatric_gwas.json");
    emit("psychiatric_gwas", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // Every disease area on the same axes, with the parallel-coordinates model and the
  // seriated matrix solved in Python (ADR 0008).
  {
    const f = join(REPO, "out", "psychiatric", "trait_atlas.json");
    emit("trait_atlas", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // Stage 1 on the obesity challenge's own aggregate — the first adapter here with a
  // DESIGNED control pool, resampled rather than assumed.
  {
    const f2 = join(REPO, "out", "psychiatric", "addiction_atlas.json");
    emit("addiction_atlas", existsSync(f2) ? JSON.parse(readFileSync(f2, "utf8")) : { generated: "" });
  }

  {
    const f = join(REPO, "out", "obesity", "obesity_thermogenesis.json");
    emit("obesity_thermogenesis", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // THE AUDIT OF THE SITE'S OWN NUMBERS. tools/z_audit.py reads every artefact in this
  // directory and holds each published z against the draw count of the null it was computed
  // from. It is emitted like any other artefact because a page that reports 3,166 z values
  // owes the reader the one figure that says what they are worth.
  {
    const f = join(REPO, "out", "z_audit.json");
    emit("z_audit", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // The predictive-technology layer's founding measurement: what a regulator has actually
  // permitted, which is the only rung of a readiness scale that can be observed rather than
  // asserted. Lives in out/devices/ because it is not about rare disease.
  {
    const f = join(REPO, "out", "devices", "cleared_devices.json");
    emit("cleared_devices", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // The morphogenesis result decomposed by pathway family — and it comes back NEGATIVE
  // against the reading scale_information gives its own finding. Published for the same
  // reason knowledge_shape's negative is published: a site that only shows confirmations is
  // advertising.
  {
    const f = join(REPO, "out", "rare", "signal_energy.json");
    emit("signal_energy", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  // Whether anyone ever collected a cell from these diseases at all. Four layers of this
  // site reason over a cell-type axis taken from an atlas of NORMAL tissue; this is the
  // denominator none of them had.
  {
    const f = join(REPO, "out", "rare", "single_cell_coverage.json");
    emit("single_cell_coverage", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }
  // Selective constraint: the one axis in this repository measured in a population nobody
  // asked about disease, and therefore the only one that cannot have been produced by the
  // curation process it is used to audit.
  {
    const f = join(REPO, "out", "rare", "gene_constraint.json");
    emit("gene_constraint", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }
  {
    const f = join(REPO, "out", "rare", "twin_propagation.json");
    emit("twin_propagation", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }
  {
    const f = join(REPO, "out", "hiv_resistance.json");
    emit("hiv_resistance", existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }

  for (const name of ["patient_frequencies", "patient_variants", "genotype_phenotype",
                      "intervals", "gap_patterns", "tropical_gap"]) {
    const f = join(REPO, "out", "rare", `${name}.json`);
    emit(name, existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : { generated: "" });
  }
  // 2.3 MB, and the per-gene table is 13,528 rows the interface does not read. Trimmed
  // rather than fetched: what the views need is the summary and the cross-check.
/** Genotype-defined subgroups, written by tools/cancer_genotype.py. */
{
  const f = join(REPO, "out", "cancer_genotype.json");
  emit("cancer_genotype", existsSync(f) ? JSON.parse(readFileSync(f, "utf8"))
    : { generated: "", controls: [], results: [],
        prediction: { claim: "", written: "", controlsAgreeing: 0, controlsTestable: 0 },
        confound: { statement: "", handling: "", minPerStratum: 0 },
        scale: { lines: 0, genesAfterStage3: 0, genotypesTested: 0, lineageStrata: 0,
                 powered: 0 } });
}

/** Cancer subgroups, written by tools/cancer_subgroups.py at three nested levels.
 *  Emitted to public/ rather than bundled: the three files together are large enough that
 *  parsing them would be charged to every route sharing the chunk, and the cancer section
 *  fetches the one level the reader is actually looking at. */
for (const lv of ["lineage", "disease", "subtype"]) {
  const f = join(REPO, "out", `cancer_subgroups_${lv}.json`);
  emit(`cancer_subgroups_${lv}`, existsSync(f) ? JSON.parse(readFileSync(f, "utf8"))
    : { generated: "", level: lv, results: [],
        scale: { lines: 0, genesAfterStage3: 0, panEssentialDropped: 0,
                 subgroups: 0, powered: 0, underpowered: 0 } });
}

  const clv = join(REPO, "out", "rare", "clinvar_evidence.json");
  emit("clinvar_evidence", existsSync(clv) ? JSON.parse(readFileSync(clv, "utf8"))
    : { generated: "", scale: {}, significance: { counts: {} },
        reviewStatus: { byStars: {} }, crossCheck: { bySignificance: {} },
        vusByGene: { worst: [] } });

  const pav = join(REPO, "out", "rare", "prevalence_audit.json");
  emit("prevalence_audit", existsSync(pav) ? JSON.parse(readFileSync(pav, "utf8"))
    : { generated: "", input: "", premise: "not generated",
        scale: { disordersWithPrevalence: 0, prevalenceRecords: 0, meanRecordsPerDisorder: 0 },
        byType: {}, byValidation: {}, byQualification: {}, byClass: {}, topGeographies: {},
        mixedTypeDisorders: { count: 0, fraction: 0, examples: [] },
        typeDisagreements: { count: 0, rows: [], says: "" },
        watched: [], finding: "" });

  const ngm = join(REPO, "out", "rare", "nongene_measured.json");
  emit("nongene_measured", existsSync(ngm) ? JSON.parse(readFileSync(ngm, "utf8"))
    : { generated: "", inputs: [], premise: "not generated",
        scale: { diseasesAnnotated: 0, withInheritanceAnnotation: 0, withGene: 0, geneLess: 0 },
        vocabulary: [], measured: [], unmeasurable: [],
        geneLessBreakdown: { total: 0, withAnyInheritance: 0, withMendelianInheritance: 0,
                             withNonMendelianInheritance: 0, withNoInheritanceAnnotation: 0,
                             says: "" },
        finding: "",
        summary: { vocabularyTerms: 0, nonMendelianTerms: 0, classesWithFootprint: 0,
                   classesWithNoVocabulary: 0 } });

  const ngj = join(REPO, "out", "rare", "nongene.json");
  emit("nongene", existsSync(ngj) ? JSON.parse(readFileSync(ngj, "utf8"))
    : { generated: "", premise: "not generated", provenance: "",
        blindSpot: { diseases: 0, withGene: 0, withoutGene: 0, fractionWithoutGene: 0, says: "" },
        slots: [], classes: [], phenocopies: [], failureModes: [],
        summary: { classes: 0, slots: 0, phenocopies: 0, failureModes: 0, examples: 0,
                   byClassPhenocopies: {} } });

  const cpm = join(REPO, "out", "rare", "capability_math.json");
  emit("capability_math", existsSync(cpm) ? JSON.parse(readFileSync(cpm, "utf8"))
    : { generated: "", inputs: [], premise: "not generated", assumptions: {},
        discrepancies: [], finding: "", capitalPerPatient: [],
        sharing: { sumOfPlansUSD: { lo: 0, hi: 0 }, unionOfInstrumentsUSD: { lo: 0, hi: 0 },
                   doubleCountedUSD: { lo: 0, hi: 0 }, doubleCountedFraction: 0,
                   distinctInstruments: 0, instrumentSlotsAcrossPlans: 0, byInstrument: [] },
        queue: [], capitalVsAnswer: [],
        summary: { plansWithPrevalence: 0,
                   capitalPerPatientRangeUSD: { lowest: null, highest: null },
                   cheapestDisease: null, dearestDisease: null,
                   biggestRankMove: null, biggestRankMoveBy: null } });

  const cpb = join(REPO, "out", "rare", "capability.json");
  emit("capability", existsSync(cpb) ? JSON.parse(readFileSync(cpb, "utf8"))
    : { generated: "", premise: "not generated", provenance: "", instruments: [],
        diagnostics: [], plans: [],
        summary: { instruments: 0, byClass: {}, withCheaperRoute: 0, diagnostics: 0, plans: 0,
                   planStages: 0, byEfficacy: {}, capexRangeUSD: { lo: 0, hi: 0 },
                   cheapestPlanUSD: 0, dearestPlanUSD: 0 } });

  const brr = join(REPO, "out", "rare", "barriers.json");
  emit("barriers", existsSync(brr) ? JSON.parse(readFileSync(brr, "utf8"))
    : { generated: "", premise: "not generated", provenance: "", barrierKinds: [],
        theories: [], diseases: [], summary: {} });

  const dos = join(REPO, "out", "rare", "dossiers.json");
  emit("dossiers", existsSync(dos) ? JSON.parse(readFileSync(dos, "utf8"))
    : { generated: "", sources: {}, caveat: "not generated", dossiers: [] });

  const dim2 = join(REPO, "out", "rare", "dimensions_two.json");
  emit("dimensions_two", existsSync(dim2) ? JSON.parse(readFileSync(dim2, "utf8"))
    : { generated: "", why: "not generated", rule: "", dimensions: [] });

  const dim = join(REPO, "out", "rare", "dimensions.json");
  emit("dimensions", existsSync(dim) ? JSON.parse(readFileSync(dim, "utf8"))
    : { generated: "", rule: "not generated", omitted: [], dimensions: [] });

  const nom = join(REPO, "out", "rare", "nomenclature.json");
  emit("nomenclature", existsSync(nom) ? JSON.parse(readFileSync(nom, "utf8"))
    : { generated: "", premise: "not generated", provenance: "", eras: [], roots: [], names: [],
        summary: { cases: 0, byEra: {}, renamedForEthics: 0, namePreservesError: 0,
                   twoLiteratures: 0, byConfidence: {} } });

  const bia = join(REPO, "out", "rare", "bias.json");
  emit("bias", existsSync(bia) ? JSON.parse(readFileSync(bia, "utf8"))
    : { generated: "", premise: "not generated", findings: [], cellPanel: [] });

  const atl = join(REPO, "out", "rare", "atlas.json");
  emit("atlas", existsSync(atl) ? JSON.parse(readFileSync(atl, "utf8"))
    : { generated: "", provenance: "not generated", sourceHeader: "",
        scale: { diseases: 0, diseasesByPrefix: {}, diseasesWithGene: 0, genes: 0,
                 genesWithCellData: 0, cellTypes: 0, diseasesPlaceableOnCellAxis: 0,
                 orphanetWithPrevalence: 0, ultraRare: 0, ultraRareWithGene: 0,
                 associationTypes: {} },
        coverage: { geneKnown: 0, cellPlaceable: 0, ultraRareGeneKnown: 0 },
        prevalenceDistribution: [], cellBurden: [], cellTypes: [] });

  const gph = join(REPO, "out", "rare", "lupus_graph.json");
  emit("lupus_graph", existsSync(gph) ? JSON.parse(readFileSync(gph, "utf8"))
    : { generated: "", provenance: "not generated",
        nodes: { genes: [], mechanisms: [], cells: [], therapies: [] }, edges: [],
        analysis: { unreachableGenes: [], cellsWithNoTherapy: [], mechanismsWithNoTherapy: [], medianHops: -1 },
        summary: { genes: 0, cells: 0, mechanisms: 0, therapies: 0, edges: 0,
                   byEvidence: {}, byEffect: {}, byModality: {}, byStatus: {} } });

  const lup = join(REPO, "out", "rare", "lupus.json");
  emit("lupus", existsSync(lup) ? JSON.parse(readFileSync(lup, "utf8"))
    : { generated: "", provenance: "not generated", cells: [], axes: [], monogenic: [],
        sle: { name: "", architecture: "", loci: "", note: "", confidence: "", disparity: "" },
        therapies: [], matrix: [],
        summary: { monogenicGenes: 0, withAlternates: 0, gainOfFunction: 0, byAxis: {},
                   byCell: {}, therapiesByCell: {}, cellsWithNoTherapy: [] } });

  const f = join(REPO, "out", "rare", "lexicon.json");
  emit("rare", existsSync(f) ? JSON.parse(readFileSync(f, "utf8"))
    : { generated: "", provenance: "not generated", definitions: [], prevalenceBands: [],
        ontologies: [], fieldFacts: [], diseases: [],
        summary: { entries: 0, withoutGene: 0, withoutMechanism: 0, withoutTherapy: 0,
                   withoutAnyOntologyId: 0, bySystem: {}, byConfidence: {} } });
}
