# References

> **Role:** everything yachay leans on, in one place — data, method, domain.
> **Last revised:** 2026-08-29 · **State:** inventory complete, link-checking pending.
>
> Companion files: `CITATION.cff` carries the same references in machine-readable form, each
> with a `notes:` line naming the claim it supports; [`../lineage.md`](../lineage.md) states
> what our measurements DO to each ancestor's claim.

Everything is in one of three kinds of entry. They are kept separate because they carry
different weight:

- **Data** — what we actually download and run on. Includes the exact file names, so a
  claim in a case study can be traced to a release.
- **Method** — the statistics the library implements or claims to reproduce. If a stage
  says "this is a known correction", the citation lives here.
- **Domain** — biology and clinical background for the disease adapters. Currently
  focused on **NF2 / NF2-related schwannomatosis**: see [`nf2.md`](nf2.md).

Two files sit outside those three kinds and say so. [`deep/foundations.md`](deep/foundations.md)
holds the mid-century work these approaches descend from — Turing, Shannon, von Neumann,
Ashby, Wiener, Waddington, Kolmogorov — each tied to a measurement or an open problem here,
and two of them tested against their own predictions (Turing's held; von Neumann's did not).
And [`theory-atlas.md`](theory-atlas.md)
catalogues the mathematics *proposed* for the multiscale atlas, graded measured / buildable /
analogy under ADR 0007. Nothing in it may be cited until it has a number.

> Verification status: entries below are recorded from working knowledge and are
> **not yet link-checked**. Accession numbers, file names, and release versions are the
> parts to verify before any of this is cited in a write-up; the conceptual claims are
> the parts that are safe to rely on today. Anything marked ⚠️ has a known gap.

---

## Data

### DepMap — the reference application

Public release files, from the figshare mirror (the portal itself sits behind a bot
check, so nothing here scrapes it). Downloaded by `python tasks.py fetch` into
`data/depmap/`.

| file | what it is | status |
|---|---|---|
| `CRISPRGeneEffect.csv` | lines × genes, Chronos gene effect. 0 = no effect, −1 = median common-essential | present |
| `AchillesNonessentialControls.csv` | the control pool for Stage 1 | present |
| `AchillesCommonEssentialControls.csv` | the known pan-essential confound, for Stage 3 | present |
| `AchillesHighVarianceGeneControls.csv` | high-variance controls | present |
| `AchillesScreenQCReport.csv` | per-screen QC, a Stage 3 covariate source | present |
| `Model.csv` | cell line annotation — lineage, disease, sex, age | present |
| `OmicsSomaticMutationsMatrixDamaging.csv` | damaging mutation matrix, defines the NF2-null subgroup | present |
| `OmicsCNGene.csv` | copy number, because NF2 is lost by deletion as often as by point mutation | present |

All three were added to `tasks.py fetch_nf2` on 2026-08-27, and the NF2 subgroup contrast
runs. Kept in the table because the sign convention below depends on knowing which files a
run actually read.

Sign convention: dependency is **negative** in DepMap, so `load_matrix` flips it. Every
stage in this library assumes larger is better.

### HPO language profiles — the language axis

`hpo-translations.tar.gz` (7.4 MB, Babelon TSV, from `obophenotype/hpo-translations`),
fetched by `python tools/ingest.py`. Fourteen languages besides English. Read by
`tools/language_coverage.py`, which reports term coverage against **annotation-weighted**
coverage — the second being what a reader actually meets, and the one that found Portuguese
at 42.9% with a 69.6-point spread across organ systems.


### The ingested catalogues, all nineteen

Downloaded by `python tools/ingest.py` into `data/ontology/` (gitignored). This table is
checked by `python tools/index_check.py`, which fails when a registered source appears in no
index — its first run found sixteen of the then eighteen named nowhere at all, and it caught
the nineteenth on the day it was added.

