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
| 2 | Power | Trusting effects estimated from too few observations |
| 3 | Confound | A ranking that reflects toxicity or technical variation, not the phenotype |
| 4 | Baseline | Complexity that does not beat a simple model out of fold |
| 5 | Validation | Optimistic numbers from leaky splits and in-metric validation |
| 6 | Prior | Ignoring known mechanism; re-nominating published dead ends |
| 7 | Shortlist | Betting every slot on a single point of failure |
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

## Development

```
python tasks.py            # list tasks
python tasks.py test       # unit tests, offline
python tasks.py fetch      # download the DepMap release files
python tasks.py depmap     # run the reference analysis
```
