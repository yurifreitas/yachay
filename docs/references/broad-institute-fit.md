# Broad Institute initiatives — where `sieve` genuinely applies, and where it does not

> **Role:** an honest fit assessment between this library and the Broad's current
> translational initiatives, using the same four-question test applied to every other
> domain. Written because "fill all their gaps" is not an achievable brief and pretending
> otherwise would be exactly the failure this repository documents.
> **Last revised:** 2026-08-27 · **Sources:** the Broad's own announcements, read on
> 2026-08-27 through a browser — **the site returns 403 to automated fetchers**, the same
> bot-check that makes the DepMap adapter use the figshare mirror.
> **State:** the published organisation inventoried and scored; two initiatives mapped in
> detail. Verified quotes, unverified inferences marked ⚠️.

---

## 0. The headline, stated plainly

**Their stated bottleneck is not the one this library addresses.** Both initiatives say so
in their own words, and both times the answer is *infrastructure*, not statistics:

> *"often not because the science doesn't exist, but because we don't yet have the
> infrastructure to bring these treatments to many patients"* — David Liu, on CTG

`sieve` builds no infrastructure, no manufacturing, no regulatory pathway. On the primary
gap either centre names, it contributes **nothing**.

What it does address is a specific, recurring failure *inside* their pipelines — the point
where a ranked shortlist is produced from noisy measurements with unequal effort behind
them, and the next expensive step is chosen from it. That happens several times in both
programmes, and one of the numbers below suggests it is not a small effect.


---

## 1. The full inventory, scored by the four-question test

The Broad's own organisation, as published: 9 disease areas, 6 research areas, 8 technology
platforms, 7 centres. Every unit is scored by the same test applied to every other domain
in this repository (`expansion-map.md`), and **most of them fail it**, which is the point of
running the test rather than asserting relevance.

> 1. Many candidate entities to rank? 2. Each score estimated from noisy observations?
> 3. Does that count **vary**? 4. Is the aggregate a **selection** operator — max, top-k,
> quantile, enrichment, best-of-N — rather than a plain mean?

### Technology platforms

| Platform | Q1 | Q2 | Q3 | Q4 | Verdict |
|---|:--:|:--:|:--:|:--:|---|
| **Genetic Perturbation** | ✅ | ✅ | ✅ | ✅ | **Strongest fit at the Broad.** See §2. |
| **Imaging** | ✅ | ✅ | ✅ | ✅ | **Strong.** High-content screens scored by a best field or well; fields per well vary. |
| **Drug discovery** (HTS) | ✅ | ✅ | ✅ | ✅ | **Strong, and unexamined.** See §3 — the literature here was never searched. |
| **Metabolomics** | ✅ | ✅ | ⚠️ | ⚠️ | Depends on the scoring: feature detection across samples with varying coverage fits; a plain abundance mean does not. |
| **Proteomics** | ✅ | ✅ | ⚠️ | ⚠️ | Same. Peptide-to-protein roll-up is often a top-k over peptides, which would fit. |
| **Spatial technologies** | ✅ | ✅ | ✅ | ⚠️ | Cells per region vary enormously; whether the aggregate selects has to be read from the pipeline. |
| **Genomics / Clinical Labs** | ✅ | ✅ | ✅ | ⚠️ | Variant calling at varying depth. Fits where a **maximum over sites** is called; see the Gerstner note in §4. |
| **Data sciences** | — | — | — | — | Not a screen; it is where a method like this would live rather than something it corrects. |

### Centres

