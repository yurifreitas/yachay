# Lineage — whose work this descends from, and what our measurements say about it

> **Role:** the intellectual genealogy. Who established each piece of the approach, what the
> original claim is, and **what our measurement does to it** — confirms, extends, quantifies,
> or contradicts.
> **Last revised:** 2026-08-29 · **State:** fifteen sections mapped, eight tied to a number
> we measured and the rest tied to work not yet done; plus §11 (rare disease) and §12 (ancestry and
> founder history), whose references are the first in this file to be **verified rather than
> recalled**. §12 is also the first added section where OUR side is a fresh measurement
> rather than a borrowed claim.
>
> ⚠ **The references in §§1-9 come from working knowledge, not from consultation.** Year,
> venue and author order **must be checked** against the source before any of this is
> published. **§11 is the exception**: every entry there was resolved through the Crossref
> API — title, authors, venue, year, DOI — before it was written down. The rest of the file
> is waiting on the verifier described in [`audit.md`](audit.md) F2.
> What is verified is the right-hand side: our own measurements, which come from
> `out/DEPMAP_FINDINGS.md` and the obesity case study.
>
> ⚠ **The local ancestors were missing from this file until 2026-08-28.** `nominator` is the
> direct methodological ancestor — nine of these ten stages are its, renumbered — and it went
> uncredited through sixteen audit sweeps while this file scrupulously credited Bailey,
> Menche and Norio. See §13 and [`references/prior-work.md`](references/prior-work.md).
>
> Form inherited from `F:\CODE\knee\docs\LINHAGEM.md`. Citations live in `CITATION.cff`;
> data and domain references in [`references/`](references/README.md).

---

## 0. The map in one table

| # | Lineage | Anchor name | What we owe it | What our measurement says |
|---|---|---|---|---|
| 1 | Expected maximum of noise | **David & Nagaraja** (order statistics) | the mechanism itself | measured, not assumed: bias **0.3934 → 0.5638** across n=347→1178 on DepMap |
| 2 | Selection bias deflation from a formula | **Bailey & López de Prado** (deflated Sharpe) | the closest prior art in spirit | we replace the formula's independence assumption with the screen's own controls |
| 3 | Effect inflation at discovered loci | **winner's curse** (GWAS) | the name for the bias in genetics | our version is *per-entity by observation count*, not per-locus at discovery |
| 4 | Analytic correction for a scanned maximum | **Darling–Erdős**, scan statistics | the one available ground truth | **not yet run** — the designated falsification test |
| 5 | Gene-based association tests | **MAGMA**, VEGAS | the correction the GWAS adapter must reproduce | **not yet run** — acceptance criterion for `adapters/gwas` |
| 6 | Toxicity is not selectivity | **DepMap** (Tsherniak, Hahn) | the framing of selective dependency | **60% of the raw top 10 are pan-essential** — the metric's maximum is toxicity |
| 7 | Error control on many tests | **Benjamini–Hochberg** | Stage 6's machinery | kept as the fix that *does not* solve this problem — see §7 |
| 14 | Chart forms — hexbin, raincloud, UpSet | **Carr 1987; Allen 2019; Lex 2014** | the three forms §7b of the visualisation canon listed as needed and unbuilt | all three built 2026-08-28; each found something its predecessor form had hidden — see §14 |
| 8 | **Ranking units of unequal precision** | **Gelman & Price (1999)** | ⚠️ **the thesis itself** — they state the confound and the z remedy | our contribution shrinks to the estimator and the operator family; see [`references/deep/selection-bias.md`](references/deep/selection-bias.md) |
| 9 | n-indexed empirical null | **Hartman et al. (2024)**, AoAS | the same three-step shape, published first | ours resamples a control pool instead of fitting a mixture to the observed z's |

---