| file | source | size | what it gives us | licence |
|---|---|---|---|---|
| `genes_to_disease.txt` | HPO gene-to-disease | 2 MB | Every gene-disease association HPO curates, keyed by OMIM and ORPHA id. This is the backbone: it turns a disease list into a gene list. | HPO licence (permissive, attribution) |
| `phenotype.hpoa` | HPO disease annotations | 35 MB | Disease-to-phenotype annotations, and the authoritative count of annotated rare diseases. Its own header states the scale: 8,574 OMIM, 4,337 Orphanet. | HPO licence (permissive, attribution) |
| `hp.obo` | HPO ontology | 11 MB | The phenotype vocabulary itself, so a term id can be given a name and a position in the hierarchy. | HPO licence (permissive, attribution) |
| `hpo-translations.tar.gz` | HPO language profiles | 7 MB | The phenotype vocabulary in fourteen languages besides English, as Babelon TSV. Ingested because this project publishes in two languages and had no way to say what a reader loses in either. | HPO licence (permissive, attribution) |
| `submission_summary.txt.gz` | ClinVar submissions | 387 MB | Each submitter's classification BESIDE the condition it was made against. The aggregate file cannot separate a contradiction from two claims about two different conditions; this one can. | US public domain (NCBI) |
| `gene2pubmed.gz` | NCBI gene2pubmed | 40 MB | Which papers cite which gene. The attention axis - what the field has chosen to study - set against the burden axis it is supposed to follow. | US public domain (NCBI) |
| `en_product6.xml` | Orphanet gene associations | 22 MB | Orphanet's own gene-disease associations, with the association type (disease-causing, modifier, candidate) that HPO's flat file loses. | CC BY-ND 4.0 — no derivatives may be redistributed · **not redistributable** |
| `en_product9_prev.xml` | Orphanet prevalence | 16 MB | Prevalence class and geographic scope per disease — the only place the rare/ultra-rare boundary can be drawn from data rather than assumed. | CC BY-ND 4.0 — no derivatives may be redistributed · **not redistributable** |
| `en_product9_ages.xml` | Orphanet age of onset | 14 MB | Average age of onset and age of death per disease — the closest thing to a human-impact axis that comes from data rather than judgement. | CC BY-ND 4.0 — no derivatives may be redistributed · **not redistributable** |
| `rna_single_cell_type.tsv.zip` | Human Protein Atlas, single-cell RNA | 16 MB | Expression of every gene across ~80 human cell types. THIS IS THE CELL AXIS: it is what turns a gene list into a gene x cell matrix, at the scale the hand-authored lupus matrix could only gesture at. | CC BY-SA 4.0 — attribution and share-alike · **not redistributable** |
| `mondo.obo` | MONDO Disease Ontology | 53 MB | The merged disease ontology, and the one identifier space that CROSSES the others. It is the missing column in tools/lexicon_check.py, which today reports every MONDO id as `unverifiable` because the ontology was named in the lexicon and never ingested - a whole column of the identifier matrix reading 'never checked'. | CC BY 4.0 |
| `UniProt2Reactome_All_Levels.txt` | Reactome — UniProt to pathway, all levels | 90 MB | Pathway membership per protein. This is what turns the MODULE argument of docs/references/rare-disease-mechanisms.md from a borrowed claim into a computable one: §4 proposes that a shortlist should be diversified over signalling modules rather than genes, and nothing on disk could say which module a gene is in. | CC0 1.0 — public domain dedication |
| `ReactomePathwaysRelation.txt` | Reactome — pathway hierarchy | 1 MB | Parent-child relations between pathways, so membership can be rolled up to a level a person recognises. The same problem the HPO `is_a` walk solved for signs, on the pathway axis. | CC0 1.0 — public domain dedication |
| `9606.protein.links.v12.0.txt.gz` | STRING — human protein interaction network | 83 MB | A REAL interactome, with confidence scores. tools/interactome_sparse.py currently measures the HPO gene-disease graph and reports modularity 0.861 against a degree-matched null - and rare-disease-mechanisms.md §5.2 names the obvious objection: that graph may be measuring how HPO was curated rather than how biology is organised. STRING is the independent graph that settles it, because its edges come from an entirely different evidence base. | CC BY 4.0 |
| `9606.protein.info.v12.0.txt.gz` | STRING — protein info (ENSP to gene symbol) | 2 MB | The preferred gene symbol for every STRING protein id. Small, and it is the difference between an interactome we can join to the disease layer and one we can only count edges in. | CC BY 4.0 |
| `9606.protein.aliases.v12.0.txt.gz` | STRING — protein aliases (UniProt and other namespaces) | 20 MB | STRING id to every other namespace, including UniProt — which is what joins the interactome to REACTOME, whose pathway file is keyed on UniProt accessions. This is the bridge that makes the Pathway rung of the thesis ladder computable rather than named. | CC BY 4.0 |
| `gnomad.v4.1.constraint_metrics.tsv` | gnomAD v4.1 constraint metrics | 95 MB | Per-gene mutational constraint (pLI, LOEUF) over 730,947 exomes. This is the STAGE 6 PRIOR that docs/references/rare-disease-scale.md §4 argues for and docs/references/rare-disease-ancestry.md §3 warns about: the best structural prior available for a gene with no literature, and one whose panel is not ancestry-neutral. Ingesting it makes both the prior and the caveat testable instead of cited. | Freely available for any use; verify the current gnomAD terms before redistributing a derivative · **not redistributable** |
| `cellxgene_collections.json` | CZ CELLxGENE Discover — collection and dataset index | 3.1 MB | WHICH DISEASES ANYONE HAS ACTUALLY SEQUENCED at single-cell resolution, as MONDO terms. Every other cell-type layer here describes where a gene is expressed in a healthy reference — the Human Protein Atlas measures normal tissue — so a claim that a disease sits on a cell type is healthy biology plus an inference. This index says whether cells were ever collected from a patient with that disease at all, and reports the denominator: 2,216 datasets, 1,527 of them normal tissue. | CC-BY 4.0 (metadata); individual datasets carry their own terms |
| `fda_ai_devices.csv` | FDA — Artificial Intelligence-Enabled Medical Devices | 0.13 MB | THE REGULATOR'S OWN LIST of every AI-enabled device authorised for clinical use in the United States: 1,524 rows with decision date, submission number, company and review panel. The only source here that separates a model that was published from a model somebody is allowed to use on a patient. Supplies the top rung of a readiness scale as an observation rather than a claim. | US Government work, public domain |
| `all_phenopackets.zip` | Monarch phenopacket-store (GA4GH phenopackets) | 19 MB | 10,377 INDIVIDUAL PATIENTS, in the GA4GH standard, each with their own HPO terms, causative variant with an ACMG class, age, sex and the PMID they came from. Every other source here is aggregate: it reports what a disease does. This reports what happened to a person, and the difference is a denominator. Crucially, a phenopacket records phenotypes that were EXPLICITLY ABSENT as well as present - 65% of the assertions in a sample were `excluded` - so a frequency can be COMPUTED as observed/(observed+excluded) for diseases where docs/references/rare-disease-scale.md §4b measured that the curated catalogue has no frequency at all. | BSD 3-Clause |
| `variant_summary.txt.gz` | ClinVar variant summary | 442 MB | The variant layer this project does not have at all. Every dossier here reports a disease's GENES and stops; a clinician's next question is which variants, of what consequence, with what interpretation - and the allelic spectrum is also the honest test of whether a 'causal gene' attribution is one variant in one family or a characterised locus. | US Government public domain (NCBI) |

