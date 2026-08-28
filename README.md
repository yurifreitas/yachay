# sieve

**Turn a large, noisy, confounded screen into a defensible shortlist for expensive validation.**

## The problem class

> You have many candidate entities. Each carries a noisy aggregate score estimated from a
> **varying** number of observations. Confounds correlate with that score. A downstream
> validation is expensive and can test only a handful. Produce a shortlist you can defend.

That shape recurs far outside biology: A/B test triage, feature selection, materials
discovery, security alert triage, recommender candidate generation. The stages are
domain-agnostic; the adapters are not.

## The stages

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

## Stage 1 is why this library exists

Most screening metrics are not means. They are maxima, top-k means, quantiles,
enrichment scores — operators that **select the largest of several noisy estimates**.
Every such operator is positively biased, and the bias grows as the estimate gets
noisier. When observation counts vary across entities, the metric is therefore *not
comparable across entities*, and its ranking is partly a ranking of who was measured
least.

```python
import sieve as sv

stat = sv.top_k_mean(3)                      # the SAME statistic your screen scores with
null = sv.fit_null(control_observations,     # rows known to carry no effect
                   stat,
                   observed_counts=df["n"])  # so the grid spans your real range
df = sv.calibrate(df, null, score="score", count="n")
df.nlargest(10, "z")                         # rank on z, never on the raw score
```

In the screen this library was distilled from, that one stage:

- showed the celebrated "maximum effect in the training data" was measured on **one
  observation**, where pure noise averages 0.845 and reaches 2.43 at the 99th percentile;
- dissolved a "viability confound" of -0.57 with observation count down to +0.07 — a
  biological story that turned out to be a statistical artifact;
- moved the single most important entity in the screen from rank 12 to **rank 1**.

None of that needed a better model.

## Status

Early. Stage 1 and the data contracts are implemented and tested; the remaining stages
are being ported and hardened against the DepMap adapter (~18,000 genes x ~1,100 cell
lines), which is the scale test — a method validated only on the screen that produced it
has not been validated.

## Documentation

| doc | what it is |
|---|---|
| `docs/methodology.md` | the ten stages, and what skipping each one cost |
| `docs/disease-expansion.md` | the disease portfolio: obesity (origin), schizophrenia, NF2, DMD |
| `docs/expansion-map.md` | where else this applies, outside biology |
| `docs/lineage.md` | whose work this descends from, and what our numbers do to each claim — including the one anomaly still open |
| `docs/audit.md` | the repository audited against its own standard: what is out of conformance, and what closed |
| `docs/roadmap.md` | the ordered backlog — every item with its cost and with what would make it not worth doing |
| `docs/references/target-model.md` | **`sieve target`** — what a gene's own evidence admits as an editing target, and which gate it fails. Deliberately not a score |
| `docs/references/prior-work.md` | the ancestors on the same machine — including `nominator`, whose ten stages these are, uncredited until 2026-08-28 |
| `tools/README.md` | the 33 scripts grouped by purpose: ingest, catalogue, patient, self-audit, authored, statistics |
| `docs/references/` | data, method, and domain references — NF2 focus in `references/nf2.md` |
| `docs/references/visualization.md` | the diagnostic figures, why each exists, and how the plotting layer scales |
| `docs/references/visualization-canon.md` | where each chart form comes from — control charts, funnel plots, Q-Q, slopegraphs, rarefaction — and the caution each carries |
| `docs/references/standards.md` | the external canon this repo answers to (Taguchi, TPS/TQC, GUM, FAIR, ADR) and where it does not conform |
| `docs/references/rare-disease-lexicon.md` | the cross-ontology crosswalk, and why the unknown is modelled as a value rather than a blank |
| `docs/references/rare-disease-scale.md` | the quantitative axis every rare disease shares — four kinds of scarcity, and which stage each activates |
| `docs/references/rare-disease-mechanisms.md` | why thousands of disorders collapse onto a few signalling modules, and what that does to Stages 6 and 7 |
| `docs/references/rare-disease-equity.md` | diagnostic delay, panel composition, naming — the social facts, and the point where each becomes a confounder |
| `docs/references/rare-disease-ancestry.md` | founder history, consanguinity, selection — and the measurement that prevalence is not a scalar in 73.5% of testable disorders |
| `docs/references/rare-layers.md` | the map of `out/rare/`: which of the twenty analytical layers are measured, derived, or written from working knowledge |
| `docs/references/patient-data.md` | 10,377 individual patients: the catalogue's `1/1` frequencies read 0.93 where the patients say 0.44 — and the access plan for the data that is not open |
| `docs/references/broad-institute-fit.md` | where this library applies to the Broad's CTG and GaMBiT initiatives — and the longer list of where it does not |
| `docs/references/state-of-the-art.md` | the frontier: what challenges this library's claim, and which approach can advance |
| `docs/references/deep/` | the five-lane adversarial review — each lane briefed to break its subject |
| `docs/adr/` | decisions with context and consequences |
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
python tasks.py fetch      # download the DepMap release files
python tasks.py depmap     # run the reference analysis
python tasks.py fetch_nf2  # genotype + lineage files for the NF2 subgroup (~1.5 GB)
python tasks.py nf2        # the NF2-null subgroup contrast, with its positive control
python tasks.py numbers    # regenerate the manuscript's numbers from out/
python tasks.py figures    # regenerate the figure data the explorer and paper read
python tasks.py rare       # regenerate the rare-disease lexicon seed
python tasks.py paper      # check the manuscript is submittable
```