| Centre | Fit | Why |
|---|---|---|
| **Stanley Center for Psychiatric Research** | **Direct** | Serious mental illness — the schizophrenia GWAS target already planned in `disease-expansion.md` §2, and the disease GaMBiT names as its hard case. |
| **Eric and Wendy Schmidt Center** | **Methodological** | Data science × life science. A scope condition tested rather than asserted is the kind of contribution this centre exists for; it is not a screen to correct. |
| **Novo Nordisk Foundation Center for Genomic Mechanisms of Disease** | **Direct** | "Scale the discovery of biological mechanisms of common, complex diseases" — variant-to-mechanism at scale, the same shape as GaMBiT. |
| **Gerstner Center for Cancer Diagnostics** | **Direct, and underrated** | See §4. Detection by a maximum over candidate sites at varying depth is a scan statistic. |
| **Klarman Cell Observatory** | **Partial** | Atlas building is not ranking. But cluster **marker selection** is a max over genes per cluster, with cells per cluster varying by orders of magnitude — that specific step fits. ⚠️ inferred. |
| **Carlos Slim Center** | **Indirect** | Population genomics; inherits whatever the GWAS adapter offers. |
| **Merkin Institute** | **Not applicable** | Early-stage technology funding, not a screen. |

### Disease areas

Eight of the nine are covered by whichever platform produces their data. One is different:

**Obesity is a listed Broad disease area — and it is the screen this library was distilled
from.** Every founding number in this repository (the 2.0047 training maximum measured on
one cell, the −0.57 → +0.07 confound, the rank 12 → 1 move) came from a perturbation screen
in that disease. That is not a claim of relevance to their programme; it is a statement that
the method has already been run once in that disease area, on a public competition's data,
and that the case study is the honest thing to point at.

**Rare disease** is CTG (§6). **Brain Health** is the Stanley Center. **Cancer** is DepMap
and Gerstner.

---

## 2. Genetic Perturbation Platform — the closest fit in the institute

Pooled CRISPR screening is where this library's exact failure mode is structural rather
than incidental:

| | |
|---|---|
| entity | a gene |
| observation | one guide RNA in one replicate, read at some depth |
| aggregate | **a rank aggregation over the gene's guides** — RIGER, RSA, MAGeCK's RRA |
| counts vary | **yes** — guides per gene, reads per guide, replicates per screen |

**Rank aggregation is a selection operator.** RSA and MAGeCK's RRA both score a gene by how
extreme its *best* guides are; a gene with more guides, or with guides read more deeply, has
more chances to produce an extreme one. The correction this library applies is defined for
exactly that class of statistic.

⚠️ **Unverified and important:** these methods carry their own permutation nulls, and MAGeCK
in particular estimates a null by permuting guides. Whether that null is indexed by *guide
count per gene* — the thing that varies — is the question that decides whether this is a
contribution or a reinvention. **It has not been checked, and it should be checked before
any claim is made.** This is the same mistake the selection-bias review caught once already:
asserting novelty in a field whose literature was not searched.

---

## 3. Drug discovery / HTS — the gap in our own review

The adversarial literature review that ran on 2026-08-26 exhausted its search budget and
recorded two unswept areas. One of them is **high-throughput screening statistics** —
SSMD, Z′, B-score, plate-level hit-rate normalisation — and it flagged that an n-indexed
null of a hit-count or top-k statistic could plausibly already exist there
(`deep/selection-bias.md` §7).

The Broad runs an HTS platform. So the honest position is: **the single field most likely to
have already solved this is the one we have not read, and it is one of theirs.** Sweeping it
is a prerequisite to any claim, not a follow-up.

---

## 4. Gerstner Center — detection as a scan statistic

Cancer early detection and MRD monitoring from liquid biopsy has a shape that is textbook
for this library and, ⚠️ on inference from the centre's public description rather than from
their protocols:

| | |
|---|---|
| entity | a candidate variant site, or a patient sample |
| observation | one read covering that site |
| aggregate | detection = **the maximum evidence over many candidate sites** |
| counts vary | **yes** — sequencing depth differs per site and per sample |

Scanning thousands of sites and calling the largest is a scan statistic, and the
literature's analytic correction for it (Darling–Erdős) is the same external ground truth
this repository has designated as its own falsification test and **never run**. A detection
threshold that does not account for how many sites were scanned, at what depth, has a
false-positive rate that varies with sequencing depth — which in a diagnostic is not a
ranking problem but a patient-facing one.

---

## 5. GaMBiT — Genes, Mechanisms, Biomarkers and Therapeutics