| 63 | Selective constraint as a prior | **Karczewski et al.** (2020) | quantifies its own stated caveat | disease genes 0.8435 against a length-matched 0.8861 (z -8.68) — but **66 %** of the distance from the genome mean is length, not constraint |
| 64 | Ancestry composition of genetic studies | **Sirugo et al.** (2019) | quantifies, and qualifies a natural reading of it | 65.8 % European across 562 psychiatric analyses — and against seven other disease areas psychiatry is the **least** European of the eight, so the problem is the field's rather than psychiatry's |
| 65 | Transferability of polygenic scores | **Martin et al.** (2019) | extends the unit of measurement | measured per ANALYSIS, not per cohort: ADHD, OCD, anorexia and Tourette carry zero analyses with an African-ancestry majority |
| 66 | Who is counted in a GWAS | **Popejoy et al.** (2016) | extends it to a unit the original did not use | 11.9 % of psychiatric analysis weight declares no ancestry whatsoever — a category the participant-level count cannot express |
| 67 | Consortium-scale psychiatric genetics | **Trubetskoy et al.** (2022) | measures its composition without touching its findings | schizophrenia carries the most analyses of the nine disorders and 3 of them have an African-ancestry majority |
| 68 | A public index of single-cell data | **CZI et al.** (2025) | uses it as a denominator nobody had applied | **77 of 14,831** catalogue diseases are reachable from a public single-cell dataset — 0.52 %, and 1,527 of 2,216 indexed datasets are normal tissue |
| 69 | Where a gene is expressed, in normal tissue | **Karlsson et al.** (2021) | states the limit of an inference built on it | the cell-type axis is an inference rather than an observation for **99.5 %** of these diseases |
| 70 | Pathways as a coarser alphabet | **Gillespie et al.** (2022) | contradicts a reading this repository had given its own result | the field-shaping families do **not** carry more about morphogenetic systems than the energy families (-0.009477 against -0.005272 bits) — so the loss is about how coarse the alphabet is, not about what its letters mean |
| 71 | Genome-scale Perturb-seq | **Replogle et al.** (2022) | applies a calibration the design invites and does not supply | the challenge's own top-3 aggregate has a floor of 0.239 at 8 cells and 0.001 at 900 — resampled from a designed non-targeting control |
| 72 | Pooled single-cell genetic screens | **Dixit et al.** (2016) | quantifies a bias the design produces | 16 of the raw top 20 survive calibration and 4 are displaced; perturbations under 100 cells in the top 20 drop from 3 to 1 |
| 73 | How cleared medical AI is evaluated | **Wu et al.** (2021) | extends its count and adds the distribution | 1,164 of 1,524 authorisations are radiology (76.4 %), one panel holds half the list, and 90 % of the list was authorised in 2019 or later |
| 74 | A database of cleared AI devices | **Benjamens et al.** (2020) | updates it and names what it did not report | the Dermatology panel does not appear at all — a fact about review pathways that the tool's own name scan corrects, finding 2 skin-lesion devices reviewed elsewhere |

## 1. The expected maximum of noise — order statistics

**The work.** That `E[max of n draws]` increases with n is textbook (David & Nagaraja,
*Order Statistics*). Extreme value theory characterises its asymptotic behaviour.

**The central claim:** any operator that *selects* the largest of several noisy estimates is
positively biased, and the bias grows with the noise.

**What we measured.** The bias, empirically, from real control observations rather than from
a distributional assumption. On DepMap, with a top-20 mean over 781 nonessential control
genes (knockouts known to do nothing):

| lines screened | null mean | null sd | p99 |
|---:|---:|---:|---:|
| 347 | 0.3934 | 0.0445 | 0.5157 |
| 736 | 0.4928 | 0.0496 | 0.6175 |
| 1178 | 0.5638 | 0.0522 | 0.7020 |

And on the obesity screen, with a top-3-of-12 statistic, where the range of n is far wider
and the effect correspondingly brutal:

| observations | null mean | null p99 |
|---:|---:|---:|
| 1 | 0.845 | 2.434 |
| 16 | 0.207 | 0.658 |
| 100 | 0.079 | 0.256 |
| 224 | 0.052 | 0.170 |

**What we add.** Two things, both about the regime rather than the mechanism.

First, **the non-asymptotic range is the one that matters**. EVT describes n → ∞; screens
live at n = 1 to 20, where the limit theorems do not apply and the empirical null does. The
obesity table's top row — a score of 0.845 expected from *nothing*, at n=1 — is the entire
argument for the library, and it is exactly where the asymptotic theory is silent.

Second, **direction reverses with the statistic**. On DepMap the null mean *rises* with n
(0.3934 → 0.5638) because a top-20 mean over more lines finds a more extreme top 20; on the
obesity screen it *falls* with n (0.845 → 0.052) because a top-3-of-12 over more cells
averages a better-estimated signature. Same mechanism, opposite slope, and the direction is
a property of the statistic — not something to be guessed. This is why `fit_null` takes the
**same statistic the screen scores with** as an argument, and why any library that hard-codes
a correction is wrong for half the screens it meets.

## 2. Deflating a selected maximum — Bailey & López de Prado

**The work.** The *Deflated Sharpe Ratio* and *Probability of Backtest Overfitting* correct a
performance number for the fact that it was selected as the best of N trials, using the trial
count and the distribution's shape.

**The central claim:** the maximum over many trials has an inflated expectation, and you can
deflate it if you know how many trials there were.

**What our approach does to it.** It agrees on the target and changes the estimator. The DSR
deflates from a formula whose inputs are trial count, skew, kurtosis, and an independence
assumption. `sieve` resamples the screen's *own* control observations and applies the *same*
statistic — so it inherits the real correlation structure, the real heavy tails, and the real
per-entity observation counts, none of which have to be named or parameterised.

