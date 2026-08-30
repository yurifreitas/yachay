# `tools/` — 65 scripts, grouped by what they are for

> **Role:** the map of this directory. It grew to 21,881 lines without any declared
> structure, and a flat listing of 65 filenames is not a structure — it is an inventory
> pretending to be one.
> **Last revised:** 2026-08-29 · **State:** complete for the 65 files on disk. The groups
> below are a reading order, not directories: renaming or moving a file would break the
> pipeline's source tracking (`sieve.pipeline.stages` hashes each tool's path to decide
> staleness), so the organisation is documentary and deliberately so.

**Read this with [`../docs/references/rare-layers.md`](../docs/references/rare-layers.md)**,
which grades the *artefacts* as measured, derived or authored. This file organises the
*producers*. A tool is listed once, in the group naming its primary job.

---

## 1. Ingest — get the data, honestly

| tool | lines | what it does |
|---|---|---|
| `ingest.py` | 90 | Downloads the 18 registered public sources (~1,339 MB). Stdlib only, resumable, licence-aware. Deliberately **not** in the build graph: a missing catalogue should stop a build with a message, never trigger a silent download mid-analysis. |

---

## 2. The catalogue layers — measured from public sources

These read an ingested file and compute. Nothing in this group is authored.

| tool | lines | reads | the number it exists for |
|---|---|---|---|
| `build_atlas.py` | 304 | HPO, Orphanet, HPA | the join: 14,831 diseases → 5,524 genes → 154 cell types |
| `atlas_bias.py` | 329 | HPO, Orphanet, HPA | six biases tested on our own reference data; ascertainment **+0.2357** |
| `prevalence_audit.py` | 380 | Orphanet | prevalence is a *list*: 17,108 records, five incommensurable types |
| `ancestry_geography.py` | 454 | Orphanet | the population axis: Europe **8.10**, Africa **0.07** |
| `evidence_atlas.py` | 272 | HPO | only **39.7 %** of diseases have one sign from a real series |
| `nongene_measure.py` | 257 | HPO | six of ten authored non-gene classes have a footprint of **zero** |
| `interactome_sparse.py` | 459 | HPO | modularity **0.861** against **0.162** for a degree-matched null |
| `knowledge_shape.py` | 406 | HPO, ClinVar, HPA, Orphanet | the shape of what is known, per disease — and the finding that **the prediction fails**: knowledge is less concentrated than independence (z = −19.04) and the residual structure is the OMIM/ORPHA registry boundary |
| `scale_information.py` | 657 | HPO, Reactome, HPA, STRING | what a change of scale costs: 181-fold compression onto 29 pathways keeps **22 %** of the information genes carry about organ system; onto 154 cell types, **31 %** |
| `conflict_decomposition.py` | 377 | ClinVar submissions | the decomposition: **57.2 %** of variant-level conflicts are across-condition only, 48.6 % with panel indications removed — about half of recorded disagreement is context, not contradiction |
| `evidence_conflict.py` | 255 | ClinVar | whether recorded conflict is contradiction or context: conflict rate rises **2.14x** with the number of conditions, and the rise survives every submitter stratum |
| `language_coverage.py` | 286 | HPO translations, HPO | what a reader loses by not reading English: Portuguese covers **42.9 %** of the annotated phenotype, with a **69.6-point** spread across organ systems |
| `dossier.py` | 796 | HPO, Orphanet, HPA, ClinicalTrials.gov | twelve diseases in full; the only tool that queries a live API |

---

## 3. The patient layers — individual people, not aggregates

Added 2026-08-27. The only group built from records of persons rather than of diseases.

| tool | lines | the number it exists for |
|---|---|---|
| `patient_frequencies.py` | 328 | at a curated denominator of **n = 1** the catalogue reads 0.932 and the patients say **0.436** |
| `patient_variants.py` | 355 | the median gene has **66.7 %** of its variants seen exactly once |
| `genotype_phenotype.py` | 267 | 510 comparisons; only **8 %** could detect a 50-point difference |
| `clinvar_evidence.py` | 274 | **52 %** of ClinVar is uncertain significance; **84.6 %** sits at ≤ 1 star |