*Launched 2026-08-10, led by Mark Daly, Klarman Family Foundation support.*

**Their stated problem**, verbatim:

> *"the interpretation of genetic variants associated with disease remains challenging,
> especially for common and chronic diseases like **schizophrenia**, Parkinson's, or
> inflammatory bowel disease, where hundreds of variants each make small contributions to
> risk."*

And the number that should stop this repository in its tracks:

> *"more than **95 times out of 100**, our genetic discoveries don't progress to concrete
> and impactful knowledge."*

### Why this is the closest fit in the document

`docs/disease-expansion.md` §2 proposed a schizophrenia GWAS adapter as the best next
target — written before this initiative was read. GaMBiT names schizophrenia as its
canonical hard case. That is a coincidence of interest, not evidence, but it means the
planned work is aimed at a problem a major centre has just funded a programme against.

### The four-question test

| | |
|---|---|
| entity | a gene or locus |
| observation | one variant's association statistic |
| aggregate | gene-based test — in practice a **max or top-k over the SNPs in the gene** |
| counts vary | **yes, enormously** — SNPs per gene spans ~1 to several thousand, and the variation is *structural* (gene length, LD), not a budget choice |

Four yeses. The correction applies.

### Three places it bites inside their described pipeline

1. **Variant-to-gene aggregation.** Any gene score built as a max or top-k over its
   variants is inflated by how many correlated variants the gene contains. The field
   corrects this parametrically (MAGMA, VEGAS) — which makes this a **validation target
   before it is an application**: the empirical null should reproduce the analytic
   correction, and if it cannot, this library is wrong. That test has not been run.
2. **Variant-to-function screens.** GaMBiT describes *"editing massive numbers of variants
   into cells and reading out mechanisms"*. Entity = variant, observation = cell or read,
   and such screens are routinely scored by a **maximum or top-k effect across guides and
   replicates**, with replicate counts that differ per variant. ⚠️ This is inference from
   the description; the actual scoring function would have to be read.
3. **The learning knowledge base.** Their strongest idea is that every experiment feeds a
   growing queryable base so later work reuses earlier results. That is also where
   selection bias *compounds*: a shortlist chosen partly on measurement effort becomes the
   input to the next round, and the bias is inherited rather than re-estimated. Nothing in
   the announcement suggests they are unaware of this — but it is the failure mode a
   learning ecosystem has that a one-shot pipeline does not.

### The honest caveat on the 95 %

Winner's curse is **a** documented contributor to non-replication, not **the**
explanation. Biology, cell-type context, pleiotropy and effect-size realism account for
most of that number. Claiming otherwise would be the overreach this document exists to
avoid.

---

## 6. CTG — the Center for Therapeutic Genetics

*Announced 2026-07-21. Broad + Boston Children's + The Jackson Laboratory. Founders David
Liu, Cat Lutz, Timothy Yu, Wendy Chung; director Winston Yan. Programmes include precision
gene-editing for rare genetic epilepsies, with an ARPA-H THRIVE award of up to $34.5 M.*

**Their stated problem:** ~8,000 rare diseases, 350–400 million people, **fewer than 1 in
20 with an approved treatment**; the traditional model is built for large populations, not
for medicines designed for one patient. Their answer is a *platform strategy* — design
tools, disease models, manufacturing, safety data and clinical protocols shared across
programmes.

### Where `sieve` applies — and one of these is a safety question