**Where that matters, concretely.** The DepMap control pool is 841,293 real (line, gene)
values, not 841,293 independent draws — cell lines share lineage, medium and batch. A formula
told there were n independent trials would under-deflate. This is also the mechanism behind
one of our two open anomalies (§8).

**Where the formula wins:** it needs no control pool. If you have no rows known to carry no
effect, `sieve`'s Stage 1 has nothing to fit and the parametric route is the only route.
That is a real limitation of this library and is stated in `methodology.md`, not hidden here.

## 3. Winner's curse — the genetics name

**The work.** In GWAS, the effect size estimated at a locus discovered by its own
significance is biased upward; the inflation grows as power falls, and replication cohorts
routinely report smaller effects.

**What ours is, and is not.** Same mechanism, different cut. The winner's curse is usually
framed *per discovery*: conditional on passing a threshold, the estimate is inflated. Stage 1
is framed *per entity by observation count*: every entity's score is inflated, by an amount
that depends on how many observations it had, whether or not it passed anything. That is the
form that breaks **comparability across entities**, which is what ranking needs.

The consequence is the number we care most about: in the obesity screen a **−0.57**
correlation between score and observation count — read as a viability confound, i.e. as
biology — fell to **+0.07** after calibration. A curse framed per-discovery would not have
caught that, because nothing had been discovered yet.

**Status of the tie-in:** the planned `adapters/gwas` (`disease-expansion.md` §2) is where
this lineage gets tested on its home turf, and it has not been run.

## 4. Darling–Erdős and scan statistics — the ground truth we have not used

**The work.** Scanning candidate change points and taking the largest test statistic is a
classical problem with an *analytic* correction for the scan.

**Why it is the most valuable entry in this file.** DepMap and the obesity screen have no
ground truth: we can show that calibration changes the ranking, but not that the calibrated
ranking is *right*. Change-point detection has a known answer. If `sieve`'s empirical null
reproduces it, the method is validated against something external. If it does not, the
library is wrong.

**Status: not run.** Stated here so the absence is visible rather than implied. Until it is
run, every claim in this repository is internal-consistency evidence.

## 5. Gene-based tests — MAGMA and VEGAS

**The work.** A gene-level score built from the SNPs inside a gene must account for the
number of SNPs and their LD; MAGMA does it with a gene model, VEGAS by simulation from an LD
reference.

**What we would add — and the flaw it will probably expose.** VEGAS is close to what `sieve`
does, so the interesting part is not the agreement but the failure mode it forces: **SNPs in
LD are not independent draws**. The current core fits its null by resampling *rows*. If
observations are correlated in blocks, row resampling understates the null's spread and the
calibrated z is too large. This is the most likely place the core is broken, it is why
schizophrenia is sequenced first, and it is written down as a prediction so it can be scored
later rather than rationalised.

**Status: not run.**

## 6. Selective dependency vs pan-essentiality — DepMap

**The work.** The Cancer Dependency Map frames the useful signal as a *selective* dependency —
a gene whose loss kills some contexts and spares others — and pan-essential genes as the
uninteresting background.

**What we measured.** That the framing is not merely a preference but a *statistical*
necessity, because the raw metric actively selects against it:

- **60% of the raw top 10 by top-20-mean dependency are known pan-essential genes** —
  SNRPD3, RAN, RRM1, SNRPF, PLK1, RPS8.
- After calibration, mean z by class: common-essential **+25.72** (n=1242) versus nonessential
  control **−4.09** (n=726).

This is the small screen's KIF11 lesson at four orders of magnitude more data: the strongest
signal in a viability screen is toxicity. Stage 0 exists because of it — decide what the
metric's maximum *is* before optimising toward it.

**What NF2 adds to this lineage.** For a benign, slow-growing, lifelong tumour, a
pan-essential hit is not just uninformative — it is an unacceptable toxicity profile. The
selectivity requirement stops being a modelling preference and becomes a clinical constraint.
See [`references/nf2.md`](references/nf2.md) §4.

## 7. Benjamini–Hochberg — kept as the fix that does not fit

**The work.** FDR control over many hypothesis tests.

**Why it is in this file.** Because it is the standard answer people reach for, and it does
not solve this problem. FDR controls the *proportion of false positives among rejections*. It
says nothing about the **ordering** among survivors — and a shortlist is an ordering. Two
genes that both clear an FDR threshold can be ranked entirely by which one was screened in
fewer lines. Stage 1 fixes the ranking; BH fixes the cutoff; they are complementary, and
substituting the second for the first is the most common way to skip Stage 1 while believing
you have not.

---

