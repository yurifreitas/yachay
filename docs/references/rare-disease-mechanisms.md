# Mechanisms, pathways and signalling — what rare diseases share

> **Role:** the mechanistic layer of the rare-disease reference. Why thousands of distinct
> ultra-rare disorders collapse onto a small number of **signalling modules**, what that
> convergence licenses, and — the part that matters here — what it does to Stages 6 and 7
> of `../methodology.md`.
> **Last revised:** 2026-08-27 · **State:** external claims verified through Crossref
> (title, authors, venue, year, DOI); internal numbers read from `out/rare/*.json` on
> disk. The **grouping** of diseases into modules below is the field's, not ours; the
> **counts** are ours and are marked as such. No claim here has been tested by an
> experiment in this repository.
>
> Explanation-mode. The per-disease facts live in the dossiers
> (`tools/dossier.py` → `out/rare/dossiers.json`); the non-gene causes live in
> [`rare-disease-lexicon.md`](rare-disease-lexicon.md) and `out/rare/nongene.json`.

---

## 0. The claim, and why this repository needs it

A rare-disease catalogue reads as maximal fragmentation: `out/rare/atlas.json` joins
**14,831 diseases** onto **5,524 genes**, and the median disease has exactly **one**
associated gene. Read that way, every disorder is its own field and nothing transfers.

The mechanistic literature reads the same data the opposite way. Distinct genes, distinct
syndromes and distinct clinical names converge on a shared **signalling module**, and the
module — not the gene — is the unit that predicts phenotype, comorbidity and, crucially,
what a drug does. The consequence is practical: a therapy developed for one disorder in a
module is a candidate for the others in it, and a screen that nominates ten genes from one
module has nominated one hypothesis ten times.

That second sentence is a Stage 7 claim (§4 below), and it is the reason this document sits
in a statistics repository rather than a biology one.

---

## 1. The modules

Each row is a group the field itself names, with the pathway that defines it. The
right-hand column is the load-bearing one: what membership *buys you* that the gene name
alone does not.

| module | shared mechanism | what membership buys |
|---|---|---|
| **RASopathies** — Noonan, Costello, CFC, NF1, Legius | germline activation of RAS–MAPK, altering proliferation in development | one of the largest groups of multiple congenital anomaly syndromes; pathway inhibitors (MEK) become cross-syndrome candidates |
| **mTORopathies** — tuberous sclerosis, focal cortical dysplasia, hemimegalencephaly | PI3K–AKT–mTOR hyperactivation, often **somatic and mosaic** | a mature clinical inhibitor class (rapalogs) exists before the individual disorder is characterised |
| **Ciliopathies** — Bardet–Biedl, Joubert, nephronophthisis, Meckel | assembly or trafficking failure of the primary cilium, a signalling organelle | otherwise unrelated organ phenotypes (retina, kidney, cerebellum, digits) become predictable from one lesion |
| **Ribosomopathies** — Diamond–Blackfan, Shwachman–Diamond, dyskeratosis congenita | impaired ribosome biogenesis or function | explains the field's oldest paradox: a defect in a universal housekeeping machine giving strictly tissue-restricted disease |
| **Spliceosomopathies** — craniofacial dysostoses, retinitis pigmentosa forms | mutation in core or accessory spliceosome components | same paradox again, and the same lesson about tissue-specific vulnerability |
| **Lysosomal storage** — Gaucher, Fabry, Pompe, NPC, MPS | substrate accumulation from a degradative or trafficking defect | the therapeutic template of the whole rare-disease field: enzyme replacement, substrate reduction, chaperones |
| **Mitochondrial** — MELAS, Leigh, LHON | oxidative phosphorylation failure, under **two genomes** and heteroplasmy | inheritance itself becomes quantitative: threshold effects, not presence/absence |
| **DNA-repair** — Fanconi, ataxia-telangiectasia, xeroderma pigmentosum | a specific repair pathway lost | predicts both the cancer risk and the treatment contraindication (radiosensitivity) |
| **Hippo / mechanotransduction** — NF2-related schwannomatosis | Merlin loss releases YAP/TAZ into the nucleus | the module this repository's own disease adapter sits in — see §3 |

Sources for the module definitions, each verified: RASopathies (Rauen 2013), mTOR (Crino
2016), ciliopathies (Reiter & Leroux 2017), ribosomopathies (Narla & Ebert 2010), lysosomal
storage (Platt et al. 2018), mitochondrial disease (Gorman et al. 2016). Full entries in
`CITATION.cff`; what each does to our claims is in [`../lineage.md`](../lineage.md) §11.

**Scope discipline.** These nine are not a taxonomy of rare disease. They are the groups
where the module is (a) named by the field, (b) mechanistically specified, and (c) tied to
a therapeutic class. Groups that fail (c) — most channelopathies, most transcription-factor
haploinsufficiency syndromes — are deliberately left out rather than stretched, per the
documentation standard §8.

---

