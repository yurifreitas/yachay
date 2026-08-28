# The common scale — what every rare and ultra-rare disease shares

> **Role:** the quantitative axis that runs through the whole portfolio. Not "these
> diseases are all rare" (a definition) but **the shared statistical structure that
> rarity forces**, and which of the ten stages that structure activates.
> **Last revised:** 2026-08-27 · **State:** internal numbers read from `out/rare/*.json`
> on disk and reproducible with the command given beside each. External figures verified
> through Crossref. ⚠ No number here carries a confidence interval — see
> [`../audit.md`](../audit.md) A6, which is the largest open defect behind this document.
>
> Explanation-mode. The identifier crosswalk is
> [`rare-disease-lexicon.md`](rare-disease-lexicon.md); the mechanisms are
> [`rare-disease-mechanisms.md`](rare-disease-mechanisms.md); the human consequences are
> [`rare-disease-equity.md`](rare-disease-equity.md).

---

## 0. The scale in one sentence

Rare diseases are individually tiny and collectively enormous, and **every methodological
problem in this repository follows from that one fact**: an entity whose observation count
is structurally small, ranked against entities whose counts are not, using an aggregate
that selects maxima.

The field's reference estimate: analysing 6,172 rare diseases in Orphanet, Nguengang Wakap
et al. (*Eur J Hum Genet*, 2020) put the cumulative point prevalence at **3.5–5.9 %** of the
population — **263–446 million people** at any moment. **71.9 %** are genetic and **69.9 %**
exclusively paediatric in onset. And the distribution inside that total is the shape this
document is about: **84.5 %** of the diseases they could analyse have a point prevalence
below **1 / 1,000,000**, while **77.3–80.7 %** of the population burden comes from the
**4.2 % (n = 149)** at the common end. A screen ranking diseases by evidence is ranking a
distribution whose mass and whose count point in opposite directions.

---

## 1. Rarity is not one axis — it is at least four

The single word "rare" hides four independent scarcities, and they activate different
stages. Conflating them is the most common error in the field and the one this repository
is best placed to avoid, because it has already been caught making it.

| axis | what is small | stage it activates |
|---|---|---|
| **prevalence** | patients in the world | 2 (Power) — sets the ceiling on any cohort |
| **ascertainment** | patients who have been *found* | 3 (Confound) — correlates with everything else |
| **measurement** | observations per entity | **1 (Null)** — the founding claim of this library |
| **evidence** | studies, annotations, genes per disease | 6 (Prior) — a thin prior is not an absent one |

They are not proportional. A disease can be common and unascertained (undiagnosed
prevalent disease), or ultra-rare and richly measured (a disorder with an active biobank
and a gene-therapy programme). **NF2-related schwannomatosis is the second kind**, which is
exactly why it was chosen as the first disease adapter and why it is a poor test of the
first kind.

---

## 2. What the catalogue actually says, measured here

`python tools/build_atlas.py` → `out/rare/atlas.json`.

| quantity | value |
|---|---|
| diseases joined | **14,831** (OMIM 8,574 · ORPHA 4,335 · DECIPHER 47) |
| with a causal gene | **11,030** — coverage **74.4 %** |
| distinct genes | 5,524, of which 5,433 have single-cell expression data |
| placeable on the cell axis | **10,941** — coverage **73.8 %** |
| Orphanet disorders with a prevalence statement | 6,728 |
| in the rarest band (< 1 / 1,000,000) | **3,987** |
| ultra-rare (< 1 / 1,000,000 **or** 1–9 / 1,000,000) | **4,586** |
| …of those, with a known gene | **2,663 — 58.1 %** |
| genes per disease | min 1, **median 1**, p95 3, max 114 |

Two of these are the point.

**The median disease has one gene.** Not "few" — one. Any aggregate over a disease's genes
is therefore an aggregate over a single observation for most of the catalogue, and a
ranking across diseases spans a **114×** range in observation count. That is this
repository's founding claim (`../methodology.md`, Stage 1) restated on its own reference
data, and it is why `tools/atlas_bias.py` exists.

**Ultra-rare diseases are less likely to have a gene** (58.1 % against 74.4 % overall).
Read naively: rare diseases are less genetic. That reading is wrong, and §3 says why.