## 8. Two anomalies — measured, and now explained

Stated in the same place as the successes, because a lineage file that only records
confirmations is advertising.

**(a) The control pool calibrates to −4.09, not ~0.** Nonessential control genes should
standardize to a mean z near zero — they are the null by construction. They come out at
**−4.09**. Leading hypothesis: the null is fit by pooling control *observations* across
genes, so it models the spread of a random draw from the pool rather than the spread of a
*gene* — and real genes carry between-gene variance the pooled draw does not. If that is
right, the fix is fitting the null on gene-shaped blocks, which is the *same* fix §5 predicts
for LD. Two independent routes to one correction is weak evidence that the correction is real.

**(b) The count correlation got worse, not better.** On the obesity screen calibration
collapsed the correlation with observation count (−0.57 → +0.07). On DepMap it moved
**−0.0252 → −0.0559** — small in absolute terms, but the wrong direction. Note that the raw
correlation was already near zero because DepMap's n range is narrow (347–1178, a factor of
3) against the obesity screen's (1–4,494, a factor of 4,494). A near-zero starting point
means there was nothing to collapse, so this may be noise around zero rather than a defect —
but "may be" is not a result, and until it is quantified with an interval it stays here.

### ✅ Both were resolved on 2026-08-26 — and both were defects

The internal-audit lane explained (a) exactly and settled (b) with the repository's first
confidence interval. Full evidence in
[`references/deep/internal-audit.md`](references/deep/internal-audit.md).

**(a) is a defect, and the hypothesis above was right.** The pooled control sd is 0.1604
against a within-gene sd of 0.1092 — the between-gene sd of 0.1131 is folded into the null
that should have described a single gene. The null mean comes out at 0.5587 against an
observed control mean of 0.3475, a gap of −0.2112, divided by a null sd of 0.0517:
**−0.2112 / 0.0517 = −4.08**, reproducing the shipped −4.09 with no residual. Fitting the
null by resampling **whole control genes** puts the controls at **mean z = +0.017, sd ≈ 1**.

*ADR 0004 predicted this before the work and is hereby scored correct.*

**(b) is a defect, not noise.** A 4,000-resample paired bootstrap over 17,916 genes gives
the change in Spearman a 95 % interval of **[−0.0344, −0.0271]**, P(>0) = 0.000. The
mechanism is the same defect: the pooled null's mean rises +0.1737 across n = 347→1178
where a gene-shaped null rises +0.0892 — **1.95× too steep**, so high-n genes are
over-corrected.

And the published number **understated** it. 95.4 % of genes share n = 1178; only 19
distinct counts exist, so the correlation rests on 829 rows — where the calibrated value is
−0.1685 against −0.0323 raw.

### §10 — the control set may not be inert (found by changing a chart)

The Q-Q plot added to the explorer on 2026-08-27 shows the blocked null is correct through
the body (median z −0.12) and has a **heavy right tail**: the 99.95th percentile of the
nonessential control set sits at **8.9**, where a standard normal gives 3.3.

The reading is that some genes in the "known to do nothing" set behave like real
dependencies — a **control-set purity** problem, not a null problem. If true it inflates the
null's spread and makes every z slightly conservative.

It was invisible in the density overlay that preceded the Q-Q, and invisible in every table.
Not fixed, not diagnosed; see `references/visualization-canon.md` §3.

### §9 — the earlier open anomaly

Two lanes proposed **different** fixes for the NF2 positive-control failure, and both
recover the biology:

- replacing the two-null z-difference with a **permutation null on the group label** moves
  the Hippo median rank from 5,216 to **716** of 17,916;
- replacing the top-k contrast with a **plain difference in means** ranks YAP1 at **30**,
  TEAD1 at **27**, WWTR1 at **55** (independently reproduced by the maintainer).

These are not the same statistic and they are not the same claim. The second implies Stage 1
is **not needed** for this analysis at all — which the library's own four-question test
predicts, since a difference in means answers *no* to question 4. Which fix is right is
open, and it decides whether NF2 is a `sieve` demonstration or merely a good analysis.

---

## 11. Rare disease — the mechanism, the scale, and the social layer

Added 2026-08-27, alongside [`references/rare-disease-mechanisms.md`](references/rare-disease-mechanisms.md),
[`references/rare-disease-scale.md`](references/rare-disease-scale.md) and
[`references/rare-disease-equity.md`](references/rare-disease-equity.md). Same rule as every
section above: the ancestor's claim on the left, **what our measurement does to it** on the
right. Where our answer is "nothing yet", that is written rather than omitted — six of the
fifteen entries below are `no measurement`, which is the honest state of a layer added this
week.

