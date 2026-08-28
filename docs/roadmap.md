# Roadmap — what is left, in the order the value falls

> **Role:** the ordered backlog. Every item names the question, what would answer it, what it
> costs, and **what would make it not worth doing** — because a plan without that last column
> is a wish list.
> **Last revised:** 2026-08-28 · **State:** written after eleven audit sweeps in one day.
> Everything here is derived from an open finding in [`audit.md`](audit.md) or a stated
> falsifier in `references/`; nothing was invented for this file.
>
> Planning-mode. The findings themselves live in [`audit.md`](audit.md); the artefact map is
> [`references/rare-layers.md`](references/rare-layers.md); the producers are
> [`../tools/README.md`](../tools/README.md).

---

## Where the project actually stands

| | |
|---|---|
| library (`src/sieve/`) | **4 of 10 stages** implemented (Null, Power, Shortlist, Design) |
| tooling (`tools/`) | 33 scripts, 11,790 lines |
| tools that call the library | **3** (`dossier.py`, `genotype_phenotype.py`, `sieve.cli`) |
| ingested sources | 14, ~899 MB |
| sources ingested and unread | **3** (Reactome ×2, gnomAD) |
| pipeline stages | 29 |
| audit findings | 26, of which 20 closed |
| authored layers tested | 2 of 9 |

The structural finding (A15) remains the one that decides everything else: the periphery is
6.5× the core and mostly does not use it. Two tools now do, which is movement, not
resolution.

---

## Tier 1 — the questions that change what the project may claim

### 1.1 Reactome, and the Stage 7 claim that has never been tested

**Question.** `references/rare-disease-mechanisms.md` §4 claims a shortlist should be
diversified over *signalling modules* rather than genes, because ten genes from one module is
one hypothesis with ten labels. Nothing has tested it.

**What answers it.** Reactome is on disk (118 MB, unread). Map genes to pathways, then run
the retrospective the document itself names: on DepMap or NF2, does a module-diversified
shortlist outperform a gene-diversified one?

**Cost.** Medium. The mapping is a join; the retrospective needs a validation set and an
honest definition of "outperform" agreed *before* it is run.

**What would kill it.** If the two shortlists perform the same, §4's main recommendation is
decoration and should be struck through the way §5.2 was.

### 1.2 The residual in the modularity claim

**Question.** A17 tested our modularity excess (0.699) against STRING (0.541–0.575) and it
survived. The residual did not: ours is still higher, and the clique construction is the
obvious explanation.

**What answers it.** The sharper test the original wording named and which has still not been
run — **a rewiring within curation source** rather than a global degree-matched null.

**Cost.** Low. The graph and the method are both in hand.

**What would kill it.** Nothing kills it; it either explains the residual or it does not, and
both are publishable.

### 1.3 ~~Confidence intervals on everything~~ ✅ **done 2026-08-28 — A26**

**Question.** The repository has produced exactly **one** interval in its life. The 73.5 %
prevalence-disagreement figure, the six bias statistics, the 39.7 % evidence share and the
8 % powered share are all point estimates carrying documented weight.

**What answers it.** Bootstrap. The machinery exists — `tools/multiplicity.py` imports scipy
and the paired bootstrap that settled lineage §8b is already written.

**Cost.** Low, and it was the highest ratio of value to effort in this list — which is why
leaving it open through thirteen sweeps was the worst prioritisation call of the day.

**What it found.** Seven of eight headlines survive. The single-case bias holds at **−0.497
[−0.591, −0.387]**, and two published sentences were **wrong in the direction of a tidier
story**: the n = 5–19 band has no detectable difference at all, and the n ≥ 20 reversal is
real rather than "if anything". See A26.

**The remainder.** The six statistics in `bias.json` still have none, because
`tools/atlas_bias.py` publishes each correlation without the per-disease vectors behind it.
That is the next low-cost item and it is a change to that tool, not to `intervals.py`.

---

## Tier 2 — the data that is on disk and unread

### 2.1 gnomAD constraint as a Stage 6 prior

95 MB, ingested, unread. `references/rare-disease-scale.md` §4 argues for it and
`references/rare-disease-ancestry.md` §3 warns that its panel is not ancestry-neutral.
Ingesting it made both testable; neither has been tested. **Cost: low.** The specific
deliverable is a prior that *carries its panel composition in the manifest*, next to
`null_blocks` — which is what ADR 0005 asks for and nothing implements.

### 2.2 The VUS layer, joined to the diseases

`clinvar_evidence.py` measured that **52 % of ClinVar is uncertain** and **84.6 % sits at one
star or less**. What it has not done is join that per-gene VUS share to the disease layer, so
a dossier can say *a new patient's variant in this gene will probably be uninterpretable*.
**Cost: low.** The per-gene table already exists in the artefact.

### 2.3 The 1,587 patient variants absent from ClinVar

28 % of our patient corpus is not in ClinVar at all, and 470 more are VUS there. Those 2,057
variants are published as causative in the literature and not confidently classified by the
field. Whether that is a lag, a submission gap, or a disagreement is unknown and checkable.
**Cost: medium** — it needs the submission dates and probably the ClinVar VCV records.

---

## Tier 3 — the structural decisions

### 3.1 A15: what is this repository?

Either the library is the project and the rare-disease work is an application of it — in
which case the **seven unimplemented stages are the backlog** — or there are two projects
sharing a download registry, in which case the README misdescribes the repository. This is a
decision, not a defect. It belongs in an ADR and it cannot be taken by anyone who has not
seen the ratio in the table at the top of this file.

### 3.2 ADR 0005, still `proposed`

Population as a typed field, and CARE beside FAIR in the standards. Now more urgent than when
it was written: `references/patient-data.md` §3b lists **four things that must exist in the
schema before any access-controlled data can be accepted**, and ADR 0005 is two of them.

### 3.3 The seven untested authored layers (A13)

`nomenclature`, `capability`, `barriers`, `lupus`, `lupus_graph`, `references`, `thesis`.
Two of nine have been tested and **both tests found something**. For the judgement layers
the honest move is not a test but **surfacing the confidence mark in the interface** — and
`lexicon_check.py` now provides the argument for it: every row the author marked *low*
confidence carried a flag, and the one marked *high* did not.

---

## Tier 4 — the long extractions, and what they would need

Not scheduled. Listed so the cost is visible before anyone starts.

| what | why it is not started |
|---|---|
| **Access-controlled patient cohorts** (dbGaP, EGA, UK Biobank, Genomics England) | needs a named PI, an ethics determination and an institutional DUA signatory. This repository has none. `references/patient-data.md` §3 has the tiers and the sequencing. |
| **A rewiring-within-curation null on the full HPO graph** | tractable, and it belongs to 1.2 |
| **Retrospective validation of the shortlist stages** | needs a held-out validation set with known answers; the NF2 positive control is the only one the project has, and `lineage.md` §9 is still open on which of two fixes is right |

---

## The one thing that is not on this list

**More aggregate catalogues.** The project ingested six sources in one day and the marginal
value of a seventh is low: three of the six are still unread, and the two patient-level
sources produced more findings in a day than the aggregate layers produced in a month. Depth
now comes from *joining what is here*, not from adding to it — which is what
[`references/patient-data.md`](references/patient-data.md) §3c argues and what the last three
sweeps demonstrated.
