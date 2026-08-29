# The multiscale formalism — what each construct actually says, and what it would take to run it here

> **Role:** explanation. The mathematical foundation behind
> [`../theory-atlas.md`](../theory-atlas.md): for each family, the formal object, the
> estimator it would reduce to on *this* project's data, the identification problem that
> could make it wrong, and what would falsify it.
> **Last revised:** 2026-08-29 · **State:** foundation written for eleven families plus a
> twelfth (§13b, language) that is not a formalism and earns its place by having a result;
> three are measured, and every other section ends with the blocker that keeps it out of §1 of the atlas.
>
> **Verification marks.** `[XR]` = title, authors, venue, year and DOI resolved through the
> Crossref API on 2026-08-29 — the same standard `../../lineage.md` §11 set. `[NCBI]` = resolved through NCBI
> E-utilities after Crossref failed on it. `[REC]` = recalled from working knowledge and
> **not resolved**; Crossref returned no confident match, usually
> because the work is a preprint, a conference volume or a database issue. A `[REC]` entry may
> not be cited in the manuscript until it is resolved. No DOI on this page was typed from
> memory: an entry either carries the one Crossref returned or carries none.
>
> Companion: [`selection-bias.md`](selection-bias.md), which did this for the library's core
> claim and concluded the diagnosis was not novel. Expect the same verdict here for most
> families — the value is in knowing *which* recombination is ours.

---

## 0. The one thing this whole file is arguing against

There is a standard move in multiscale biology: draw the ladder — variant, protein, pathway,
cell, tissue, organ, phenotype — assert that a disease is a perturbation propagating up it,
and never measure the rungs. The ladder is then a diagram, not a model, and its main effect is
to make an under-determined problem look solved.

Every section below is written so that the rung it describes can **fail**. Where the failure
condition cannot be stated with data this project has, the section says so and the construct
stays out.

---

## 1. Coarse-graining and information — the measured family

### 1.1 The formal object

Renormalisation asks what a description keeps when its resolution drops. Given a micro state
`X` and a coarse-graining `R: X_micro → X_macro`, the classical programme studies the flow of
`R` under iteration and its fixed points `R(X*) = X*`. `[XR]` Kadanoff's block-spin argument
and Wilson's renormalisation group are the anchors — Kadanoff, *Scaling laws for Ising models
near Tc*, reprinted, DOI `10.1142/9789812798763_0011`; Wilson, *Renormalization Group and
Critical Phenomena I*, Phys. Rev. B 4:3174, 1971, DOI `10.1103/physrevb.4.3174`.

The information-theoretic cousin asks not for a fixed point but for a *sufficient* summary.
The information bottleneck seeks `Z` minimising `I(X;Z) − β I(Z;Y)`: compress `X`, keep what
it says about `Y`. `[REC]` Tishby, Pereira & Bialek, *The information bottleneck method*, 37th
Allerton Conference, 1999 — **unresolved in Crossref**; it circulates as arXiv `physics/0004057`.
`[XR]` The estimator literature that matters for the *bias* of any such measurement is
Paninski, *Estimation of entropy and mutual information*, Neural Computation 15:1191, 2003,
DOI `10.1162/089976603321780272`, and Kraskov, Stögbauer & Grassberger, *Estimating mutual
information*, Phys. Rev. E 69:066138, 2004, DOI `10.1103/physreve.69.066138`.

The stronger claim in the neighbourhood is that a coarse description can carry *more* causal
power than the fine one. `[XR]` Hoel, Albantakis & Tononi, *Quantifying causal emergence shows
that macro can beat micro*, PNAS 110:19790, 2013, DOI `10.1073/pnas.1314922110`. Effective
information there is computed over an *intervention distribution* — `EI = I(X;Y)` when the
inputs are set by `do(·)` at maximum entropy — which is precisely what a catalogue cannot give.

### 1.2 What it reduces to here

`tools/scale_information.py`, stage `scale_information`, artefact
`out/rare/scale_information.json`. `F` is the disease's feature set at a scale, `S` its organ
systems, each of 9,142 diseases weighted 1. Reported quantity is the **excess** `I − I_null`
over 25 permutations of the disease→system assignment.

