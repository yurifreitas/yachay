# The social layer — delay, access, naming, and where they enter the statistics

> **Role:** the part of rare disease that is not biology. Diagnostic delay, who is in the
> reference data, who is not, what a name costs, and what the money is actually spent on.
> Included **only** where it becomes a measurable confounder or a design constraint — not
> as context, and not as advocacy.
> **Last revised:** 2026-08-27 · **State:** external figures verified through Crossref
> with sample sizes and intervals carried over. Internal figures read from
> `out/rare/*.json`. ⚠ The barriers and nomenclature layers this document draws on are
> marked in their own provenance fields as **written from working knowledge**; that mark
> is carried here rather than dropped.
>
> Explanation-mode. This is **not clinical guidance and not a policy recommendation.**
> Companion files: [`rare-disease-scale.md`](rare-disease-scale.md) (the quantitative
> axis), [`rare-disease-mechanisms.md`](rare-disease-mechanisms.md) (the biology), and
> [`rare-disease-ancestry.md`](rare-disease-ancestry.md), which measures the population
> axis this file could only assert when it was written.

---

## 0. Why a statistics repository has this file

A confounder is a confounder wherever it comes from. This repository's Stage 3 exists to
stop a ranking reflecting toxicity or technical variation instead of the phenotype; the
same stage has to stop a ranking reflecting **who got diagnosed, in which country, under
which name**. Those are social facts with statistical consequences, and the consequence is
measured on our own reference data at **+0.2357** (`tools/atlas_bias.py`, ascertainment).

So the rule for this file is the repository's scope discipline (documentation standard §8),
applied strictly: an entry earns its place only if it names a mechanism by which a social
fact becomes a number in a dataset used here. Everything else is deleted rather than
stretched, however important.

---

## 1. Diagnostic delay, with its determinants

The best-measured social fact in the field. Faye et al. (*Eur J Hum Genet*, 2024) surveyed
**6,507 people living with 1,675 rare diseases across 41 European countries** through
EURORDIS's Rare Barometer:

- average total diagnosis time **4.7 years**;
- **56 %** were diagnosed more than six months after first medical contact.

The determinants are reported as odds ratios with 95 % intervals, which is why this study
is usable here rather than merely quotable:

| determinant | OR (95 % CI) |
|---|---|
| symptom onset in adolescence | **4.79** (3.7–6.2) |
| symptom onset in childhood | **3.11** (2.4–4.0) |
| number of healthcare professionals consulted | **5.15** (4.1–6.4) |
| having been misdiagnosed | **2.48** (2.1–2.9) |
| **being a woman** | **1.22** (1.1–1.4) |
| having a genetic disease | 1.33 (1.1–1.5) |
| unmet need for psychological support | 1.34 (1.2–1.5) |

**What this does to a dataset.** Delay is not a delay in the patient's record only. A
disease whose patients wait five years for a diagnosis accumulates annotations, publications
and cohort members five years later than one that does not — and *annotation count* is
precisely the proxy `atlas_bias.py` uses for attention, the one correlating +0.2357 with
having a known gene. The sex effect (OR 1.22) is small per-patient and enters the catalogue
as a systematic offset applied to every female-predominant disorder simultaneously.

Note the direction carefully before using it: this survey covers **geographical Europe**,
where diagnostic infrastructure is comparatively dense. Northern (OR 2.15) and Western
(1.96) Europe show *longer* delays than the Southern/Eastern reference — plausibly a
measurement of how completely a delay gets *recorded*, not of how long it is. That is the
same ascertainment problem one level up, and it is why the figure is not extrapolated to
the rest of the world here.

---

## 2. Who is in the reference data

Every prior in Stage 6 comes from a reference dataset, and those datasets have a
population.

**The geography of the prevalence field is measurable, and it is lopsided.**
`tools/prevalence_audit.py` over Orphanet's 17,108 records: **65 % (11,193) carry no named
place at all**. Among those that do, records per hundred million population run
Netherlands **1,233**, United Kingdom **532**, Italy **442**, France **422**, United States
**132**. This is a map of who publishes epidemiology, not of where disease is.

That measurement has since been taken properly, and it is worse than this paragraph
suggested. `tools/ancestry_geography.py` weights each region's records against its share of
the world's people: **Europe 8.10, Africa 0.07** — a factor of **116** — with Africa's 1.45
billion people contributing **77** prevalence records in total. Per capita the extremes run
Iceland **18,500** per hundred million against Indonesia **0.7**, a ratio of **26,429×**.
The full measurement, its founder-history context and the limits on reading any of it as
ancestry are in [`rare-disease-ancestry.md`](rare-disease-ancestry.md).

**Genomic reference panels are worse, and the field has documented it.** Popejoy &
Fullerton (*Nature*, 2016) and Sirugo, Williams & Tishkoff (*Cell*, 2019) established that
participants in genetic studies are overwhelmingly of European ancestry. The mechanism that
matters for a rare-disease pipeline is specific: a variant's rarity is judged against a
population panel, so under-represented ancestry yields **more apparently rare variants**,
more variants of uncertain significance, and a lower diagnostic yield. gnomAD's constraint
metrics (Karczewski et al., *Nature*, 2020; 141,456 individuals) are the best available and
inherit the same composition.

