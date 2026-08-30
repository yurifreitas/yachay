# Theory atlas — the mathematics proposed for this project, and what each one would have to measure

> **Role:** reference, with one explanatory section (§0) stating why the grades exist. Every
> mathematical construct proposed for the multiscale atlas is graded
> by whether it has been measured here, could be measured from data already on disk, or is
> still an analogy with no estimator attached. The mathematics itself — formal object,
> estimator, blocker, verified citations — is in
> [`deep/multiscale-formalism.md`](deep/multiscale-formalism.md); the mid-century work it
> descends from, with the two of those ancestors whose predictions were tested here, is in
> [`deep/foundations.md`](deep/foundations.md).
> **Last revised:** 2026-08-29 · **State:** 4 measured (10 findings, one of them a failed
> prediction), 9 buildable, the rest
> analogy. One of the three was not on the theory list at all — see §1, language.
> Governed by [`../adr/0007-theory-enters-by-measurement.md`](../adr/0007-theory-enters-by-measurement.md),
> which is what makes the grades binding rather than decorative.
>
> **The literature is verified.** 35 works were resolved through the Crossref API on
> 2026-08-29 — title, authors, venue, year, DOI — and they carry `[XR]` in the deep file. Six
> could not be resolved and carry `[REC]`; those may not be cited until they are. This makes
> the atlas the second part of the repository, after [`../lineage.md`](../lineage.md) §11, whose
> references are checked rather than recalled.
>
> **Scope discipline** (standards §8): an entry that cannot name the file it would read is an
> analogy, and analogies that stop being interesting get deleted rather than stretched.

---

## 0. Why this file exists

The project's own thesis is a ladder of scales — genotype, protein, conformational dynamics,
interactome, pathway, cell state, tissue, patient — and `tools/thesis_seed.py` grades most of
its rungs *named-only*. A design conversation then produced roughly ninety formalisms that
would fill those rungs. All ninety are more interesting than anything currently built.

That is the hazard this file is built around. `tools/README.md` §5 already records the
project's standing embarrassment: nine authored layers, **two tested**. A catalogue of ninety
formalisms written as prose would be the tenth and largest authored layer, in a repository
whose one claim on a reader is that every number traces to the artefact that produced it.

So the catalogue is kept, in full, and given no standing. Three grades:

| grade | meaning | count |
|---|---|---|
| **measured** | a tool computes it from an ingested source, with a null and an interval | 4 constructs, 10 findings — **one of them negative** |
| **buildable** | every file it needs is already in `data/`; only work stands in the way | 10 |
| **analogy** | needs data this project does not have, or has no estimator attached | the rest |

---

## 1. The measured rows

### Cross-scale information — what a change of scale costs

**Grade:** measured · **Tool:** [`../../tools/scale_information.py`](../../tools/scale_information.py) ·
**Artefact:** `out/rare/scale_information.json` · **Stage:** `scale_information`

**The construct.** Renormalisation asks what survives when you change scale; the information
bottleneck asks for the smallest description of X that keeps what matters about Y. Applied
here: a disease is described by its causal genes; collapse those genes onto a coarser alphabet
and ask how much of what they said about the disease's **organ systems** survives.

**What was measured.** 9,142 diseases carrying both a causal gene (HPO `genes_to_disease`) and
a phenotype annotation (`phenotype.hpoa`, lifted through `hp.obo` to the 23 organ systems under
HP:0000118). Mutual information in bits, each disease weighted 1, reported as **excess over a
permutation null** because MI rises with alphabet size for free.

| scale | n | alphabet | I | null | **excess** | 95% CI | kept vs gene | compression |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| gene | 9,142 | 5,260 | 1.2712 | 0.9920 | **0.2791** | [0.2583, 0.3000] | 1.00 | 1× |
| cell type | 9,067 | 154 | 0.1048 | 0.0172 | **0.0877** | [0.0806, 0.0947] | 0.31 | 34× |
| pathway | 7,350 | 29 | 0.0675 | 0.0064 | **0.0611** | [0.0544, 0.0678] | 0.22 | 181× |

