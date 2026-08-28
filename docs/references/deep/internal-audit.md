# Internal audit — the core, adversarially

> **Role:** the code-and-statistics lane of the deep review. Briefed to assume `sieve`'s
> core is wrong and to try to prove it, from the repository and the data on disk only —
> no literature, no web. Every claim below is either a line that was read or a number
> that was computed in this session, with the command that produced it.
> **Last revised:** 2026-08-26 · **State:** complete. Both open anomalies of
> [`lineage.md`](../../lineage.md) §8 are **explained, and they are the same defect**.
> The NF2 positive-control failure is also explained, and it is a third face of a
> different defect. Nothing here is a fix; §6 lists the fixes and their tests.

Everything was run from the repository root against `data/depmap/` (1,178 cell lines ×
17,916 genes, the same files the shipped findings used). Throwaway scripts lived in the
session scratchpad and are quoted inline; no repository file was modified except this one.

---

## 1. VERDICT

**The core is not correct.** The stage that the whole library exists for — Stage 1, null
calibration — is fitted on the wrong resampling unit, and that single choice produces
both of the repository's open anomalies plus the failure of its only positive control.
The failure is not in the *idea* (a top-k statistic is biased, and the bias depends on
`n` — both were reproduced here and both hold). It is in the *estimator*: the null is
built by drawing individual observations i.i.d. from a pool that mixes many entities, so
it estimates the sampling distribution of a synthetic entity that does not exist in the
screen. Every z the library has published is on the wrong scale.

Defects, by severity.

**D1 — The null resamples pooled observations, not entities.**
`src/sieve/stages/null.py:204` (`rng.integers(0, len(control), size=(take, int(m)))`),
fed by `src/sieve/adapters/depmap/__init__.py:95` (`vals = self.values[:, idx].ravel()`).
The control pool is 726 nonessential genes flattened into 841,293 scalars, and the null
draws `m` of them i.i.d. Two consequences, both measured in §2: the pooled distribution
is 47% wider than a real gene's (sd 0.1604 vs a median within-gene 0.1092, because
between-gene variance sd 0.1131 has been folded in), so the null's top-20 tail is too
high; and the null sd is the sd of a *draw*, 3.27× too small to be the sd of a *gene*.
This is D1 alone producing −4.09.

**D2 — The same defect makes the count correction over-shoot.** Because the pooled
distribution has the fatter tail, the null mean rises with `n` roughly twice as fast as a
real gene's score does: **+0.1737 from n=347 to n=1178 for the pooled null, +0.0892 for a
gene-shaped null** (§3). Subtracting a slope that is 1.95× too steep tilts z against
well-measured entities — which is exactly Anomaly B, and it is a defect, not noise.

**D3 — Differencing two z-scores fitted against two different nulls is not a valid
contrast.** `analyses/nf2_subgroup.py:162-163` fits a separate null per group and
`analyses/nf2_subgroup.py:183` takes `z_null - z_wt`. The two z's have sds 8.906 and
6.932 on the real data; the OLS slope of `z_null` on `z_wt` is **1.235**, not 1, so the
difference carries 0.235 of `z_wt` as pure scale mismatch, and it is centred at **+2.363**
rather than 0. Replacing it with a permutation null on the group label moves the Hippo
positive control from median rank **5,216 → 716** of 17,916 (§4). The control did not
fail because of biology or subgroup size. It failed because of this statistic.

**D4 — `calibrate()` validates nothing.** `src/sieve/stages/null.py:243-251` checks only
that the two column names exist. `fit_null` guards that the grid spans the observed
counts (`null.py:184-189`) — but that guard is at *fit* time and `calibrate` may be handed
any other frame. Measured: a row with `n = -5` returned `z = -0.2004` with no warning
(`moments` clamps via `np.maximum(n, 1.0)` at `null.py:90`); a row with `n = 1e9` was
silently clamped to the top of the grid. `calibrate` also never checks
`null.reduce` against how the caller's score was built, although the field is recorded on
the model (`null.py:79`) and the two settings differ by **9.2×** in sd on identical data
(§5). The docstring says "the library refuses to guess"; the code guesses at exactly one
place and it is the place that matters.

