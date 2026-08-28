# Patient-level data — what is open, what is not, and the plan for the rest

> **Role:** the only layer in this project built from individual people rather than from
> aggregate catalogues, plus the honest map of what patient data can and cannot be obtained.
> Every other source here reports what a *disease* does; a patient record reports what
> happened to a *person*, and the difference is a denominator.
> **Last revised:** 2026-08-28 · **State:** §1–2 are **measured** from 10,377 individuals
> already on disk. §3 is a **plan**, not a result: nothing in it has been applied for, and
> it is written so that the cost of each route is visible before anyone commits to one.
>
> ⚠ **Everything measured here comes from published case reports and series.** It carries
> publication bias in full and is not a population sample. See §2d.

---

## 1. What is openly available, and it is more than the field assumes

The reflex answer is that rare-disease patient data is all access-controlled. That is true
of the large cohorts and false of a real and useful corner of the field.

**`phenopacket-store` (Monarch Initiative), BSD-3-Clause, 19.4 MB.** Individual patients in
the GA4GH phenopacket standard, extracted from the published literature:

| | |
|---|---|
| patients | **10,377** |
| diseases | **780** |
| source publications | **1,733** |
| per patient | own HPO terms, causative variant with an ACMG class, age, sex, vital status |

**The detail that makes it worth more than its size.** A phenopacket records phenotypes
that were **explicitly absent** as well as present. In a 1,500-packet sample, **28,475 of
43,499** assertions were `excluded` — 65 %. An excluded term is not a gap in the record; it
is a patient who was examined for that feature and did not have it. So a frequency can be
*computed*:

```
frequency = observed / (observed + excluded)
```

with a denominator that is the number of patients actually assessed — the quantity
[`rare-disease-scale.md`](rare-disease-scale.md) §4b measured the curated record as almost
never having.

---

## 2. What the patients say about the catalogue

`python tools/patient_frequencies.py` → `out/rare/patient_frequencies.json`.

### 2a. Denominators that did not exist before

**19,534 disease-feature pairs** get a computed denominator (≥ 2 assessed): median **6**,
p95 **41**, max **354**. **6,320** pairs rest on ten or more assessed patients and **1,506**
on thirty or more. Twelve diseases get a denominator the curated record never gave them at
all.

### 2b. Where both exist, the patient side almost always has more people behind it

**16,276 pairs are comparable.** In **14,747 of them — 91 %** — the *patient* set has the
larger denominator. The reference ontology's frequency field is, in the overwhelming
majority of comparable cases, the weaker of the two estimates.

15,063 pairs agree within 20 percentage points. **631 differ by 50 or more.**

### 2c. The single-case bias, which is this library's founding claim measured on people

The disagreements are not scattered. Grouped by the denominator **the catalogue** used:

| curated denominator | pairs | curated mean | patient mean | **difference, 95 % CI** |
|---|---|---|---|---|
| **n = 1** | 354 | **0.932** | **0.436** | **−0.497 [−0.591, −0.387]** |
| n = 2–4 | 6,489 | 0.700 | 0.684 | −0.016 [−0.026, −0.008] |
| n = 5–19 | 7,417 | 0.439 | 0.444 | +0.005 **[−0.000, +0.011]** |
| n ≥ 20 | 2,016 | 0.322 | 0.342 | +0.020 [+0.005, +0.038] |

**When the catalogue's frequency rests on one patient it reads 0.932; the patients say
0.436** — a difference of **−0.497**, whose interval **[−0.591, −0.387]** is nowhere near
zero.

> **The intervals were added on 2026-08-28 and they corrected two sentences that had been
> published here.** Both errors were in the direction of a tidier story:
>
> - This paragraph said *"at n ≥ 20 it reverses sign — the curated value is, **if anything**,
>   slightly conservative."* The hedge was unnecessary and therefore wrong in its own way:
>   the difference is +0.020 with an interval of [+0.005, +0.038], which **excludes zero**.
>   At large denominators the curated value is not "if anything" conservative; it is
>   conservative.
> - The n = 5–19 row was presented as part of a smooth trend towards reversal. Its interval
>   **includes zero** — there is **no detectable difference at all** in that band, which is
>   a different statement from a small one.
>
> The shape that survives is sharper than the one first published: **enormous at n = 1,
> small but real at n = 2–4, undetectable at n = 5–19, and slightly reversed above 20.**
> `references/standards.md` §4 adopts GUM precisely so a story cannot be smoother than its
> error bars.