> ⚠ **These two rows were corrected on 2026-08-27, and the correction is large.** They
> previously read *770* ultra-rare diseases and *50.7 %* with a gene. Orphanet writes the
> rarest class as `&lt;1 / 1 000 000`, and `tools/build_atlas.py` read the XML with a
> regular expression rather than a parser — so it never unescaped the entity, the string
> matched no entry in the rank table, and **3,987 diseases, the largest band in the
> catalogue, were invisible**. A membership test naming that class was dead code that
> could never fire. Full account in [`../audit.md`](../audit.md) A11.

---

## 3. Prevalence is not a number, and the catalogue's own biases are measured

### 3a. The audit of the prevalence field

`python tools/prevalence_audit.py`. The dashboard had been reading one collapsed string per
disease — `"1-9 / 100 000"`. Orphanet does not record a string. It records **17,108
prevalence records across 6,728 disorders** (mean 2.54 each), and each carries a type, a
population, a geography and a validation status that the collapse discards:

| type | records |
|---|---|
| Point prevalence | 8,304 |
| Cases / families | 3,619 |
| Annual incidence | 3,068 |
| Prevalence at birth | 2,070 |
| Lifetime prevalence | 47 |

**68.6 % of disorders (4,614) carry records of more than one type.** Point prevalence,
annual incidence and prevalence-at-birth are three different quantities; averaging or
first-matching across them produces a number that means nothing, and for a lethal
early-onset disorder birth prevalence and point prevalence differ by the mortality. Only
**4,444 disorders** have a *validated point-prevalence class* — the subset where the cohort
denominator means one thing. `tools/capability_math.py` now divides by that subset and
reports the two disorders where the old collapse gave a different answer, rather than
silently correcting them.

**Geography is the missing dimension.** Of 17,108 records, **11,193 (65 %) carry no named
place at all**, and among those that do, the density is a map of who publishes: the
Netherlands contributes 1,233 records per hundred million people, the United States 132.
A "global" prevalence is a European prevalence with error bars nobody computed.

### 3b. The catalogue as a screen, audited by its own library

`python tools/atlas_bias.py` applies this repository's argument to this repository's
reference data — the test that is hardest to pass and least optional.

| bias | test | statistic | verdict |
|---|---|---|---|
| **Ascertainment** | rank corr. of annotation count vs. having a known gene | **+0.2357** | real |
| **Streetlight** | rank corr. of prevalence band (rarest first) vs. having a gene | **−0.113** | small |
| **Panel coverage** | genes measured in a cell type vs. disease genes peaking there | **−0.2469** | real, **and it hits our own chart** |
| **Varying n** | genes per disease | **114× spread** | real |
| **MNAR** | gene known, among diseases with vs. without stated prevalence | **−0.0756** | real |
| **Survivorship** | — | — | **untestable** |

Three of these deserve their own sentence.

**Ascertainment (+0.2357) is why §2's coverage figures are not facts about the world.**
Median annotations: 19 for diseases with a gene, 10 for those without (9,028 vs. 3,648
diseases). "Has a known gene" is partly a measure of how much attention a disease received.
So the 58.1 % of §2 does not say ultra-rare disease is less genetic; it says ultra-rare
disease is less studied, and the gene-finding is downstream of the studying.

With the missing band restored the gradient is monotone and reads cleanly across all six
bands — **59 % of 3,987 · 52 % of 599 · 46 % of 535 · 35 % of 189 · 33 % of 6** — which
*strengthens* the denominator-fallacy correction the explorer already published: the rarer
the band, the **more** likely a causal gene is known, because an ultra-rare disease is
usually ultra-rare *because* it is monogenic.

**Panel coverage (−0.2469) falsifies a chart this project had already drawn.** The
cell-burden bar chart in the explorer ranks cell types by disease genes peaking in them —
neutrophils 1,086, late spermatids 747, hepatocytes 562. The measured correlation says that
ranking is partly a ranking of sequencing depth. It is recorded here because a project that
audits only other people's data is decoration.

**Survivorship is untestable and is the most important of the six.** Every disease in the
catalogue is one somebody described, named and got accepted into a reference. Diseases too
rare to have been seen twice, or seen only where no catalogue reaches, are absent — and
absent in a way that no statistic computed *from* the catalogue can detect. **The
denominator of every percentage in this document is the catalogue, not the world.**

---

## 4. Which stages rarity activates, and which it does not

The four-question fit test (`../expansion-map.md`) applied to the rare-disease setting.