**D5 — A degenerate control pool produces a NullModel instead of an exception.**
`fit_null` checks dimensionality and `len(control) >= 50` (`null.py:168-175`) but never
checks finiteness or spread. An all-NaN control of 100 rows returned
`mean=[nan nan] sd=[nan nan]`; a constant control returned `sd = 0` at every grid point,
and `z()` then converts that to NaN at `null.py:96` — so a fully degenerate input becomes
a silently all-NaN `z` column rather than an error.

**D6 — `top_k_mean` silently degrades to a plain mean.** `null.py:60-61`: when the row
has `k` or fewer elements it returns `block.mean(axis=-1)`. `top_k_mean(20)` applied to a
5-element row returned `2.0` — the arithmetic mean — with no signal that the requested
statistic was not the one computed. `_default_grid` starts at the smallest observed count
(`null.py:113-118`), so any screen whose minimum `n` is below `k` has grid points where
the fitted null is a different statistic from the one being calibrated.

**D7 — Monte-Carlo error in the null sd is not negligible and is not reported.** At the
shipped `n_draws=2000`, the null sd at n=1178 varied 0.05216 / 0.05372 / 0.05357 across
seeds 0/1/2 — a **1.6% seed-to-seed spread**, which at DepMap's z magnitudes (z≈86–109 for
the top genes) is ±1.5 z units of pure resampling noise in the published ranking. Raising
to `n_draws=8000` reduced it only to 1.45%, because the residual is dominated by the
control pool itself, not by the draw count (§5).

**D8 — The test suite cannot detect D1.** `tests/test_ranking_scope.py:87` asserts
`abs(small_z) < 4 and abs(large_z) < 4` for entities with *no real effect*. The shipped
DepMap defect is a mean z of −4.09; a bound of 4 was chosen wide enough to accommodate
exactly the failure the library has. No test anywhere constructs a control pool with
between-entity structure, which is the only construction under which D1 appears.

---

## 2. ANOMALY A — explained

**The standing hypothesis is correct, and it accounts for the number to two decimals.**

Command: `python scratchpad/a2.py` (loads the cached `float32` matrix, re-derives the 726
matched nonessential genes, refits the shipped null, and compares against a gene-shaped
null that resamples whole control genes).

```
control genes scored: 726
control gene score: mean 0.3475  sd(between-gene) 0.1691
control gene per-line mean 0.01181 sd 0.1604
per-gene MEAN of control values: between-gene sd = 0.1131 (within-gene sd median 0.1092)
POOLED null: mean z of control genes = -4.083 (sd of z 3.30)
  null_mean at control ns: 0.5587   observed mean 0.3475  gap -0.2112
  null_sd 0.0517 vs between-gene sd 0.1691  ratio 3.27
GENE-SHAPED null: mean 0.3447 sd 0.1646
  mean z of control genes under gene-shaped null = +0.017
```

Read that in three steps.

**The pool is not a gene.** A control gene's own line values have a median sd of 0.1092.
The pool of all 841,293 control values has sd 0.1604, because pooling adds the
between-gene variance of the per-gene means (sd 0.1131): √(0.1092² + 0.1131²) = 0.157,
which recovers the pooled 0.1604 almost exactly. The pooled draw is therefore a **47%
wider** distribution than any gene in it.

**A wider distribution has a higher top-20.** The statistic is the mean of the top 20 of
`n`≈1178 — roughly a 3-sd upper region — so a 47% wider parent lifts the null mean from
the true 0.3447 to 0.5587, a gap of **−0.2112** against the observed control mean 0.3475.

**And the denominator is the wrong sd entirely.** The null sd 0.0517 is the sd of *one
pooled draw's* top-20 mean. The quantity actually being standardized varies across genes
with sd 0.1691 — **3.27× larger**. That ratio is visible directly in the output: the z's
of the control genes have sd 3.30.