**The resampling unit is the disease, not the pair.** Two features of one disease share
patients, a curator and usually a publication; treating them as independent would narrow
every interval above in the direction that flatters the claim. This library exists because a
null fitted on the wrong resampling unit produced a z of −4.09 for two months
([`../lineage.md`](../lineage.md) §8a), and repeating that here would be unforgivable.

That shape is the whole argument of this repository, appearing in a place it was never aimed
at. A `1/1` frequency is a **selected observation**: the first patient written up is not a
random patient, and the feature that got them written up is the one most likely to be
recorded. Selecting the largest of a few noisy estimates is positively biased, and the bias
shrinks as the denominator grows — which is precisely `docs/methodology.md` Stage 1, here
measured against real people rather than against a resampled null.

Individual cases make the point concrete:

| disease | feature | catalogue | patients |
|---|---|---|---|
| Intellectual developmental disorder | Seizure | `1/1` = 100 % | **0 of 16 assessed** |
| Neurodevelopmental disorder … | Sloping forehead | `1/1` = 100 % | **0 of 15** |
| Neurodevelopmental disorder … | Mandibular prognathia | `2/2` = 100 % | **0 of 11** |
| STAR syndrome | Duane anomaly | `1/1` = 100 % | **0 of 6** |

### 2d. What this is not

**Not a population sample.** A patient reaches phenopacket-store by being written up, and
unusual presentations get written up. Both sides of the comparison read the same literature,
which is what makes the comparison meaningful — and also what stops either side being a
population frequency.

**Not proof the catalogue is wrong in a particular row.** 1,529 pairs have the larger
denominator on the *curated* side; there the curated value is the better estimate and the
patient set is the thin one. The table in §2c reports the direction of a bias across
thousands of pairs, not a verdict on any single annotation.

---

## 2e. The genotype half, which the first extraction threw away

The pass above kept two things per patient: the disease, and which HPO terms were observed
or excluded. A field census showed what that discards, and it is most of the record:

| field | present |
|---|---|
| variant allelic state | **11,454 — 100 %** of genomic interpretations |
| variant gene | 11,385 — 99 % |
| variant ACMG class | 11,243 — 98 % |
| variant VCF coordinates (hg38) | 10,812 — 94 % |
| variant HGVS (c. / g. / p.) | 10,810 — 94 % |
| subject sex | 9,578 — 92 % of patients |
| subject age at last encounter | 7,939 — 77 % |

`tools/patient_variants.py` reads it: **11,454 variants over 699 genes and 780 diseases**.

### The allelic spectrum, which says what a "causal gene" rests on

Per gene: how many *distinct* variants, over how many patients, and what share were seen
exactly once. The median gene has **66.7 %** of its variants private to a single patient,
and **189 of 699 genes (27 %) have every reported variant seen exactly once.**

The contrast between genes is the useful part:

| gene | patients | distinct variants | private | most recurrent allele |
|---|---|---|---|---|
| **NF1** | 405 | 42 | 43 % | **107 patients share one variant** |
| **STXBP1** | 462 | 259 | **81 %** | 19 |
| ANKRD11 | 333 | 231 | 86 % | 34 |
| LMNA | 259 | 55 | 55 % | 62 |

NF1 is a characterised locus with recurrent alleles. STXBP1 and ANKRD11 are the opposite:
hundreds of variants, each seen once or twice. Both are "the causal gene" in every catalogue
this project reads, and the evidence behind those two words is not the same kind of thing.

### Consequence and zygosity

| consequence | variants |
|---|---|
| missense | 5,293 |
| frameshift | 1,826 |
| nonsense | 1,514 |
| **unclassified** | **1,341** |
| splice region | 912 |
| deletion / duplication / indel | 638 |

Zygosity: heterozygous **8,529**, homozygous **2,556**, hemizygous **369**. The consequence
class is derived from the HGVS protein expression by textual rules — not a variant effect
predictor — and 1,341 that the rules cannot place are `unclassified` rather than guessed.

### A check that was wrong, and what it took to see it