**Stage 2 (Power) dominates, and it is not fixable by method.** When the world contains 200
patients, no estimator recovers what the cohort cannot contain. This is the axis where
statistical care runs out and study design takes over: natural-history registries, n-of-1
designs, and external or historical controls. The field's demonstration is `milasen` (Kim
et al., *NEJM*, 2019) — an antisense oligonucleotide designed, manufactured and dosed for
**one patient**, from diagnosis to treatment in about a year. It is the limiting case of
this whole axis: n = 1, and the methodological weight moves entirely onto mechanism.

### 4a. Measured, on the clinical record — added 2026-08-27

The claim above was an argument until `tools/dossier.py` was made to ask it of the trials
themselves. Every other view of ClinicalTrials.gov here counts studies, which answers *is
anyone trying*. This asks what the library exists to ask: **could a study of that size have
found anything.**

For a two-arm, two-sided comparison at α = 0.05 and 80 % power, the minimum detectable
effect is `MDE = 5.6 / √n` in standard deviations of the outcome. It is a **floor**: it
assumes even allocation, no dropout, one primary endpoint and no covariate adjustment, and
a real trial violates all four, so a real trial detects less. Across the twelve-disease
portfolio, using the median *interventional* trial that states an enrolment:

| disease | median enrolment | MDE (floor) | organ systems with no quantified sign |
|---|---|---|---|
| Full NF2-related schwannomatosis | 25 | **1.12** | 9 of 9 |
| Zellweger syndrome | 25 | **1.12** | 15 of 15 |
| Duchenne muscular dystrophy | 26 | **1.10** | 6 of 6 |
| Proximal spinal muscular atrophy | 30 | **1.02** | 11 of 11 |
| Dravet syndrome | 30 | **1.02** | 5 of 5 |
| Rett syndrome | 30 | **1.02** | 11 of 13 |
| Alkaptonuria | 30 | **1.02** | 8 of 15 |
| CDKL5-deficiency disorder | 32 | 0.99 | 11 of 11 |
| Cystic fibrosis | 40 | 0.89 | 3 of 13 |
| Sickle cell anaemia | 47 | 0.82 | 14 of 14 |
| Fibrodysplasia ossificans progressiva | 48 | 0.81 | 14 of 14 |
| Systemic lupus erythematosus | 50 | 0.79 | 9 of 14 |

**Ten of the twelve cannot detect a large effect.** Cohen's convention puts a large effect
at 0.8 SD; only lupus and, marginally, FOP clear it — and both clear it by a hair, on a
bound that flatters them. For Duchenne, **90 of the 139 interventional trials that state an
enrolment** are below that line individually, with a further **6 too small to assess at
all** — enrolments of two and three, where a two-arm comparison is not a weak study but not
a study of that shape at all.

> ⚠ **That count read 96 until 2026-08-27, and the change is a semantic one, not a
> correction of arithmetic.** The figure was produced by arithmetic living inline in
> `tools/dossier.py`, which treated any trial below n=4 as under-powered. Extracting the
> arithmetic into `sieve.stages.power` (Stage 2 of the library, see
> [`../audit.md`](../audit.md) A15) separated the two states: 90 under-powered, 6
> unassessable, 96 in total. Merging them let a count of rumours pass as a count of weak
> studies. The **floors themselves did not move** — `tests/test_power.py` pins the published
> portfolio values precisely so a refactor cannot shift a number already in this file.

Two things this does **not** say, stated because the number invites both errors:

1. **It is not a claim that these trials were badly designed.** A crossover design, a
   within-patient endpoint, a biomarker with a tight variance or a genuinely enormous effect
   all beat this floor honestly. The floor describes the two-arm comparison of means, which
   is what a registrational trial usually needs, and rare disease is where that design runs
   out of patients first.
2. **It is not an argument for bigger trials.** For most of this portfolio the patients do
   not exist to enrol. It is an argument that the endpoint and the design carry the weight
   the sample size cannot — which is Stage 2's actual instruction, and the reason
   `docs/references/rare-disease-mechanisms.md` §4 puts so much on mechanism.

**And the phenotype side of the same scarcity.** Rolling every sign up the HPO `is_a` graph
to its top-level organ systems gives the fourth column above. For **six** of the twelve
diseases, *every* organ system the disease is recorded as attacking has **zero** signs
estimated from a real series. Duchenne is the sharpest case: its cardiovascular system
carries five signs — cardiomyopathy, arrhythmia, abnormal EKG, dilated cardiomyopathy — and
**four of the five have no recorded frequency at all**, in the organ that causes most of the
deaths.