---

## 4. The self-audit — this project checking itself

The group with no analogue in most repositories, and the one that has produced the most
uncomfortable findings.

| tool | lines | what it confronts |
|---|---|---|
| `consistency.py` | 307 | the layers against each other: 3 contradictions, one an identity conflict |
| `lexicon_check.py` | 455 | every authored identifier against the real catalogues: 5 of 12 flagged |
| `interactome_string.py` | 218 | our own weakest published claim against an independent graph — it survived |
| `ecosystem.py` | 283 | which libraries are installed and unused, and which sources are named and not ingested |
| `pipeline_state.py` | 123 | publishes staleness, so freshness is not a terminal-only fact |
| `autism_convergence.py` | 342 | HPO, Reactome, HPA | 717 genes converge on one phenotype and the convergence is **spatial, not mechanistic**: less pathway-concentrated than chance (z = −2.32), more cell-type-concentrated (z = **+3.68**) |
| `gene_ladder.py` | 348 | six sources | one gene from residue to organ system as a single object — and the finding that **only 2 of 6** steps between scales have ever been measured, with the other four carrying the reason instead of a number |
| `gap_taxonomy.py` | 262 | MONDO, HPO, Orphanet | five kinds of hole told apart by what would close each: of **42,645** field gaps, **6,874** are interoperability — both halves already on this disk and the join is what failed |
| `knowledge_void.py` | 283 | knowledge_shape | the void as an object: **318 of 1,024** cells occupied, z **−270.51** against independence, **95 %** of occupied cells on the frontier — a filament, not a blob — and **232 anti-forms** holding 4,286 expected diseases and none real |
| `view_models.py` | 427 | the artefacts above | layouts solved in Python so the browser only draws: a seriated 14×23 matrix, a slopegraph of the scale inversion, binned parallel coordinates over 12,994 diseases, and the conflict gradient as a grid |
| `attention_burden.py` | 310 | gene2pubmed, HPO, Orphanet | attention against burden: **+0.331** with prevalence, **+0.254** once gene popularity is removed — and the severity arm **refuses to report**, because every ORPHA-coded disease has zero evidenced signs |
| `gene_constraint.py` | 330 | gnomAD v4.1 constraint, HPO, gene2pubmed | selective constraint as the axis the curation could not have produced: attention tracks it at **-0.317**, and **66 %** of the disease-gene shift is gene length rather than constraint |
| `single_cell_coverage.py` | 230 | CZ CELLxGENE index, MONDO, HPO | whether anyone ever collected a cell: **77 of 14,831** catalogue diseases are reachable from a public single-cell dataset, and 1,527 of 2,216 indexed datasets are normal tissue |
| `cleared_devices.py` | 200 | FDA AI-enabled device list | what a regulator has actually permitted: **1,164 of 1,524** authorisations are radiology (76.4 %), one panel holds half the list, and the **Dermatology panel does not appear at all** — a fact about review pathways that the tool's own name scan corrects, finding 2 skin-lesion devices reviewed elsewhere |
| `index_check.py` | 145 | every artefact, tool, stage, source and ADR against the document that claims to enumerate it — A36, and its first run found **sixteen of eighteen** ingested sources named in no index |
| `verify_claims.py` | 246 | every published number against the artefact that produced it — F1, and it found stale docs on its first run |
| `intervals.py` | 268 | a 95 % interval on every headline — A6, and it corrected two published sentences |

| `cancer_subgroups.py` | 262 | selective dependency per cancer subgroup at three nesting levels — audit A29, and the first analysis here to run several library stages on one question |
| `status.py` | 620 | the derived project checklist — writes `docs/status.md`, and `--check` fails the gate when the repository contradicts the disk (audit A34) |

