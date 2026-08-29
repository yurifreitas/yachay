# yachay

> **Role:** the entry point — what yachay is, what it has actually measured, what `sieve` does,
> and where every other document lives.
> **Last revised:** 2026-08-29 · **State:** restructured. The previous version led with the
> library and made the larger half of the project a parenthesis; an audit found that a reader
> came away with five wrong impressions, and each is now addressed in the text rather than in
> a footnote.

> **yachay** — Quechua: *to know*, and the knowledge itself. A language still spoken by
> several million people across the Andes.
>
> The name is the whole intention. Knowledge about what keeps people alive should be free to
> use, and it is most often missing exactly where there is nobody to demand it: the diseases
> too rare to fund, the patients with no advocate, the professional who needs a number and
> finds an empty field. This repository is years of reading, distilled into something a
> person can check, argue with, and reuse.

**An atlas of rare disease that says where the evidence stops, and a method for turning a
large, noisy, confounded screen into a shortlist you can defend.**

**Explorer:** <https://yurifreitas.github.io/yachay/> · English and Portuguese.

---

## The rule this repository runs on

Most of what is interesting here is a claim about biology that somebody could make in prose.
The whole point of the project is that prose is not enough, so there is a rule, written down
as [ADR 0007](docs/adr/0007-theory-enters-by-measurement.md):

> An idea has **no standing** — it may not be cited, shipped, or described as part of the
> method — until a tool computes it from ingested public data and writes a number with a null
> and an interval.

Ninety mathematical constructs are catalogued in
[`docs/references/theory-atlas.md`](docs/references/theory-atlas.md), graded **measured /
buildable / analogy**. Three are measured. The default grade for a new idea is *analogy*, and
nothing is promoted by argument.

The same discipline runs through the rest: every threshold is registered with whether the data
had been seen when it was chosen (`manifests/thresholds.yaml`), every published number is
checked against the artefact that produced it (`tools/verify_claims.py` — 37 claims, 12
artefacts, 10 documents), and the project's own state is generated rather than typed
(`docs/status.md`).

---

## What has actually been measured here

These carry a governing ADR, a null, an interval, and a registered drift check. They are the
most defensible thing in the repository.

**What a change of scale costs.** A disease is described by its causal genes; collapse those
genes onto a coarser alphabet and ask what survives. Over 9,142 diseases: a 181-fold
compression onto 29 Reactome top-level pathways keeps **22 %** of the information genes carry
about a disease's organ systems; a 34-fold compression onto 154 cell types keeps **31 %**.
Retention spans **5.6-fold** across organ systems — pathways hold what is pathway-shaped
(neoplasm, metabolism) and lose what is structural (eye, limb, cardiovascular). **There is no
single right coarse-graining for a multiscale atlas**, which is an engineering consequence and
not only a finding. Genes also predict organ system **2.91×** better than organ system predicts
genes, and that asymmetry collapses to 1.02 under compression: the summary destroyed the
direction, not only the magnitude.

**What a reader loses by not reading English.** HPO ships fourteen language profiles besides
English and coverage runs from 100 % to zero. Weighted by the annotations diseases actually
carry, Portuguese — *this project's own second language* — covers **42.9 %** of the annotated
rare-disease phenotype, with a **69.6-point** spread across organ systems, worst in the nervous
system, which carries 6,254 of those 9,142 diseases. The explorer's language switch is a
partial translation whose gaps are concentrated, and now that is measured rather than assumed.

**Whether recorded scientific conflict is really disagreement.** ClinVar records 165,843
variants as carrying conflicting classifications. Reading the 6,428,687 per-submission rows,
each with the condition it was made against: **57.2 %** of variant-level conflicts are
*across-condition only* — every individual condition internally consistent, the conflict
appearing only when conditions are pooled into one column. Removing panel indications takes it
to **48.6 %**. About half of the largest curated disagreement corpus in human genetics is
context rather than contradiction. And redundancy does not resolve it: with the condition held
fixed, internal disagreement rises to about a quarter by the third submitter and stays there
through the eleventh — **an aggregate classification is not a consensus.**

**Two of these were predicted by somebody, and one prediction failed.** Splitting organ systems
by Turing's 1952 distinction — a structure that formed wrongly against a process running
wrongly — the pathway alphabet retains 0.238 in the physiological class against 0.138 in the
morphogenetic one (p = 0.0185, and marked as a description with target contact, not a
pre-registered test). Von Neumann's 1956 multiplexing predicts that redundancy buys
reliability; ClinVar says it does not.
[`docs/references/deep/foundations.md`](docs/references/deep/foundations.md) has both in full.