| scale | alphabet | excess (bits) | 95% CI | kept vs gene | compression |
|---|---:|---:|---|---:|---:|
| gene | 5,260 | 0.2791 | [0.2583, 0.3000] | 1.00 | 1× |
| cell type | 154 | 0.0877 | [0.0806, 0.0947] | 0.31 | 34× |
| pathway | 29 | 0.0611 | [0.0544, 0.0678] | 0.22 | 181× |

### 1.3 Three things the pooled table does not say, and now do

**(a) The loss is not uniform — it is concentrated.** One-vs-rest per organ system, admitted
only where the gene-scale excess clears 5 null SD (20 of 23 systems qualify):

| organ system | n | pathway retention | cell-type retention |
|---|---:|---:|---:|
| Abnormality of the breast | 403 | **0.39** | 0.18 |
| Neoplasm | 951 | **0.38** | 0.22 |
| Abnormal cellular phenotype | 829 | 0.28 | 0.30 |
| Abnormality of metabolism/homeostasis | 3,503 | 0.27 | 0.22 |
| Abnormality of blood and blood-forming tissues | 1,772 | 0.19 | 0.28 |
| … | | | |
| Abnormality of the eye | 4,462 | 0.08 | 0.12 |
| Abnormality of limbs | 3,644 | 0.08 | 0.12 |
| Abnormality of the cardiovascular system | 3,645 | **0.07** | 0.12 |

**A 5.6-fold spread, and it is legible.** Pathways retain most for neoplasm, metabolism and
cellular phenotype — the systems whose diseases *are* pathway-shaped. They retain least for
eye, limb and cardiovascular abnormality, which are structural and developmental: what is
wrong is where and when a structure formed, and a top-level pathway label has no vocabulary
for that. Cell types invert the ranking for exactly those systems (cardiovascular 0.12 against
pathway 0.07; blood 0.28 against 0.19), which is what a spatial alphabet should do.

This is the observational form of the atlas's research problem 10, *cross-scale invariants*.
It is also a usable engineering result: **there is no single right coarse-graining for the
atlas**, and a per-system choice of scale is defensible where a global one is not.

**(b) The relation is directional.** `I` is symmetric; the two uncertainty coefficients are
not. `U(S|F) = I/H(S)` is how much of the organ system the features pin down; `U(F|S) = I/H(F)`
is the reverse.

| scale | U(S\|F) | U(F\|S) | ratio |
|---|---:|---:|---:|
| gene | 0.3091 | 0.1062 | **2.91** |
| cell type | 0.0255 | 0.0155 | 1.64 |
| pathway | 0.0164 | 0.0161 | 1.02 |

Genes predict organ systems nearly three times better than organ systems predict genes — the
familiar clinical asymmetry (many genes converge on one phenotype; a phenotype rarely names its
gene), now with a number. And the asymmetry **collapses under coarse-graining**: at pathway
scale the ratio is 1.02, statistically a symmetric relation. Compression destroyed the
direction, not just the magnitude. That is the honest, information-theoretic shadow of the
Finsler intuition in `../theory-atlas.md` (`d(A→B) ≠ d(B→A)`) — and it is worth stating that
what was measured is *conditional-entropy asymmetry*, which is not a metric asymmetry and does
not license the word "Finsler" anywhere in a figure caption.

**(c) The estimator's own failure is on the record.** The first bootstrap resampled diseases
with replacement and produced a gene-scale point estimate of 0.2791 against a percentile
interval of [0.1745, 0.2163]. Mutual information is biased in `n`; a resample holds ~63% of the
diseases; the interval was displaced. This is Paninski's bias, met in the wild. The interval is
now point ± 1.96 bootstrap SE and the diagnosis is kept in a comment at the estimator.

### 1.4 What would falsify it

A coarse-graining that preserves *more* excess information than the gene scale would break the
framing (nothing here can gain information; a positive result would indicate a leak between the
feature construction and the label). Retention that is flat across organ systems would kill
finding (a). An asymmetry ratio near 1 at gene scale would kill finding (b).

### 1.5 What it is still not

Not effective information, not causal emergence, not a renormalisation flow. There is no
intervention, no dynamics, no scale parameter, no fixed point. ADR 0007 exists because the
distance between §1.2 and Hoel *et al.* is one word in a caption.

---

## 2. Propagation on a network — the partly built family

### 2.1 The formal object