**What it says.** Collapsing 5,260 genes onto 29 Reactome top-level pathways — a 181-fold
compression — keeps **22%** of the information the genes carried about organ system. Collapsing
onto 154 cell types keeps **31%** at 34-fold compression. Per category, the coarse alphabets are
enormously more efficient: the pathway scale carries roughly 40× as much excess information per
category as the gene scale. The intervals do not overlap, so the ordering
*cell type > pathway* is a difference rather than noise.

**And the pooled table hides two things, so both were measured.**

*The loss is concentrated, not uniform.* One-vs-rest per organ system (20 of 23 clear a
gene-scale z ≥ 5), pathway retention spans **5.6-fold**:

| organ system | n | pathway retention | cell-type retention |
|---|---:|---:|---:|
| Abnormality of the breast | 403 | **0.39** | 0.18 |
| Neoplasm | 951 | **0.38** | 0.22 |
| Abnormal cellular phenotype | 829 | 0.28 | 0.30 |
| Abnormality of metabolism/homeostasis | 3,503 | 0.27 | 0.22 |
| Abnormality of blood and blood-forming tissues | 1,772 | 0.19 | 0.28 |
| Abnormality of the eye | 4,462 | 0.08 | 0.12 |
| Abnormality of limbs | 3,644 | 0.08 | 0.12 |
| Abnormality of the cardiovascular system | 3,645 | **0.07** | 0.12 |

Pathways hold what is pathway-shaped — neoplasm, metabolism, cellular phenotype — and lose what
is structural and developmental. Cell types invert the ranking for exactly those structural
systems. **There is therefore no single right coarse-graining for this atlas**, and a per-system
choice of scale is defensible where a global one is not. That is research problem 10 answered in
its observational form.

*And the loss lines up with a prediction from 1952.* Split the twenty systems by the KIND
of process whose failure produces their abnormalities — a structure that formed wrongly against
a process running wrongly — and the pathway alphabet retains **0.276** in the physiological
class against **0.136** in the morphogenetic one (difference +0.140, permutation p = 0.00955
as a median over five seeds and never above 0.02185,
20,000 draws). A pathway is an inventory of reactions; Turing's morphogenesis says form comes
from a field with a geometry and a time, which an inventory has no words for. ⚠️ The retentions
were visible when the classification was written, so this is a description with a p-value
rather than a pre-registered test — see [`deep/foundations.md`](deep/foundations.md) §1 for the
full caveat and the way to promote it.

*The relation is directional.* `U(S|F) = I/H(S)` against `U(F|S) = I/H(F)`:

| scale | U(S\|F) | U(F\|S) | ratio |
|---|---:|---:|---:|
| gene | 0.3091 | 0.1062 | **2.91** |
| cell type | 0.0255 | 0.0155 | 1.64 |
| pathway | 0.0164 | 0.0161 | 1.02 |

Genes predict organ system nearly three times better than organ system predicts genes — and the
asymmetry **collapses under coarse-graining** (1.02 at pathway scale). Compression destroyed the
direction, not only the magnitude. This is B9, promoted; it is *conditional-entropy* asymmetry
and does not license the word "Finsler".

**What it does not say.** This is observational mutual information over a static catalogue.
It is **not** effective information and **not** causal emergence: there is no intervention and
no dynamics here. Calling it EI would be exactly the promotion ADR 0007 forbids.

**Prior art, with its verification marks in
[`deep/multiscale-formalism.md`](deep/multiscale-formalism.md) §1:** Shannon (mutual
information); Tishby, Pereira & Bialek `[REC]` (information bottleneck); Hoel, Albantakis &
Tononi `[XR]` (causal emergence — named as what this is deliberately *weaker* than); Paninski
`[XR]` and Kraskov *et al.* `[XR]` for the estimator bias that bit us below; Kadanoff `[XR]` and
Wilson `[XR]` for the question, borrowed without the method.

