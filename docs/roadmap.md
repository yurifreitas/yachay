# Roadmap — what is left, in the order the value falls

> **Role:** the ordered backlog. Every item names the question, what would answer it, what it
> costs, and **what would make it not worth doing** — because a plan without that last column
> is a wish list.
> **Last revised:** 2026-08-29 · **State:** six tiers. Tiers 1-4 are derived from an open
> finding in [`audit.md`](audit.md) or a stated falsifier in `references/`. **Tiers 5 and 6
> are new**: 5 is the atlas's own catalogued-and-unbuilt knowledge, every item graded
> *buildable* in [`references/theory-atlas.md`](references/theory-atlas.md) under ADR 0007;
> 6 is the explorer. Nothing here was invented for this file, and every item still carries
> the column that says what would make it not worth doing.
>
> Planning-mode. The findings themselves live in [`audit.md`](audit.md); the artefact map is
> [`references/rare-layers.md`](references/rare-layers.md); the producers are
> [`../tools/README.md`](../tools/README.md).

---

## Where the project actually stands

| | |
|---|---|
| library (`src/sieve/`) | **4 modules** implemented (Null, Power, Design, Target); six of the ten stages have no implementation |
| tooling (`tools/`) | 58 scripts, 19,642 lines |
| tools that call the library | **3** (`dossier.py`, `genotype_phenotype.py`, `sieve.cli`) |
| ingested sources | 18, ~1,339 MB |
| sources ingested and unread | **3** (Orphanet gene associations, Orphanet age of onset, phenopacket-store) — gnomAD is read by `tools/gene_world.py`, Reactome by `tools/scale_information.py` |
| pipeline stages | 36 |
| audit findings | 35, of which 28 closed |
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

**What answers it.** Reactome is on disk and **now read** — `tools/scale_information.py` maps genes onto its 29 top-level pathways and measures what the collapse costs. What is still not done is the retrospective below (118 MB). Map genes to pathways, then run
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

## Tier 2 — the data that is on disk and under-used

### 2.1 gnomAD constraint as a Stage 6 prior

95 MB, ingested, and **read** — `tools/gene_world.py` uses it. What is unbuilt is the use this
item exists for: a Stage 6 prior. `references/rare-disease-scale.md` §4 argues for it and
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

---

## Tier 5 — the atlas's own knowledge, catalogued and not built

Every item here comes from the design work recorded in
[`references/theory-atlas.md`](references/theory-atlas.md), and every one is graded
**buildable** there: the file it would read is already in `data/`. They are ordered by what a
reader of the explorer would gain.

### 5.1 Knowledge completeness, per disease and per scale

**Question.** "How much is known about this disease?" is currently answerable only by reading
several artefacts. The design work proposes a vector rather than a score — maturity in
genetics, molecular, cellular, natural history, therapy — so two diseases can be compared **by
the shape of what is known about them** rather than by their biology.

**What answers it.** A join over the existing `out/rare/*.json` layers. No new source.
`distance(K_A, K_B)` over those vectors is a different similarity from any in the field, and
it is the one a funder or a patient organisation actually wants.

**Cost.** Low. **What would kill it.** If the vector is dominated by one component — most
likely publication count — it is an attention index wearing a lab coat, and §5.3 should be
built instead.

### 5.2 A typed gap taxonomy

**Question.** The atlas currently has one kind of hole. The design work names five, and they
have different remedies: **epistemic** (nobody knows), **accessibility** (known, not
reachable), **interoperability** (exists, does not join), **population** (no cohort exists),
**model** (data exists, no computational representation).

**What answers it.** `evidence_atlas.json` and `consistency.json` already carry most of the
signal. The classification is a rule set over fields that exist.

**Cost.** Low. **What would kill it.** If four of the five classes come back near-empty, the
taxonomy is a vocabulary rather than a measurement — the same result `nongene_measure.py`
returned for six of ten authored causal classes, and it would be just as useful to know.

### 5.3 Research attention against disease burden

**Question.** Two diseases of similar prevalence receive 4,000 papers and 38. Is attention
explained by burden, by tractability, or by neither?

**What answers it.** `gene2pubmed.gz` (on disk, unread for this purpose) against Orphanet
prevalence and the severity signal in the annotations. The output is an inequality measure over
the field's own attention, which is metascience rather than biology — and it sits directly
beside the ancestry axis this project already measures at Europe 8.10 against Africa 0.07.

