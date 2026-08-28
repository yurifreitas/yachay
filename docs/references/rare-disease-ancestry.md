# Ancestry, founder history and geography — the population axis

> **Role:** the axis every other document here treats as absent. A rare disorder's
> prevalence is a property of the disorder **in a population**; the catalogues on disk
> record it as a scalar. This measures the size of that error, explains the history that
> produced it, and states what the project must not do with the answer.
> **Last revised:** 2026-08-27 · **State:** §1 is **measured** — new, by
> `tools/ancestry_geography.py`, reproducible with one command. §§2–4 are borrowed and
> every reference was resolved through Crossref before it was written. §5 is a
> **conformance finding against this repository**, not against anyone else.
>
> ⚠ **Geography is not ancestry, and this document never treats it as such.** See §0b.
> Explanation-mode. Companions: [`rare-disease-scale.md`](rare-disease-scale.md),
> [`rare-disease-equity.md`](rare-disease-equity.md),
> [`rare-disease-mechanisms.md`](rare-disease-mechanisms.md).

---

## 0. Why the project needed this, and could not fake it

Every rare-disease layer built here joins on a gene and reports a prevalence band. Both
moves assume the same thing: that a disorder has *a* rate. For recessive disease that
assumption is not an approximation, it is a category error. Founder events, drift,
endogamy, consanguinity and selection move carrier frequencies by **orders of magnitude**
between populations, and the same allele in the same protein produces a disease that is
common in one community and unrecorded in another.

The question was whether anything on disk could show that, or whether it would have to be
asserted. It could be shown. Orphanet stamps every prevalence record with a
`PrevalenceGeographic` field, and no layer in this repository had ever read it.

```bash
python tools/ancestry_geography.py     # writes out/rare/ancestry_geography.json
```

### 0b. The limit, stated before the numbers rather than after

**A place is not a people.** A record stamped `Brazil` describes whoever was studied in
Brazil — a population Indigenous, African, European and Japanese in proportions that vary
by region, none of which the catalogue records. Nothing in §1 is a statement about a
genetic ancestry group. Every number in §1 is a statement about **where someone published**,
which is the ascertainment quantity `tools/atlas_bias.py` measures at **+0.2357**.

That limit is not a hedge. It is the reason §1's headline finding is about *epidemiology as
an activity* and not about *disease as a distribution* — and it is why §5 exists.

---

## 1. What the catalogue actually records — measured, 2026-08-27

`tools/ancestry_geography.py` over Orphanet's **17,108** prevalence records.

### 1a. Most of the corpus has no population at all

| | records | share of tagged |
|---|---|---|
| `Worldwide` | **9,518** | **55.6 %** |
| a named country | 5,769 (130 distinct) | 33.7 % |
| a supranational region (`Europe`, `Africa`, …) | 1,716 | 10.0 % |
| **`Specific population`** | **105** | 0.6 % |

`Worldwide` is a **claim**, not a missing value, and it is the majority of the corpus. It
asserts that a disorder's rate does not depend on which population you measure — which §1c
shows is false for 73.5 % of the disorders where the assertion can be checked.

### 1b. Representation, against population rather than against itself

Records naming a country, grouped by world region, against that region's share of the ~8.05
billion people alive.

| region | records | % of placed records | % of world population | **representation ratio** |
|---|---|---|---|---|
| **Europe** | 4,296 | 74.5 % | 9.2 % | **8.10** |
| Oceania | 160 | 2.8 % | 0.5 % | 5.05 |
| Northern America | 526 | 9.1 % | 4.7 % | 1.94 |
| Latin America & Caribbean | 150 | 2.6 % | 8.1 % | 0.32 |
| **Asia** | 557 | 9.7 % | **59.0 %** | **0.16** |
| **Africa** | 77 | 1.3 % | **18.0 %** | **0.07** |

Europe is over-represented by **8.1×**, Africa under-represented by **14×**. The gap between
them is a factor of **116**. Africa — 1.45 billion people — contributes **77** prevalence
records to the world's reference rare-disease epidemiology.

Per capita the extremes are starker. Iceland contributes **18,500** records per hundred
million people; Indonesia contributes **0.7**. That is a ratio of **26,429×**, and it is a
ratio of *who publishes epidemiology*, not of who has disease. Nigeria (224 million people)
appears **3** times; Malta (0.5 million) appears **87**.

### 1c. Prevalence is population-specific in almost three quarters of testable cases