**One failure kept.** The first version's bootstrap resampled diseases with replacement and
returned a gene-scale point estimate of 0.2791 against a percentile interval of
[0.1745, 0.2163] — an interval not containing its own estimate, because MI is biased in n and a
resample holds ~63% of the diseases. The fix is that the bootstrap now supplies the standard
error only; the diagnosis stays in a comment at the estimator.

### Language as a subgroup axis — what a reader loses by not reading English

**Grade:** measured · **Tool:** [`../../tools/language_coverage.py`](../../tools/language_coverage.py) ·
**Artefact:** `out/rare/language_coverage.json` · **Stage:** `language_coverage`

Not from the theory conversation. HPO made internationalisation the headline of its 2024
release and ships fourteen language profiles; that headline is an aggregate, and this is the
same distrust of an aggregate over unequal subgroups that the rest of the library runs on.
Weighted by the annotations diseases actually carry:

| language | terms | term coverage | annotation-weighted | spread across organ systems |
|---|---:|---:|---:|---:|
| Spanish | 19,356 | 97.6% | 100.0% | 0.1 |
| Chinese | 18,858 | 95.1% | 100.0% | 1.6 |
| French | 13,733 | 69.2% | **98.3%** | 5.2 |
| Czech | 13,603 | 68.6% | 97.4% | 14.7 |
| Japanese | 17,142 | 86.4% | 93.7% | 2.1 |
| Turkish | 12,540 | 63.2% | 92.2% | 32.1 |
| **Portuguese** | 7,158 | 36.1% | **42.9%** | **69.6** |
| German / Italian / Dutch / Twi / Kadazan Dusun / Nyangumarta | ≤ 588 | ≤ 3% | ≤ 9.1% | — |
| Arabic | 0 | 0% | 0% | — |

Two findings. **Translators went for the terms that matter first** — French covers 69.2% of the
vocabulary but 98.3% of the annotation mass, a +29.0-point gain that a progress report counting
terms cannot show. And **this project's own second language is the seventh row**, at 42.9%, with
a 69.6-point spread: 78.4% for the eye, **20.8% for the nervous system** — the system carrying
6,254 of the 9,142 gene-linked diseases. The explorer's language switch is a partial translation
whose gaps are concentrated, and now it is measured rather than assumed.

### Conflict and context — whether the sheaf has anything to describe

**Grade:** measured · **Tools:** [`../../tools/evidence_conflict.py`](../../tools/evidence_conflict.py) (association) and [`../../tools/conflict_decomposition.py`](../../tools/conflict_decomposition.py) (decomposition) ·
**Artefacts:** `out/rare/evidence_conflict.json`, `out/rare/conflict_decomposition.json` · **Stages:** `evidence_conflict`, `conflict_decomposition`

§3 files sheaf theory as the most attractive formalism here and refuses to build it until one
number exists: **do apparent conflicts dissolve when context is conditioned on?** ClinVar can
answer the empirical half. 4,488,337 variants on GRCh38, **165,843** carrying the aggregate
"Conflicting classifications of pathogenicity", each with the conditions it was submitted
against.

Conflict rate by number of distinct conditions, held inside submitter strata because review
depth drives both sides:

| submitters | 0 cond | 1 | 2 | 3 | 4+ | RR 4+/1 |
|---|---:|---:|---:|---:|---:|---:|
| 2 | 7.6% | 13.2% | 11.2% | 28.1% | 17.4% | 1.32 |
| 3 | 13.7% | 21.3% | 22.5% | 18.7% | 22.1% | 1.03 |
| 4-5 | 13.5% | 24.1% | 31.4% | 29.9% | 29.2% | 1.21 |
| 6-9 | 11.4% | 18.1% | 31.3% | 37.2% | 39.1% | **2.16** |
| 10+ | — | 10.2% | 20.1% | 28.3% | 34.5% | **3.39** |
| **marginal** | 8.5% | 15.6% | 18.2% | 28.0% | 33.5% | **2.14** |