---

## The other half: the method

`sieve` is the Python package — the ten-stage method the atlas is meant to be run through.

> **The problem class.** You have many candidate entities. Each carries a noisy aggregate
> score estimated from a **varying** number of observations. Confounds correlate with that
> score. A downstream validation is expensive and can test only a handful. Produce a shortlist
> you can defend.

That shape recurs far outside biology: A/B test triage, feature selection, materials
discovery, security alert triage, recommender candidate generation. The stages are
domain-agnostic; the adapters are not.

| # | Stage | What it protects you from |
|---|-------|---------------------------|
| 0 | Objective | Optimising a metric whose maximum is an artifact |
| 1 | **Null** | **Ranking a max-order statistic that is biased by observation count** |
| 2 | **Power** | **Trusting effects estimated from too few observations** |
| 3 | Confound | A ranking that reflects toxicity or technical variation, not the phenotype |
| 4 | Baseline | Complexity that does not beat a simple model out of fold |
| 5 | Validation | Optimistic numbers from leaky splits and in-metric validation |
| 6 | Prior | Ignoring known mechanism; re-nominating published dead ends |
| 7 | **Shortlist** | **Betting every slot on a single point of failure** |
| 8 | Report | Claims with no executable assertion behind them |
| 9 | Repro | An artifact nobody, including you, can regenerate |

### Stage 1 is why the library exists

Most screening metrics are not means. They are maxima, top-k means, quantiles, enrichment
scores — operators that **select the largest of several noisy estimates**. Every such operator
is positively biased, and the bias grows as the estimate gets noisier. When observation counts
vary across entities, the metric is therefore *not comparable across entities*, and its ranking
is partly a ranking of who was measured least.

```python
import sieve as sv

stat = sv.top_k_mean(3)                      # the SAME statistic your screen scores with
null = sv.fit_null(control_observations,     # rows known to carry no effect
                   stat,
                   observed_counts=df["n"])  # so the grid spans your real range
df = sv.calibrate(df, null, score="score", count="n")
df.nlargest(10, "z")                         # rank on z, never on the raw score
```

On DepMap, at 1,178 cell lines × 17,916 genes, that one stage shows **60 % of the raw top 10
are known pan-essential genes** — the metric's maximum is toxicity, not selectivity. Grouping
the same lines by lineage instead of pooling recovers textbook dependencies blind, and 27 of
37 subtypes are reported as *underpowered* rather than as negative.

**⚠️ The obesity figures this library was distilled from** — noise averaging 0.845 and reaching
2.43 at p99 against a celebrated "maximum" measured on one observation, a −0.57 viability
confound dissolving to +0.07, an entity moving from rank 12 to rank 1 — **were measured on a
screen that is not in this repository** and cannot be reproduced from it. They are the origin
story, not evidence you can check here.

---

## Status, stated so it cannot flatter

**The library.** Four modules implemented and tested in `src/sieve/` — Null, Power, Design,
Target — plus the data contracts. Six of the ten stages have no implementation.

**The atlas, which is the larger half.** 63 tools, 40 registered pipeline stages, 39 artefacts
in `out/rare/`, 18 ingested public sources (~1.3 GB). Almost every measured finding in this
repository comes from here.

**And they do not meet.** The atlas half does **not** use the library — three tools call it.
That is audit finding A15, open, and it is the most important structural fact about this
repository.

**The reference application is gated shut.** The NF2 subgroup contrast reports its positive
control as `NOT RECOVERED`, which by this project's own
[ADR 0003](docs/adr/0003-positive-control-gates.md) means its shortlist may not be used. Said
here because a reader who missed it would overestimate what has been validated.

**Self-audit.** 37 findings, 28 closed, in [`docs/audit.md`](docs/audit.md). Nineteen
thresholds registered, five of them honestly marked as chosen after seeing the data.

---

## Documentation