## 2. Convergence is a network property, and it was measured before it was named

Two results predate the module vocabulary and generalise it.

**The human disease network** (Goh et al., *PNAS*, 2007) built the bipartite disease–gene
graph and showed it is far from random: diseases sharing a gene share phenotype, and
disease genes cluster in the interactome rather than scattering. **The incomplete
interactome** (Menche et al., *Science*, 2015) made this quantitative and falsifiable —
each disease occupies a connected *module* in the network, and the network **distance**
between two disease modules predicts whether they share symptoms and comorbidity. The
"module" of §1 is the biologist's name for the object those papers measured.

That claim is topological, and this repository has measured the topology of exactly the
same graph. `tools/interactome_sparse.py`, run on the HPO gene-to-disease graph, reports
**modularity 0.861** against **0.162** for a rewiring with the identical degree sequence.
Community-aware reordering cuts cache lines per row by **51.7 %** on the real graph and
**2.5 %** on the degree-matched null.

That measurement was taken for a computational reason — memory locality — and it is
evidence for a biological one. The community structure that makes the graph cache-friendly
is the same structure Menche et al. call disease modules; a degree-matched null does not
have it. Our number does not *confirm* their claim (a different graph, a different
statistic, no error bar) but it is an independent observation of the same object, and it is
the strongest link this repository currently has between its computational and its
biological literatures.

⚠ The reference audit (`../references/deep/`) found those two literatures had never once
discussed the same object here. This section is the first place they do.

### 2a. And the objection in §5.2 was tested — the claim survives

The paragraph above was published with its own falsifier attached (§5.2 below), because our
graph joins two genes when they cause a common disease, so **a disease with *k* genes
contributes a *k*-clique by construction**. Cliques are the most modular object there is,
and a degree-matched rewiring cannot separate that from biology because it destroys both.

STRING is the independent graph that can: 16,201 human proteins and 236,930 high-confidence
interactions, from experiments, curated complexes, co-expression and text mining — an
evidence base with no disease labels in it at all. Run through the *same* method, the same
Louvain implementation and the same seed (`tools/interactome_string.py`):

| graph | modularity | degree-matched null | **excess** |
|---|---|---|---|
| STRING, score ≥ 700 | 0.6822 | 0.1409 | **0.5413** |
| STRING, score ≥ 900 | 0.7727 | 0.1976 | **0.5751** |
| HPO gene–disease (ours) | 0.8605 | 0.1617 | **0.6988** |

**Absolute modularity is not comparable across these graphs** — it depends on size and
density, and STRING is far denser. The excess over each graph's *own* null is, and STRING's
is **77 %** of ours. The excess also *rises* as edge confidence rises, which is the right
direction: the more the edges are trusted, the more modular the graph.

**What this settles, and what it does not.** It settles the objection as posed: the excess
is not merely an artefact of how HPO records diseases, because a graph containing no disease
labels shows a comparable one. It does **not** show our number is free of construction
effect — ours remains higher (0.699 against 0.575), and the clique construction is the
obvious candidate for that gap. The direction survives; part of the magnitude is still
ours.

### 2a. And the objection in §5.2 was tested — the claim survives

The paragraph above was published with its own falsifier attached (§5.2 below), because our
graph joins two genes when they cause a common disease, so **a disease with *k* genes
contributes a *k*-clique by construction**. Cliques are the most modular object there is,
and a degree-matched rewiring cannot separate that from biology because it destroys both.

STRING is the independent graph that can: 16,201 human proteins and 236,930 high-confidence
interactions, from experiments, curated complexes, co-expression and text mining — an
evidence base with no disease labels in it at all. Run through the *same* method, the same
Louvain implementation and the same seed (`tools/interactome_string.py`):

| graph | modularity | degree-matched null | **excess** |
|---|---|---|---|
| STRING, score ≥ 700 | 0.6822 | 0.1409 | **0.5413** |
| STRING, score ≥ 900 | 0.7727 | 0.1976 | **0.5751** |
| HPO gene–disease (ours) | 0.8605 | 0.1617 | **0.6988** |

**Absolute modularity is not comparable across these graphs** — it depends on size and
density, and STRING is far denser. The excess over each graph's *own* null is, and STRING's
is **77 %** of ours. The excess also *rises* as edge confidence rises, which is the right
direction: the more the edges are trusted, the more modular the graph.

**What this settles, and what it does not.** It settles the objection as posed: the excess
is not merely an artefact of how HPO records diseases, because a graph containing no disease
labels shows a comparable one. It does **not** show our number is free of construction
effect — ours remains higher (0.699 against 0.575), and the clique construction is the
obvious candidate for that gap. The direction survives; part of the magnitude is still
ours.

---

## 3. Convergence works the other way too: causes that are not genes

The modules above are entered by mutation. They can also be entered by an antibody, a
molecule at a dose, a diet or delivered energy, and the resulting disease is often
clinically indistinguishable. `out/rare/nongene.json` records eight such **phenocopy
pairs**, each with the point of convergence stated:

| non-gene cause | genetic counterpart | converges on |
|---|---|---|
| thalidomide, weeks 4–6 | SALL4-related syndromes | loss of SALL4 in the developing limb |
| lead poisoning | ALAD-deficiency porphyria | inhibited ALAD, same metabolite pattern |
| anti-NMDA-receptor encephalitis | *GRIN1* / *GRIN2B* encephalopathy | reduced synaptic NMDA receptor density |
| pellagra | Hartnup disease | insufficient tryptophan reaching the tissue |
| acquired TTP | congenital TTP (Upshaw–Schulman) | absent ADAMTS13 activity |
| aminoglycoside exposure | m.1555A>G in 12S rRNA | irreversible cochlear hair-cell loss |
| congenital rubella | CHARGE and related syndromes | a disrupted developmental window |
| konzo | hereditary spastic paraplegia | symmetrical upper motor neuron loss |

Two of these are mechanistically load-bearing for the module story. Thalidomide does not
merely resemble a genetic syndrome — it *causes* the same molecular lesion, by hijacking
cereblon and redirecting an E3 ligase onto SALL4. And the Hippo module of §1 is entered
mechanically: cells read substrate stiffness through the cytoskeleton into YAP/TAZ
localisation, so the same node that NF2 loss dysregulates is also a **force** sensor.

**And the number that limits all of it.** `tools/nongene_measure.py` asked what the
catalogue can actually record about a non-gene cause, and six of the ten authored classes
have a measured footprint of **exactly zero** — not because the diseases are rare, but
because HPO's inheritance vocabulary is a vocabulary *of inheritance*. There is no term for
a molecule at a dose, an antibody clone, a pathogen at eight weeks, a diet, or delivered
energy. Thalidomide embryopathy cannot be annotated as caused by thalidomide.

So the convergence in this section is real and **structurally unsearchable**. Every count
in §1 and §2 is computed over the half of the causal world that has somewhere to be
written down.

---

## 4. What this does to the stages

This is the part that changes code, and it is why the document is here.

**Stage 6 (Prior) — module membership is prior information, and it is cheap.** The stage
exists to stop a screen re-nominating published dead ends. Gene-level prior lists do that
poorly for rare disease, where most genes have no literature. Module membership
generalises: a nominated gene in a module with an existing inhibitor class is a different
proposition from one in a module with none, and the module is known even when the gene is
not studied.

**Stage 7 (Shortlist) — this is the sharp one.** The stage's rule is *do not bet every slot
on a single point of failure*. Module structure says the failure modes are **correlated by
construction**: a shortlist of ten genes drawn from one signalling module is one hypothesis
with ten labels, and if the module is wrong, all ten die together. The diversification
constraint should therefore be over **modules**, not genes — and no current adapter
implements that. It is the clearest actionable consequence in this document.

**Stage 3 (Confound) — with a warning.** Module membership correlates with attention, and
attention is the ascertainment bias `tools/atlas_bias.py` measures at **+0.2357**. A
well-characterised module is well characterised partly because it was studied. Conditioning
a screen on "belongs to a known module" will therefore rank the studied above the tractable,
which is the exact error this repository exists to catch. See
[`rare-disease-scale.md`](rare-disease-scale.md) §3.

**Stage 1 (Null) — no.** Nothing here changes the null. Module structure is a *dependence*
between entities, which is a multiplicity problem (`tools/multiplicity.py`), not a
calibration one. Stating this explicitly because "everything is connected, so the null must
change" is the plausible wrong inference from §2.

---

## 5. What would falsify this document

Kept short and specific, so the next pass has a target rather than an impression.

1. **The Stage 7 claim.** If shortlists diversified over modules do not outperform
   shortlists diversified over genes on a retrospective DepMap or NF2 validation, §4's main
   recommendation is decoration. Not tested.
2. ~~**The §2 link.** If the modularity excess (0.861 vs 0.162) survives on a graph with the
   biology removed but the *annotation process* preserved … **This is the weakest claim in
   the document and it is stated as such.**~~

   **✅ Tested 2026-08-27, and it survives.** STRING — an independent human interaction
   network with no disease labels anywhere in its evidence base — shows a modularity excess
   of **0.5413** over its own degree-matched null, rising to **0.5751** at the stricter
   confidence cut, against our **0.6988**. Same method, same Louvain, same seed
   (`tools/interactome_string.py`); §2a carries the table.

   The objection **as posed** is answered. What is *not* answered is the residual: ours is
   still the higher number, and the clique construction remains the obvious explanation for
   the gap between 0.699 and 0.575. The sharper test named in the original wording — a
   rewiring **within curation source** — has still not been run, and it is the one that
   would settle the magnitude rather than the direction.
3. **The module table.** If a module's therapeutic class fails across the module (a MEK
   inhibitor helping one RASopathy and no other), then "membership buys you a candidate" is
   false and column three collapses.