**The association survives every stratum** (lowest risk ratio 1.03), so it is not manufactured
by review depth. But the interesting part is the *gradient*: at two or three submitters the
number of conditions barely matters (1.32, 1.03); at ten or more it triples the conflict rate
(3.39). **Where the evidence is thinnest, conflict looks like disagreement. Where it is
thickest, conflict looks like context.**

That is an answer to §3's precondition and it points both ways: a context-aware representation
has genuine work to do, and most of it exactly where the archive is best reviewed.

**And then the file that would settle it was ingested, so it is settled.**
`tools/conflict_decomposition.py` reads ClinVar's 6,428,687 per-submission rows, each carrying
the condition it was made against, and splits every disagreement in two:

| | variants | share of conflicts |
|---|---:|---:|
| in agreement | 347,227 | — |
| **in conflict** | **112,016** | 100% |
| within a condition — a contradiction | 47,984 | **42.8%** |
| across conditions only — context | 64,032 | **57.2%** [56.9, 57.5] |

**The majority of recorded conflict is not disagreement.** In 57.2% of cases every single
condition is internally consistent and the conflict appears only when the conditions are
pooled into one column — nobody is wrong, the archive is answering two questions at once.

**The obvious objection, tested.** A variant called Pathogenic for a named disease and
Uncertain for a panel indication like "Inborn genetic diseases" is arguably one question at two
resolutions rather than two questions. Dropping the three umbrella indications
(362k, 257k and 95k submissions; the next condition down is 36k) takes the share from 57.2% to
**48.6%** [48.2, 48.9]. Granularity is worth about nine points. **Roughly half of the largest
curated disagreement corpus in human genetics is context rather than contradiction, under
either reading.**

**One defect found and kept.** The first version of the decomposition trusted ClinVar's
condition identifier, and ClinVar issues identifiers to its placeholders — `CN169374:not
provided` is a real row. Half the corpus (3,211,994 of 6,428,687 submissions) was being
counted as context. The rule now checks the label before the identifier, and the comment at
`condition_key` says why.

### Knowledge shape — the atypical idea that did not survive contact

**Grade:** measured · **Tool:** [`../../tools/knowledge_shape.py`](../../tools/knowledge_shape.py) ·
**Artefact:** `out/rare/knowledge_shape.json` · **Stage:** `knowledge_shape`

**The idea, and it is the most unusual one in the catalogue.** Not *how much* is known about a
disease but the **shape** of it: a vector over genetics, phenotype, cellular, natural history
and population, and the claim that a disease with a thousand genetics papers and two on
natural history is not well studied — it is bright on one axis and dark on the rest.

**It fails twice, and both failures are worth more than the idea.**

*First:* knowledge is **less** concentrated than independence would give — mean anisotropy
0.2633 against a null of 0.2723, z = **−19.0**. The axes rise and fall together. The intuition
describes a handful of famous diseases, not the catalogue.

*Second, and worse for the statistic:* anisotropy tracks the **number of populated axes**
almost arithmetically — 0.590 at two live axes, 0.346 at three, 0.160 at four, 0.021 at five.
It answers "how broad is the coverage", not "what shape is the knowledge".

**So the question was replaced with the one it should have been:** which axes co-occur?

| pair | Spearman | |
|---|---:|---|
| natural history ~ population | **+0.759** | both counted from Orphanet — an artefact of construction |
| genetics ~ cellular | **+0.640** | the cellular axis is *derived from* the genes — near-tautological |
| phenotype ~ cellular | +0.044 | |
| genetics ~ phenotype | **+0.012** | knowing a disease's genes predicts nothing about how well its phenotype is annotated |
| phenotype ~ population | **−0.332** | and every cross-catalogue pair is negative |

**The residual structure is a registry boundary, not a shape of knowledge.** HPO annotation is
OMIM-heavy; prevalence exists only under ORPHA codes. The negative correlations are that fault
line — already recorded in the visualisation work — reappearing dressed as epistemology.