**Cost.** Low-medium. **What would kill it.** Publication counts are confounded by gene
popularity; if the index tracks the gene rather than the disease it measures citation habits.

### 5.4 Typed evidence edges, and lineage

**Question.** The atlas stores that a claim exists. Science needs *supports*, *refutes*,
*fails to replicate*, *ambiguous*, *not tested* — and the route back from any displayed number
to the observation behind it.

**What answers it.** The conflict decomposition (§ measured, ADR 0007) already proves the
field records disagreement at scale and that **about half of it is context, not
contradiction**. Typed edges are how that finding becomes navigable rather than a paragraph.

**Cost.** Medium — it is a schema change, and schema changes propagate.
**What would kill it.** If almost every edge lands in one type, the typing is decoration.

### 5.5 Three clocks

**Question.** The atlas has one time axis and needs three: **knowledge time** (when the field
learned it), **biological time** (when it happens in a person), **model time** (which version
produced a number). Conflating them is why "the gene affects the brain" reads as timeless when
the mechanism may occupy one embryonic window.

**What answers it.** Knowledge time is derivable today from publication dates in
`gene2pubmed.gz` and the HPOA biocuration field — enough to rebuild the atlas as it stood in
1995, 2005 and 2026 and watch it appear. Biological time needs onset data (`en_product9_ages`,
ingested and unread). Model time is a provenance field.

**Cost.** Medium. **What would kill it.** Nothing — the failure mode is that it is merely
beautiful, so it should ship attached to a question, not as an animation.

### 5.6 Where a new observation would be worth most

**Question.** The atlas shows what is known. The design work proposes it also show **where a
new measurement would reduce uncertainty most** — expected information gain, `H(θ|D) −
E[H(θ|D,new)]`.

**What answers it.** For ultra-rare disease this is unusually tractable: with n = 5, one new
case moves the posterior visibly. The prerequisite is §5.1 and §5.2, which is why it is here
rather than higher.

**Cost.** High. **What would kill it.** If the ranking it produces is "whatever has fewest
cases", it is a count in disguise. That is the acceptance test, and it should be stated before
the first run.

### 5.7 The model as a first-class object

**Question.** The atlas links disease to paper. It should link disease to **model** — with the
model's equations, parameters, assumptions, calibration, validation, licence, and the
genealogy that produced it (`healthy model → mutation → disease model → patient parameters`).

**What answers it.** Physiome/CellML publishes hundreds of executable physiological models and
is **not ingested**. Indexing rather than duplicating is the whole move. Alongside it: the
L0–L5 grading (descriptive, associative, predictive, mechanistic, causal, calibrated) so that
nobody reads an embedding as a causal model, and a **twin readiness** row per disease that
says plainly which layers exist and which do not.

**Cost.** High, and the highest-value item in this tier.
**What would kill it.** If fewer than a handful of Physiome models map to rare disease, the
index is empty and the grading has nothing to grade. **That check is one afternoon and should
be done before anything else here.**

### 5.8 Higher-order relations, and synergy

**Question.** `variant + cell type + developmental stage + exposure → phenotype` is one
relation. The atlas stores four binary edges and destroys the context. How much does that cost?

**What answers it.** The same excess-MI estimator `scale_information.py` already runs, pointed
at structure instead of scale: hyperedges against their pairwise projection. Then partial
information decomposition — redundant, unique, **synergistic** — over gene pairs co-annotated
to a disease.

**Cost.** Medium. **What would kill it.** If binarisation costs nothing measurable, the
hypergraph is an aesthetic preference.

### 5.9 Two more from the buildable list

**Spectral perturbation signature** — `Δλ` of the STRING Laplacian when a disease's genes are
removed, against a degree-matched null. The network sibling of `twin_propagation.py`, and it
needs no new data. **Persistent homology of the phenotype space** — whether the disease cloud
has structure beyond clusters. **Its trap is named in advance**: on a binary annotation matrix
whose density varies 100-fold, the most persistent feature will be the curation gradient
unless the same permutation null is applied to barcodes.

### 5.10 The two controls this repository owes itself

**A36** — a checker that enumerates `out/rare/*.json` and fails when an artefact appears in no
index. `verify_claims.py` protects a number; nothing protects a list, and six indexes drifted
in one day because of it. **Cost: low, and it pays immediately.**

**A37** — a test that asserts the read-site detector finds the reader of a known-read file,
then a fix against that test. The obvious fix was tried and made the count worse, which means
the diagnosis is wrong and a test is the only way through.

