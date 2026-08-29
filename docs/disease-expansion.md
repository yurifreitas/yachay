# Disease expansion — from one obesity screen to a disease portfolio

> **Role:** the disease portfolio — which screens the method is being widened onto, and the test each had to pass.
> **Last revised:** 2026-08-29 · **State:** plan, not result. NF2 is the only entry with a run behind it.

`sieve` was distilled from a single obesity perturbation screen and hardened against
DepMap. This document plans the next widening: **several diseases whose screens have
different shapes**, so that the core stops being a generalisation of one assay.

The rule from `expansion-map.md` still governs. For every disease below we state the
**entity, the observation, the aggregate, and whether observation counts vary**. If those
four do not map, the entry is deleted rather than stretched — a disease being important
is not a reason to claim the method applies to it.

> Terminology note: the third disease is **NF2** — the gene on 22q12, and the condition now
> called *NF2-related schwannomatosis*. It is not NF1, and not `SMARCB1`/`LZTR1`
> schwannomatosis. The domain reference is [`references/nf2.md`](references/nf2.md).

---

## 0. Why more than one disease

The obesity screen and DepMap share a shape: *perturbation × cells, score = top-k*. Every
design decision in the core was made while looking at that shape, and the LLM-eval adapter
already proved the core was overfitted to it (`reduce="mean"` vs `reduce="raw"`). Adding
diseases that are **not** perturbation-vs-cells is the cheapest remaining way to find the
next such flaw.

The three candidates were chosen because they stress three *different* axes:

| disease | what it stresses | axis that is new |
|---|---|---|
| schizophrenia (GWAS / eQTL) | thousands of entities, max over a variable number of SNPs | the count is a **structural** property (gene length, LD), not a budget choice |
| NF2-related schwannomatosis | a **small genotype-defined subgroup** of an existing dataset | the inflation is driven by subgroup size, and there is a built-in positive control |
| Duchenne (DMD) | tiny n, expensive validation, strong prior | Stages 2 and 6 dominate; Stage 1 has little to bite on |

The third is deliberately a **weak** fit. Keeping it in the portfolio and reporting that the
headline correction barely moves it is the same discipline as the `synth` entry in the
expansion map.

---

## 1. Obesity — the origin (already documented)

| | |
|---|---|
| entity | perturbation (307 of them) |
| observation | one cell |
| aggregate | top-3 of 12 signature z-scores |
| counts vary | **yes**, 1 → 4,494 cells |

Status: the worked example behind `docs/methodology.md`. Nothing new is planned here beyond
keeping it as the regression case — any change to the core must reproduce its three
published numbers (2.0047 at the ~93rd noise percentile; −0.57 → +0.07; rank 12 → 1).

---

## 2. Schizophrenia — GWAS and brain eQTL

*The best next disease adapter, because the bias is structural and the field already has an
analytic correction to check against.*

| | |
|---|---|
| entity | gene or locus |
| observation | one variant's association statistic |
| aggregate | gene-based test — in practice a **max or top-k over the SNPs in the gene** |
| counts vary | **yes, enormously** — SNPs per gene spans ~1 to several thousand |

Why this is a strong fit: a gene-based score built as `max(-log10 p)` over its SNPs is a
max-order statistic whose inflation grows with the number of (correlated) SNPs tested. Long
genes and high-LD regions therefore top the ranking partly because they were measured more.
The field knows this and corrects it parametrically (MAGMA's gene model, VEGAS, the
effective number of independent tests). That makes schizophrenia a **validation target, not
just an application**: the empirical null should reproduce the analytic correction. If it
does not, the library is wrong, and we would rather find that out here than in a screen with
no ground truth.

Data, all public and download-scriptable (no scraping):
- PGC3 schizophrenia GWAS summary statistics (per-variant p-values).
- A reference LD panel (1000G EUR) to define the effective count per gene.
- Optional: PsychENCODE / CommonMind cis-eQTL, where the aggregate is `max over cis-SNPs`
  per gene — the same operator on a second data type.