| ancestor | their claim | what our number does to it |
|---|---|---|
| **Nguengang Wakap et al. 2020** | 3.5-5.9% of people, 263-446M; 84.5% of analysable diseases below 1/1,000,000 while 4.2% carry ~80% of the burden | **Extends, on a different join.** Our atlas reaches 14,831 diseases against their 6,172 (different scope: we join OMIM + ORPHA + DECIPHER), and finds the same lopsidedness from the other side — the median disease has **one** gene and the count spread is **114×**. Their distribution of prevalence and our distribution of evidence are the same shape. |
| **Nguengang Wakap et al. 2020** | prevalence is a usable per-disease quantity | **Qualifies, sharply.** `tools/prevalence_audit.py` finds **17,108 records over 6,728 disorders** in five incommensurable types, with **68.6%** of disorders carrying more than one type and **65%** of records carrying no geography. Prevalence is a list of measurements, not a number; only **4,444** disorders have a validated point-prevalence class. |
| **Goh et al. 2007** | disease genes cluster in the network rather than scattering | **Adjacent, not confirmatory.** We measured the HPO disease-gene graph for a computational reason and found **modularity 0.861** against **0.162** for a degree-matched rewiring. Same object, different statistic, no interval. |
| **Menche et al. 2015** | each disease occupies a connected module; network distance predicts shared phenotype | **No measurement.** We have not computed a module separation and have not tested the phenotype prediction. §2 of the mechanisms doc states the null (rewiring within curation source) that would show our 0.861 is measuring curation rather than biology. |
| **Rauen 2013**; **Crino 2016**; **Reiter & Leroux 2017**; **Narla & Ebert 2010**; **Platt et al. 2018**; **Gorman et al. 2016** | distinct rare disorders converge on a shared signalling module, and the module predicts therapeutic class | **No measurement, and one prediction.** The module grouping is entirely theirs. What is ours is the consequence for **Stage 7**: a shortlist of ten genes from one module is one hypothesis with ten labels. Untested — and the mechanisms doc §5 names the retrospective that would falsify it. |
| **Karczewski et al. 2020** | constraint over 141,456 humans is the best available structural prior | **Adopts, with a condition attached.** Used as the Stage 6 prior for entities with no literature, and required by the equity doc §5 to carry its panel composition in the manifest the way `null_blocks` is. Not yet implemented. |
| **Köhler et al. 2021** | HPO is the interoperable phenotype vocabulary for rare disease | **Confirms, and bounds.** Every layer here joins on it. And `tools/nongene_measure.py` measures the bound: **six of ten** authored non-gene causal classes have a footprint of **exactly zero**, because the inheritance vocabulary has no term for a dose, an antibody clone, a pathogen or a diet. Not under-counting — nowhere to write. |
| **Kim et al. 2019 (milasen)** | an n=1 therapy is achievable in about a year | **Marks the edge of our scope.** At n=1 no calibration helps: Stage 1 has nothing to bite on and the weight moves entirely to mechanism. Cited to bound the library's claim, not to extend it. |
| **Faye et al. 2024** | average time to diagnosis 4.7 years; adolescence OR 4.79, misdiagnosis 2.48, being a woman 1.22 | **Supplies the missing mechanism for our own number.** `tools/atlas_bias.py` measures ascertainment at **+0.2357** and calls it "attention". Faye et al. say what attention is made of, with intervals. Our statistic has none — [`audit.md`](audit.md) A6. |
| **Popejoy & Fullerton 2016**; **Sirugo, Williams & Tishkoff 2019** | genetic reference panels are overwhelmingly European-ancestry | **No measurement, and a direct consequence for our code.** We cannot measure panel composition from anything on disk. What follows is architectural: a constraint prior is not ancestry-neutral, and a screen that does not say so is making an unstated claim about its patients. |
| **100,000 Genomes pilot 2021** | 25% diagnostic yield, 14% of those outside standard panel regions | **Adopts as denominator.** Three quarters undiagnosed in the best-resourced programme available is the base rate any claim about rare-disease evidence coverage sits on. |
| **Boycott, Giugliani et al. 2025 (RDI-Lancet)** | 400 million people; the problem is visibility and health-care disparity | **Contradicts one of our own layers, in our favour and against our prose.** `tools/capability_math.py` computes capital per patient at **$0.10-$1,001** — laboratory capital is not the expensive part; the released dose and the trial are. That cuts against the economic barrier as our own `barriers.json` states it. The measured layer wins and the authored one is left standing beside it, per hansei. |

**The pattern in this table is itself a finding.** Six rows say `no measurement`. This is the
first lineage section where the borrowed claims outnumber the tested ones, which is the
correct state for a layer added this week and an incorrect state to leave in place. The
three documents it supports say so in their own headers.

---

## 12. Ancestry, founder history and geography

