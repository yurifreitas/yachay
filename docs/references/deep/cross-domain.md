# Cross-domain review — where this bug lives, and who already killed it

> **Role:** the external audit of `sieve`'s central claim. Seven domains asked the same four
> questions — is the bug present, does the field know, what is their fix, and how does that
> fix compare to an empirical count-indexed null — with the explicit aim of finding fields
> that have **already solved it**, because those are worth more to us than fields that have not.
> **Last revised:** 2026-08-26 · **State:** first pass. Search-and-abstract depth, not
> full-text depth. Every claim below carries a verification mark; nothing here is safe to
> cite in a manuscript without opening the primary source.
>
> ⚠️ **Verification status, stated once and applying throughout.** This document was
> assembled on 2026-08-26 from web search plus **abstracts, landing pages, and publisher
> metadata**. Full text was read for only a handful of items (marked *full text* inline).
> Several negative findings ("we found no work that…") rest on ten to twenty searches each,
> not on a systematic review — they are phrased as *we are not aware of*, and must not be
> upgraded to *nobody has*. Individual items that could not be confirmed at all are marked
> **⚠️ unverified** and must not be cited as they stand.
>
> Companion to [`state-of-the-art.md`](../state-of-the-art.md), which asks what challenges
> the claim; this file asks how far the claim reaches. The non-biology application inventory
> is [`expansion-map.md`](../../expansion-map.md); the ancestry is
> [`lineage.md`](../../lineage.md).

---

## 1. Verdict — how general is this really?

**The mechanism is universal. The contribution is not.** The bug — a selection operator
applied to a varying number of noisy observations produces a ranking partly of observation
count — was found in every domain examined, without exception, and in most of them it has a
name. What varies enormously is whether the field has a fix, and whether that fix is
*better* than ours.

The honest summary is that `sieve` has invented nothing. Each of its three components has
decades of prior art:

- **an empirical null built from real controls** — high-throughput screening has done exactly
  this since 1999 (DMSO control wells, SSMD's "negative reference group"), and Efron named the
  general principle in 2004;
- **a null indexed by how much you looked** — neuroimaging's permutation max-statistic null,
  gene-set enrichment's size-matched null, Dodge et al.'s expected validation performance as a
  function of search budget, and the Deflated Sharpe Ratio's dependence on both trial count and
  track-record length;
- **z-scoring entities against that null to make a ranking comparable** — standard everywhere.

What we did not find, in any of the seven domains, is the **composition**: a null resampled
from real control observations, tabulated as a function of *the per-entity observation count*,
and used to make entities with different counts comparable on one ranking scale. The gap is
narrow and it is real, but it must be claimed narrowly.

**Where the claim is strongest.** Four conditions have to hold together, and where they do,
nothing in the literature covers the case:

1. observation counts vary **across the entities being ranked**, by a large factor;
2. the counts are **exogenous** — an entity has fewer observations for reasons unrelated to
   its outcome;
3. the aggregate is a **selection** operator, so the count moves the statistic's *location*,
   not merely its spread;
4. a pool of observations known to carry no effect exists, and no cheap exact analytic null
   does.

Domains that satisfy all four: LLM leaderboards with heterogeneous sampling and battle
budgets; HTS and virtual screening with unequal replicate counts; genotype-defined subgroup
contrasts in genomics; and security/UEBA entity scoring, which is the least defended of all.

**Where it collapses.** Five failure modes, each of which someone will raise:

- **Equal counts.** With homogeneous *n* the correction is one common monotone transform and
  cannot reorder anything. This is Forster et al.'s regime and their result stands
  ([`state-of-the-art.md`](../state-of-the-art.md) §1); the repo already pins it with a test.
- **Plain means.** A mean is unbiased. The count then affects variance only, and the entire
  league-table literature — funnel plots, James–Stein, Fay–Herriot, hierarchical shrinkage —
  already solves it, better than we would. Say so and step aside.
- **Endogenous counts.** If an entity has more observations *because it looked promising*,
  the bias is selection-on-outcome, and the adaptive-experiment literature (Nie et al.; Shin,
  Ramdas & Rinaldo; Hadad et al.) treats a strictly harder problem. A count-indexed
  permutation null is **not sufficient** there. This is the single most important thing to
  check before publishing, because the LLM-eval adapter's motivating story — "promising
  variants get more runs" — is *precisely* an endogenous count, and would put our own
  flagship non-biology example inside the regime where our method does not suffice.
- **A cheap exact analytic null.** Where the null is `F(x)^n` in closed form, or a pinned-*k*
  combinatorial estimator, simulation buys nothing but cost. We must be able to say what the
  empirical route buys, per case.
- **No control pool.** With no rows known to carry no effect, Stage 1 has nothing to fit and
  the parametric route is the only route. Already conceded in `methodology.md`.

**The most uncomfortable finding.** The winner's-curse literature reports that correction
*does not improve the ranking*, and Shen & Louis showed in 1998 that good ranks, a good
histogram, and good unit estimates cannot be simultaneously optimised — ranking has a
different optimum from estimation. Two literatures, from different directions, warning that
fixing the estimate does not fix the order. Our answer is the heterogeneous-*n* scope
condition, and it is currently supported by one internal measurement (the NF2 run). That is
thin. It needs an external ground truth, which is §4.

---

## 2. Domain by domain

| # | Domain | Bug present? | Field aware? | Their fix | Overlap with a count-indexed empirical null |
|---|---|---|---|---|---|
| 1 | **LLM eval / leaderboards** | Yes, twice: max-over-private-variants, and budget-monotone metrics (coverage, pass@n) with order-of-magnitude budget spread | Partly. Named and quantified for Arena in 2025; largely unnamed for sampling budgets | Pin *k* and use the unbiased combinatorial pass@k estimator; compare at matched budget; bootstrap CIs; governance caps on private variants | **High and favourable.** Their fixes are parametric (i.i.d. fixed decoder) or protocol-based (you must *control* the budget). A resampled null works post hoc on someone else's leaderboard |
| 2 | **A/B testing platforms** | Yes — winner's curse on shipped features; peeking; metric multiplicity | Yes, and shipped in production (Optimizely, Statsig, Bing, Airbnb) | Empirical Bayes shrinkage from historical experiments; conditional-likelihood debiasing; anytime-valid CIs; BH-FDR; holdout re-tests | **Partial.** A/A resampling from control logs is published practice — cede that component. Indexing it by *n* is where we found nothing |
| 3 | **Adaptive experiments / bandits** | Yes, and it is the closest structural analogue: unequal arm counts, biased sample means | Yes — mature 2018–2023 literature, essentially no platform deployment | Selective-inference debiasing; adaptively-weighted AIPW; batched OLS; online debiasing | **Overlaps and dominates us where counts are endogenous.** Do not compete here. Cite it as the harder neighbouring problem |
| 4 | **League tables** (schools, hospitals, sport) | Yes, and demonstrably costly — small schools at both tails; five-star hospitals with too little data to rate | **Fully, since 1996.** Do not call this field naive | Funnel plots; hierarchical shrinkage / partial pooling; small-area estimation; loss-matched ranking; rating deviation carried alongside the rating (Glicko) | **Low, and that is the opening.** Every estimand there is a mean or rate whose count affects only *variance*. We found no treatment of a max/top-k estimand, whose count moves the *location*. Shrinking toward a global mean cannot fix that |
| 5 | **Virtual screening / HTS / materials** | Yes. EF and BEDROC are functions of the active ratio; docking hit rates from n=44 and n=1,521 appear in the same tables | Fragmented. Ratio-dependence is named; count-dependence was demonstrated by subsampling in 2024; materials-ML shows no awareness at all | Fix the dataset's ratio (DUD-E → AVE → LIT-PCBA); normalise the metric analytically (BEDROC, SSMD\*/z\*); bootstrap CIs; "just test more" | **Closest prior art of any field, and the most instructive.** HTS *has* the empirical control null but indexes it by **plate**; HTS *has* an *n*-correction but derives it analytically under normality; docking *has* the *n*-dependence insight but uses it as a caveat. Nobody assembled the three |
| 6 | **RL / ML benchmark reporting** | Yes — max-over-seeds, and unequal seed counts across compared methods | Diagnosed in 2018; the adjacent problem won an Outstanding Paper in 2021 | Protocol advice (don't report max, fix N); IQM + stratified bootstrap + performance profiles + probability of improvement; and — the real one — Dodge's expected max as an explicit function of budget | **Very high.** rliable is count-indexed for the wrong statistic (median bias, not max) and handles unequal N by analysing cohorts *separately*. Dodge is count-indexed for the right statistic but parametric under i.i.d. — and its estimator was itself shown to be biased in 2020 |
| 7 | **Recommenders** | Yes — exposure counts vary by orders of magnitude; sampled top-k metrics depend on candidate-set size | **The most mature of all seven.** Unbiased estimators, not guidelines | Inverse-propensity scoring for exposure and position bias; bias/MSE-minimising corrections to sampled metrics as an explicit function of sample size | **High conceptual overlap, no methodological collision.** Both are corrections *in expectation*; neither constructs a chance distribution for the top-ranked item at count *n*. The vocabulary (propensity, inconsistency-in-expectation) is there to borrow |
| 8 | **Neuroimaging / physics / scan statistics** | Yes, and it is the field's central methodological problem | **Maximally.** The max-statistic null *is* the fix | Permutation max-statistic null (empirical, FWE-controlling); random field theory; look-elsewhere trial factors, estimated from a few background-only runs at a low threshold and extrapolated analytically into the tail | **This is our closest methodological relative — but on a different axis.** Their null is indexed by *how many places were searched*; ours by *how much evidence each place has*. Same idea, orthogonal index |
| 9 | **Finance / backtest selection** | Yes | Yes, with the sharpest formalisation anywhere | Deflated Sharpe Ratio; probability of backtest overfitting; raised t-hurdles for factor discovery | **Our closest analytic competitor.** DSR is indexed by trial count *and* sample length, closed-form, one line of code. Its weaknesses are our differentiators: it needs an *effective independent* trial count it admits is hard to estimate, its sample length is one global *T* rather than a per-entity count, and its `E[max]` is a Gumbel approximation that converges notoriously slowly at small N |
| 10 | **Security alert triage / UEBA** | Almost certainly, and event counts per host or user are heavy-tailed, so the effect should be large | **No.** We found no peer-reviewed statement of it | Peer-group normalisation — which corrects for **role**, the wrong variable. Score aggregation is heuristic | **Nothing to compare against.** Most novel, least contested, and correspondingly the domain with no ground truth to validate against. A bad first demonstration for exactly that reason |

The base-rate fallacy result in intrusion detection is *adjacent* — both are "per-alert
significance is not what you think at scale" — but it is a different bug and must not be
cited as if it were this one.

---

## 3. What we should cede, and what we should reproduce

A field that has already solved it is worth more to us than one that has not. Three lists.

### Cede outright — claim none of this

- **The empirical null from real controls.** HTS has z-scored compounds against pooled
  negative-control wells for a quarter of a century, and SSMD is explicitly a z-score against
  a negative reference group. Efron named the general principle. Our contribution is not the
  empirical null; it is its index.
- **Effect-size estimation.** Bootstrap and convoluted empirical Bayes do it better than a
  resampled null. Already conceded in [`state-of-the-art.md`](../state-of-the-art.md) §4.
- **The equal-*n* regime.** No method can improve a ranking it cannot alter.
- **Means and rates with unequal counts.** Funnel plots and hierarchical shrinkage own this,
  and have since 1996. Anyone who arrives at `sieve` with a plain-mean league table should be
  sent there. This is already the `synth` and DMD verdict; it now has citations behind it.
- **Endogenous counts.** The bandit debiasing literature treats a harder problem and we do
  not solve it.
- **Analytic corrections where the null is exact and cheap** — pinned-*k* pass@k, `F(x)^n`,
  the truncated-normal conditional mean.

### Reproduce as a validation target — these are free ground truth

These fields did the work; if our empirical null cannot recover their answer where their
answer is known correct, the library is wrong. In rough order of cheapness:

1. **Exact order statistics.** The CDF of a max of *n* i.i.d. draws is `F(x)^n` exactly, for
   any *n*, with no asymptotics. This is the cheapest and most exact check available, and it
   should be a unit test rather than a result.
2. **The Deflated Sharpe Ratio's closed form for `E[max]`.** A one-line Euler–Mascheroni
   expression, and the paper ships its own Monte-Carlo-versus-analytic verification harness —
   we get the formula *and* the reference test design for free. Note the known caveat that
   Gumbel convergence is slow, so this is a large-N check, not a small-N one.
3. **The unbiased pass@k estimator.** Exact under a binomial model. Our calibration must
   agree with it in the regime where it is valid, and we must be able to state precisely what
   we add outside that regime.
4. **Expected validation performance as a function of budget**, and its 2020 bias
   correction. This is the single most directly comparable prior method found, and it comes
   with released reference code.
5. **Permutation max-statistic nulls** in neuroimaging, where the empirical null was shown to
   hold calibration while the parametric approximation failed badly in the tail. This is the
   strongest published argument for our own design stance — borrow it, and cite the published
   correction and rebuttals alongside the original, or be called on it.
6. **The size-matched empirical null in gene-set enrichment.** A random-gene-set null drawn at
   *the same set size as the set under test*, used to normalise a size-biased max-like
   statistic. Of everything found, this is the nearest thing to `sieve` in construction. It is
   never framed as ranking and never connected to shrinkage — but a reviewer who knows it will
   ask, and we should answer before they do.
7. **The 2024 docking subsampling result**, which characterised hit rate as a function of how
   many molecules were tested and found convergence only in the hundreds. An empirical curve,
   published, that our machinery should reproduce.

### Borrow the vocabulary

Propensity and inconsistency-in-expectation from recommenders; trial factor from physics;
rating deviation from Glicko; effective independent trials from the DSR. Naming our quantity
in a vocabulary a reader already has is cheaper than teaching a new one.

---

## 4. The best demonstration target, ranked

Criterion: **value of a positive result × cheapness of the check**, with a strong preference
for an analytic ground truth or a known-correct answer to check against — because everything
in the repository today is internal-consistency evidence.

**Gate (do first, counts as a test not a result): the exact order-statistic check.** Verify
that `fit_null` recovers `F(x)^n` quantiles and the DSR closed form for `E[max]` on synthetic
i.i.d. data across the *n* range a real screen sees. Sub-hour, exact target, no data
required. Its value is not publishable — it is the precondition for believing anything below.
Failing it invalidates every other entry.

**Rank 1 — budget-indexed maxima in LLM / ML evaluation.** The highest product of the two
factors, for five reasons that stack: there is an **analytic ground truth** (the pinned-*k*
combinatorial estimator, and the `F(x)^n` order-statistic form of expected max under budget);
there is a **known-correct competing method** whose published estimator was itself shown to
be biased, which is exactly the opening for a resampling approach that needs no i.i.d.
assumption; there is a **published real-world control** — two identical model checkpoints
submitted to the same arena, returning ratings far enough apart to move several leaderboard
positions, which is a one-point version of our null that we can generalise into a full
surface; the **data is public and small**; and the repo **already has the adapter**. The
result would be a lost 2019-era correction reconnected to the leaderboards that most need it.
The risk to check first, and it is serious: if the counts in the chosen dataset are
endogenous, this demonstration lands in the regime where our method is insufficient. Prefer a
dataset with exogenous budgets.

**Rank 2 — the scan-statistic / change-point check.** Already designated in
[`lineage.md`](../../lineage.md) §4 as the falsification test, and still the cleanest external
ground truth we have identified. Downgraded from where the repo currently places it for one
reason this review surfaced: the classical limits are asymptotic and converge slowly, so
agreement at the small *n* a screen actually sees is not what the theory promises. Frame it as
validating the *large-n* limb and use exact order statistics for the small-*n* limb, or the
test will look like a failure when it is a mismatch of regimes.

**Rank 3 — the gene-set-enrichment size-matched null.** Cheap, and uniquely valuable as a
*defensive* result: reproducing a size-matched null with a count-indexed one establishes
equivalence with the nearest prior art on its home ground, which is the reviewer objection
most likely to be fatal. Low novelty, high insurance.

**Rank 4 — virtual screening hit rate versus number tested.** A published empirical curve to
reproduce, in a field with money attached and a live methodological argument. More expensive:
the data needs assembling, and the control pool question (which observations carry no effect)
is real work.

**Rank 5 — an A/A empirical null indexed by sample size.** Platforms already resample from
control logs; nobody appears to index it by *n*. Genuinely unoccupied, and immediately useful
to practitioners. Ranked here only because it needs proprietary log data we do not have, and
because two recent items flagged in the research remain unread and could already contain the
construction.

**Do not start with security triage.** It is where the method is most novel and least
contested — and therefore where there is no ground truth, no control pool convention, and no
audience able to check us. It is a second paper, not a first demonstration.

---

## 5. Sources

Grouped by section. ⚠️ marks items whose authors, venue, or year could not be confirmed —
do not cite these as they stand.

**LLM evaluation and leaderboards**
- [Chen et al., *Evaluating Large Language Models Trained on Code*, arXiv:2107.03374 (2021)](https://arxiv.org/abs/2107.03374) · [openai/human-eval](https://github.com/openai/human-eval) — the unbiased pass@k estimator; the repository states there is no unbiased estimate when samples < k
- [Brown et al., *Large Language Monkeys: Scaling Inference Compute with Repeated Sampling*, arXiv:2407.21787 (2024)](https://arxiv.org/abs/2407.21787) — coverage as an explicit function of N
- [Singh et al., *The Leaderboard Illusion*, arXiv:2504.20879 (2025)](https://arxiv.org/abs/2504.20879) · [NeurIPS 2025 Datasets & Benchmarks version](https://papers.neurips.cc/paper_files/paper/2025/file/70a93f260a51123b3c0e33ecd1b4de97-Paper-Datasets_and_Benchmarks_Track.pdf) — states the max-over-variants bias in our own terms
- [Miller, *Adding Error Bars to Evals*, arXiv:2411.00640 (2024)](https://arxiv.org/abs/2411.00640) — abstract only; multiple comparisons and unequal counts **not observed**, which is not the same as absent
- [LMSYS leaderboard update](https://www.lmsys.org/blog/2023-12-07-leaderboard/) — bootstrap CIs and CI-overlap ranks; ⚠️ read via blog snippets, not the paper
- ⚠️ arXiv:2510.05197, arXiv:2508.11847, arXiv:2605.30315, arXiv:2606.17930 — surfaced and relevant; author lists unconfirmed

**Budget-indexed reporting and RL benchmarking**
- [Dodge et al., *Show Your Work: Improved Reporting of Experimental Results*, EMNLP 2019](https://aclanthology.org/D19-1224/) · [arXiv](https://arxiv.org/abs/1909.03004) — *full text*; expected max as an explicit function of budget, `P(V*_n ≤ v) = P(V ≤ v)^n`
- [Tang et al., *Showing Your Work Doesn't Always Work*, ACL 2020](https://aclanthology.org/2020.acl-main.246/) — the above estimator shown biased; unbiased alternative released
- [Henderson et al., *Deep Reinforcement Learning that Matters*, AAAI 2018](https://arxiv.org/abs/1709.06560) — *full text*; identical configurations, split by seed, give significantly different distributions
- [Agarwal et al., *Deep RL at the Edge of the Statistical Precipice*, NeurIPS 2021](https://arxiv.org/abs/2108.13264) · [rliable](https://github.com/google-research/rliable) — *full text*; IQM, stratified bootstrap, performance profiles. ⚠️ the claims that max-over-seeds is critiqued in an appendix and that unequal run counts are analysed cohort-by-cohort came through a fetch summariser, not direct reading
- [Colas et al., arXiv:1806.08295](https://arxiv.org/abs/1806.08295) · [Jordan et al., ICML 2020](https://proceedings.mlr.press/v119/jordan20a.html) · [Patterson et al., arXiv:2304.01315](https://arxiv.org/abs/2304.01315)
- [Lucic et al., *Are GANs Created Equal?*, NeurIPS 2018](https://arxiv.org/abs/1711.10337) · [Melis et al., ICLR 2018](https://openreview.net/pdf?id=ByJHuTgA-) — budget-matched comparison
- ⚠️ No paper titled "hyperparameter tuning inflates reported performance" exists; the claim is carried by the four items above

**A/B testing, platforms, adaptive experiments**
- [Lee & Shen, *Winner's Curse: Bias Estimation for Total Effects of Features in Online Controlled Experiments*, KDD 2018](https://dl.acm.org/doi/10.1145/3219819.3219905)
- [Deng, *Objective Bayesian Two Sample Hypothesis Testing for Online Controlled Experiments*, WWW 2015](https://alexdeng.github.io/public/files/BayesianAB.pdf) — priors learned from thousands of historical experiments
- [Johari, Pekelis & Walsh, *Always Valid Inference*, arXiv:1512.04922](https://arxiv.org/abs/1512.04922) · [*Operations Research* version](https://pubsonline.informs.org/doi/pdf/10.1287/opre.2021.2135) — corrects stopping-time bias, **not** count-indexed comparability
- [Howard, Ramdas, McAuliffe & Sekhon, *Annals of Statistics* 49(2), 2021](https://projecteuclid.org/journals/annals-of-statistics/volume-49/issue-2/Time-uniform-nonparametric-nonasymptotic-confidence-sequences/10.1214/20-AOS1991.full)
- [Nie, Tian, Taylor & Zou, *Why Adaptively Collected Data Have Negative Bias*, AISTATS 2018](https://proceedings.mlr.press/v84/nie18a.html)
- [Shin, Ramdas & Rinaldo, *Are sample means in multi-armed bandits positively or negatively biased?*, NeurIPS 2019](https://arxiv.org/abs/1905.11397) — separates sampling, stopping and choosing as three signed channels
- [Hadad, Hirshberg, Zhan, Wager & Athey, *PNAS* 118(15), 2021](https://www.pnas.org/doi/10.1073/pnas.2014602118) · [Zhang, Janson & Murphy, NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/hash/6fd86e0ad726b778e37cf270fa0247d7-Abstract.html) · [Deshpande, Javanmard et al., *JASA* 118(542)](https://www.tandfonline.com/doi/abs/10.1080/01621459.2021.1979011)
- [Microsoft ExP, *p-Values for Your p-Values: Validating Metric Trustworthiness by Simulated A/A Tests*](https://www.microsoft.com/en-us/research/group/experimentation-platform-exp/articles/p-values-for-your-p-values-validating-metric-trustworthiness-by-simulated-a-a-tests/) — resamples control logs into an empirical null; explicitly does **not** index by sample size
- [Larsen et al., *Statistical Challenges in Online Controlled Experiments*, *The American Statistician* 2023](https://www.tandfonline.com/doi/full/10.1080/00031305.2023.2257237) — ⚠️ author list unconfirmed; best single survey
- ⚠️ arXiv:2512.03366 and the *Annual Reviews* survey *Demystifying Inference After Adaptive Experiments* — unread, and either could already contain the *n*-indexed construction. **Read before claiming novelty.**

**League tables, shrinkage, small-area estimation**
- [Spiegelhalter, *Funnel plots for comparing institutional performance*, *Statistics in Medicine* 24(8), 2005](https://onlinelibrary.wiley.com/doi/10.1002/sim.1970)
- [Goldstein & Spiegelhalter, *League Tables and Their Limitations*, *JRSS-A* 159(3), 1996](https://www.dcscience.net/Goldstein-Spiegelhalter-1996league-tables-RSS.pdf) — ⚠️ page range differs across indexes (385–409 vs 385–443 with discussion)
- [Wainer, *The Most Dangerous Equation*, *American Scientist* 95(3), 2007](https://www.americanscientist.org/article/the-most-dangerous-equation) — small schools at both tails
- [Kane & Staiger, *The Promise and Pitfalls of Using Imprecise School Accountability Measures*, *JEP* 16(4), 2002](https://www.aeaweb.org/articles?id=10.1257%2F089533002320950993)
- [Efron & Morris, *JASA* 70, 1975, pp. 311–319](https://vincentarelbundock.github.io/Rdatasets/doc/pscl/EfronMorris.html) — ⚠️ issue number unconfirmed · [Morris, *JASA* 78(381), 1983](https://errorstatistics.com/wp-content/uploads/2015/11/morris.pdf)
- [Shen & Louis, *Triple-goal estimates*, *JRSS-B* 60(2), 1998](https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/1467-9868.00135) — good ranks, good histogram and good unit estimates cannot be optimised together
- [Lin, Louis, Paddock & Ridgeway, *Loss Function Based Ranking*, *Bayesian Analysis* 1(4), 2006](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2896056/)
- [Fay & Herriot, *JASA* 74(366), 1979](https://www.tandfonline.com/doi/abs/10.1080/01621459.1979.10482505) — James–Stein under unequal variances · [Rao & Molina, *Small Area Estimation*, 2nd ed., 2015](https://onlinelibrary.wiley.com/doi/book/10.1002/9781118735855)
- [Normand & Shahian, *Statistical Science* 22(2), 2007](https://arxiv.org/abs/0710.4622) · [Health Affairs Forefront on CMS star ratings](https://www.healthaffairs.org/content/forefront/cms-hospital-quality-star-ratings-fail-pass-common-sense-test) — ⚠️ the "40% of five-star hospitals lacked minimum data" figure is trade-press secondary; re-source before use
- [Glickman, *JRSS-C* 48(3), 1999](https://www.glicko.net/research/glicko.pdf) — rating deviation as a count-indexed uncertainty carried alongside the estimate
- [*Elo Uncovered*, arXiv:2311.17295](https://arxiv.org/pdf/2311.17295) · [Simultaneous confidence intervals for ranks, arXiv:1812.05507](https://arxiv.org/pdf/1812.05507) — ⚠️ preprints, metadata only
- ⚠️ **Not verified and not to be cited:** Gelman & Nolan on small schools; a Laird & Louis ranking paper; Efron & Morris, *Scientific American* 1977; the hot-hand literature (not searched at all)

**Virtual screening, HTS, materials**
- [Truchon & Bayly, *JCIM* 2007](https://pubs.acs.org/doi/abs/10.1021/ci600426e) — BEDROC; ⚠️ metadata verified, abstract paywalled and not read; the ratio-dependence description comes from converging secondary sources
- [Mysinger et al., *DUD-E*, *J. Med. Chem.* 2012](https://doi.org/10.1021/jm300687e) · [Chen et al., *PLOS ONE* 14(8):e0220113, 2019](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0220113) · [Wallach & Heifets, *JCIM* 2018](https://pubs.acs.org/doi/10.1021/acs.jcim.7b00403) — ⚠️ title differs between the arXiv/S2 record and the published ACS version · [Tran-Nguyen et al., *LIT-PCBA*, *JCIM* 60(9), 2020](https://pubs.acs.org/doi/10.1021/acs.jcim.0c00155)
- [Lyu et al., *Ultra-large library docking*, *Nature* 2019](https://www.nature.com/articles/s41586-019-0917-9) — hit rates from campaigns of 44 and 549 reported side by side
- [Liu et al., *The impact of Library Size and Scale of Testing on Virtual Screening*, *Nat. Chem. Biol.* 2024](https://www.biorxiv.org/content/10.1101/2024.07.08.602536) — **the field's explicit statement of this bug**: subsampling 1,521 tested molecules shows hit rates converge only in the hundreds
- [Zhang, Chung & Oldenburg, *J. Biomol. Screen.* 4(2), 1999](https://journals.sagepub.com/doi/abs/10.1177/108705719900400206) — Z-factor, assay-level, not replicate-indexed · [Zhang et al., *SSMD*, *J. Biomol. Screen.* 12(4), 2007](https://journals.sagepub.com/doi/10.1177/1087057107300646) — a z-score against a negative reference group, presented as a *ranking* metric
- [Riebesell et al., *Matbench Discovery*, *Nat. Mach. Intell.* 2025](https://www.nature.com/articles/s42256-025-01055-1) — no count-indexed awareness found
- ⚠️ B-score (Brideau et al. 2003) and Malo et al. 2010 on replicate-aware HTS design were not verified from primary records; the latter is the most likely place someone got there first, and should be swept before any novelty claim

**Recommenders**
- [Schnabel et al., *Recommendations as Treatments*, ICML 2016](https://arxiv.org/abs/1602.05352) · [Joachims, Swaminathan & Schnabel, *Unbiased Learning-to-Rank with Biased Feedback*](https://arxiv.org/abs/1608.04468) — ⚠️ WSDM 2017 venue attribution standard but not re-confirmed
- [Krichene & Rendle, *On Sampled Metrics for Item Recommendation*, KDD 2020](https://research.google/pubs/on-sampled-metrics-for-item-recommendation/) — sampled top-k metrics are inconsistent with their exact versions *not even in expectation*, and the distortion is indexed by sample size
- [Ferrari Dacrema, Cremonesi & Jannach, RecSys 2019](https://arxiv.org/abs/1907.06902) · [Ferrari Dacrema, Boglio, Cremonesi & Jannach, *TOIS* 39(2), 2021](https://dl.acm.org/doi/10.1145/3434185) — distinct papers, different author lists

**Max-statistic nulls, empirical nulls, analytic ground truth**
- [Nichols & Holmes, *Human Brain Mapping* 15(1), 2002](https://www.fil.ion.ucl.ac.uk/spm/doc/papers/NicholsHolmes.pdf) — the permutation max-statistic null · Westfall & Young, *Resampling-Based Multiple Testing*, Wiley 1993 (max-T / min-P)
- [Eklund, Nichols & Knutsson, *PNAS* 113(28), 2016](https://www.pnas.org/doi/10.1073/pnas.1602413113) — parametric cluster inference badly miscalibrated in the tail while permutation held; **cite the [published correction](https://www.pnas.org/doi/10.1073/pnas.1612033113) and the [rebuttal line](https://www.pnas.org/doi/10.1073/pnas.1614502114) alongside it**
- [Efron, *Large-Scale Simultaneous Hypothesis Testing: The Choice of a Null Hypothesis*, *JASA* 99(465), 2004](https://www.stat.cmu.edu/~jiashun/Teaching/F08STAT756/Lectures/Efron.pdf) — *full text*; the conceptual parent, indexed by nothing. Our delta: Efron refits the null, we refit it as a function of *n*
- [Gross & Vitells, *Trial factors for the look elsewhere effect*, *Eur. Phys. J. C* 70(1), 2010](https://arxiv.org/abs/1005.1891) — *full text*; a hybrid template — estimate empirically where it is cheap, extrapolate analytically into the tail
- [Bailey & López de Prado, *The Deflated Sharpe Ratio*, *J. Portfolio Management* 40(5), 2014](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) — *full text*; **two authors only** — a fetch summariser invented a third during this research, which is the failure mode this file exists to guard against. Indexed by trial count, cross-trial variance, sample length, skew and kurtosis
- [Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253) — ⚠️ *Journal of Computational Finance*, exact year and volume inconsistent across sources
- [Harvey, Liu & Zhu, *… and the Cross-Section of Expected Returns*, *RFS* 29(1), 2016](https://academic.oup.com/rfs/article-abstract/29/1/5/1843824)
- [Darling & Erdős, *Duke Math. J.* 23, 1956](https://projecteuclid.org/euclid.dmj/1077466684) · [Glaz, Naus & Wallenstein, *Scan Statistics*, Springer 2001](https://link.springer.com/book/10.1007/978-1-4757-3460-7) · ⚠️ Fisher–Tippett and Gnedenko not consulted as primary sources
- [Zöllner & Pritchard, *AJHG* 80(4), 2007](https://www.cell.com/ajhg/fulltext/S0002-9297(07)61097-0) — winner's curse by conditional likelihood
- [GSEA documentation](https://www.genepattern.org/modules/docs/GSEA/17/) · [GOAT, *Communications Biology* 2024](https://www.nature.com/articles/s42003-024-06454-5) — the size-matched empirical null: the nearest thing in construction to `sieve`
- [*Two Types of Size-Biased Samples When Modeling Extreme Phenomena*, *Stats* 7(4):81](https://doi.org/10.3390/stats7040081) — ⚠️ metadata only; the closest formal statement of the bug's mathematical form

**Security triage**
- [Axelsson, *The base-rate fallacy and the difficulty of intrusion detection*, *ACM TISSEC* 3(3), 2000](https://dl.acm.org/doi/10.1145/357830.357849) — **a different bug**; adjacent, not ours
- [Microsoft Sentinel UEBA](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics) · [Exabeam on scored events](https://www.exabeam.com/blog/ueba/understanding-ueba-from-raw-events-to-scored-events/) — practitioner documentation; normalisation is by peer group, not by event count
- Astronomy transient detection: **not searched** — the search budget was exhausted. The hypothesis that periodogram false-alarm probabilities are a max-over-frequencies null is untested and must not be reported as a finding.