---

## Tier 6 — the explorer

The interface is where the epistemics either survive or get flattened into a badge. These are
ordered by how badly the current version misrepresents what is underneath.

### 6.1 The four measured results are rendered nowhere · **the A29 shape, again**

`build-data.mjs` carries a comment saying it exactly: *a dashboard that publishes twenty
aggregate layers while its strongest result sits in a JSON file is publishing that result
nowhere.* Four artefacts added under ADR 0007 — the only results in the repository with a
governing ADR, a null and an interval — are not emitted to the bundle.

**Cost.** Low to emit, medium to render well. **Do not emit without a view**: shipping data
nothing renders is bundle weight and a second kind of dishonesty.

### 6.2 Projections instead of pages

**The idea, and it is the strongest UI idea in the design work.** A disease is not a page. It
is one object seen through a chosen projection — clinical, molecular, cellular, network,
temporal, evidence, uncertainty, case, computational — and **the interface should say which
projection is on screen and what that projection discards.**

This is no longer only an aesthetic argument. `scale_information.py` measured the discard:
collapsing genes onto pathways keeps 22 % of the information about organ system, and retention
varies 5.6-fold across systems. **The interface can now print the loss beside the view**, which
nothing in this field does.

**Cost.** High — it is the navigation model, not a screen. **What would kill it.** If users
cannot tell two projections apart without reading, it is a tab bar with ambitions.

### 6.3 Uncertainty as geometry, not as a badge

Today: ✅ ❓ ⚠️. Proposed: the *appearance* of a node carries its epistemic status — diffuse
where evidence is thin, sharp where it is strong — and the three quantities the design work
insists on separating stay separate: **evidence strength**, **epistemic confidence**, and
**effect probability**. They are not the same number and the interface currently implies they
are.

**Cost.** Medium. **What would kill it.** Diffuseness that reads as "loading".

### 6.4 The unknown as a navigable object

Every system renders what is known and lets the unknown disappear. Invert it: a `KnowledgeGap`
with upstream, downstream, missing relation, evidence density, contradiction — clickable, and
feeding §5.6. This is the single most distinctive thing the explorer could do, and it depends
on §5.2 rather than on design.

### 6.5 Say what the translation costs, in the translation

The language switch offers Portuguese. Portuguese covers **42.9 %** of the annotated phenotype
with a **69.6-point** spread across organ systems. **A reader in Portuguese should be told, on
the page, when the section they are reading falls in the weak part of that distribution** —
which for the nervous system is most of it. This is cheap, it is honest, and no atlas does it.

### 6.6 Scientific zoom

Organism → system → organ → tissue → cell → organelle → pathway → complex → protein → domain →
residue → variant, and back up. The measured result says what the ascent costs at each step, so
the zoom can be **annotated with its own information loss** instead of pretending the scales
are commensurable.

**Cost.** High. **Prerequisite:** 6.2. Building it before the projection model exists produces
an animation.

---

## The order I would actually take

1. **§5.10** — the two controls. A day, and they stop the next drift.
2. **§5.7's afternoon check** — do Physiome models map to rare disease at all? It gates the
   most valuable item in the plan and it is cheap to answer.
3. **§6.1 + §6.5** — render what has been measured, and tell a Portuguese reader what the page
   is costing them. The results exist; only the view is missing.
4. **§5.1 → §5.2 → §6.4** — completeness, then typed gaps, then the unknown made navigable.
   This chain is what turns the atlas into something no other rare-disease resource is.
5. **§5.3, §5.8, §5.9** — the measurements that need no new source, in whatever order the
   questions get interesting.
6. **§6.2 → §6.6** — the navigation model, once there is enough measured to project.

Everything dynamical — attractors, Koopman, viability, memory — stays out until there is
longitudinal data. That is not a scheduling decision; it is
[`references/deep/multiscale-formalism.md`](references/deep/multiscale-formalism.md) §14.

---

## The one thing that is not on this list

**More aggregate catalogues.** The project has ingested eighteen sources and the marginal
value of a nineteenth is low: three of them are still unread, the two added on 2026-08-29 were
read the same day and each produced a headline, and the two patient-level sources produced more
findings in a day than the aggregate layers produced in a month. Depth
now comes from *joining what is here*, not from adding to it — which is what
[`references/patient-data.md`](references/patient-data.md) §3c argues and what the last three
sweeps demonstrated.