| doc | what it is |
|---|---|
| **`docs/references/theory-atlas.md`** | the ninety formalisms proposed for the multiscale atlas, graded measured / buildable / analogy under ADR 0007 — three are measured |
| `docs/references/deep/multiscale-formalism.md` | the mathematics behind that atlas: formal object, estimator, blocker and verified citations, family by family |
| `docs/references/deep/foundations.md` | Turing, Shannon, von Neumann, Ashby, Wiener, Waddington, Kolmogorov — each tied to a number measured here or an open problem, two of them tested |
| `docs/methodology.md` | the ten stages, and what skipping each one cost |
| `docs/status.md` | the derived checklist — generated by `tools/status.py`, never edited by hand |
| `docs/audit.md` | the repository audited against its own standard: what is out of conformance, and what closed |
| `docs/roadmap.md` | the ordered backlog — every item with its cost and with what would make it not worth doing |
| `docs/lineage.md` | whose work this descends from, and what our numbers do to each claim — including the one anomaly still open |
| `docs/disease-expansion.md` | the disease portfolio: obesity (origin), schizophrenia, NF2, DMD |
| `docs/expansion-map.md` | where else this applies, outside biology |
| `docs/references/rare-layers.md` | the map of `out/rare/`: which of the thirty-four analytical layers are measured, derived, or written from working knowledge |
| `docs/references/patient-data.md` | 10,377 individual patients: the catalogue's `1/1` frequencies read 0.93 where the patients say 0.44 — and the access plan for the data that is not open |
| `docs/references/rare-disease-scale.md` | the quantitative axis every rare disease shares — four kinds of scarcity, and which stage each activates |
| `docs/references/rare-disease-ancestry.md` | founder history, consanguinity, selection — and the measurement that prevalence is not a scalar in 73.5% of testable disorders |
| `docs/references/rare-disease-equity.md` | diagnostic delay, panel composition, naming — the social facts, and the point where each becomes a confounder |
| `docs/references/rare-disease-mechanisms.md` | why thousands of disorders collapse onto a few signalling modules, and what that does to Stages 6 and 7 |
| `docs/references/rare-disease-lexicon.md` | the cross-ontology crosswalk, and why the unknown is modelled as a value rather than a blank |
| `docs/references/target-model.md` | **`sieve target`** — what a gene's own evidence admits as an editing target, and which gate it fails. Deliberately not a score |
| `docs/references/prior-work.md` | the ancestors on the same machine — including `nominator`, whose ten stages these are, uncredited until 2026-08-28 |
| `docs/references/standards.md` | the external canon this repo answers to (Taguchi, TPS/TQC, GUM, FAIR, ADR) and where it does not conform |
| `docs/references/state-of-the-art.md` | the frontier: what challenges this library's claim, and which approach can advance |
| `docs/references/broad-institute-fit.md` | where this work applies to the Broad's CTG and GaMBiT initiatives — and the longer list of where it does not |
| `docs/references/visualization.md` · `visualization-canon.md` | the diagnostic figures, and where each chart form comes from — with the caution each carries |
| `docs/references/deep/` | the five-lane adversarial review — each lane briefed to break its subject |
| `docs/adr/` | decisions with context and consequences, written before the change where possible |
| `tools/README.md` | the 63 scripts grouped by purpose: ingest, catalogue, patient, gene, self-audit, authored, statistics |
| `archive/MANIFEST.md` | dead ends, each with the number that killed it |
| `CITATION.cff` | how to cite the software, annotated with the claim each reference supports |
| `paper/` | the manuscript standard: advanced LaTeX, a bibliography with mandatory annotations, and **numbers generated from the analysis so they cannot drift** |

### Skills

Repository practice, executable as Claude Code skills in `.claude/skills/`:

| skill | when |
|---|---|
| `sieve-stage-gate` | run or audit an analysis through the ten stages, stopping at the first failed gate |
| `sieve-new-adapter` | add a domain — gated on the four-question fit test |
| `sieve-doc` | write or revise anything under `docs/`, the README, or `CITATION.cff` |
| `sieve-hansei` | close out an experiment: record, archive the dead end, drive the anomaly to cause |
| `sieve-paper` | write, revise, or build a manuscript under `paper/` |

## Development

```
python tasks.py            # list tasks
python tasks.py test       # unit tests, offline
python tools/ingest.py     # download the 18 public catalogues (~1.3 GB), licence-aware
python tasks.py fetch      # download the DepMap release files
python tasks.py depmap     # run the reference analysis
python tasks.py fetch_nf2  # genotype + lineage files for the NF2 subgroup (~1.5 GB)
python tasks.py nf2        # the NF2-null subgroup contrast, with its positive control
python tasks.py numbers    # regenerate the manuscript's numbers from out/
python tasks.py figures    # regenerate the figure data the explorer and paper read
python tools/status.py --check   # fail if the repository contradicts its own documents
python tools/verify_claims.py    # fail if a published number no longer matches its artefact
```