So −4.09 = (a real bias of −0.211) ÷ (an sd that is 3.27× too small). Divide the same gap
by the correct, gene-shaped sd and it is only −1.28. Replace the null outright with the
gene-shaped one and the controls land where they must: **mean z = +0.017** (was −4.083),
with the spread of z back near 1.

Anomaly A is D1, in full, with no residual to explain.

---

## 3. ANOMALY B — a defect, not noise

**Point estimate reproduced, interval computed, and it excludes zero decisively.**

Command: `python scratchpad/b.py` — 4,000 nonparametric bootstrap resamples of the 17,916
gene rows in `out/depmap_genes.csv`, recomputing both Spearman correlations on each
resample so the raw/calibrated comparison stays paired.

```
point: raw -0.0252  cal -0.0559  diff -0.0307
ties in n: 19 distinct values, largest tie group 95.4% of rows
raw           mean -0.0250  95% CI [-0.0394, -0.0105]  P(>0)=0.001
calibrated    mean -0.0557  95% CI [-0.0693, -0.0418]  P(>0)=0.000
cal-raw diff  mean -0.0307  95% CI [-0.0344, -0.0271]  P(>0)=0.000
|cal| - |raw| 95% CI: [+0.0271, +0.0344]
```

**The answer to §8(b) is: not noise.** The 95% bootstrap interval on the *change* is
**[−0.0344, −0.0271]**, and the interval on the change in absolute magnitude is
**[+0.0271, +0.0344]** — calibration reliably makes the count correlation worse, by about
0.03, on this dataset. The "may be noise around zero" reading is refuted: the raw
correlation is near zero, but the *degradation* is not, and it is estimated with a
standard error of roughly 0.0019.

**And the mechanism is D1 again.** The pooled null's mean rises far too fast in `n`:

```
$ python scratchpad/d.py
control genes with full 1178 lines: 612
  n   gene-shaped null mean   sd
  347   0.2427   0.1274
  505   0.2700   0.1413
  736   0.2914   0.1311
  976   0.3227   0.1549
 1178   0.3318   0.1497
gene-shaped null mean rise 347->1178: 0.0892
pooled     null mean rise 347->1178: 0.1737 (0.3908 -> 0.5645)
```

The gene-shaped null (subsample `m` lines from one real control gene, take its top-20
mean) rises by **0.0892** across the observed count range. The shipped pooled null rises
by **0.1737** — **1.95× too steep**. Calibration therefore subtracts about 0.085 too much
from the highest-`n` genes, which is around 1.6 pooled-sd units, pushing them down
relative to sparsely-screened genes. That is precisely a *more negative* correlation
between z and log n, which is what was observed:

```
$ python scratchpad/c.py   (excerpt)
n bin        mean score   mean z    size
(340, 700]     0.7315     +7.575     129
(1000,1177]    0.5456     -0.056     700
(1177,1178]    0.5737     +0.189   17087
within the 829 genes with n<1178: raw -0.0323 cal -0.1685
```

Two things worth stating plainly. First, the 129 genes screened in 347–700 lines come out
at a mean z of **+7.57** against +0.19 for the fully-screened majority — the count
artifact Stage 1 exists to remove has been *created* by Stage 1 at the low end. Second,
this correlation is a weak instrument for detecting it: **95.4% of genes share a single
value of n (1178)**, only 19 distinct counts exist, and the whole statistic rests on 829
rows. Within those 829 the calibrated correlation is −0.1685 against a raw −0.0323 — five
times worse, and far more visible than the pooled −0.0559 suggests. The headline number in
`out/DEPMAP_FINDINGS.md` understates the problem rather than overstating it.

---

## 4. The two-group z-difference in the NF2 analysis

**It is not a valid contrast, and it is the reason the positive control did not pass.**

`analyses/nf2_subgroup.py:156-164` fits one null per group — 32 NF2-null lines against a
control pool of 22,889 values, and 1,146 wildtype lines against 818,404 — and
`analyses/nf2_subgroup.py:182-183` differences the resulting z's. Three separate problems.