**What this does to the roadmap.** §5.1 proposes a knowledge-completeness vector as a
buildable item. It stays, with a condition now attached: **any such vector must be shown not to
be measuring provenance before it is shown to anyone.** That condition did not exist an hour
ago and it is the whole return on building this.

---

## 2. Buildable — the data is already on disk

Ordered by what they would cost. Each names the ingested file it would read; that naming is
what makes it buildable rather than an analogy.

| # | construct | what it would measure here | reads |
|---|---|---|---|
| B1 | **Knowledge fingerprint / completeness** | a per-disease vector of maturity by scale (genetics, molecular, cellular, natural history, therapy), and the distance between two diseases *by the shape of what is known* rather than by biology | the existing `out/rare/*.json` layers |
| B2 | **Attention against burden** | papers per disease against prevalence and severity, the "knowledge inequality" axis | `gene2pubmed.gz`, Orphanet prevalence |
| B3 | **Gap taxonomy, typed** | separate *epistemic* (nobody knows), *accessibility* (known, not reachable), *interoperability*, *population*, *model* gaps instead of one "unknown" | `evidence_atlas.json`, `consistency.json` |
| B5 | **Higher-order relations** | replace binary gene→disease edges with hyperedges {variant, gene, cell type, phenotype} and measure how much context a binary projection destroys | HPO + HPA + ClinVar |
| B6 | **Partial information decomposition** | for gene pairs co-annotated to a disease: how much of the phenotype information is redundant, unique, synergistic | the same join as the measured row |
| B7 | **Spectral perturbation signature** | Δλ of the STRING Laplacian when a disease's genes are removed, against a degree-matched null — the network sibling of `twin_propagation` | `9606.protein.links.v12.0.txt.gz` |
| B8 | **Persistent homology of the phenotype space** | whether the disease cloud has structure beyond clusters — loops and voids that survive scale | HPO annotation vectors |
| B10 | **Knowledge time** | rebuild the same measurement at 1995, 2005, 2026 and watch the graph appear — evidence versioning by publication date | `gene2pubmed.gz` dates, HPOA biocuration dates |
| B11 | **Model genealogy as a typed artefact** | every derived artefact carrying `derivedFrom` / `calibratedWith`, so nothing floats free | the pipeline's own stage graph |

**B1, B3 and B10 are the three the explorer would visibly gain from**, because each of them
produces a per-disease number the atlas can already render.

---

## 3. Analogy — kept, named, and not built

Nothing here has an estimator this project can run today. They are recorded so they are not
re-proposed as if new, and because several are genuinely the right frame if the data ever
arrives. The blocker is stated for each; a blocker that dissolves promotes the row to §2.

**Dynamics.** Disease as attractor and bifurcation; Waddington landscape `Ẋ = −∇V + η`;
catastrophe theory; critical slowing down and dynamic network biomarkers; Koopman operators
with every dataset as an observable `gᵢ(X)` of a hidden state, and `Kᵢ = K₀ + ΔKᵢ` to share
dynamics across patients when n is tiny; stochastic differential equations, jump processes,
piecewise-deterministic Markov processes, hybrid systems.
*Blocker:* all of them need **longitudinal** patient data. This project has cross-sectional
catalogues and one phenopacket corpus with no time axis. Without repeated observations there
is no trajectory, and a fitted attractor would be a drawing.

**Geometry.** State-dependent Riemannian metric; Fisher information geometry; geodesics as
minimum-cost intervention; **Finsler** asymmetry (`d(disease→healthy) ≫ d(healthy→disease)`);
optimal transport and Gromov-Wasserstein for aligning modalities.
*Blocker:* needs per-patient molecular measurements, not per-disease annotations. The
directional measurement in §1 is the one checkable shadow of this family.