Added 2026-08-27 with [`references/rare-disease-ancestry.md`](references/rare-disease-ancestry.md)
and ADR [0005](adr/0005-population-as-a-typed-field.md). Unlike §11, most rows here have a
**number of ours** on the right: `tools/ancestry_geography.py` read the Orphanet
`PrevalenceGeographic` field that no layer in this repository had ever opened.

| ancestor | their claim | what our number does to it |
|---|---|---|
| **Norio 2003** (Finnish Disease Heritage I-III); **Uusimaa et al. 2022** | a founder population carries a distinctive set of recessive disorders, enriched by bottlenecks and drift, and lacks others | **Confirms, from an unexpected direction.** We did not look for founder effects; we asked whether prevalence varies by country. **386 of 525 (73.5%)** multi-country disorders fall in different prevalence classes, and the extreme rows are the canonical founder cases — Faroese carnitine deficiency, Cypriot ATTR amyloidosis, Nordic sarcoidosis. The heritage concept is visible in a catalogue that never names it. |
| **Scriver 2001** (Quebec) | founder structure is regional, with sub-founder effects inside one population | **Bounds our measurement.** Our field is country-level, so Saguenay-Lac-Saint-Jean is invisible to it. Every number in §1 of the ancestry doc is therefore a *lower* bound on population structure. |
| **Ostrer & Skorecki 2012** | Ashkenazi Jewish population structure underlies a specific disorder set | **Supplies the name our data cannot.** Orphanet's `Specific population` tag — 105 records, 87 disorders, no identifier — is currently hiding Canavan disease, mucolipidosis II and IV and cystinosis. The catalogue records the fact and cannot express it. This is the single sharpest argument for ADR 0005. |
| **Rasmussen et al. 2013** (Faroe Islands, 26,462 screened) | nationwide screening reveals a founder carrier frequency far above the global rate | **Confirms, and then undercuts our own reading.** It is the most extreme row we surfaced — and it came from a deliberate national screen, so it is a founder effect AND an ascertainment artefact simultaneously. `tools/ancestry_geography.py` reports that it cannot separate them, in its own output. |
| **Bittles & Black 2010** | ~10.4% of the world's people are in or descended from unions of second cousins or closer; recessive homozygosity rises accordingly | **Confirms, weakly and indirectly.** The Saudi Arabia row for propionic acidemia (`1-5 / 10 000` against China's `<1 / 1 000 000`) is consistent with it. One row is not a test; we have no consanguinity covariate and cannot build one from anything on disk. |
| **Piel et al. 2013** | sickle haemoglobin frequency tracks historical malaria endemicity — enrichment by balancing selection, not drift | **No measurement, and a consequence for Stage 6.** An allele common in one population and rare in a global panel breaks the routine 'too common to be causal' filter. Our data cannot see selection at all. |
| **Tishkoff et al. 2009** | African populations carry more genetic diversity than all non-African populations combined | **Reframes our worst number.** Africa's representation ratio of **0.07** (77 records for 1.45 billion people) is not a small gap in a small place — it is the least-described and most-diverse portion of human variation. Their claim is what makes ours serious. |
| **Kore et al. 2025** (gnomAD local ancestry) | 78.5% and 85.1% of variants in two admixed groups differ at least twofold in ancestry-specific frequency | **Adopts as the magnitude for a design decision.** It converts 'panels are skewed' into the reason a Stage 6 prior must carry panel composition in the manifest beside `null_blocks` (ADR 0005). |
| **Martin et al. 2019** | polygenic scores lose accuracy off their training ancestry and may worsen disparities | **No measurement.** Cited to bound what this library may claim: nothing here has been tested for transfer across populations, and Stage 5 has no split that would test it. |
| **Carroll et al. 2020** (CARE); **Hudson, Garrison, Sterling et al. 2020** | FAIR governs data movement and is silent on who data is about; Indigenous data governance requires authority to control | **Contradicts our own standards file, and we are recording the contradiction rather than the fix.** `references/standards.md` lists FAIR and not CARE. No obligation is currently breached — every input here is a public aggregate — but the architecture has one untyped string for a population and no field for provenance-of-consent. ADR 0005 proposes the change; this row exists so the gap is on the record first. |
| **Isshiki et al. 2025** (NYC founder populations) | founder structure travels with people and persists inside large diverse cities | **Undercuts the framing of our own measurement.** A country-level geography field cannot see a founder community inside a metropolis, so our §1 is measuring places where a country-level view happens to work. Stated in the ancestry doc §2a as a limit rather than left for a reader to find. |

**What this section adds that §11 could not.** §11 was eleven borrowed claims and six rows
saying `no measurement`. Here the borrowed claims are load-bearing but the right-hand column
is mostly ours — and two of the rows (Rasmussen, Isshiki) are ancestors whose work
**weakens** our reading. Those are kept because a lineage file that only cites the ancestors
who agree with it is the advertising this file exists not to be.

