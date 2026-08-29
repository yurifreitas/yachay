# The methodology

> **Role:** the ten stages, and what skipping each one cost. Explanation, with a worked example.
> **Last revised:** 2026-08-29 · **State:** ⚠️ still mixes Diátaxis modes (audit A4, open); the case study it points at was never written.

Ten stages. Each one exists because skipping it cost something real, and each entry
below names what it cost. The worked example is the obesity screen — a public
competition where the method was developed, and where every number quoted here was
measured. Its numbers and their genealogy are in [`lineage.md`](lineage.md);
⚠️ a dedicated case-study document was cited here for months and **was never written**,
which `tools/status.py` found by resolving the link.

Where the work actually stands — which stages are stale, which data is ingested and unread,
which thresholds were calibrated rather than pre-registered — is in
[`status.md`](status.md), which is **generated**: it is recomputed from the repository on
every run of the submission gate rather than maintained by hand.

The stages are ordered by dependency, not by importance. Running them out of order is
how most of the failures below happened.

---

## Stage 0 — Decode the objective

**Ask: what is the maximum of this metric, and is it attainable by an artifact?**

Before modelling anything, find the metric's degenerate maxima. Write down the input
that maximises it, and check whether that input is something you would actually want.

> In the obesity screen the "maximum perturbation score in the training data" — the
> number a $23,400 eligibility gate was defined against — was `2.0047`, achieved by a
> perturbation observed in **one cell**. It was not an outlier to be excluded. It was
> the metric behaving exactly as designed on a single noisy observation.