### 4b. The same question, asked of the whole catalogue

Everything in §4a is computed on **twelve** diseases, and they were chosen partly because
they are well studied — so the sample is biased in the direction that makes the finding look
mild. `tools/evidence_atlas.py` asks it of all of them, over **267,782 phenotype
annotations across 12,935 diseases**, importing the grading rules from `tools/dossier.py`
rather than restating them.

The claim does not merely survive. It gets worse.

| | |
|---|---|
| diseases with **at least one** sign estimated from a real series | **5,133 — 39.7 %** [38.8, 40.5] |
| diseases with **no fraction of any kind**, anywhere | **7,256 — 56.1 %** [55.2, 57.0] |
| annotations by grade | class **118,576** · quantified **76,927** · none **52,819** · single-case **19,460** |
| median denominator, where one exists | **5 patients** |
| quantified signs resting on **fewer than 10** patients | **55,184 of 76,927 — 72 %** |
| quantified signs resting on **fewer than 30** | **73,362 — 95 %** |
| largest series in the entire corpus | 1,827 |

**Three fifths of the rare-disease catalogue contains no proportion at all**, and where a
proportion exists the median one is five patients. Duchenne's zero is not an outlier; it is
the tail of a distribution whose centre is almost as uninformative.

**By organ system, and the flatness is the finding.** Across 23 top-level systems the share
of signs that are quantified runs from **7.9 %** (thoracic cavity) to **35.5 %** (abnormal
cellular phenotype), with head/neck — the largest, 41,026 signs — at 32.8 %, and neoplasm at
**14.0 %**. There is no well-measured system. The variation is between *barely* and *hardly*,
which means this is a property of how the field records phenotype rather than of any
particular organ being neglected.

**And the number is an upper bound, for a reason the repository has already measured.** A
disease with a quantified sign carries a median of **18** annotations against **13** for one
without. Quantification is not independent of how much a disease was looked at, so the
39.7 % describes the studied half of the catalogue better than the unstudied half — the same
ascertainment confound `tools/atlas_bias.py` measures at +0.2357, appearing again one level
down, in evidence *quality* rather than in gene discovery.

> **What this cannot say.** Absence of a frequency in HPO is not absence of knowledge in the
> world: a frequency can be published in a paper and never curated into the ontology. Every
> number above is a statement about the **curated record** — which is precisely what every
> downstream computation in this repository, and every dashboard built on it, actually
> reads. A pipeline cannot use a number that is not in its inputs.

**Stage 1 (Null) applies wherever the aggregate selects.** Not everywhere. It bites when a
score is a maximum, top-k, quantile or enrichment over a varying number of observations —
gene burden over a variable number of variants, a phenotype match over a variable number of
annotated terms, a dependency score over a variable number of screened lines. It does *not*
bite on a difference in means, which is the finding of `lineage.md` §9 and the reason NF2
may not be a `sieve` demonstration at all.

**Stage 6 (Prior) changes character.** Elsewhere the prior's job is to suppress rediscovery
of dead ends. In rare disease most entities have no literature at all, so the prior must
come from **structure** rather than publication: constraint (Karczewski et al., *Nature*,
2020, over 141,456 humans), module membership
([`rare-disease-mechanisms.md`](rare-disease-mechanisms.md) §4), phenotype-ontology distance
(Köhler et al., *NAR*, 2021). Absence of literature is informative about attention, not
about the gene.

**Stage 3 (Confound) acquires a confounder the other domains do not have: the patient
population itself.** That belongs to [`rare-disease-equity.md`](rare-disease-equity.md).

---

## 5. The honest summary

Three sentences, each of which the numbers above support.

1. Rarity forces small and *unequal* observation counts, which is the precise condition
   under which a selecting aggregate stops being comparable across entities — so the
   library's core stage is not a coincidental fit to this domain, it is the domain's
   defining problem.
2. Every coverage percentage in this document is conditioned on a catalogue whose own
   ascertainment bias is measured at +0.2357 and whose survivorship bias is unmeasurable,
   so these are lower bounds on ignorance, not estimates of the world.
3. The scale is shared; the fix is not. Prevalence-scarcity needs study design,
   measurement-scarcity needs calibration, and evidence-scarcity needs structural priors —
   and calling all three "rare disease is hard" is what lets a project apply the wrong one.