---

## 13. The local ancestors — the author's own prior projects

Added 2026-08-28, after sixteen audit sweeps in which this file credited every published
ancestor and none of the ones on the same machine. Full survey in
[`references/prior-work.md`](references/prior-work.md).

| ancestor | their claim | what our work does to it |
|---|---|---|
| **`nominator`** (Apache-2.0, 921 lines) | ten stages that turn a noisy, confounded screen into a defensible shortlist, with a module implementing each | **Extends by one stage and regresses by six.** `sieve` inserts **Stage 1, Null** — the empirical null fitted on the statistic the screen actually uses — and that stage produced every headline result here. It also implements **four** of the ten where `nominator` implemented all ten in fewer lines. The frame is inherited and was, until now, presented as ours. |
| **`nominator`**, specifically `core/validation.py` | `bootstrap_ci`, `leave_one_entity_out`, `cold_start_split`, `orthogonal_validation` | **Contradicts our own audit's history.** A6 — no intervals on published numbers — stayed open here for fourteen sweeps and was closed by writing a bootstrap from scratch. The ancestor had one. Stage 5's leakage-safe splitting is still prose here and code there. |
| **`F:\CODE\climate`** | with n = 36 and SE(RPSS) ≈ 0.10–0.15, the standard error is the order of the signal, so **no empirical arbitrage between models exists** | **Confirms, and shames the timing.** A26 reached the same conclusion for rare-disease evidence on 2026-08-28. `climate` reached it first and let it *govern the architecture* rather than annotate a table. |
| **`F:\CODEdia`** | board TS-AUC 0.5910 against a local holdout of ~0.60 — a measured optimism of ≈ +0.013 — and therefore *prune, do not add* | **No measurement of ours to compare.** This is Stage 5's own output and `sieve` has never produced it. Recorded as an open gap rather than a difference. |
| **`F:\CODE\knee`** | the documentation discipline: role/last-revised/state, a lineage file, an archive of dead ends with the number that killed each | **Adopted wholesale, and the only local ancestor this file credited before today.** It is also the smallest of the debts on this page. |

**The pattern, and it is the finding.** This file exists to enforce a rule — every borrowed
claim gets its ancestor and a statement of what our measurement does to it. The rule was
applied rigorously to strangers and not at all to the author's own prior work, which is the
form of citation failure that is easiest to commit and hardest to notice.

---

## 14. The chart forms — who invented each, and what ours did with it

Added 2026-08-28. ⚠️ **From working knowledge; year, venue and author order must be checked
before publication.** The right-hand column is measured.

`docs/references/visualization-canon.md` had, since it was written, carried a table of forms
the project needed and had not built. Building them borrowed three claims, and this file's
own rule is that a borrowed claim owes its ancestor a statement of what our measurement does
to it.

| # | Lineage | Anchor name | What we owe it | What our measurement says |
|---|---|---|---|---|
| 14.1 | Density for over-plotted clouds | **Carr, Littlefield, Nicholson & Littlefield** (hexagonal binning, *JASA* 1987) | the form, and the reason for hexagons over squares | **Confirms, and finds something.** The linear 800-point scatter of the selectivity plane read as one blob; binned, on a symlog x and a log y, it resolves into **two separated clouds**. The bimodality was in the shipped file the whole time. |
| 14.2 | Distributions as shapes, not five numbers | **Allen, Poggiali, Whitaker, Marshall & Kievit** (raincloud, *Wellcome Open Res.* 2019); **Matejka & Fitzmaurice** (Datasaurus) | the argument that summary statistics hide shape | **Confirms on our own data.** The populations panel's box plot drew the candidate class as one wide box; the raincloud shows it is **bimodal** — mass at z ≈ −1.3 and again at z ≈ +15. The class this project calls "candidates" is two populations, and no figure here had said so. |
| 14.3 | Set intersections at scale | **Lex, Gehlenborg, Vuillemot, Streit & Pfister** (UpSet, *IEEE TVCG* 2014) | intersections on a common baseline instead of areas in a Venn | **Extends to a population nobody had counted.** Applied to the run: **64 genes** sit in the raw top 100, the calibrated top 100 and the common-essential flag at once. Applied to the catalogue (`tools/gap_patterns.py`, 8,574 OMIM-coded diseases): **53 % record all four fields**, and the largest gap pattern is **1,326 diseases missing gene, onset and sign denominators together** — emptiness is concentrated, not scattered. |