The first version of the inheritance cross-check flagged **65 diseases** for "declared
recessive, but no homozygous patient". That is the **expected signature of compound
heterozygosity**: a recessive patient carrying two different variants is recorded as two
heterozygous calls and never as a homozygote. 61 of the 65 were that. *A check that fires on
the normal case is not a check* — and the code carried a comment saying exactly this while
doing the opposite.

Moved to the patient, where the question lives: a recessive diagnosis explained by **one**
heterozygous variant and nothing else. Diseases with both modes declared are skipped rather
than judged. Result: **3,486 recessive patients checked, 275 skipped as ambiguous, 4
diseases flagged** — 4 to 9 patients each, every one a single heterozygous call. Those are
worth reading; the 65 were not.

### Two selection effects to carry with every number above

**Every one of the 11,243 ACMG classifications is `PATHOGENIC`.** Not one likely-pathogenic,
not one VUS. phenopacket-store contains *solved* cases, so the variant set is the answer key
rather than the diagnostic pile — and any rate computed over it inherits that.

**`vitalStatus` is a trap.** It is recorded on 707 of 10,377 patients and **every one is
`DECEASED`**; `ALIVE` is never written down. A mortality rate from this field would be 100 %
by construction. It is a death register, not a survival denominator.

---

## 2f. The join — the only thing an aggregate catalogue cannot do at all

§2 reads the phenotype half and §2e the genotype half. Neither joins them, and the join is
the whole reason patient-level data is worth having: a disease-level record can say *this
disease involves seizures* and *this gene has nonsense variants*; only a patient record can
say *the patients with nonsense variants had the seizures*.

`tools/genotype_phenotype.py` splits each gene's patients by what their variant does —
**loss of function** (nonsense or frameshift: a truncated or absent protein) against
**missense** (one amino acid changed: a protein that is present and different) — and tests
every HPO feature assessed in both groups.

Patients who cannot be assigned are **excluded, not forced**: 277 carried both a truncating
and a missense allele, 69 had variants in more than one gene, 2,304 had neither class.
Pushing ambiguous patients into a group would put them exactly where the comparison is made.

### The result this repository cares about first

**510 comparisons across 31 genes. Only 40 of them — 7.8 %, Wilson interval
[5.8 %, 10.5 %] — could have detected a 50-point difference at these group sizes.**

That number comes from `sieve.stages.power`, the library's Stage 2, called *before* any
p-value is read. **470 of the 510 tests are incapable of the result they are being asked
for**, and reporting them as "no difference" would convert a sample-size limit into a
biological claim. The honest negative is the other column: **38 comparisons were powered and
came back null.**

### The six that survive correction — and they are known biology, recovered blind

Benjamini-Hochberg across all 510 tests, because picking the smallest p-value out of
hundreds is itself a selection operator — this library's founding argument, one level up.

| gene | feature | loss of function | missense | difference | q |
|---|---|---|---|---|---|
| **LMNA** | Lipodystrophy | **0 / 14** | **120 / 206** | **−0.58** | 1.2e-03 |
| **GNAS** | Subcutaneous ossification | 22 / 34 | 3 / 50 | +0.59 | 3.7e-06 |
| **SETD2** | Macrocephaly | 14 / 14 | 4 / 24 | +0.83 | 8.1e-05 |
| EPG5 | Hypopigmentation of the skin | 12 / 12 | 1 / 14 | +0.93 | 4.6e-04 |
| EPG5 | Cataract | 10 / 12 | 1 / 17 | +0.77 | 3.3e-03 |
| SATB2 | Cleft palate | 39 / 68 | 11 / 49 | +0.35 | 2.3e-02 |

**These are textbook genotype–phenotype splits, and the pipeline was told none of them.**

- **LMNA** is the cleanest validation available. Familial partial lipodystrophy is caused by
  specific *missense* variants; *truncating* LMNA variants cause cardiomyopathy and muscular
  dystrophy instead. The table recovers that split — zero of fourteen against 120 of 206 —
  from patient records alone.
- **GNAS**: inactivating variants give Albright hereditary osteodystrophy with heterotopic
  ossification; activating missense gives McCune-Albright. The direction is right.
- **SETD2**: loss of function gives the overgrowth phenotype with macrocephaly; missense
  does not.

A method that recovers known biology blind is a method whose *negative* results are worth
something — which is the only reason the 38 powered nulls above are worth reporting.

### And what it cannot say