**The two z's are not on one scale.** Each group's null sd is fitted for that group's own
sampling model, so the two standardizations differ. On the shipped output
(`out/nf2_genes.csv`, 17,916 genes): `z_null` has sd 8.906 and mean +2.005; `z_wt` has sd
6.932 and mean −0.358; their correlation is 0.961. The regression slope of `z_null` on
`z_wt` is **1.235**. A difference of two variables related by a slope of 1.235 is not a
contrast — it is `0.235 × z_wt` plus a residual, so it leaks the gene's *overall*
dependency strength into the "NF2-selective" score. Measured leakage:
`corr(contrast_z, z_wt) = +0.554`.

**Its null distribution is unknown and is not centred.** `contrast_z` has mean **+2.363**
and sd 2.943 across all genes. Nothing in the code establishes what value a gene with no
NF2-specific effect should take, and it is demonstrably not 0, and its spread is
demonstrably not 1. The reported "median rank" statistic inherits that: it ranks a
quantity whose null location is a free parameter.

**The right statistic is a permutation null on the group label**, which is available and
cheap. Draw 32 lines at random from all 1,178, compute the same top-10 contrast against
the same wildtype reference, repeat, and standardize each gene against *its own* empirical
null. That respects the two things the z-difference violates: the null is built for the
statistic that is actually reported, and it is built per gene, so between-gene variance
never enters the denominator (it is the same fix D1 needs).

```
$ python scratchpad/e.py
--- scale-mismatch leak in contrast_z = z_null - z_wt ---
OLS slope of z_null on z_wt: 1.235 (1.000 if the two nulls shared a scale)
corr(contrast_z, z_wt) = +0.554 ; corr(contrast_z, z_null) = +0.762
mean contrast_z = +2.363, sd 2.943
Hippo median rank: contrast_z 5216 -> scale-matched residual 8308 (of 17916)

--- permutation null for the group contrast (300 permutations of 32 lines) ---
null 32 wt 1146
permutation-calibrated contrast: Hippo median rank 716 of 17916 (random ~8958)
entity     zperm  rank_perm
 LATS1  0.623084     2538.0
 LATS2  1.144989     1102.0
 TEAD1  3.951657        6.0
 TEAD2 -0.462451     9138.0
 TEAD3  0.634803     2491.0
 TEAD4  1.796929      329.0
 WWTR1  2.522026       86.0
  YAP1  1.858322      297.0
permutation null of contrast_z itself: mean -0.381 sd 0.949
```

**The positive control passes under the correct statistic.** Hippo median rank **716 of
17,916** — the top 4% — comfortably inside the analysis's own `n_genes * 0.25` gate at
`analyses/nf2_subgroup.py:215`, against 5,216 under the shipped contrast. TEAD1 ranks 6th
of 17,916; WWTR1 86th; YAP1 297th. The four candidate causes the script lists on failure
(`nf2_subgroup.py:220-222`) — under-called subgroup, subgroup too small, lineage confound,
wrong contrast statistic — resolve to the fourth. Note the honest partial credit: the
script *named* the right cause, and the jidoka gate correctly refused to emit a shortlist.

One caveat on this number, recorded because it matters: the permutation groups are drawn
from all 1,178 lines, so a permuted group can include NF2-null lines; with 32 of 1,178
that contamination is small and conservative (it dilutes the observed effect, not
inflates it). The permutation sd is estimated from 300 draws, so individual ranks are
noisy even though the median-rank verdict is not. A control that was destroyed by the
scale mismatch is not restored by 300 lucky permutations: the shift is 5,216 → 716.

The scale-matched residual row is the diagnostic that isolates blame: regressing out the
1.235 slope alone moves the Hippo median to 8,308 — i.e. removing the leak *without*
fixing the per-gene null leaves the control at chance. Both halves are needed.

---

## 5. Fragility and silent-failure inventory

All rows measured by `python scratchpad/c.py`.