**Evidence.** **Sheaf theory** — local sections over contexts, and cohomological obstruction as
the signature of a conflict that is genuinely global rather than contextual. This is the most
attractive entry in the file and the one most likely to be misused: a `H¹ ≠ 0` printed over a
catalogue whose contexts are unevenly curated would measure the curation. B4 is the honest
first step, and a sheaf is only worth building after B4 says how many conflicts survive
conditioning.

**Composition.** Category theory for model interfaces; an algebra of models
`M_patient = M_organ ∘ M_tissue ∘ M_cell`; the "Frankenstein model problem" — submodels with
incompatible units and time scales composed because the diagram looked good.
*Blocker:* there are no executable models here yet to compose. Physiome/CellML indexing would
be the first step, and it is a download this project has not made.

**Causality and control.** Structural causal models and `do`-calculus; controllability
(minimum intervention set); observability (minimum diagnostic sensor set); optimal control.
*Blocker:* a knowledge graph is not a causal graph, and this repository's own Stage 10 exists
to say so. Nothing here should be labelled causal from annotation data.

**Thermodynamics.** Entropy production `σ = ΣJᵢFᵢ`; thermodynamic uncertainty relations;
flux balance analysis on genome-scale metabolic models.
*Blocker:* FBA is the closest to buildable — the models are public — but it needs a metabolic
reconstruction this project has not ingested, so it stays here until it does.

**Emergence and memory.** Causal emergence and effective information (§1 states plainly what
the measured row is *not*); **Mori–Zwanzig** — the result that coarse-graining generates memory
and noise rather than another clean equation, which is the strongest available argument that
memory in a multiscale model is derived rather than invented.
*Blocker:* both are defined over dynamics. §1 is their observational shadow, and the distance
between the two is exactly the honesty this file is enforcing.

**Viability and resilience.** The viability kernel — the states from which some trajectory
stays functional — with severity read as `Volume(Viab_D)` or distance to its boundary; health
as *capacity to remain in a functional region under perturbation* rather than as normality.
*Blocker:* dynamics again. Recorded here because it is the most promising reframing of
"severity" in the whole catalogue, and because the reframing survives even if the mathematics
never gets built.

**Gauge invariance.** Batch effect restated as a symmetry question: which transformations
belong to the group of the observation and which change the biology, `F(gX) = F(X)`.
*Blocker:* needs multi-platform measurements of the same tissue.

**Explicitly rejected, not merely unbuilt.** The **free energy principle** as a foundation.
Its components (variational inference, Markov blankets) are usable where they earn their place;
the universal reading is contested in the literature and would import a controversy this
project has no way to settle. The source conversation reached the same conclusion, and it is
recorded here so the question is closed rather than reopened each time.

---

## 4. The ten research problems, and which are open here

Named in the source conversation as research rather than features. Marked against §§1-3.

| # | problem | status here |
|---|---|---|
| 1 | optimal causal scale `s* = argmax EI(s)` | §1 measures its observational shadow; the causal form is analogy |
| 2 | coarse-graining with minimal causal loss | **partly measured** — §1, without the causal half |
| 3 | disease as deformation of a dynamic geometry | analogy |
| 4 | patient viability landscape | analogy |
| 5 | asymmetric distance disease ↔ health | **measured** in its information-theoretic form: ratio 2.91 at gene scale, 1.02 at pathway scale |
| 6 | evidence sheaf: real conflict vs different context | **measured, and decomposed**: 57.2% of variant-level conflicts are across-condition only (48.6% with panel indications removed). About half of recorded disagreement is context |
| 7 | Mori–Zwanzig: memory created by scale reduction | analogy |
| 8 | higher-order causal networks (hypergraph + PID) | **buildable** as B5 + B6 |
| 9 | shared multiscale Koopman across patients | analogy — needs longitudinal data |
| 10 | cross-scale invariants, molecular to phenotype | **measured** — retention spans 5.6-fold across organ systems; pathway-shaped systems keep their signal, structural ones do not |

Three of ten are now measured and two more are buildable from files already on disk. That is
the queue, and §5 below is what the three of them add up to.