### HIV drug resistance — the second Stage 1 domain

Stanford HIV Drug Resistance Database genotype-phenotype datasets, public, downloaded to
`data/hiv/` by `curl` (not yet in `tools/ingest.py`).

| file | what it is | status |
|---|---|---|
| `PI_DataSet.txt` | 2,171 isolates, 9 protease inhibitors, amino acid at each of 99 positions | present |
| `NRTI_DataSet.txt` | 1,867 isolates, 7 nucleoside RT inhibitors | present |
| `NNRTI_DataSet.txt` | 2,272 isolates, 6 non-nucleoside RT inhibitors | present |
| `INSTI_DataSet.txt` | integrase inhibitors | ⚠️ **empty on download** — the URL resolves and returns 0 rows |

Read by `analyses/hiv_resistance.py`. See [`../expansion-map.md`](../expansion-map.md) for the
fit test, the control pool and what this domain broke.

### Planned data, not yet fetched

| dataset | for | note |
|---|---|---|
| PGC3 schizophrenia GWAS summary statistics | `adapters/gwas` | public download, per-variant p-values |
| 1000 Genomes EUR LD reference | effective SNP count per gene | needed for `n_eff` |
| PsychENCODE / CommonMind cis-eQTL | second data type, same max-over-SNPs operator | access terms to check |
| ROSMAP / ACT neuropathology | imaging-count adapter | ⚠️ requires a DUA; assume synthetic structure until granted |