Every ACMG class in this corpus is `PATHOGENIC` and every patient arrived by being written
up (§2e). A feature recorded more often in one group may be recorded more often **because
that group was studied by people looking for it**. This measures the record. The record is
what every downstream computation in this project reads, which is what makes it worth
measuring — and not the same thing as measuring patients.

---

## 3. The plan for the data that is not open

Nothing below has been applied for. It is written so the cost is visible **before** anyone
commits, and so that the architecture the first application would require exists in advance
rather than under deadline.

### 3a. The tiers, by what they actually cost

| tier | examples | what it takes | what it gives |
|---|---|---|---|
| **open, now** | phenopacket-store, ClinVar submissions, ClinicalTrials.gov results | download | individual phenotypes and variants from the literature; aggregate trial arms |
| **registered access** | dbGaP, EGA | institutional signatory, a data access request per study, a DUA, usually IRB/ethics determination | individual genotypes and phenotypes at cohort scale |
| **cohort platform** | UK Biobank, All of Us, Genomics England | application with a stated research question, a fee, analysis inside their environment — data does not come to you | population-scale linked genotype–phenotype–EHR |
| **consortium membership** | RD-Connect / EJP-RD, Matchmaker Exchange, GA4GH Beacon networks | institutional membership, a named PI, contribution obligations | federated discovery across national registries |
| **direct partnership** | patient organisations, natural-history registries | ethics approval, a data-sharing agreement, and usually co-authorship or governance participation | the deep longitudinal data no public source has |

**The unavoidable prerequisite for every tier below the first is institutional.** A named
principal investigator, an ethics or IRB determination, and a signatory who can bind an
organisation to a DUA. This repository has none of those, so the honest sequencing is: the
open tier now, and the rest only alongside an institutional host.

### 3b. What has to exist in the code before any of it arrives

[ADR 0005](../adr/0005-population-as-a-typed-field.md) already proposed the population field
and the CARE row in the standards, and it did so before there was any patient data at all.
That timing is now the point rather than a formality:

1. **A typed population field**, distinguishing *place of measurement* from *described
   population* — ADR 0005, still `proposed`.
2. **Provenance-of-consent as a field, not a note.** The current schema has nowhere to
   record what a participant agreed to. Every tier from "registered access" down carries
   consent terms that constrain what may be computed and what may be published.
3. **CARE beside FAIR in `standards.md`** ([`rare-disease-ancestry.md`](rare-disease-ancestry.md)
   §5, audit A10). Currently unlisted, and the moment Indigenous or community-held data is in
   scope it stops being a documentation gap.
4. **A publish-time gate.** Aggregate counts are safe; small cells are not. A rare-disease
   cohort crossed with geography and age reaches identifiability faster than intuition
   suggests, and the explorer currently renders whatever the JSON contains.

None of the four is implemented. They are listed in the order the first data-access
agreement would demand them.

### 3c. The next open source worth taking, and why it is not more cohorts

~~**ClinVar is already on disk** (442 MB, ingested 2026-08-27) and unread.~~
**It has since been read**, and what it says belongs here because it bounds everything above.

`tools/clinvar_evidence.py` read all **9,048,962** rows (4,490,695 on GRCh38). Two results
change how §2 should be used:

- **52.0 % of ClinVar is of uncertain significance**, and **84.6 %** of it sits at one star
  or less on ClinVar's own review scale. The corpus this project treats as the field's
  variant record is mostly uncertain and mostly unreviewed.
- **Our patient corpus does not survive the comparison intact.** Of the 5,713 coordinates,
  all `PATHOGENIC` by construction, **1,587 are absent from ClinVar entirely** and of those
  present, 470 are uncertain and 313 conflicting. **21.1 % of the answer key is not
  confidently pathogenic to the rest of the field** — Wilson interval **[19.9 %, 22.4 %]**,
  so "about a fifth" is not a rounding, it is the estimate.

That does not make the published cases wrong — a variant can be causative in a family and
never submitted, and ClinVar lags the literature. It does mean every rate computed over the
patient corpus inherits a classification the wider field has not confirmed, and §2 should be
read with that attached. Full account in [`../audit.md`](../audit.md) A21.

**And the conclusion that survives:** adding a fifth aggregate catalogue would not deepen
anything. Reading what is already downloaded does — Reactome and gnomAD remain unread, each
with a question waiting in [`../roadmap.md`](../roadmap.md).