Control pool for Stage 1, in descending order of trust:
1. Permuted phenotype labels, if individual-level data were available (assume it is not).
2. Intergenic windows matched on SNP count and LD structure, scored identically. This is the
   realistic control, and it mirrors the NONESSENTIAL-gene-set trick from DepMap.
3. Summary-statistic permutation within chromosome. Weakest; a real signal contaminates it.

Confounds for Stage 3: gene length, SNP density, LD block size, the MHC region, GC content.
The Stage 3 assertion is the same one as the obesity screen's viability confound —
correlation with count must collapse after calibration, or the calibration failed.

**Concrete first step:** implement `sieve.adapters.gwas` with `load_sumstats`,
`map_variants_to_genes`, `score_genes` (top-k over SNPs), and an intergenic control pool.
Then report: how many of the top-50 genes by raw gene score survive calibration, and how
strongly the raw ranking correlates with SNP count.

---

## 3. NF2-related schwannomatosis — a small subgroup inside a dataset we already have

*The cheapest of the three, because it needs no new data modality: it is a genotype-defined
contrast inside DepMap. Full domain reference in [`references/nf2.md`](references/nf2.md).*

| | |
|---|---|
| entity | a gene (~18,000) |
| observation | one cell line's Chronos gene effect |
| aggregate | top-k dependency **within the NF2-null subgroup**, contrasted against NF2-wildtype lines |
| counts vary | **yes, and severely** — the NF2-null subgroup is small, and lines screened per gene differ |

Why it is worth doing: a top-k over a *small* subgroup is the most inflated case Stage 1
handles. With a handful of NF2-null lines, pure noise reaches a large maximum, so the raw
"strongest dependency in NF2-null lines" ranking is substantially a ranking of who was
measured least. The obesity screen made that point at n=1; this makes it at the subgroup
sizes real precision-oncology analyses actually use.

And it comes with something DepMap and the obesity screen both lack: **a positive control**.
Merlin (the NF2 protein) is an upstream activator of the Hippo pathway, so NF2-null cells
lean on YAP/TAZ–TEAD. If the calibrated ranking does not recover `YAP1`, `WWTR1`, `TEAD1-4`,
and `LATS1/2`, the pipeline is broken and no novel hit from it should be believed.

Stage 0 has real teeth here. The tumours are benign, slow-growing, and lifelong; the endpoint
is preserving hearing, not maximal cytotoxicity. A gene that kills every line is not merely
uninteresting — it is an unacceptable toxicity profile for this disease.

The dominant threat is **Stage 3, lineage**: mesothelioma is over-represented among NF2-null
lines, so lineage-specific dependencies will masquerade as NF2 dependencies unless lineage is
regressed out. Stage 2 binds too — state the subgroup size up front.

**Blocker, and it is only data:** defining the subgroup needs `Model.csv` (lineage),
`OmicsSomaticMutations.csv`, and `OmicsCNGene.csv`, none of which `tasks.py fetch` downloads
yet. Copy number is not optional — NF2 is lost by deletion as often as by point mutation, so
a mutation-only subgroup would be wrong.

**Concrete first step:** extend `tasks.py fetch` with those three files, define NF2-null by
mutation *or* deletion, and report (a) the subgroup size, (b) how much of the raw subgroup
ranking is line count, and (c) where the Hippo genes sit before and after calibration.

---

## 4. Duchenne muscular dystrophy — the honest weak fit

| | |
|---|---|
| entity | a candidate compound, an ASO/exon-skipping construct, or a genetic modifier |
| observation | one well, one myotube, one muscle fiber |
| aggregate | % dystrophin-positive fibers, or **best-responding field**; modifier studies use a plain effect estimate |
| counts vary | yes, but the entity count is small (tens, not thousands) |

Stage 1's leverage scales with how many entities you rank and how much their counts differ. A
DMD modifier study with 30 candidates and a plain-mean endpoint is a **variance** problem, not
a selection-bias problem: the fix is an interval, not a null model — the `synth` verdict,
applied to a disease.

