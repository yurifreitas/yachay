# The rare-disease layers — what each artefact is, and whether anyone measured it

> **Role:** the map of `out/rare/`. Thirty-four artefacts feed the explorer and get quoted in
> prose, and until this file existed nothing stated, per artefact, **whether its content was
> measured or authored**. That distinction is the whole epistemic contract of this project,
> and it was legible only to someone reading the Python.
> **Last revised:** 2026-08-29 · **State:** complete for the artefacts on disk. Provenance
> strings are quoted from each payload rather than paraphrased.
>
> ⚠ **This file went stale within a day of being written**, and `tools/verify_claims.py`
> caught it on its first run: four artefacts created after it — the whole patient layer and
> ClinVar — were missing from a document whose entire job is to be the complete map. Adding
> a layer now means adding a row here, and the checker enforces it.
>
> Reference-mode (Diátaxis): a lookup table, not an argument. The arguments are in
> [`rare-disease-scale.md`](rare-disease-scale.md),
> [`rare-disease-mechanisms.md`](rare-disease-mechanisms.md),
> [`rare-disease-equity.md`](rare-disease-equity.md) and
> [`rare-disease-ancestry.md`](rare-disease-ancestry.md).
>
> This file closes finding **A3** of [`../audit.md`](../audit.md), which had been open since
> the first sweep and was flagged there as "related to A2 but distinct, and the more
> dangerous of the two".

---

## How to read the grade

Every layer carries one of three grades. They are not a quality ranking — an authored layer
can be excellent and a measured one can be measuring the wrong thing. They say **what would
have to be true for the numbers to be wrong**, which is a different and more useful question.

| grade | what it means | how it fails |
|---|---|---|
| **measured** | every number is computed from an ingested public source; changing the source changes the answer | the join is wrong, or the source is wrong |
| **derived** | computed from *our own* earlier artefacts rather than from a source directly | inherits every defect of its inputs, silently |
| **authored** | written from working knowledge by a person | the person is wrong, and no rerun will tell you |

The scripts are scrupulous about this in their own docstrings and provenance fields. The
grades below are read from those fields, not assigned here.

---

## The layers