| # | Input | What the code does | Should do |
|---|---|---|---|
| 1 | `calibrate` with `n = -5` | returns `z = -0.2004`; `moments` clamps at `null.py:90` | raise — a negative count is not a count |
| 2 | `calibrate` with `n = 1e9`, grid tops out at 1178 | clamps to the n=1178 null, silently | raise, as `fit_null:184-189` already does at fit time |
| 3 | `calibrate` with `n = NaN` | `null_mean=NaN`, `z=NaN`, no message | raise or count-and-report |
| 4 | all-NaN control, 100 rows | `NullModel` with `mean=[nan…] sd=[nan…]` | raise at `fit_null:168-175` |
| 5 | constant control | `sd = 0` at every grid point → every `z` is NaN via `null.py:96` | raise; a zero-spread null cannot standardize |
| 6 | `reduce` mismatch | never checked by `calibrate`; on identical data `reduce="mean"` gave sd 0.0305 and `reduce="raw"` 0.2817 at n=200 — a **9.2×** difference in every z | record how the score was built on the frame and assert it matches `null.reduce` |
| 7 | `top_k_mean(20)` on a 5-element row | returns the plain mean (2.0), no warning (`null.py:60-61`) | warn, or refuse when `min(observed_counts) < k` |
| 8 | `observed_counts` containing 0 or NaN | dropped silently at `null.py:178`, narrowing the grid; those same rows are then clamped by `calibrate` | raise, since Stage 1 "cannot be honest without" the count (`contracts.py:133-138`) |
| 9 | `n_draws` | seed-to-seed spread of the null sd is 1.86% at 500, 1.62% at 2000 (shipped), 1.45% at 8000 — it does **not** converge away, because the limiting error is the control pool | report a resampling interval on `null_sd`, and stop treating `n_draws` as the knob |
| 10 | `float32` matrix | `load_matrix:127` stores float32; the pool has 836,772 distinct values out of 841,293 (0.54% collisions) | benign at this precision — the only clean row in this table |
| 11 | ties in ranking | `spearman()` in both analyses uses average ranks via `Series.rank()`, which is correct; but 95.4% of `n` values are identical, so the count correlation is estimated from 829 rows | report the tie fraction next to the correlation |
| 12 | `_default_grid(5, 5)` | returns `[5, 6]` — a grid point above the observed maximum | harmless, but the invariant "the grid spans the observed range" is enforced only one-sided |

Row 5 and row 4 together are the general shape of the answer to *"can the code produce a
confident number from a degenerate input without raising?"* — it produces NaN rather than
a wrong number, which is the better of the two failures, but it produces it silently, and
`calibrate` returns a frame whose `z` column is entirely NaN with a normal return code.
Row 1 is the exception and the worst of the set: it produces an actual finite number.

---

## 6. Fixes, in priority order

**F1 — Fit the null on entity-shaped blocks, not pooled observations.**
`fit_null` should resample *rows of a control entity* (or accept a `groups` argument
labelling which entity each control observation came from) and apply the statistic to one
entity's block at a time, so that between-entity variance sits in the null's spread where
it belongs. This is the same correction `lineage.md` §5 predicts for LD, arrived at from a
second direction.
*Test that proves it:* build a control pool with explicit between-entity variance
(per-entity offsets, e.g. sd 0.11 on top of within-entity sd 0.11 — the measured DepMap
ratio), score the control entities themselves, and assert `|mean z| < 0.25` **and**
`0.7 < sd(z) < 1.4`. Against the current code that test fails at −4.08 with sd 3.30;
against the gene-shaped null it passes at +0.017. This test is the one D8 says is missing,
and it is also the regression test for Anomaly B, because the slope in `n` is fixed by the
same change (0.1737 → 0.0892).

**F2 — Make the two-group contrast a permutation statistic.**
Add a group-contrast entry point that permutes the group label rather than differencing
two independently-fitted z's, and delete `contrast_z = z_null - z_wt` from
`analyses/nf2_subgroup.py:183`.
*Test:* on the shipped NF2 setup, assert the Hippo median rank is below `0.25 * n_genes`.
Currently 5,216 (fails at the 4,479 threshold); under the permutation contrast 716
(passes). Assert also that the permuted-null z's have `|mean| < 0.5` and `0.8 < sd < 1.2`
across genes — measured −0.381 / 0.949 — where the shipped contrast gives +2.363 / 2.943.