Where it *does* apply: high-content imaging screens that score a compound by its best field or
best well, and any "best of N constructs" selection. There, best-of-N is the same bug as the
prompt workbench.

What actually bites here is the rest of the pipeline:
- **Stage 2 (power)** — n is small and effects get reported anyway.
- **Stage 4 (baseline)** — does the model beat "rank by exon number and known skippability"?
- **Stage 6 (prior)** — the DMD literature is full of re-nominated dead ends.
- **Stage 7 (shortlist)** — with validation this expensive, betting every slot on one
  mechanism is the failure mode.

Keeping DMD in the portfolio is what stops the library from claiming Stage 1 is the answer to
everything. **First step:** run Stages 2, 4, 6, 7 on a public DMD dataset and publish the
result that Stage 1 moved nothing.

---

## 5. Shared machinery this implies

Three diseases, but not three unrelated adapters. The work factors:

- `adapters/gwas` — variant→gene mapping, LD-aware effective counts, intergenic control pool.
  Serves schizophrenia and any other GWAS trait, obesity included.
- `adapters/subgroup` — a genotype- or covariate-defined subgroup contrast on top of the
  existing DepMap adapter: subgroup definition, subgroup-size-aware nulls, and a lineage
  covariate slot. Serves NF2 and any other precision-oncology contrast.
- `adapters/imaging_counts` — long-format `(entity, unit, value)` with peak/top-k aggregates
  and a batch-covariate slot. Deferred; the DMD imaging screens are its first customer.
- Core additions likely to be forced by the above, in the spirit of the `reduce=` flaw:
  1. **correlated observations** — SNPs in LD are not independent draws; the null must be fit
     on blocks, not rows. This is the most likely place the current core breaks.
  2. **an effective-count argument** — `n_eff` distinct from raw `n`.
  3. **covariate-conditioned nulls** — fit the null within batch, for Stage 3.

If (1) is real, it is a genuine finding about the core, and it is the reason to do
schizophrenia first.

---

## 6. Sequencing and acceptance criteria

Ordered by expected value = likelihood the bug is present × cheapness of the check.

| # | Work | Done when |
|---|---|---|
| 1 | `adapters/gwas` on PGC3 schizophrenia | The empirical null reproduces the analytic gene-based correction within a stated tolerance, **or** we document where it does not and why |
| 2 | Core: block/LD-aware null fitting (`n_eff`) | `test_correlated_observations` fails before the change and passes after |
| 3 | NF2 subgroup analysis on DepMap (`adapters/subgroup`) | The Hippo axis (`YAP1`, `WWTR1`, `TEAD*`, `LATS1/2`) is recovered after calibration, and the lineage confound is shown to be removed rather than assumed away |
| 4 | Stage 3 with covariate-conditioned nulls | A batch effect that survives naive calibration is removed by the conditioned one |
| 5 | DMD: Stages 2/4/6/7, no Stage 1 claim | The write-up reports a null result for Stage 1 and is kept anyway |
| 6 | `docs/case-studies/` one page per disease | Each page carries an executable assertion (Stage 8) and regenerates from `python tasks.py` (Stage 9) |

## 7. What would falsify this plan

Stated in advance, so it cannot be rationalised later:

- If the NF2 analysis fails to recover the Hippo axis and we cannot attribute the miss to a
  named cause, the subgroup machinery is not trustworthy and no NF2 shortlist is published.
- If the schizophrenia empirical null **disagrees** with MAGMA-style corrections and we cannot
  explain the gap, the core is wrong and this expansion stops until it is fixed.
- If every disease adapter needs its own bespoke null, there is no shared method — only a
  collection of scripts, and the library's central claim is false.
- If Stage 1 moves nothing on two of the three biology-facing diseases, the honest conclusion is that the
  effect is specific to perturbation screens, and the README's framing must narrow.