| artefact | produced by | grade | what it is for, and the number it carries |
|---|---|---|---|
| `atlas.json` | `build_atlas.py` | **measured** | The join: **14,831** diseases → **5,524** genes → **154** cell types. Coverage is reported rather than assumed — 74.4 % have a gene, 73.8 % are placeable on the cell axis. Feeds the hero counters. |
| `evidence_atlas.json` | `evidence_atlas.py` | **measured** | The catalogue's evidence profile over **267,782** annotations: only **39.7 %** of diseases have one sign estimated from a real series, and the median denominator is **5**. The full-scale version of the dossier's per-disease grading. |
| `prevalence_audit.json` | `prevalence_audit.py` | **measured** | All **17,108** Orphanet prevalence records, by type, validation and geography. Established that a prevalence is a *list*, not a number; **68.6 %** of disorders carry more than one type. |
| `ancestry_geography.json` | `ancestry_geography.py` | **measured** | The population axis. **386 of 525** multi-country disorders disagree about their prevalence band; representation runs Europe **8.10** to Africa **0.07**. |
| `bias.json` | `atlas_bias.py` | **measured** | Six named biases tested against our own reference data. Ascertainment **+0.2357**; panel coverage **−0.2469**, which falsifies a chart this project had already drawn. |
| `dossiers.json` | `dossier.py` | **measured** (trials cached live) | Twelve diseases in full: genes, graded signs, organ-system rollup, prevalence spread, cells, trials with their power arithmetic. The one layer that queries an external API, cached to disk so the artefact stays reproducible. |
| `patient_frequencies.json` | `patient_frequencies.py` | **measured, patient-level** | Frequencies computed from 10,377 individuals. At a curated denominator of **n = 1** the catalogue reads 0.932 and the patients say **0.436**. |
| `patient_variants.json` | `patient_variants.py` | **measured, patient-level** | The genotype half: **11,454** variants over **699** genes. The median gene has 66.7 % of its variants seen exactly once. |
| `genotype_phenotype.json` | `genotype_phenotype.py` | **measured, patient-level** | The join. **510** comparisons, of which only **40** could detect a 50-point difference — Stage 2 applied before any p-value is read. |
| `clinvar_evidence.json` | `clinvar_evidence.py` | **measured** | All 4,490,695 GRCh38 rows. **52.0 %** uncertain significance; **84.6 %** at one star or less; a fifth of our patient corpus not confidently pathogenic to the field. |
| `nongene_measured.json` | `nongene_measure.py` | **measured** | The test of the authored `nongene.json`: **six of ten** authored causal classes have a measured footprint of exactly **zero**, because HPO has nowhere to write them. |
| `gene_network.json` | `interactome_sparse.py` | **measured** | The HPO gene–disease graph and its sparse structure: modularity **0.861** against **0.162** for a degree-matched rewiring. |
| `community_stability.json` | `community_stability.py` | **measured** | The partition above, asked the questions it was never asked. Twelve seeds of the same algorithm agree at **ARI 0.901** [0.888, 0.915] and as low as 0.79 for one pair; two different algorithms agree at **0.29**, against **0.089** for a rewired graph with no communities at all. Sweeping the resolution twelvefold moves modularity by 0.03 while the largest community falls 777 → 192. **83 %** of the 3,335 scored genes keep their partners in nine runs of ten, published per gene. |
| `community_identity.json` | `community_identity.py` | **measured** | What the blocks ARE. Reactome enrichment against a null matched on annotation count, BH-corrected across 2,987 tests: **22 of 28** testable communities carry a pathway that both survives FDR and covers a tenth of the community. Sound perception 33 genes against **2.8** expected; ciliary trafficking **28×**; cohesin loading **22×**. Phenotype profiles are published but marked circular — the edges ARE disease co-membership. |
| `partition_flow.json` | `partition_flow.py` | **measured** | The ARI of 0.29 turned into the genes it is about. Communities matched by exact assignment before comparison, band order by barycentre sweeps (crossings 1,542 → 739). **Louvain→Leiden keeps 92.5 %** of genes in matched communities; **Leiden→label propagation keeps 50.0 %**, and label propagation finds 447 communities against 213. The disagreement is a re-partition, not border cases. |
| `gene_embedding.json` | `gene_embedding.py` | **measured** | A UMAP of 8,890 genes over 11 features, published as an object under test. **Trustworthiness 0.945** — locally faithful. **Neighbour overlap between seeds 0.627** — a third of every neighbourhood changes with the seed. **HDBSCAN on the embedding vs on the features: ARI 0.003**, because it calls 75 % of genes noise in eleven dimensions and 0.01 % on the picture. The tidiness is the projection, not the data. |
| `clusterability.json` | `clusterability.py` | **measured** | The prior question: does the gene feature space contain clusters at all? Hopkins **0.885** real against **0.817** for a marginal-preserving shuffle; best silhouette **0.231** against **0.117**; HDBSCAN noise **75 %** against **83 %**. All three separate, so structure exists — and it is weak. ⚠️ The shuffle, which has no joint structure by construction, scores above the textbook Hopkins cutoff of 0.75. |
| `nonreciprocal.json` | `nonreciprocal.py` | **measured** | The author's own hypothesis, with his own falsifier. Asymmetric affinity w(i→j) = |D_i∩D_j|/|D_i| against its symmetric projection, judged on recovering held-out disease genes. **S_NR = +0.0334 [+0.0182, +0.0506]** over 246 diseases; randomising the direction while preserving its magnitude gives **−0.0261**. Neither the weak nor the strict form of the falsifier triggers. Small: only 22.8 % of diseases gain, 67.9 % move less than 0.01. |
| `relational_primacy.json` | `relational_primacy.py` | **measured** | Relations against attributes, both arms given the same seeds. **ΔAUPRC = +0.287** [+0.239, +0.339] over 155 diseases, relations winning 83.9 %, and +0.297 over a degree-matched rewiring. Leave-one-disease-out: the first run leaked the disease under test into its own graph and returned +0.925. |
| `methods.json` | `methods_seed.py` | **encoded** | The author's five constructs, each with statement, precedent, measurement and falsifier. **2 measured, 2 specified but not run, 1 with no public falsifier** — the last being his own verdict, not one added here. |
| `moderated_calibration.json` | `moderated_calibration.py` | **measured, negative** | Empirical-Bayes moderation (Smyth 2004) applied to a permutation null's variance rather than a measurement's. It **does not fix** the near-degenerate denominator: moderation recovers what a noisy estimate lost around a good trend, and here the trend is the defect — every low-degree gene has a near-zero spread, so each already agrees with its neighbours. Top of the list moved ~15 %, ordering unchanged. The finding is why the empirical tail replaced it. |
| `capability_math.json` | `capability_math.py` | **derived** | Capital per patient, **$0.10–$1,001**, from `capability.json` ÷ validated point prevalence. Contradicts the economic barrier as `barriers.json` states it — published rather than reconciled. |
| `dimensions.json` | `dimensions.py` | **derived** | Seven transforms borrowed from named figures, each applied to data already here. A name earns its place only if it changes a number. |
| `dimensions_two.json` | `dimensions_two.py` | **derived** | Ten more, written because the first seven all came from men and the omitted work is load-bearing. |
| `lupus_graph.json` | `lupus_graph.py` | **derived** from `lupus.json` | Reachability gene → mechanism → cell → therapy. A path question a table cannot answer. ⚠ inherits the authored edge set. |
| `nongene.json` | `nongene_seed.py` | **authored** | Ten causal classes for when the cause is not a gene, with eight phenocopy pairs. *"Mechanisms and phenocopy pairs are established in their fields."* Tested by `nongene_measured.json`. |
| `barriers.json` | `barriers_seed.py` | **authored** | 29 barriers in four classes across 12 diseases. *"Written from working knowledge… the judgement that an approach is UNDERUSED is a judgement"* — marked low/medium confidence throughout. |
| `capability.json` | `capability_seed.py` | **authored** | Instruments, physics and cost. *"The physics is textbook and checkable. The cost bands are engineering estimates."* The physics and the money have different grades inside one file. |
| `nomenclature.json` | `nomenclature_seed.py` | **authored** | Twelve naming cases. *"Dates and first-description attributions are the least reliable field here."* Confidence marked per entry: 7 high, 5 medium. |
| `lexicon.json` | `rare_disease_seed.py` | **authored**, tested | The cross-ontology crosswalk. *"Every identifier must be resolved before use."* Now it is — see below. |
| `lexicon_check.json` | `lexicon_check.py` | **measured** | The audit of the row above against the catalogues: **8 of 12 clean**, and CDKL5 deficiency disorder carries a code that resolves to *Atypical Rett syndrome*. |
| `consistency.json` | `consistency.py` | **measured** | The only artefact whose subject is the **system** rather than a layer: where several layers claim the same thing, do they agree? **3 contradictions**, one of them an identity conflict, one of them against this file's own generalisation. |
| `lupus.json` | `lupus_seed.py` | **authored** | Lupus as gene × cell. *"CELL-TYPE ATTRIBUTIONS ARE SIMPLIFICATIONS"* — the file says so in capitals. |
| `references.json` | `references_seed.py` | **authored** | ~80 references tagged by community and ladder rung, then computed: which rungs are bridged and which carry one community only. |
| `thesis.json` | `thesis_seed.py` | **authored**, audited | The research thesis, encoded with its own register intact, then checked against what is built. Several rows read *"named, not built"*, which is the reason to run it. |
| `gap_patterns.json` | `gap_patterns.py` | **measured** | Which catalogue fields go missing together, at atlas scale. The largest single pattern is **1,326** diseases missing gene, onset and sign denominators at once — emptiness is concentrated, not scattered. |
| `tropical_gap.json` | `tropical_gap.py` | **measured** | The neglected-disease axis, from MONDO and the HPO gene-to-disease table. |
| `twin_propagation.json` | `twin_propagation.py` | **measured** | The first DYNAMICAL layer: a perturbation spreading from a disease's genes on STRING v12, every value a z against degree-stratified null seed sets. |
| `intervals.json` | `intervals.py` | **derived** | A 95 % interval on every headline another layer already published — audit A6/A26. It corrected two published sentences on its first run, and reports five headlines it cannot reach. |
| `scale_information.json` | `scale_information.py` | **measured** | What a change of scale costs. Genes carry **0.2791 bits** [0.2583, 0.3000] of excess information about organ system; 181-fold compression onto 29 Reactome pathways keeps **22 %**, 34-fold onto 154 cell types keeps **31 %**. Observational mutual information, deliberately *not* effective information — ADR 0007. |
| `language_coverage.json` | `language_coverage.py` | **measured** | What a reader loses by not reading English, over 19,836 HPO terms, 285,598 annotations and 14 non-English profiles. Portuguese — this project's own second language — covers **42.9 %** of the annotated phenotype with a **69.6-point** spread across organ systems. |
| `evidence_conflict.json` | `evidence_conflict.py` | **measured** | Whether recorded disagreement is contradiction or context, over 4,488,337 GRCh38 variants. Conflict rate rises **2.14×** from one condition to four or more, and the rise survives every submitter stratum. |
| `conflict_decomposition.json` | `conflict_decomposition.py` | **measured** | The split the aggregate could not do, from 6,428,687 per-submission rows: **57.2 %** [56.9, 57.5] of variant-level conflicts are across-condition only, **48.6 %** once panel indications are removed. About half of recorded disagreement is context. |
| `knowledge_shape.json` | `knowledge_shape.py` | **measured** | The shape of what is known per disease over five axes — and a NEGATIVE result: knowledge is **less** concentrated than independence would give (z **−19.04**), the anisotropy statistic tracks how many axes are populated rather than their shape, and the residual structure is the OMIM/ORPHA registry boundary. Kept because a catalogue where every idea works is a catalogue nobody tested. |
| `attention_burden.json` | `attention_burden.py` | **measured** | Research attention against burden. Citations of a disease's genes track prevalence at **+0.331**, and **+0.254** once diseases whose top gene clears 1,000 citations are dropped — so gene popularity does not explain it away. The severity arm **refuses to report a coefficient**: every disease with an Orphanet prevalence band is ORPHA-coded, and all 118,774 PCS-evidenced annotations are OMIM-coded. |
| `gene_constraint.json` | `gene_constraint.py` | **measured** | Selective constraint as an OUTSIDE axis: gnomAD v4.1 LOEUF, counted in 800,000 exomes from a population nobody asked about disease. Disease genes are more intolerant than a **length-matched** draw (0.8435 against 0.886, z -8.68) — but **66 %** of the distance from the genome mean is reproduced by drawing genes of the same length, so most of the apparent effect is length. The autism-sign set is far more intolerant (0.6189 against 0.8347, z -16.72) with only 38 % explained by length. And attention tracks constraint at **-0.317** [-0.3431, -0.2909] over the same disease genes `attention_burden.py` scored — the confound that file could state and not answer. Fails question 4 of the adapter gate, so there is no shortlist and no gene is ranked. |
| `single_cell_coverage.json` | `single_cell_coverage.py` | **measured** | The denominator of the cell axis. Four layers here place a disease on a cell type and all four read an atlas of NORMAL tissue, so each is healthy biology plus an inference. CZ CELLxGENE indexes 2,216 public single-cell datasets, **1,527 of them normal tissue**; 320 distinct disease terms carry cells, and only **77 of 14,831** catalogue diseases can be reached from one — 0.52 %. It does not correct the four layers; it says how often their inference could have been checked. Not an adapter: fails question 1 of the gate, no ranking and no null. |
| `psychiatric_gwas.json` | `psychiatric_gwas.py` | **measured** | Who was in the sample for nine psychiatric disorders, largely Psychiatric Genomics Consortium output: **65.8 %** of analysis weight European, **11.9 %** stating no ancestry at all, and ADHD, OCD, anorexia nervosa and Tourette with **zero** analyses carrying an African-ancestry majority. Two joins had to be fixed first and both are recorded in the tool. |
| `trait_atlas.json` | `trait_atlas.py` | **measured** | The same axes across every EFO disease area, and the comparison **qualifies the line above**: psychiatry is the least European of the eight areas, against cancer at 80.8 % and the residual disease bucket at 83.5 %. The problem is the field's rather than psychiatry's. Carries the parallel-coordinates model and the doubly seriated matrix, both solved in Python. |
| `signal_energy.json` | `signal_energy.py` | **measured, and NEGATIVE** | The morphogenesis result decomposed. `scale_information.py` reads its own finding as showing that a pathway alphabet has no vocabulary for WHERE — but it treats the 29 top-level pathways as one undifferentiated alphabet. Taken one at a time as single bits against permutation nulls, the field-shaping families do **not** carry more about morphogenetic systems than the energy families do: **-0.009477** against **-0.005272** bits, with every family leaning the same way. The arms differ in entropy (3.5815 against 2.5746 bits) and normalising for it does not change the ordering. The measurement in `scale_information.json` stands; the reading it invites does not. |
| `view_models.json` | `view_models.py` | **derived** | Solved layouts, no measurement of its own: a seriated 14×23 language matrix, the scale slopegraph, binned parallel coordinates over 12,994 five-dimensional vectors, and the conflict gradient as a grid. Here because **a seriation is an argument** — an ordering computed inside a component is one nobody can audit or version. |
| `knowledge_void.json` | `knowledge_void.py` | **measured** | The void as a first-class object. Of 1,024 ways a disease could be known, **318** occur; the space is emptier than independence by **z = −270.51**, so the void is structural. **95 %** of occupied cells touch an empty one — what is known is a filament, not a body — and **232 anti-forms** are empty cells where the catalogue's own marginals expect 4,286 diseases and find none. |
| `gap_taxonomy.json` | `gap_taxonomy.py` | **measured** | The unknown, typed by what would close it. Of **42,645** field-level gaps: 61.5 % accessibility, 21.0 % epistemic, **16.1 % interoperability** and 1.4 % population. The interoperability class is the one nobody counts — **6,874** gaps where a MONDO counterpart already carries the field and the join does not reach it. |
| `gene_ladder.json` | `gene_ladder.py` | **derived** | Fifteen genes joined across seven scales — residue, protein, interaction, pathway, cell type, organ system, disease — with the transition between each pair carrying its measured retention or an explicit `null` and the reason. **Only two of six transitions have a number behind them.** |
| `autism_convergence.json` | `autism_convergence.py` | **measured** | 714 diseases and 717 genes carry an autism term. Against size-matched random gene sets the convergence is **spatial, not mechanistic**: pathway concentration 0.1042 [0.0976, 0.1144] against a null of 0.1159 (**z = −2.32**, less than chance) and cell-type concentration 0.0326 [0.0289, 0.0366] against 0.0249 (**z = +3.68**). NOT a Stage 1 adapter — it fails question four of the fit test and says so. |