A metric whose maximum is an artifact will pull every model toward the artifact. If the
objective was written by someone else (a competition, a stakeholder, a paper's reviewer),
Stage 0 is also where you find out that the written rule and the intended rule differ —
which is worth raising early, not after you have optimised against the written one.

## Stage 1 — Null calibration

**Ask: what does this score read when nothing is happening?**

This is the stage most pipelines skip and the one that changed the most in practice.

Screening metrics are usually not means. They are maxima, top-k means, quantiles,
enrichment scores — operators that **select the largest of several noisy estimates**.
Every such operator is positively biased, and the bias grows as the estimate gets
noisier. Since observation counts always vary across entities, the raw score is **not
comparable across entities**, and ranking on it partly ranks who was measured least.

The fix is cheap and empirical: resample real control observations, apply the *same*
statistic, and standardize.

```
z = (observed − null_mean(n)) / null_sd(n)
```

> Measured null of a top-3-of-12 statistic, from real control cells:
>
> | observations | null mean | null p99 |
> |---:|---:|---:|
> | 1 | 0.845 | 2.434 |
> | 16 | 0.207 | 0.658 |
> | 100 | 0.079 | 0.256 |
> | 224 | 0.052 | 0.170 |
>
> Consequences: the "training maximum" of 2.0047 sat at the ~93rd percentile of **pure
> noise**; a −0.57 correlation with observation count that had been diagnosed as a
> *viability confound* fell to +0.07 after calibration; and the single most important
> entity in the screen moved from rank 12 to **rank 1**.

Use real controls, not a parametric null: they inherit the screen's own correlation
structure, which is precisely what inflates a top-k statistic. Twelve nominal signatures
in that screen carried only **3.08 effective dimensions**, so taking the top 3 of 12
mostly re-read one axis.

**The trap:** interpolating null moments outside the fitted grid. `np.interp` clamps, so
a grid ending at 512 calibrates a 1,645-observation entity against the 512 null and
understates its z by nearly half. `sieve.fit_null` raises rather than allowing this.

## Stage 2 — Power and reliability

**Ask: how much of this estimate is the estimate, and how much is the prior?**

Empirical-Bayes shrinkage pulls low-power estimates toward the prior mean. It improves
correlation accuracy and it **compresses the top**, which matters when the objective is
to exceed a threshold rather than to rank.

> Shrinkage is not free and not always right. In the obesity screen, EB was believed to
> be the validated improvement; under a leakage-safe split its advantage was **not
> statistically established** (paired bootstrap P(EB ≥ raw) = 0.463, permutation
> p = 0.054), and against the null-calibrated truth the *unshrunk* score tracked better
> (Spearman +0.97 vs +0.64). Shrinkage and null calibration are different corrections;
> one does not substitute for the other.

Power-gate before you headline: compute the number on adequately-powered entities, and
report how many you dropped.

## Stage 3 — Confounds

**Ask: what else is correlated with this score, and would it produce the same ranking?**

The dominant confound in a viability screen is death. In an A/B screen it is traffic. In
an LLM eval it is response length. Name yours, measure the correlation, residualize, and
check whether the top survives.

> The strongest "hit" in the obesity screen was `KIF11+NR3C1`, and KIF11 is a
> mitotic-arrest gene whose knockout kills cells. But the honest verdict was subtler
> than "exclude it": after Stage 1, that pair was the *most statistically solid*
> observation in the entire screen (z = +14.75, rank #1). Stage 3 tells you what a
> signal might be; it does not by itself tell you to drop it.

Distinguish the two questions: *is this real?* (Stage 1) and *is it the phenotype I
want?* (Stage 3). Conflating them is how a real effect gets discarded and an artifact
gets promoted.

## Stage 4 — Baseline first

**Ask: does the complexity beat a linear/additive baseline out of fold?**

Fit the trivial model. Compare with a paired bootstrap over folds. If the CI crosses
zero, the complexity has not earned its place.

> Deep perturbation models did not beat a control-relative additive baseline. And the
> additive baseline itself explained **0.1%** of the variance of double perturbations —
> which is the number that should have redirected the whole project, and was computed
> last.

Calibrate the baseline against observations before comparing magnitudes:

> `obs ~ 0.203 + 0.080 × additive`. The slope is 0.08, not 1 — so predicted and observed
> values were never on the same scale, and every absolute "% of the target" claim built
> on that comparison was meaningless. A flag named `CALIBRATE` existed, was documented,
> defaulted ON, and was read by nothing.

## Stage 5 — Leakage-safe validation

**Ask: could an entity in my validation set have been seen in training?**

For pair or interaction data, a random split puts the same entity on both sides.
Cold-start (neither entity seen) and leave-one-entity-out are the honest splits. Report
bootstrap CIs, not point estimates, and prefer pooled out-of-fold statistics over
means-of-fold statistics when folds are small.

> A "mean_diff −0.115, CI (−0.222, −0.009)" that appeared decisive came from
> mean-of-fold-rho over 17 tiny folds. Under a paired bootstrap the same effect was
> P = 0.463 — not significant. The fold statistic, not the data, produced the result.

## Stage 6 — Mechanism priors

**Ask: what is already known, and am I re-nominating a published dead end?**

Fold domain knowledge in at *lower weight than measurement*: it should reorder ties and
rescue obvious false positives, never dominate. Down-weight rather than delete, so the
choice stays auditable.

## Stage 7 — Shortlist and portfolio

**Ask: if my top pick fails, what else is on the list?**

Diversify, cap appearances per entity, and measure concentration. A shortlist that puts
every slot on one entity is a single point of failure that must be disclosed.

Also decide explicitly **which score orders the shortlist**. The score that ranks best
and the score that maximises absolute magnitude are usually different, and the objective
decides which one you owe.

## Stage 8 — Honest reporting

**Ask: does every claim have an executable assertion behind it?**

This is the rule the whole method converges on, and it generalises past reporting:

> **Every claim the code makes about itself — in a flag, a docstring, a report, or a
> filename — must have an executable assertion behind it.**

Four failures in one project were that rule broken at four scales: a config flag nothing
read; a module describing a ranking that shipped only in an unshipped copy; a report
whose headline number was wrong for seven weeks; and a `Report.md` describing uncertainty
handling built on 307 summaries while the underlying distribution sat unused on disk.

Disclose the negative space too: what fraction of your output carries signal at all.

> 0.198% of a 4.47-million-row submission had both entities measured. 91.31% had neither
> and carried a constant score. This was never stated in the report.

## Stage 9 — Reproducibility

**Ask: can this artifact be regenerated, and would I notice if it changed?**

Deterministic seeds, frozen environment, and a **fingerprint over the whole artifact** —
not over its summary.

> During a refactor, a relative path broke and the model silently fell back to a
> different estimator than its docstring named. The test suite passed. The shortlist was
> unchanged. The only thing that noticed was the artifact fingerprint changing from
> `a0ac612d` to `acd1162c`.

Reports are generated, never hand-written. A finding whose numbers cannot be regenerated
is an opinion.