Of the disorders with placed records in more than one country, **386 of 525 (73.5 %,
Wilson interval [69.6 %, 77.1 %])** have records that fall in **different prevalence
classes** in different countries — the interval sits entirely above one half, so "most" is a
measurement rather than a manner of speaking. Every other tab
in this project collapses each of those to a single band.

The examples are not noise. They are the textbook cases, surfaced without being looked for:

| disorder | the spread the catalogue itself records |
|---|---|
| **Systemic primary carnitine deficiency** | Faroe Islands `6-9 / 10 000` and `>1 / 1000` · China `<1 / 1 000 000` |
| **Propionic acidemia** | Saudi Arabia `1-5 / 10 000` · China `<1 / 1 000 000` · Italy `1-9 / 1 000 000` |
| **Fetal alcohol syndrome** | South Africa `>1 / 1000` · Poland `1-9 / 1 000 000` |
| **Sarcoidosis** | five classes across 20+ countries, Nordic and Caribbean at the top |
| **Hereditary ATTR amyloidosis** | Cyprus `1-9 / 100 000` against `1-9 / 1 000 000` almost everywhere |

Three different mechanisms are visible in that table, and a pipeline that averages them is
wrong three different ways. The Faroese and Cypriot spreads are **founder effects**; the
Saudi spread is **consanguinity**; the South African fetal alcohol syndrome spread is
**neither** — it is exposure, poverty and measurement, and it belongs to
[`rare-disease-equity.md`](rare-disease-equity.md), not here. §2 separates them.

### 1d. The catalogue can see founder structure and cannot name it

The population axis has exactly one slot: the string `Specific population`. **105 records
over 87 disorders**, with no identifier, no population named, and nothing to join on.
Compare the gene axis (HGNC) and the phenotype axis (HPO); the population axis has an
untyped string.

What is hiding inside it is not subtle. The disorders tagged `Specific population` include
**Canavan disease**, **mucolipidosis type IV**, **cystinosis** and **mucolipidosis type II**
— canonical Ashkenazi Jewish founder disorders, recorded as belonging to a population the
catalogue has no way to name. The information is present and unaddressable.

### 1e. And the coverage that bounds all of the above

**5,773 of 6,728** disorders with any prevalence statement have **no placed record at all**.
Every figure in §1b and §1c is computed on the **14 %** of the corpus that says where it was
measured.

### 1f. Where to look at it

The measurement is a section of the explorer — **Rare disease → What is known → *Whose
numbers these are*** (`web/`, deep-linkable at `#rare?s=population`). Three views, one
question each:

| view | question | form, and why that form |
|---|---|---|
| *Represented, against the world* | is the epidemiology proportional to the world? | diverging lollipop on a **log** axis with parity at 1.0 — a representation ratio is multiplicative, and on a linear axis Africa's 0.07 and Asia's 0.16 are both indistinguishable stubs beside Europe's 8.10, which is to say the finding would be invisible in the chart drawn to show it |
| *Who was looked at* | who, specifically? | 130 countries as a jittered strip on a log axis, coloured by region, searchable |
| *Prevalence is not one number* | does a disorder have *a* prevalence? | all 386 discordant disorders as ranges on the shared six-band rarity axis, windowed, with a per-country breakdown beside the list |

The third view ships the **whole** table rather than a head of it. A truncated list ranked
by disagreement would make the visible set a sample drawn by rank from the population it
claims to describe — the selection error this repository exists to catch, committed in a
build script. The note is in `web/scripts/build-data.mjs` so the next person does not
"optimise" it.

---

## 2. The history that produced the structure

Four mechanisms, kept separate because their consequences for a screen differ. The
distinction matters: they are frequently collapsed into "some populations have more genetic
disease", which is false in a specific and correctable way.

### 2a. Founder effect and drift — a small number of ancestors, a long time ago

A population descended from few founders carries whatever alleles those founders happened to
have, amplified by drift and isolation. This is not a property of the population's health;
it is a property of its **demographic history**, and it is symmetrical — the same mechanism
that raises one disorder to visibility removes others entirely.

- **Finland.** Norio's three-part *Finnish Disease Heritage* (*Human Genetics*, 2003) is the
  founding description: ~36 autosomal-recessive disorders enriched by repeated bottlenecks
  and internal isolation, most of them rare or absent elsewhere — and, symmetrically, cystic
  fibrosis is rare in Finland. Uusimaa et al. (*Disease Models & Mechanisms*, 2022) update
  it from diagnosis to translational research.