A perturbation on a graph with adjacency `A` and Laplacian `L = D − A`. Continuous:
`dx/dt = −Lx + F(x)`. Discrete and stationary: random walk with restart,
`p = (1−α) s + α W p`, whose fixed point is the network-propagation kernel. Spectral form: a
disease alters not only edges but the modal structure, `L_D = L_H + ΔL`, and
`Δλᵢ = λᵢ(L_D) − λᵢ(L_H)` is a candidate signature.

`[XR]` Menche *et al.*, *Uncovering disease-disease relationships through the incomplete
interactome*, Science 347:1257601, 2015, DOI `10.1126/science.1257601` — the disease-module
framing this project's interactome work already answers to. `[XR]` Cowen, Ideker, Raphael &
Sharan, *Network propagation: a universal amplifier of genetic associations*, Nature Reviews
Genetics 18:551, 2017, DOI `10.1038/nrg.2017.38` — the method review, and the source of the
warning that propagation finds hubs. `[XR]` Goh *et al.*, *The human disease network*, PNAS
104:8685, 2007, DOI `10.1073/pnas.0701361104`. `[XR]` The graph itself: Szklarczyk *et al.*,
*STRING v11*, Nucleic Acids Res. 47:D607, 2019, DOI `10.1093/nar/gky1131`.

### 2.2 Status here

**Built**, as `tools/twin_propagation.py`: random walk with restart on STRING ≥ 700, every
value reported as a z against degree-stratified null seed sets. The spectral half
(`Δλᵢ`) is **buildable** and unbuilt — it needs no new data, only the eigendecomposition of a
graph already loaded.

### 2.3 The identification problem

An undirected co-functional graph has no causal direction and no time. A propagation is a
*reachability* statement wearing a probability, and the degree-matched null is what keeps it
from being a measurement of the hubs. Any spectral extension inherits both limits: a shifted
eigenvalue says the modal structure moved, not that the disease moved it.

---

## 3. Higher-order structure — hypergraphs, simplicial complexes, Hodge

### 3.1 The formal object

A binary edge cannot hold "X activates Y **in hepatocytes, at embryonic stage, under low
compensator expression**". A hyperedge `e ⊆ V` can. Simplicial complexes add the closure
condition that makes homology available, and the Hodge decomposition splits an edge flow into
`f = ∇φ + curl*ψ + h` — gradient, circulation, and a harmonic part indexing global cycles.

`[XR]` Bick, Gross, Harrington & Schaub, *What are higher-order networks?*, SIAM Review 65:686,
2023, DOI `10.1137/21m1414024`. `[XR]` Salnikov, Cassese & Lambiotte, *Simplicial complexes and
complex systems*, Eur. J. Phys. 40:014001, 2018, DOI `10.1088/1361-6404/aae790`. `[XR]` Lim,
*Hodge Laplacians on graphs*, SIAM Review 62:685, 2020, DOI `10.1137/18m1223101`.

### 3.2 What it reduces to here

**Buildable, and cheap.** The atlas already stores (variant, gene, cell type, phenotype)
tuples; the measurement is: how much information does binarisation destroy? Take the tuple set
as hyperedges, project to all pairwise edges, and compute the same excess-MI the measured
family uses, on both. The difference is the cost of the projection — the identical estimator,
pointed at structure instead of at scale.

### 3.3 The identification problem

Context in this catalogue is unevenly recorded. A hyperedge that looks richer may simply come
from a better-curated disease, so the measurement must be conditioned on curation depth or it
reproduces `tools/atlas_bias.py`'s +0.2357 ascertainment bias in a new coordinate system.

---

## 4. Evidence, context and conflict — the sheaf family

### 4.1 The formal object

A cellular sheaf `F` assigns data `F(U)` to each open set / cell and restriction maps
`ρ_{UV}` to inclusions. Local sections `sᵢ ∈ F(Uᵢ)` agreeing on overlaps glue to a global
section — or fail to, and the obstruction lives in `H¹`. The claim on this project: "Paper A
says X in hepatocytes, Paper B says not-X in neurons" is not a contradiction but two local
sections over different contexts, and a naïve knowledge graph destroys the distinction.

`[XR]` Hansen & Ghrist, *Toward a spectral theory of cellular sheaves*, J. Appl. Comput.
Topology 3:315, 2019, DOI `10.1007/s41468-019-00038-7`. `[XR]` Robinson, *Understanding networks
and their behaviors using sheaf theory*, IEEE GlobalSIP 2013, DOI
`10.1109/globalsip.2013.6737040`. `[XR]` Kvinge, Jefferson, Joslyn & Purvine, *Sheaves as a
framework for understanding and interpreting model fit*, ICCVW 2021, DOI
`10.1109/iccvw54120.2021.00469`.