Concretely: a Stage 6 prior built on constraint is a prior built on who was sequenced. It
is still the right prior — it is simply not ancestry-neutral, and a screen that never says
so is making an unstated assumption about its patients.

**And the diagnostic yield to keep in view.** The 100,000 Genomes pilot (*NEJM*, 2021)
reported a diagnosis in **25 %** of rare-disease participants, with 14 % of those found in
regions that standard clinical gene panels do not cover. Three quarters undiagnosed, in the
best-resourced programme available, is the honest denominator for anything downstream.

---

## 3. Names, and the literature they hide

`tools/nomenclature_seed.py` — ⚠ **authored from working knowledge**, with a confidence
mark per entry (7 high, 5 medium), not a measured layer.

The causal chain it exists to close is short and entirely statistical:

> a disease's **name** decides what a literature search finds → which decides what
> evidence is discoverable → which is the **ascertainment bias measured at +0.2357**.

Of the twelve documented cases: **four were renamed for ethical reasons** (eponyms
belonging to physicians implicated in Nazi-era medicine, among others), **two carry a name
that preserves a factual error** about the disease, and **one has two live literatures**
under two names. A searcher who knows one name sees half the evidence, and the half they
miss is not random.

This repository's own domain is an instance. The disease adapter's terminology note exists
because *NF2-related schwannomatosis* was called *neurofibromatosis type 2* until 2022, is
not NF1, and is not `SMARCB1`/`LZTR1` schwannomatosis — three distinct name confusions, any
of which silently truncates a query. That is why the crosswalk in
[`rare-disease-lexicon.md`](rare-disease-lexicon.md) is infrastructure and not decoration.

---

## 4. What actually blocks a therapy — and what the money is for

`tools/barriers_seed.py` — ⚠ **written from working knowledge**; mechanistic claims are
well established in their fields, the judgement that an approach is *underused* is a
judgement and is marked at low or medium confidence throughout.

Across 12 diseases it records **29 barriers in four classes, kept separate because the fix
differs**: molecular 13, **trial design 10**, delivery 4, economic 2. The distribution is
the finding. The largest non-molecular class is not money and not chemistry — it is
**trial design**: a cohort too small to power an endpoint, an endpoint that does not move
in the available follow-up, a natural history nobody recorded. That is a *statistical*
barrier, and it is the one this repository is actually equipped to work on.

**The economic barrier, as arithmetic rather than assertion.** `tools/capability_math.py`
divides plan capital by the validated point-prevalence cohort, and its conclusion cuts
against the barriers layer that precedes it: capital per patient runs from about **$0.10**
(interferon stratification in lupus) to about **$1,001** (Duchenne), and both ends are upper
bounds because the cohorts are under-counted. Against a rare-disease therapy priced in the
hundreds of thousands, **laboratory capital is not the expensive part**. What is dear is the
released dose and the trial.

Two consequences, and the second is uncomfortable.

1. It reframes the standard economic argument. "There is no market" is usually stated about
   discovery cost; the arithmetic says discovery is cheap per patient and *delivery* is not.
2. It contradicts a claim made on this project's own barriers tab. That contradiction is
   published rather than reconciled, per the hansei rule (`standards.md` §2) — the two
   layers disagree, one is measured and one is authored, and the reader is told which.

The Lancet Commission on rare diseases (Boycott, Giugliani et al., 2025) frames the same
gap at policy scale — visibility and health-care disparity for a population it counts at
**400 million**, consistent with the 263–446 million interval of
[`rare-disease-scale.md`](rare-disease-scale.md) §0.

---

## 5. Where this enters the code

The test of this file is whether any of it changes a line. Four places it should.

| finding | stage | concrete change |
|---|---|---|
| delay correlates with annotation count | **3 (Confound)** | annotation count is *already* used as an attention proxy; it must never be used as an evidence proxy without saying which it is |
| reference panels are ancestry-skewed | **6 (Prior)** | a constraint-based prior must carry its panel composition in the manifest, the way `null_blocks` is carried |
| two literatures under two names | **6 (Prior)** | prior lookup goes through the lexicon crosswalk, never through a single label |
| trial design is the largest non-molecular barrier | **2 (Power)** and **8 (Report)** | shortlist output should state the cohort a validation would need, not only the rank |
| prevalence differs by population in 73.5 % of testable disorders | **2 (Power)** | a cohort derived from one band is wrong for three quarters of disorders — [ADR 0005](../adr/0005-population-as-a-typed-field.md) |
| FAIR is in the standards; CARE is not | **9 (Repro)** | `standards.md` gains a CARE row with its conformance status set honestly — [ADR 0005](../adr/0005-population-as-a-typed-field.md) |

None of the four is implemented. They are stated as a checklist so the next pass measures
against an intention rather than re-deriving one.

---

## 6. What this file refuses to do

- **No severity score, no burden index, no composite.** The dossier layer already states
  this: those need value judgements this project has no basis for. Human impact is reported
  as onset age, sign frequency **with its denominator**, and trial activity. The reader does
  the weighing.
- **No prioritisation of diseases by social importance.** Stage 0 exists because optimising
  a metric whose maximum is an artifact is the failure mode of this whole class of work, and
  a hand-built importance score is that failure wearing an ethical costume.
- **No extrapolation of European figures to the world.** §1 and §2 both stop at the edge of
  their sampling frame, and the missing region is named rather than averaged over.