---

## What the table shows when you stand back from it

**Eighteen of the thirty-four mapped here are measured; five are derived; eight are authored**
(three carry a compound grade and are counted in none of the three). The patient-level layers
added on 2026-08-28 and the four ADR 0007 constructs added on 2026-08-29 are all measured,
which moved the ratio twice. That is not
a complaint — the authored layers carry domain knowledge no ingested source contains, and each
one says so in its own provenance field. But it is the first time the ratio has been
visible, and two things follow.

**The authored layers are the ones the dashboard renders most confidently.** Barriers,
capability and nomenclature all present as tables of facts. Their provenance strings are in
the payloads and were not on screen. Any interface change that surfaces those strings is an
improvement; any that does not is trading on the reader's assumption.

**Two authored layers have now been tested, and both tests found something.**
`nongene_seed.py` was checked by `nongene_measure.py`: **six of its ten classes came back at
a measured footprint of zero**. `lexicon.json` was checked by `lexicon_check.py`: **four of
its twelve diseases carry a flag**, including one — CDKL5 deficiency disorder — whose ORPHA
code resolves to *Atypical Rett syndrome*, the superseded classification, while our own
*measured* dossier uses the correct one.

~~That is the pattern worth naming: in every case so far, where an authored layer and a
measured layer disagree, the measured layer is right.~~