**And one thing the forms did to us.** Prevalence was to be the fifth field of 14.3. It came
back missing for 100 % of the population, which is the shape of a broken join rather than of
a fact, and the count that explains it is new: in the HPO annotation file, ORPHA-coded rows
carry **zero** inheritance annotations and **zero** fractional sign frequencies against
OMIM's 9,065 and 103,106. The two catalogues annotate different things in one file and
prevalence exists only under ORPHA codes. That defect was found by trying to draw a chart
and by nothing else — recorded in `visualization-canon.md` §8, which is the table that keeps
score of exactly this.

**The caution that applies to all three.** Cleveland & McGill's ordering ⚠️ says position on
a common scale beats length beats angle beats area. Every form above trades some positional
precision for density or for narrative, and each trade is stated in the component that makes
it rather than left for a reader to discover. A form that needs a manual gets annotated in
the piece itself — which is why `ReadAloud` is a component and not a convention.

---

## 15. Changing scale — what a coarse-graining costs, and who established the question

Added 2026-08-29, under [`adr/0007-theory-enters-by-measurement.md`](adr/0007-theory-enters-by-measurement.md).
⚠️ **From working knowledge; year, venue and author order must be checked before publication.**
The right-hand column is measured, from `out/rare/scale_information.json`
(`tools/scale_information.py`, 9,142 diseases, 25 permutations, 200 bootstrap resamples).

| # | Lineage | Anchor name | What we owe it | What our measurement says |
|---|---|---|---|---|
| 15.1 | Information as the currency of a summary | **Shannon** (mutual information) | the statistic itself, and the fact that a summary can only lose | **Quantifies, on this catalogue.** Genes carry **0.2791 bits** [0.2583, 0.3000] of excess information about a disease's organ systems. That number had never been put on the atlas's own join. |
| 15.2 | The smallest description that keeps what matters | **Tishby, Pereira & Bialek** (information bottleneck, 1999) | the framing: compress X, preserve information about Y | **Extends to an ontology rather than a learned code.** Their Z is optimised; ours are two *given* coarse-grainings a biologist already uses — Reactome top-level pathways and HPA cell types. Compressing 5,260 genes 181-fold onto 29 pathways keeps **22 %** of the information; 34-fold onto 154 cell types keeps **31 %**. The intervals do not overlap. |
| 15.3 | A coarser description can be the better one | **Hoel, Albantakis & Tononi** (causal emergence, effective information) | the claim that macro can beat micro, and the discipline of measuring it rather than asserting it | **Neither confirms nor contradicts — it is deliberately weaker, and that is the finding.** EI is defined over interventions; ours is observational MI over a static catalogue, so it cannot speak to causal emergence. What it does show is the per-category efficiency their argument predicts: **the pathway scale carries ≈ 40× the excess information per category** that the gene scale does. Reading that as causal emergence is exactly the promotion ADR 0007 forbids, and the artefact's `says` field states so. |
| 15.4 | Coarse-graining as a physical operation | **Kadanoff / Wilson** (renormalisation group) | the question — what survives a change of scale — and nothing else | **Borrowed as a question, not as a method.** There is no fixed point here, no flow and no scale parameter; ADR 0007 grades every dynamical form of this family as `analogy`. Recorded so the word "renormalisation" cannot enter a figure caption on the strength of §15's number. |
| 15.5 | Asymmetry of a directed relation | **conditional entropy** (Shannon again), read as the two uncertainty coefficients | the observational form of the Finsler asymmetry the atlas grades `analogy` | **Quantifies, and finds a collapse.** Genes predict organ system **2.91×** better than organ system predicts genes (U(S\|F) 0.3091 against U(F\|S) 0.1062). At pathway scale the ratio is **1.02** — coarse-graining destroyed the direction, not only the magnitude. Nobody had put a number on the clinical commonplace that many genes converge on one phenotype. |
| 15.6 | Scale-dependent structure | **Hoel et al.** again, and the multiscale-biology literature generally | the claim that the right scale is a property of the phenomenon, not of the analyst | **Extends, per organ system.** Pathway retention spans **5.6-fold** across the 20 organ systems that clear a z of 5: 0.39 for breast and 0.38 for neoplasm, 0.07 for cardiovascular. Pathways hold what is pathway-shaped and lose what is structural; cell types invert the ranking for exactly those structural systems. **There is no single right coarse-graining for this atlas** — which is a design consequence, not only a finding. |

**And one thing the measurement did to us.** The first estimator bootstrapped diseases with
replacement and returned a gene-scale point estimate of **0.2791** against a percentile
interval of **[0.1745, 0.2163]** — an interval that does not contain its own estimate, because
mutual information is biased in n and a resample holds ~63 % of the diseases. Caught before
publication by looking at the printed table rather than by any test. The interval is now
point ± 1.96 SE, and the failed version is kept in a comment at the estimator rather than
tidied away.

