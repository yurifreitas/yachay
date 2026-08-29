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