**F3 — Give `calibrate` the guards `fit_null` already has.**
Validate the frame against `entity_scores()` inside `calibrate`, and raise when any count
falls outside `[null.counts[0], null.counts[-1]]` instead of clamping.
*Test:* `pytest.raises` on `n = -5`, on `n = NaN`, and on `n = 10 * null.counts[-1]`. All
three currently return numbers or NaN.

**F4 — Refuse degenerate control pools.**
In `fit_null`, after the `len(control) >= 50` check: require every value finite and
require `control.std() > 0`.
*Test:* `pytest.raises` for an all-NaN pool and for a constant pool; both currently return
a `NullModel`.

**F5 — Carry `reduce` on the scored frame and assert it in `calibrate`.**
The adapters already know which one they used — `depmap` documents `reduce="raw"` at
`adapters/depmap/__init__.py:78-91` and both manifests record it — but nothing connects
that to the model.
*Test:* fit with `reduce="mean"`, calibrate a frame tagged `raw`, assert it raises. The 9.2×
sd difference measured in §5 row 6 is what the test is protecting against.

**F6 — Report a confidence interval on every published statistic.**
The repository has none anywhere, which is the standards gap that made Anomaly B
unresolvable for as long as it was. At minimum: a bootstrap interval on each count
correlation in both findings files, and a resampling interval on `null_sd` (§5 row 9).
*Test:* assert every headline number in a manifest has an accompanying interval key.

**F7 — Warn when `min(observed_counts) < k`,** so `top_k_mean` cannot silently become a
mean at the bottom of the grid.
*Test:* `top_k_mean(20)` with `observed_counts=[5, 500]` warns or raises.

---

## 7. What could not be determined

**Whether the gene-shaped null is itself sufficient.** It fixes the mean (+0.017) and the
sd (3.30 → ~1) for the *control* genes, but the control genes are the entities the null was
fitted from, so this is an in-sample check. Whether a gene-shaped null is correctly
calibrated for a gene *outside* the nonessential set — which is every gene the shortlist
cares about — cannot be settled from this data without an external truth. It needs the
held-out construction: fit on half the control genes, calibrate the other half.

**Whether the correlation structure across cell lines matters on top of D1.** Lines share
lineage, medium and batch (`lineage.md` §2 says so), so even a gene-shaped null that
resamples lines i.i.d. within a gene understates the spread. The gene-shaped null used
here in §3 subsamples lines without replacement from one real gene, which preserves within-
gene structure only partially. Quantifying the residual needs a line-block bootstrap, which
was out of scope for this lane.

**Whether the DepMap shortlist changes under the corrected null.** Re-running the full
analysis with an entity-shaped null was not attempted, because that is a code change and
this lane was scoped read-only. The direction is predictable — the −0.211 bias and the
1.95× slope both act on `n`, so the low-`n` genes now sitting at mean z +7.57 should fall —
but the resulting top-20 list is not something to guess at.

**The absolute calibration of the permutation contrast in §4.** 300 permutations pin the
median-rank verdict (5,216 → 716) but give roughly 6% relative error on each gene's null
sd, so individual `zperm` values — TEAD1 at 3.95, for instance — should not be read as
p-values without more permutations.

**Nothing in `adapters/llm_eval` was tested against real data,** because none is in the
repository. It was read: `permutation_pool` returns its caveat as a value rather than a log
line (`llm_eval/__init__.py:162-178`), which is the right pattern, and `baseline_pool`'s
`features > 1` branch is an unguarded `reshape(-1, features)` (`llm_eval/__init__.py:159`)
that will raise on a ragged count rather than silently mis-shape. But D1 applies verbatim to `permutation_pool` — it
pools every execution across every variant into one flat array — so the LLM adapter is
expected to carry the same defect, and that prediction is written here so it can be scored
rather than rationalised later.
