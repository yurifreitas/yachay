# Selection bias — is the core claim novel?

> **Role:** the adversarial novelty check on the one thing this library claims. Briefed to
> find the paper that makes `sieve` redundant.
> **Last revised:** 2026-08-26 · **State:** lane completed its research but was killed by a
> session limit before writing; this file is transcribed from its returned findings by the
> maintainer, so **quotations are second-hand** and every one must be checked against the
> primary source before it appears in a manuscript. The lane's own verification marks are
> preserved: `[FT-self]` full text read by the lane, `[FT-del]` full text read by a
> delegate, `[ABS]` abstract or metadata only.

---

## §1 VERDICT — blunt

**The diagnosis is not novel. The z-form of the remedy is not novel. What remains is a
recombination, not a discovery.**

This contradicts what `../state-of-the-art.md` §4 said this morning ("nobody is currently
making this contribution"). That sentence was wrong and has been corrected. The correction
is the most valuable thing this review produced.

Three papers have a prior claim on the idea and **must** be cited:

1. **Gelman & Price (1999), "All maps of parameter estimates are misleading",
   *Statistics in Medicine* 18(23):3221–3234.** `[FT-self]` States the confound *and*
   proposes a z indexed by n. This is `sieve`'s thesis sentence, in 1999.
2. **Subramanian et al. (2005), GSEA, *PNAS* 102(43):15545–15550.** `[FT-del]` A
   permutation null of a genuine selection statistic (the enrichment score is *"the maximum
   deviation from zero"* of a running sum), explicitly normalised for entity size.
3. **Liu et al. (2010), VEGAS, *AJHG* 87(1):139–145.** `[FT-del]` A **max / top-10 %**
   statistic whose null is simulated per gene, calibrated to that gene's SNP count, using LD
   from a **real reference panel**. The nearest thing in print to what this library does.

### The sentence that removes any claim to the diagnosis

Gelman & Price, verbatim `[FT-self]`:

> *"It is well known that, if the n_j's vary, the procedure of selecting the counties with
> the highest observed means tends to yield counties with few observations; we will quantify
> this artefact."*

**"It is well known" — in 1999.** Any framing of the form "we noticed screening metrics are
n-confounded" is a citation failure, not a contribution.

Their remedy is the same formula this library ships:

> *"artefacts based on sample size can be eliminated by highlighting the counties for which
> the quantity z_marg = (y_j − μ)/(τ² + σ²/n_j)^{1/2} is highest… does not depend on n_j —
> thus, no artefacts due to sample size."*

The difference is where the moments come from: theirs from an assumed normal hierarchical
model, ours from resampled controls.

---

## §2 The nearest prior art, ranked by closeness

Three overlap tests are applied to each: **(a)** does it treat the ranking-vs-n confound
explicitly? **(b)** does it build an empirical null of a *selection* statistic indexed by n?
**(c)** does it use *real control observations resampled*, rather than a model fitted to the
analysis data?

| # | Work | (a) | (b) | (c) | Why it is close, and where it stops |
|---|---|---|---|---|---|
| 1 | **Hartman et al. (2024)**, individualised empirical null for transplant centres, *AoAS* 18(1) `[FT-self, methods]` | ✅ | ❌ | ❌ | **"Empirical null indexed by n, then z, then rank" is already published.** The statistic is a standardised mean/SMR, not a selection operator, and the null comes from fitting a mixture to the observed z-distribution, Efron-style. |
| 2 | **Gelman & Price (1999)** `[FT-self]` | ✅ | ⚠️ partial | ❌ | The confound and the z remedy. The operator is a threshold on a *mean*, not a max/top-k. |
| 3 | **VEGAS**, Liu et al. (2010) `[FT-del]` | ✅ | ✅ | ⚠️ partial | Max/top-10 % statistic, per-entity null, real LD reference. Output is an empirical p-value, not a z; simulation from a fitted MVN rather than direct resampling. |
| 4 | **GSEA**, Subramanian et al. (2005) `[FT-del]` | ✅ | ✅ | ⚠️ partial | Corrects only the null **mean** (NES divides by the mean of the permutation ES), leaving the n-dependence of the **spread** to the FDR step. Permutes the analysis data, not a separate control pool. |
| 5 | **Henderson & Newton (2016)**, r-values, *JRSS-B* 78(4):781–804 `[FT-del]` | ✅ | ❌ | ❌ | *"units that are associated with relatively high standard error are overrepresented among the top units by [the] MLE ranking"* — the confound is the paper's motivation. Parametric hierarchical model. |
| 6 | **Spiegelhalter (2005)**, funnel plots, *Stat Med* 24(8):1185–1202 `[ABS]` | ✅ | ❌ | ❌ | A funnel *is* a null band indexed by precision. The plotted quantity is always a rate or proportion with closed-form null moments. **Its prescription is the opposite of ours: do not rank at all.** |
| 7 | **Goldstein & Spiegelhalter (1996)**, league tables, *JRSS-A* 159(3):385–443 `[FT-self]` | ⚠️ | ❌ | ❌ | Recommends ordering by n rather than by the performance measure. The "small units dominate both ends" remark is **Goodhardt's discussion contribution**, not the authors' text — a distinction worth keeping. |
| 8 | **Mogstad, Romano, Shaikh & Wilhelm (2024)**, *ReStud* 91(1):476–518 `[FT-del]` | ⚠️ | ❌ | ⚠️ | Confidence sets for ranks without normality or equal variances. **Raises a live objection to us** — see §4. |
| 9 | **Rarefaction** in ecology: Hurlbert (1971); Gotelli & Colwell (2001); Chao et al. (2014) `[ABS]` | ✅ | ✅ | ✅ | Same statistic, resampled real observations, brought to a **common n**. This is the *equalise-n* alternative to our *standardise-against-n*. A reviewer will raise it. |
| 10 | **Winner's curse**: Andrews, Kitagawa & McCloskey (2024) *QJE* 139(1):305–358; Efron (2011) *JASA* 106(496):1602–1614; Zöllner & Pritchard (2007) `[ABS]` | ❌ | ❌ | ❌ | Correct the *value* of the selected unit under a model. None index by n; none re-rank. Omitting this literature is the second-worst citation gap after Gelman & Price. |
| 11 | **Efron (2004)**, empirical null, *JASA* 99(465):96–104 `[ABS]` | ❌ | ❌ | ⚠️ | The origin of "estimate the null from the data" — but a **single pooled null**, not indexed by n. Hartman et al. name this gap explicitly. |
| 12 | **Ranking & selection (OR)**: Bechhofer (1954), OCBA, KN `[ABS]` | ❌ | ❌ | ❌ | **Safe ground.** R&S handles unequal n by *choosing* it or *stopping* on it. It never asks whether a score is comparable given an n you did not choose. |

---

## §3 What the literature says about RANKING — the crux

Forster et al. (2025) report that correction *"generally does not improve the feature
ranking"*. This review sharpens rather than overturns the scope answer already in
`tests/test_ranking_scope.py`, and adds a second, harder objection:

**Gelman & Price already stated the price of ranking on z**, verbatim `[FT-self]`:

> *"the low-sample-size counties highlighted on such a map will have lower values of θ_j, on
> average, than the highlighted counties with high sample size."*

Standardising buys comparability by **giving up the score's interpretation as an estimate of
the quantity you care about**. If the screen's goal is high *true effect* rather than high
*surprise*, ranking on z is the wrong objective. This library has never stated that
trade-off, and it must — it is the honest counterweight to every "rank 12 → rank 1" claim.

---

## §4 Threats — four objections the literature raises

1. **The score stops meaning what you want** (Gelman & Price, quoted above). z-ranking
   systematically over-promotes small-n entities that merely surprised.
2. **Discreteness breaks the fix.** Verbatim: *"this works only for continuous data; any
   discreteness in the distribution of y_j causes the probabilities to vary with n_j."*
   Count and binary screens retain residual n-dependence after standardisation. **The
   `llm_eval` adapter scores pass rates — binary. This objection lands directly on it.**
3. **The ranking step still carries no uncertainty statement**, and Mogstad et al. show
   bootstrap *rank* procedures fail coverage near ties with more than two populations.
4. **Control exchangeability is an assumption, not an escape from assumptions.** Swapping a
   hierarchical model for a control pool swaps "the prior is right" for "the controls are
   exchangeable with the entities' null behaviour and span the required n range."

---

## §5 Opportunities — what is actually unclaimed

Four things, all narrow, all defensible:

1. **Operator generality.** No source treats max / top-k mean / quantile / enrichment /
   best-of-N as one family with a common n-indexed calibration. GSEA does one enrichment
   score; VEGAS does one gene statistic; Gelman & Price do a threshold on a mean.
2. **Control-pool null.** Every source either fits a model to the analysis data or permutes
   the analysis data. Resampling a *designated real control pool* differs, and it matters
   exactly when the entities' own observations are the thing under suspicion.
3. **Mean *and* sd over a grid of n.** GSEA corrects only the mean; Hartman et al. model
   only the variance of an already-standardised score. Doing both, tabulated and
   interpolated, is the one genuinely unclaimed cell.
4. **The LLM-eval / leaderboard application.** *The Leaderboard Illusion*
   (arXiv:2504.20879, 2025) `[FT-self]` documents the bias — Appendix C *"formalizes the
   selection bias arising when one reports the best out of N noisy skill estimates"*, and
   Figure 7 finds *"testing just 10 variants yields a notable increase of approximately 100
   points in the maximum score"* — but **its remedy is policy, not statistics**: cap the
   variants, mandate disclosure. No null indexed by N, no z. That is a current, citable gap.

---

## §6 Recommendations for the library

1. **Rewrite the framing.** Claim the four items in §5, not the diagnosis. Cite Gelman &
   Price (1999) in the first paragraph of the README, not in a bibliography.
2. **State the z trade-off** (§3) in `methodology.md` Stage 1 and in the manuscript's
   limitations. It is the strongest honest objection and hiding it is worse than facing it.
3. **Check the discreteness objection against `llm_eval`.** Pass rates are discrete; the
   correction may not fully remove n-dependence there. This is a testable prediction and
   should become a test.
4. **Add rarefaction as an explicit alternative** in the docs — equalise n by subsampling to
   a common count, and say when that is the better move than standardising.
5. **Do not compete on effect-size estimation.** Bootstrap and convoluted empirical Bayes are
   better at it. Cede, cite, stay on ranking and comparability.

---

## §7 What was not searched — absence of a hit is absence of a search

The lane exhausted its search budget. **Two areas were never swept**, and both could
plausibly contain the claim:

- **High-throughput / RNAi / compound screening statistics** — SSMD, Z′, B-score,
  plate-level hit-rate normalisation. An n-indexed null of a hit-count or top-k statistic
  could exist here.
- **Sports analytics and fund-manager skill** — the same order-statistic argument is
  common in both.

Until these are swept, **no novelty claim is final.** A follow-up lane was launched for the
HTS half and also died to the session limit.

## §8 Could not verify

Carried over verbatim from the lane, because it governs what may be quoted: Efron & Morris
(1975) publisher returned 403 and the "equal at-bats" detail is secondary; Shen & Louis
(1998), Louis (1984), Laird & Louis (1989), Klein–Wright–Wieczorek (2020), Fay & Herriot
(1979), Andrews et al. (2024), Efron (2004), Efron (2011), Zöllner & Pritchard (2007) are
abstract-only; Normand, Glickman & Gatsonis (1997) is metadata only and its (b)/(c) marks
are inference; the GSEA NES formula and the Henderson & Newton and Lin et al. quotations
come from fetch summaries and were not eyeballed; Efron (2004)'s subtitle is not confirmed
in the Crossref record; Bechhofer/Santner/Goldsman authorship is unverified.