---

## 5. What three measurements add up to

Three constructs were promoted. They were chosen for different reasons — one from the theory
list, one from a data source nobody had classed as evidence, one as the precondition for the
formalism this file most wanted to build — and they converge on a single statement.

**Every one of them found that the aggregate was hiding a gradient, and that the gradient was
the finding.**

| measurement | what the aggregate said | what the gradient said |
|---|---|---|
| cross-scale information | a coarse-graining onto pathways keeps 22% of the information | retention runs from **0.39** (neoplasm, metabolism) to **0.07** (cardiovascular) — 5.6-fold. Pathways hold what is pathway-shaped. **There is no single right scale for this atlas.** |
| language coverage | HPO is available in thirteen languages | coverage runs from 100% to **zero**, and this project's own second language sits at 42.9% with a **69.6-point** spread across organ systems — worst where rare disease is heaviest |
| conflict and context | 165,843 variants carry conflicting classifications | **57.2%** of them are not conflicts at all — every condition internally consistent, disagreement only on pooling. 48.6% after removing panel indications. About half |

This is the same shape three times, and it is the shape this library was built for. Stage 1
exists because the maximum of many noisy estimates is biased by how many estimates there were;
Stage 3 exists because a confound must be measured rather than disclaimed. Both are statements
about **populations that a single number cannot represent**. The three results above say the
atlas has the same problem in three more places, and that in each of them the pooled figure is
not merely imprecise — it points at the wrong conclusion:

* "22% survives" reads as *lossy but uniform*. It is not; it is adequate for some biology and
  useless for other biology, and which is which is legible.
* "available in Portuguese" reads as *translated*. It is not; it is 42.9% translated with the
  holes concentrated in the nervous system.
* "165,843 conflicts" reads as *a field that disagrees with itself*. About half of it is a
  field answering different questions and recording the answers in one column.

**The methodological conclusion**, which is the one worth carrying out of this file: the unit
of honesty in this project is not the interval, it is **the subgroup**. An interval says how
sure we are of a number; a subgroup profile says whether the number refers to anything. Every
headline this atlas publishes should be asked, in order: *what is the population, does the
figure represent it, and where is the gradient?* Three for three, there was one.

**The formal conclusion is narrower and less comfortable.** Of roughly ninety formalisms
catalogued, three are measured, nine are buildable, and the rest are held back by exactly two
blockers (§14 of the deep file): no longitudinal data, and no per-patient molecular
measurement. Neither is removed by choosing a better formalism; both are data-acquisition
problems with known solutions.

**The third blocker dissolved during this pass, and how it dissolved is the lesson.** "Context
is too shallow to condition on" was true of the file being read and false of the archive: the
context was in `submission_summary.txt.gz` the whole time, 387 MB behind a URL, and reading it
turned a 2.14× association into a decomposition with an interval. Twice now — language, then
context — the blocker was not missing data but a missing question. **Before accepting that a
measurement cannot be made, name the file that would make it.** Both times the file existed.

**And one result cost nothing.** The language measurement had no blocker at all: the data was
named, found, ingested and measured in an hour, and it changed what the project ships. It was
not on the theory list. Eleven mathematical families are waiting on cohorts that do not exist;
one axis was waiting only for somebody to decide it was an axis. That asymmetry is worth
remembering the next time this catalogue is read for what to build next.

---

## 6. How to use this file


1. To propose something new, add a row with its grade and **the file it would read**. If you
   cannot name the file, the grade is `analogy` (ADR 0007).
2. To promote a row, write the tool, register the stage, and move the row into §1 with its
   number, its null and its interval.
3. To cite any of this in the manuscript, it must be in §1. There is no second route.

Related: [`standards.md`](standards.md) for the conformance targets this all has to live
inside; [`rare-layers.md`](rare-layers.md) for how the *artefacts* are graded (measured,
derived, authored) — this file grades the *ideas*, and the two vocabularies are deliberately
distinct.