- **Quebec.** Scriver's *Lessons from Quebec Populations* (*Annu Rev Genomics Hum Genet*,
  2001): a founder population from roughly 8,500 permanent settlers, with regional
  sub-founder effects (Saguenay–Lac-Saint-Jean) producing 30+ enriched Mendelian conditions.
- **Ashkenazi Jewish populations.** Ostrer & Skorecki (*Human Genetics*, 2012) on the
  population-genetic structure behind the disorders §1d found hiding in an untyped string.
- **Faroe Islands.** Rasmussen et al. (*J Inherit Metab Dis*, 2013) screened **26,462
  individuals** nationwide for primary carnitine deficiency. That is the source of the
  Faroese row in §1c — and note what it demonstrates: the extreme value in our data came
  from a *deliberate national screen*, not from the disorder being unusually visible. The
  measurement produced the number.

### 2b. Consanguinity — recent relatedness, a continuing demography

Distinct from 2a in time-depth and in kind. Bittles & Black (*PNAS*, 2010) put couples
related as second cousins or closer, and their children, at about **10.4 % of the global
population**; in several Arab, South Asian and North African countries first-cousin marriage
runs 20–50 % of unions. The consequence is mechanical and expected: elevated homozygosity,
so a higher rate of autosomal-recessive disease — the Saudi propionic acidemia row in §1c.

Two things follow that are routinely got wrong. First, this raises recessive burden without
implying anything about allele *quality* — the alleles are the ones everyone carries.
Second, it makes those populations **exceptionally informative** for gene discovery, which
is the opposite of the deficit framing: homozygosity mapping in consanguineous families has
identified a large share of known recessive disease genes.

### 2c. Selection — the alleles that are common because they were useful

Not all enrichment is drift. Piel et al. (*The Lancet*, 2013) modelled the global birth
distribution of sickle haemoglobin, whose frequency tracks historical malaria endemicity —
the archetype of balancing selection, where the heterozygote's advantage keeps a
homozygous-lethal allele common. G6PD deficiency and the thalassaemias follow the same
geography.

For a screen this matters because such an allele is **common in one population and rare in
the global panel**, so the standard variant-frequency filter — "too common to be causal" —
has a different threshold depending on whose genome is on the bench.

### 2d. Depth of history, and the population that is not a founder population

Tishkoff et al. (*Science*, 2009), on the genetic structure of Africans and African
Americans, is the necessary counterweight to §§2a–2c. African populations carry **more**
genetic diversity than all non-African populations combined, because everyone else descends
from a subset that left. So "Africa" is not a population, founder logic does not transfer to
it, and its **0.07** representation ratio in §1b is not a small gap in a small place — it is
the least-described *and* most-diverse portion of human variation.

---

## 3. What this does to the reference panels a pipeline actually uses

The history above enters the code through one door: allele frequency panels.

**gnomAD v4** holds 807,162 individuals, of whom roughly 138,000 are of non-European genetic
ancestry — and the release added 416,555 UK Biobank participants, which raised the European
share relative to previous versions. Kore et al. (*Nature Communications*, 2025) applied
local ancestry inference to over 27 million variants in two admixed groups (Admixed American
n = 7,612; African/African American n = 20,250) and found that **78.5 %** and **85.1 %** of
variants respectively show at least a **twofold** difference in ancestry-specific frequency.
A single pooled frequency is the wrong number for most variants in an admixed genome.

**Polygenic scores do not transfer.** Martin et al. (*Nature Genetics*, 2019) — *Clinical use
of current polygenic risk scores may exacerbate health disparities* — is the reference
statement, and the mechanism is the panel, not the biology.

The consequence for **Stage 6** is exact, not rhetorical. A constraint- or
frequency-based prior is a measurement taken on a population; applying it to a patient from
a different one is an extrapolation whose error is the twofold-plus difference above. The
prior is still the best available. It is simply **not ancestry-neutral**, and a manifest
that records `null_blocks` while omitting panel composition is recording the smaller of the
two facts.

---

## 4. The four kinds of scarcity, revisited

[`rare-disease-scale.md`](rare-disease-scale.md) §1 separates prevalence, ascertainment,
measurement and evidence scarcity. This document supplies the missing dimension: **each of
those four is population-dependent**, and they do not co-vary.