> ⚠ **That sentence was written here on 2026-08-27 and falsified the same day**, by the
> cross-layer check it prompted (`tools/consistency.py`, [`../audit.md`](../audit.md) A14).
> On cystic fibrosis the authored lexicon says `1-5 / 10 000` and the measured dossier says
> `1-9 / 1 000 000` — and the **authored layer is the better number**. The dossier is not
> wrong about the data; it exposes the *rarest* band on record, which for CF is a single
> outlying report, while the lexicon quotes the band the disease is actually known at.
> "Measured beats authored" was a prior stated as a finding. The honest version is narrower:
> **where the disagreement is about a fact, the measured layer has won every time so far;
> where it is about which summary to expose, being measured buys nothing.**

Testing the remaining seven authored layers is still the right call, and it is recorded in
[`../audit.md`](../audit.md) as **A13**.

---

## Regenerating them

Every layer is a pipeline stage, so staleness is tracked and a stale artefact is not
silently served. **One exception remains and it is named**: `capability_math` reads
`build_atlas` output with no declared edge. It is the only ⚠️ entry left in the exemption
list at the top of `tools/index_check.py`; everything else in that list is exempt on merit —
a network fetch, an audit, a renderer — with the reason written beside it.

This sentence used to read "most layers are pipeline stages", because on 2026-08-30 twenty-four
of the sixty-four artefact-writing tools were run by hand, including the entire gene chain: the
index the navigator reads, the facet index that is the only way into 18,140 genes that is not a
search box, and the shards the browser fetches. Their run order lived only in a sentence at the
bottom of each tool's docstring. All twenty-four were registered, with `analyses/
obesity_thermogenesis.py` and `build_atlas` itself, and the order is now an edge the runner
enforces:

```
gene_index -> gene_world -> gene_geometry, gene_domains, gene_datasheet
           -> gene_insights, gene_attention, gene_related
           -> gene_facets, gene_space -> gene_shards
```

`tools/index_check.py` holds every artefact-writing script to two things now, and it imports
the stage graph rather than grepping it — the earlier version asked whether a tool's name
appeared anywhere in `stages.py`, which a comment satisfies:

1. the script is some stage's declared `code`;
2. the file it writes is some stage's declared `outputs`.

The second matters more than it looks. A stage with no declared outputs always runs, so it
never serves something stale — but it also never skips, and nothing can tell you whether its
artefact is current. Both arms were verified to fail before being trusted.

```bash
python tools/index_check.py --check   # including the staging family
```

The stages that ARE registered regenerate like this:

```bash
python tasks.py status          # what is fresh, what is stale, and why
python tasks.py build           # run what is stale, in dependency order
python tasks.py <stage>         # one layer
```

The stage tracks **source code** as an input, not only data — an analysis whose code changed
is stale even when its inputs did not. That is how the defective null was caught
(`../lineage.md` §8), and it is why the A11 entity fix invalidated every dependent layer the
moment it landed.