Two further controls live in `tests/` rather than here, both transferred from sibling
projects (audit A28): `test_determinism.py` reruns five stages and compares hashes
(from `F:\CODE\adia`), and `test_thresholds_manifest.py` holds `manifests/thresholds.yaml`
against the code (from `F:\CODE\climate`).

---

## 5. The authored layers — domain knowledge, marked as such

Written from working knowledge. Each carries its own `provenance` field saying so, and
[`../docs/audit.md`](../docs/audit.md) A13 tracks which have been tested. **Two of nine have
been** (`nongene_seed` by `nongene_measure`, `rare_disease_seed` by `lexicon_check`).

| tool | lines | status |
|---|---|---|
| `capability_seed.py` | 817 | untested — physics is textbook, costs are estimates |
| `nongene_seed.py` | 547 | **tested**, and six of ten classes came back at zero |
| `references_seed.py` | 574 | untested |
| `barriers_seed.py` | 527 | untested — "underused" is a judgement, marked low/medium confidence |
| `thesis_seed.py` | 455 | audited against what is built; several rows read "named, not built" |
| `dimensions.py` / `dimensions_two.py` | 461 / 412 | derived transforms borrowed from named figures |
| `nomenclature_seed.py` | 279 | untested |
| `rare_disease_seed.py` | 249 | **tested** by `lexicon_check.py` |
| `lupus_seed.py` / `lupus_graph.py` | 232 / 311 | untested; cell-type attributions marked as simplifications |

---

## 6. Statistics and output

| tool | lines | what it does |
|---|---|---|
| `multiplicity.py` | 211 | from a calibrated z to a defensible cut — the step the library had skipped |
| `tail_calibration.py` | 258 | how far the calibrated z departs from normal, and where it matters |
| `capability_math.py` | 362 | capital per patient, derived; contradicts the authored barriers layer |
| `figure_data.py` | 314 | one data contract, two renderers — the paper and the explorer cannot disagree |
| `paper_numbers.py` | 104 | no number is typed into the manuscript; each is a macro from a manifest |

---

## 7. The gene layers — one gene, every layer

Added over 2026-08-28/29 and, until now, invisible in this map: thirteen `gene_*` tools plus
three others build the per-gene view the explorer serves. They are grouped here because they
share an axis, not a method — each reads the catalogue layers above and pivots them onto a
single gene.

| tool | what it produces |
|---|---|
| `gene_index.py` / `gene_shards.py` | the gene list the explorer loads, and its sharding |
| `gene_datasheet.py` | one gene as a datasheet: every measured field with its provenance |
| `gene_domains.py` / `gene_geometry.py` | protein domains and the variant geometry along them |
| `gene_attention.py` | the attention a gene has received, against what it carries |
| `gene_facets.py` / `gene_related.py` / `gene_insights.py` | facets, neighbours, and the read-outs |
| `gene_space.py` / `gene_world.py` | the gene placed among the others |
| `cancer_genotype.py` | genotype-defined subgroups with the confounds measured |
| `gap_patterns.py` | which fields are missing together, at catalogue scale |
| `tropical_gap.py` | the neglected-disease axis |
| `twin_propagation.py` | the first dynamical layer: perturbation spread on STRING, against a degree-matched null |
| `scale_information.py` | the first cross-scale layer — see group 2 |

---

## The three rules this directory follows

1. **A tool answers one question.** When a second question appears it gets its own file, even
   when the extraction is shared — which is why `patient_frequencies` and `patient_variants`
   read the same zip twice. The duplication is cheaper than a tool that does two things and
   fails at one.
2. **Authored and measured never mix inside one file.** Where a tool needs a judgement it
   goes in a named constant with a comment saying it is one — `MODALITY_MARKS` in
   `dossier.py`, the population table in `ancestry_geography.py`.
3. **A refusal beats a plausible number.** `sieve.stages.power` raises rather than
   interpolating an unlisted alpha; `lexicon_check.py` reports `unverifiable` rather than
   `pass`; `clinvar_evidence.py` counts what is absent from ClinVar rather than dropping it.