| axis | population dependence | number from §1 |
|---|---|---|
| prevalence | **strong and real** — founder, consanguinity, selection | 73.5 % of testable disorders disagree across countries |
| ascertainment | **strongest** — this is who publishes | Africa representation ratio 0.07; 26,429× per-capita disparity |
| measurement | **strong** — a national screen creates the extreme value | Faroese carnitine deficiency, 26,462 screened |
| evidence | **strong** — panels and literature carry the same skew | 78.5–85.1 % of variants twofold-different by ancestry |

**The trap this table exists to name.** A disorder's rate looking high in a well-studied
population and absent elsewhere is compatible with two opposite readings: a real founder
enrichment, or the disorder simply never having been looked for. §1's data cannot separate
them — `tools/ancestry_geography.py` says so in its own output, under `concentration.confound`.
The Faroese row is a founder effect *and* a screening artefact at once, and both are true.

---

## 5. FAIR is in this repository's standards. CARE is not. — a conformance finding

`references/standards.md` names FAIR among the external canons this project answers to.
There is a second framework that governs precisely the data this document is about, and it
is absent from the standards file, from the code, and from every prior document here.

The **CARE Principles for Indigenous Data Governance** (Carroll et al., *Data Science
Journal*, 2020) — Collective benefit, Authority to control, Responsibility, Ethics — exist
because FAIR is a framework for *data movement* and is silent on who a dataset is about and
who decides what happens to it. Hudson, Garrison, Sterling et al. (*Nature Reviews
Genetics*, 2020), *Rights, interests and expectations: Indigenous perspectives on
unrestricted access to genomic data*, states the case directly against unrestricted access
as an unqualified good.

The history is not abstract. Blood samples given by Havasupai tribal members for a diabetes
study were subsequently used in unrelated research, litigated, and settled with the samples
returned — the canonical instance of consented data used beyond its consent.

**What follows for this repository, concretely and at its current size:**

1. Everything ingested here (Orphanet, HPO, HPA, DepMap) is aggregate and public, so **no
   CARE obligation is currently being breached**. That is a fact about our inputs, not a
   virtue of our design.
2. The design gap is real anyway: the architecture has **one untyped string** for a
   population (§1d) and no field anywhere for provenance-of-consent. A project whose stated
   direction includes patient-derived and biobank data would be adding that field under
   deadline instead of before need — the exact failure `docs/adr/` exists to prevent.
3. **`standards.md` should list CARE beside FAIR, with the conformance status honestly set
   to "not applicable yet, and not designed for".** Recorded here and reflected in
   [`../audit.md`](../audit.md) as an open finding rather than silently fixed, because
   changing a standards file is a decision and decisions get an ADR first.

---

## 6. What this changes in the code

| finding | stage | change |
|---|---|---|
| 73.5 % of testable disorders have population-specific prevalence | **2 (Power)** | a cohort size derived from a single band is wrong for three quarters of disorders; the cohort must carry its population, or say it is a world average |
| 55.6 % of records assert `Worldwide` | **8 (Report)** | `Worldwide` must render as an *assertion of population-independence*, never as a default; it is falsifiable and often false |
| panels are ancestry-skewed, 78.5–85.1 % of variants twofold-different | **6 (Prior)** | a frequency- or constraint-based prior carries its panel composition in the manifest, next to `null_blocks` |
| ascertainment is the dominant axis (ratio 0.07 vs 8.10) | **3 (Confound)** | a ranking over diseases must not use record count as an evidence proxy; it is a publication-intensity proxy |
| founder enrichment and non-ascertainment are indistinguishable here | **0 (Objective)** | no objective may be defined over "diseases concentrated in one population" without an external ascertainment model |

None is implemented. They are a checklist so the next pass measures against a stated
intention.

---

## 7. What would falsify this document

1. **§1b could be an artefact of Orphanet's remit.** Orphanet is a European infrastructure;
   a European skew may reflect its scope rather than the world's epidemiology. The test is
   external: the same measurement against GARD, ClinVar submission origins, or a
   non-European rare-disease registry. If the skew is comparable there, it is the field's;
   if not, it is partly Orphanet's and §1b must be restated. **Not done.**
2. **§1c could be measuring diagnostic capacity.** Prevalence classes differing across
   countries is consistent with founder structure *and* with unequal case-finding. Splitting
   them needs a covariate this repository does not have (screening programme coverage, per
   country, per disorder).
3. **No interval anywhere in §1.** The 73.5 % is a proportion over 525 disorders and could
   carry one; the representation ratios are ratios of complete counts and mostly could not.
   The absence is the same defect as [`../audit.md`](../audit.md) A6, and it applies to this
   document's headline number.