### Non-biology data already in use

| source | for |
|---|---|
| `prompt-workbench` (Oráculo) `runs/` directory | `adapters/llm_eval` — best-of-N and unequal run budgets |

---

## Method

The statistics the library implements, and the prior art each stage should agree with.

**Stage 1 — selection bias in a maximum.** The whole library exists for this.

- *Order statistics / extreme value theory* — the expected maximum of n i.i.d. noise
  grows with n. This is the mechanism; everything else is a special case.
- *Winner's curse* — in GWAS, the effect size at a locus discovered by its own
  significance is biased upward, and the bias grows as power falls. The genetics-facing
  name for exactly what Stage 1 measures.
- *Regression to the mean* — the clinical-trial-facing name for it.
- *Deflated Sharpe ratio / probability of backtest overfitting* (Bailey & López de Prado)
  — the finance-facing name. A strategy selected as the max over many trials has an
  inflated expected Sharpe, deflated by a formula. `sieve` computes the empirical version
  from control periods instead of from the formula's assumptions.
- *Scan statistics, Darling–Erdős* — the change-point-facing name, and the one place with
  a clean analytic answer to check the empirical null against.
- *Gene-based association tests* (MAGMA's gene model, VEGAS, effective number of
  independent tests) — the correction the schizophrenia adapter must reproduce. This is
  the designated **falsification test** for the core: disagreement without an explanation
  means the library is wrong.

**Stage 2 — power.** Standard power analysis; the point is that an effect estimated from
one observation is not an effect.

**Stage 3 — confounds.** The assertion form used throughout: a correlation between the
score and a nuisance variable must *collapse* after calibration. If it does not, the
calibration failed. (In the obesity screen: −0.57 → +0.07 with observation count, which
dissolved a "viability confound" that was a statistical artifact.)

**Stage 4–5 — baseline and validation.** Out-of-fold evaluation, leakage-safe splits, and
the rule that a complex model must beat a simple one *out of fold* before it is believed.

**Stage 6 — prior.** Multiple testing and false discovery control (Benjamini–Hochberg) for
the ranking, plus a literature check so the shortlist does not re-nominate published dead
ends.

---

## Rare disease — the nine-document layer

Added 2026-08-27. They are separated because they answer different questions and carry
different evidence, and merging them would hide which is which.