### 4.2 The honest first step, which is not a sheaf — and its answer

Count how many apparent conflicts **travel with context**. If the answer is "nearly all", the
sheaf is describing a real structure and is worth building. If "nearly none", the conflicts are
genuinely global and `H¹` would be an expensive way to say what a contingency table said.

**That number now exists, in its association form.** `tools/evidence_conflict.py` asked it of
ClinVar: 4,488,337 variants on GRCh38, 165,843 carrying "Conflicting classifications of
pathogenicity". Conflict rate rises **2.14×** from one condition to four or more, and the rise
survives inside every submitter stratum, so review depth does not manufacture it. The gradient
is the result: at two or three submitters the number of conditions barely matters (risk ratio
1.32, 1.03); at ten or more it triples the rate (**3.39**). Where evidence is thin, conflict
looks like disagreement; where it is thick, conflict looks like context.

**And then the file was read.** `submission_summary.txt.gz` — 6,428,687 rows, each a
submitter's classification beside the condition it was made against — is ingested, and
`tools/conflict_decomposition.py` does the split the aggregate could not:

    variants with >= 2 classifiable submissions   459,243
      in agreement                                347,227
      in conflict                                 112,016
        within a condition   (a contradiction)     47,984   42.8%
        across conditions only   (context)         64,032   57.2%  [56.9, 57.5]