| # | Decision point | Shape | Fit |
|---|---|---|---|
| 1 | **Off-target site ranking** | candidate sites ranked by read support, a max/top-k over a **varying sequencing depth** | **Strong.** A site called only in a shallowly-sequenced sample, or missed in one, is a count artefact with a safety consequence. This is Stage 1 on its home ground. |
| 2 | **Guide and editor selection** | pick the best of N designs, each measured in few replicates | **Strong.** Best-of-N is the `llm_eval` adapter's exact shape: the winner is partly the design that got lucky, and its reported efficiency will regress. |
| 3 | **Disease-model selection** (JAX) | choose the model that best recapitulates the phenotype, from several, each with few animals | **Moderate.** Same best-of-N, small n, expensive validation — and DMD-shaped: Stages 2, 4, 6 and 7 matter more than Stage 1. |
| 4 | **n-of-1 efficacy** | one patient, one time course | **This is the origin case, at its limit.** The obesity screen's founding number was a record score measured on **one observation**, where pure noise averages 0.845. An n-of-1 result is that regime by construction, and the null has to come from pre-treatment or control periods. |
| 5 | **The platform-reuse claim** | "methods developed for one disease carry to the next" | **Stages 4 and 5, not 1.** It is a transfer claim, and it needs a baseline and a leakage-safe evaluation before it is believed. |

### Where it applies to nothing

Manufacturing scale-up, regulatory frameworks for n-of-1 medicines, reimbursement, clinical
operations, and the editing chemistry itself. **That list contains their actual
bottleneck.** Stated here rather than buried, because a fit assessment that only lists fits
is advertising.

---

## 7. DepMap 3D — the frontier already in this repository

*2026-08-05: the Cancer Dependency Map now includes next-generation 3D models (147
genome-scale CRISPR screens in organoids and spheroids, 10 cancer types).*

Already recorded in `state-of-the-art.md` §3 with the consequence that matters here:
**every such expansion shrinks the subgroups being contrasted**, and the inflation of a
top-k statistic grows as n falls. The frontier is moving toward the regime where an
uncorrected subgroup contrast is most wrong — which is also, per this repository's own
NF2 run, the regime where getting the *statistic* wrong costs more than getting the
*calibration* wrong.

---

## 8. What could actually be offered, in order of honesty

Nothing here is a claim to fill anyone's gap. These are checks that are cheap, falsifiable,
and runnable on public data.

1. **Run the MAGMA reproduction.** Build `adapters/gwas`, score genes by top-k over SNPs on
   public PGC3 schizophrenia summary statistics, and report whether the empirical null
   reproduces the analytic gene-based correction. **A negative result is the valuable one**
   — it would say this library is wrong, and it is the only external ground truth available.
2. **Quantify the count artefact in one variant-to-function screen** with public data:
   how much of the hit ranking is replicate count. One number, one afternoon.
3. **Publish the control-calibration check as a one-page diagnostic.** The Q-Q plot that
   caught a four-sigma defect here costs nothing to run on any screen with a control set,
   and this repository has now measured what it is worth.
4. **Read the HTS literature before claiming anything** (§3). The field most likely to have
   solved this already is one of theirs, and our own review flagged it as unswept.
5. **Check whether MAGeCK's null is indexed by guide count** (§2). One reading of one
   method's source settles whether the Genetic Perturbation fit is a contribution or a
   reinvention.
6. **Say plainly what does not transfer.** The strongest thing this project can offer a
   platform organisation is the discipline it has been forced into: positive controls that
   can fail and block the shortlist, dead ends archived with the number that killed them,
   a scope condition tested rather than asserted, and a chart whose job is to make a
   defect impossible to miss.

## 9. Verification status

- **Verified**, read directly from the source pages on 2026-08-27: the existence, dates,
  institutions, named people, funding figures and all quoted statements for CTG and GaMBiT;
  and the published list of disease areas, research areas, technology platforms and centres.
- ⚠️ **Inferred, not verified**, and this is the larger half: **every entry in the §1
  inventory tables is scored from a unit's public one-line description, not from its
  protocols.** A platform's page says what it does, not what statistic it ranks on, and the
  fourth question can only be answered by the latter. Also inferred: that GaMBiT's
  variant-to-function screens are scored by a selection operator; that CTG's off-target
  pipelines rank by read-support maxima; that Klarman's marker selection is a per-cluster
  maximum; the Gerstner shape in §4; and the whole of §2 beyond the fact that rank
  aggregation is a selection operator.
- **Not attempted**: any contact, proposal, or claim of collaboration. This is an internal
  fit assessment.