| file | question | evidence |
|---|---|---|
| [`rare-disease-scale.md`](rare-disease-scale.md) | what does every rare disease share, quantitatively? | **measured here** — `out/rare/atlas.json`, `bias.json`, `prevalence_audit.json` — plus one external prevalence estimate |
| [`rare-disease-mechanisms.md`](rare-disease-mechanisms.md) | why do thousands of disorders collapse onto a few pathways? | **borrowed** — the module grouping is the field's; only the Stage 7 consequence is ours, and it is untested |
| [`rare-disease-equity.md`](rare-disease-equity.md) | which social facts become confounders? | **mixed** — external survey figures with intervals, over two internal layers explicitly marked as authored |
| [`rare-disease-ancestry.md`](rare-disease-ancestry.md) | whose numbers are these, and which population are they about? | **measured here** — `tools/ancestry_geography.py`, over the Orphanet geography field no layer had opened |
| [`rare-layers.md`](rare-layers.md) | which of these thirty-four artefacts did anyone actually measure? | the map of `out/rare/`: producer, grade and load-bearing number for each, with provenance quoted from the payloads |
| [`patient-data.md`](patient-data.md) | what do individual patients say, and what data can we actually get? | **measured** on 10,377 individuals — plus the access plan for the tiers that are not open |
| [`target-model.md`](target-model.md) | which editing strategy does a gene's evidence admit? | the how-to for `sieve target` — the one part of the project meant to be run by other people |
| [`prior-work.md`](prior-work.md) | which ancestors does this project have, and did it credit them? | the local lineage — `nominator`, `climate`, `adia`, `knee` — and the one it never mentioned |

The producers of all of the above are grouped in [`../../tools/README.md`](../../tools/README.md),
and what is left to do is ordered in [`../roadmap.md`](../roadmap.md).
| [`rare-disease-lexicon.md`](rare-disease-lexicon.md) | how do the identifiers join? | the crosswalk, and the unknown modelled as a value rather than a blank |

Everything cited by the first three was resolved through the Crossref API before it was
written down. That does **not** apply to the entries below, which carry the warning above —
see [`../audit.md`](../audit.md) A5 and F2.

## Domain

- [**NF2 / NF2-related schwannomatosis**](nf2.md) — the focused reference. Gene, protein,
  pathway, tumour spectrum, therapeutic history, and the specific DepMap analysis it
  makes possible.

---

## Sibling projects — what this repository borrows from the rest of the workspace

References are not only papers. These are the neighbouring campaigns whose practice is
already load-bearing here, each with what it contributes and where it lives.

| project | what yachay takes from it | where |
|---|---|---|
| `knee` (RSNA knee MRI, Kaggle 2026) | the **documentation apparatus**: role/last-revised/state header on every doc, an annotated `CITATION.cff` where each reference carries the claim it supports, a lineage file that says what our measurement DOES to the ancestor's claim, and an `archive/` of dead ends each with the number that killed it | `F:\CODE\knee` |
| `agentComp` (ARC-AGI-3) | the methodological laws `knee` inherited, above all "a wrong premise costs more than wrong code" — which is Stage 0 | via `knee/docs/METHOD.md` |
| `prompt-workbench` (Oráculo) | the second adapter, and the flaw it exposed in the core (`reduce="mean"` vs `reduce="raw"`) | `sieve.adapters.llm_eval` |
| `adia/structural-break-...` | the only candidate with an analytic ground truth to validate the null against | `expansion-map.md` §2 |

Three practices from `knee` are adopted here deliberately, and it is worth naming why:

1. **Every reference states the claim it supports.** A citation with no stated purpose is
   decoration; `CITATION.cff` refuses it by convention.
2. **Findings live in the citation header.** `knee` puts its measured numbers at the top of
   `CITATION.cff` so the claim and its number cannot drift apart. Done here too.
3. **Dead ends are archived with the number that killed them.** Adopted:
   `archive/MANIFEST.md` records each with the measurement that ended it.

---

## How to add an entry

Same discipline as the expansion map. An entry must state **what it is, what it is for,
and what state it is in** (present / not downloaded / access-gated / unverified). A
reference nobody can act on is noise, and a link with no stated purpose gets deleted.