**57.2% of recorded conflict is not disagreement**: every condition internally consistent, the
conflict appearing only on pooling. Removing the three umbrella indications ("Inborn genetic
diseases", "Hereditary cancer-predisposing syndrome", "Cardiovascular phenotype") takes it to
**48.6%** [48.2, 48.9] — granularity is worth nine points and about half the corpus is context
either way.

**So the precondition is met and the sheaf has a real object.** What it would describe is not a
metaphor: roughly half of a 112,016-variant disagreement corpus consists of locally consistent
sections that fail to glue only because the pooling operation throws the context away. That is
the situation sheaves were invented for. Whether cohomology *earns its cost* against a
contingency table on `(variant, condition)` is now an engineering question rather than an open
one, and it is the right next question.

### 4.3 The identification problem

The contexts in `phenotype.hpoa` are shallow and inconsistently populated: `aspect`, `evidence`
and `frequency` are present, cell type and developmental stage generally are not. A sheaf over
a context space that is itself mostly missing would compute the missingness.

---

## 5. Dynamics — attractors, landscapes, transitions, Koopman

### 5.1 The formal objects

`dX/dt = F(X, θ, u, t)`, with health and disease as regions or attractors rather than points; a
variant moves `θ` and can cross a bifurcation. The landscape form is `Ẋ = −∇V(X) + η`, with the
mutation reshaping `V` rather than merely displacing `X`. Approaching a transition, relaxation
slows and variance and autocorrelation rise — early-warning signals. Koopman replaces the
non-linear state map with a *linear* operator on observables, `Kg(x) = g(F(x))`, which is
exactly the right shape for a project where every dataset is an observable `gᵢ(X)` of a state
nobody sees.

`[XR]` Wang, Zhang, Xu & Wang, *Quantifying the Waddington landscape and biological paths for
development and differentiation*, PNAS 108:8257, 2011, DOI `10.1073/pnas.1017017108`.
`[XR]` Waddington, *The Strategy of the Genes*, reissue, DOI `10.4324/9781315765471`.
`[XR]` Scheffer *et al.*, *Early-warning signals for critical transitions*, Nature 461:53,
2009, DOI `10.1038/nature08227`. `[XR]` Chen, Liu, Liu & Aihara, *Detecting early-warning
signals for sudden deterioration of complex diseases by dynamical network biomarkers*, Sci. Rep.
2:342, 2012, DOI `10.1038/srep00342`. `[XR]` Williams, Kevrekidis & Rowley, *A data-driven
approximation of the Koopman operator*, J. Nonlinear Sci. 25:1307, 2015, DOI
`10.1007/s00332-015-9258-5`. `[XR]` Brunton *et al.*, *Chaos as an intermittently forced linear
system*, Nat. Commun. 8:19, 2017, DOI `10.1038/s41467-017-00030-8`. `[XR]` Gross & Blasius,
*Adaptive coevolutionary networks: a review*, J. R. Soc. Interface 5:259, 2007, DOI
`10.1098/rsif.2007.1229` — the state↔topology feedback that makes `Γ` dynamic.

### 5.2 The blocker, stated once for the whole family

**Every construct here needs repeated observations of the same unit.** This project holds
cross-sectional catalogues and a phenopacket corpus with no time axis. A fitted attractor, a
reconstructed landscape or an estimated Koopman operator would each be a drawing whose
parameters came from the fitting procedure and not from the data. The `n = 5` ultra-rare case
makes it worse, not better: `K_i = K_0 + ΔK_i` is a good idea precisely because `n` is small,
and it still needs a trajectory per patient.

**What would unblock it:** a longitudinal registry with ≥ 3 timepoints per patient. Naming that
requirement is the useful output of this section.

---

## 6. Geometry and transport

`[XR]` Mémoli, *Gromov-Wasserstein distances and the metric approach to object matching*,
Found. Comput. Math. 11:417, 2011, DOI `10.1007/s10208-011-9093-5` — comparing spaces that share
no coordinates, which is the transcriptome↔proteome problem stated properly. `[XR]` Schiebinger
*et al.*, *Optimal-transport analysis of single-cell gene expression identifies developmental
trajectories in reprogramming*, Cell 176:928, 2019, DOI `10.1016/j.cell.2019.02.026`.
`[XR]` Bunne, Schiebinger, Krause, Regev *et al.*, *Optimal transport for single-cell and
spatial omics*, Nat. Rev. Methods Primers 4, 2024, DOI `10.1038/s43586-024-00334-2`.

**Blocker:** all of it operates on per-cell or per-patient measurement distributions. This
project's unit is a disease annotation. §1.3(b) is the one shadow of this family that the
current data can cast.

---

## 7. Topology of data

`[XR]` Nicolau, Levine & Carlsson, *Topology based data analysis identifies a subgroup of breast
cancers with a unique mutational profile and excellent survival*, PNAS 108:7265, 2011, DOI
`10.1073/pnas.1102826108` — the existence proof that TDA finds a real clinical subgroup.
`[XR]` Chan, Carlsson & Rabadan, *Topology of viral evolution*, PNAS 110:18566, 2013, DOI
`10.1073/pnas.1313480110`. `[XR]` Ghrist, *Barcodes: the persistent topology of data*, Bull.
AMS 45:61, 2007, DOI `10.1090/s0273-0979-07-01191-3`. `[XR]` Edelsbrunner & Harer, *Persistent
homology — a survey*, Contemp. Math. 453, 2008, DOI `10.1090/conm/453/08802`.

**Buildable** (atlas B8) on HPO annotation vectors. **The trap:** persistent homology on a
binary annotation matrix whose density varies 100-fold across diseases will find the curation
gradient as its most persistent feature. The control is the same permutation null used in §1,
applied to barcodes rather than to bits.

---

## 8. Causality, control, observability

`[XR]` Pearl, *Causal inference in statistics: an overview*, Statistics Surveys 3:96, 2009,
DOI `10.1214/09-ss057`. `[XR]` Liu, Slotine & Barabási, *Controllability of complex networks*,
Nature 473:167, 2011, DOI `10.1038/nature10011`, and *Observability of complex systems*, PNAS
110:2460, 2013, DOI `10.1073/pnas.1215508110`. The observability result is the one with the
sharpest rare-disease reading: the minimum sensor set that reconstructs an internal state is
the mathematical form of *which tests would actually be worth running*.

**Blocker:** a knowledge graph is not a causal graph, and the controllability results assume a
directed dynamical system with known `A` and `B`. This project has an undirected association
graph. Stage 10 of the method exists to make exactly this refusal.

---

## 9. Thermodynamics and constraint-based metabolism

`[XR]` Seifert, *Stochastic thermodynamics, fluctuation theorems and molecular machines*, Rep.
Prog. Phys. 75:126001, 2012, DOI `10.1088/0034-4885/75/12/126001`. `[XR]` Barato & Seifert,
*Thermodynamic uncertainty relation for biomolecular processes*, PRL 114:158101, 2015, DOI
`10.1103/physrevlett.114.158101` — precision costs dissipation, which is a genuine physical
bound rather than an analogy. `[XR]` Orth, Thiele & Palsson, *What is flux balance analysis?*,
Nat. Biotechnol. 28:245, 2010, DOI `10.1038/nbt.1614`.

**FBA is the nearest thing to buildable in this section** — `Sv = 0`, `l ≤ v ≤ u`, `max cᵀv`,
with public genome-scale reconstructions — and it is still out, because no metabolic
reconstruction is ingested. That is a download, not a research problem, and it is the one item
in this file that could move to `buildable` by a `tools/ingest.py` entry alone.

---

## 10. Memory from coarse-graining — Mori–Zwanzig

`[XR]` Zwanzig, *Memory effects in irreversible thermodynamics*, Phys. Rev. 124:983, 1961, DOI
`10.1103/physrev.124.983`. `[XR]` Mori, *Transport, collective motion, and Brownian motion*,
Prog. Theor. Phys. 33:423, 1965, DOI `10.1143/ptp.33.423`.

Projecting a high-dimensional dynamics onto a few variables does not yield another clean ODE.
It yields `d/dt = Markovian + memory kernel + noise`. **This is the strongest available
argument that memory in a multiscale biological model is *derived* rather than invented** —
if you coarse-grain, memory appears whether you wanted it or not.

It also sharpens §1: this project measured what a coarse-graining costs *in information*. Mori
and Zwanzig say a coarse-graining also costs a *memory term*, and that term is invisible to a
static measurement. The gap between those two statements is the honest size of the distance
between this atlas and a dynamical one.

**Blocker:** dynamics. Same as §5.

---

## 11. Viability and resilience — the reframing worth keeping even unbuilt

`[XR]` Aubin, *Viability Theory*, Birkhäuser, DOI `10.1007/978-0-8176-4910-4`.

Given `ẋ = f(x,u)` and a constraint set `K`, the viability kernel `Viab(K)` is the set of states
from which *some* control keeps the trajectory inside `K` forever. Read clinically: health is
not a normal value, it is **the capacity to stay in a functional region under perturbation**,
and severity is distance to the boundary of that region or the shrinkage of the kernel itself,
`Viab_D ⊂ Viab_H`.

**Blocker:** dynamics again, and a constraint set nobody has written down. Kept in full because
the *reframing* survives even if the mathematics is never built — it is a better definition of
severity than any this project currently publishes, and it costs nothing to hold.

---

## 12. Explicitly closed: the free energy principle as a foundation

`[XR]` Friston, *The free-energy principle: a unified brain theory?*, Nat. Rev. Neurosci.
11:127, 2010, DOI `10.1038/nrn2787`. `[XR]` Bruineberg, Dołęga, Dewhurst & Baltieri, *The
Emperor's New Markov Blankets*, Behav. Brain Sci., 2021, DOI `10.1017/s0140525x21002351`, and
the reply, DOI `10.1017/s0140525x22000656`.

The components — variational inference, Bayesian model comparison, Markov blankets as interface
variables between scales — are usable where they earn their place. The universal reading is
contested in print by the second reference, and adopting it as a foundation would import a
dispute this project has no instrument to settle. **Closed, not open**: this section exists so
the question is not reopened each time the idea is attractive again.

---

## 13. Standards and catalogues the atlas actually stands on

Not theory, but they belong in the same verified list because the measured result reads them.

`[XR]` Jacobsen *et al.*, *The GA4GH Phenopacket schema defines a computable representation of
clinical data*, Nat. Biotechnol. 40:817, 2022, DOI `10.1038/s41587-022-01357-4`.
`[XR]` Putman *et al.*, *The Monarch Initiative in 2024*, Nucleic Acids Res., DOI
`10.1093/nar/gkad1082`. `[XR]` Buniello *et al.*, *Open Targets Platform: facilitating
therapeutic hypotheses building in drug discovery*, Nucleic Acids Res., 2024, DOI
`10.1093/nar/gkae1128`. `[XR]` Milacic *et al.*, *The Reactome Pathway Knowledgebase 2024*,
Nucleic Acids Res., DOI `10.1093/nar/gkad1025` — read directly by §1. `[XR]` Rath *et al.*,
*Representation of rare diseases in health information systems: the Orphanet approach*, Human
Mutation 33:803, 2012, DOI `10.1002/humu.22078`. `[XR]` Landrum *et al.*, *ClinVar: improvements
to accessing data*, Nucleic Acids Res., 2019, DOI `10.1093/nar/gkz972`.

**Both were resolved on the same day this file was written**, and the route is worth
recording because Crossref failed on both. `[XR]` Karlsson *et al.*, *A single-cell type
transcriptomics map of human tissues*, Science Advances 7:eabh2169, 2021, DOI
`10.1126/sciadv.abh2169` — Crossref's top hit had been a different journal's paper of nearly
the same title, which is exactly the confusion the mark exists to flag; a query naming three
authors reached the right one. `[NCBI]` Gargano *et al.*, *The Human Phenotype Ontology in
2024: phenotypes around the world*, Nucleic Acids Res. 52:D1333-D1346, DOI
`10.1093/nar/gkad1005` — Crossref's bibliographic search returned unrelated matter three
times; NCBI E-utilities on PMID 37953324 returned it immediately. **A failed Crossref lookup
is not evidence that a work does not exist**, and treating it as such would have left two
papers this project directly reads uncited. Second route, then mark which one answered.

---

## 13b. Language, which is not a formalism and belongs here anyway

The one section that is not a formalism at all, and the only one in this file whose result
changes what the project ships.

Two principles, neither exotic. **Normalise in the ontology, not in the translation** —
translate the strings and the concepts stay untranslated, so a coverage question has to be asked
against HPO ids rather than against display text. And **a defect confined to one subgroup is
divided by the number of subgroups in any pooled figure** — the same argument Stage 3 of this
library makes about confounds, pointed at language.

`tools/language_coverage.py` asks both against HPO's thirteen language profiles, weighted by the
annotations diseases actually carry. Portuguese — this project's own second language — reads
**42.9%** of the annotated rare-disease phenotype, with a **69.6-point spread** across organ
systems: 78.4% for the eye, 20.8% for the nervous system, which carries 6,254 of the 9,142
gene-linked diseases. Full numbers in [`../theory-atlas.md`](../theory-atlas.md) §1.

`[NCBI]` Gargano *et al.* 2024 (above) is the published anchor. `[XR]` Ninomiya, Takatsuki &
Kushida, *Choosing preferable labels for the Japanese translation of the Human Phenotype
Ontology*, Genomics & Informatics, 2020, DOI `10.5808/gi.2020.18.2.e23` — a translated label
is a curatorial decision, not a lookup. `[XR]` Wołk & Wołk, *Machine enhanced translation of
the Human Phenotype Ontology project*, Procedia Computer Science, 2017, DOI
`10.1016/j.procs.2017.11.003`. `[XR]` Jain, Rollins & Jain, *Access to COVID-19 clinical
trials by English and non-English speakers*, Clin. Infect. Dis., 2020, DOI
`10.1093/cid/ciaa493` — independent evidence that a language barrier is an access barrier, and
the reason language sits beside ancestry and geography here rather than under presentation.

**This is the one family in the file with no blocker.** The data was on disk within an hour of
being named, which is worth noticing next to eleven families waiting on longitudinal cohorts.

---

## 14. What this file concludes

Eleven families, one measured. The blockers are not eleven different problems — they are
**three**:

1. **No longitudinal data.** Kills §5 (dynamics, Koopman, early warning), §10 (memory), §11
   (viability), and most of §6. Unblocked by a registry with ≥ 3 timepoints per patient.
2. **No per-patient molecular measurement.** Kills the geometry of §6 and the sensor-set
   reading of §8. Unblocked by patient-level omics, which raises access questions this project
   has already framed as federation rather than collection.
3. **Context is too shallow to condition on.** ~~Blocks §4~~ — **this one dissolved.** The
   claim was true of the file being read and false of the archive: ClinVar records the
   condition beside every classification, and reading `submission_summary.txt.gz` turned the
   blocker into a decomposition with an interval. What survives of it is narrower and still
   real: §3 and §7 remain at risk of measuring curation instead of biology, and a context
   ontology would still be worth more than another disease ontology.

Naming three blockers instead of eleven is the actual output of writing this down. Two of the
three are data-acquisition problems with known solutions, and none of the three is solved by
picking a more sophisticated formalism.

**And §13b is the control on that claim.** The language family had no blocker at all: the data
was named, found, ingested and measured inside an hour, and it produced a finding that changes
what this project ships. Eleven families wait on cohorts; one was waiting only on somebody
deciding that language is a subgroup axis. The second kind of blocker is the cheaper one to
remove and the easier one to miss.
