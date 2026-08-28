# State of the art — what the field already knows, and where the opening is

> **Role:** the frontier. What is settled, what moved recently, what directly challenges
> this library's claim, and which approach can actually advance from here.
> **Last revised:** 2026-08-26 · **Source:** web search and abstracts read on 2026-08-26;
> ⚠️ **abstracts and news reports, not full texts** — the three claims marked ⚠️ must be
> checked against the primary article before they are cited in a manuscript.
>
> Exists for the same reason `knee/docs/ESTADO_DA_ARTE.md` does: the most expensive wrong
> premise is assuming the frontier does something it does not.
>
> ⚠️ **§4 item 1 was corrected on 2026-08-26**, the day it was written, by
> [`deep/selection-bias.md`](deep/selection-bias.md). The original claimed a novelty that
> Gelman & Price (1999) and Hartman et al. (2024) already hold. The correction is left
> visible rather than silently rewritten.

---

## 1. The direct challenge to this library

**Forster et al., *Biostatistics* 26(1), 2025 — "The winner's curse under dependence:
repairing empirical Bayes using convoluted densities".** A comparative study of
winner's-curse corrections across four method families (separate estimation, conditional
likelihood, bootstrap, empirical Bayes). Two of its findings land squarely on this
repository:

**(a) The challenge.** They report that a bootstrap method and empirical Bayes with density
convolution correct the bias best, but that *"this correction generally does not improve the
feature ranking"*. Ranking is the only thing `sieve` claims to fix.

**(b) The confirmation.** They prove Tweedie's formula is biased under strong dependence
between estimates, and repair it by convolving the density estimator. That is the same
failure `docs/lineage.md` §5 predicted for us from a different direction: **correlated
observations break a null fitted as if they were independent draws.**

### The answer, and it is a scope condition — now enforced by a test

Their setting estimates every feature with the **same precision**. There, the correction is
one common monotone transform applied to every estimate, so the ordering cannot change ---
no method can improve a ranking it is incapable of altering. `sieve` lives in the
complement: **observation counts vary**, the transform differs per entity, and the ordering
therefore does move.

This is not a rhetorical escape; it is falsifiable, and `tests/test_ranking_scope.py` now
pins both halves:

- `test_equal_counts_cannot_change_the_ranking` — with homogeneous $n$, calibration must
  reorder **nothing**. The library agrees with the literature in the literature's regime.
- `test_varying_counts_do_change_the_ranking` — with heterogeneous $n$ and no real effect
  anywhere, entities must calibrate near zero at **both** counts, which is precisely the
  comparability a ranking needs.

**Measured support, from this repository's own NF2 run (2026-08-26):** contrasting 32
NF2-null cell lines against 1146 wildtype, the raw contrast ranks the known-true Hippo axis
at median **12 738 of 17 916 — worse than random**, because a top-$k$ over 32 lines is not
comparable with a top-$k$ over 1146. After calibration it moves to **5 216**, better than
random. The ranking changed, and it changed toward biology known independently. That is the
regime Forster et al. do not evaluate.

⚠️ Read from the abstract only. Before citing: confirm whether their simulations include a
varying-precision arm, and whether "ranking" there means the ordering of selected features
or the selection itself.

---

## 2. The NF2 therapeutic frontier — the Hippo bet is being placed right now

This changes what a shortlist for NF2 is *for*.

- **VT3989 (Vivace Therapeutics), a first-in-class YAP–TEAD inhibitor**, reported phase 1/2
  results at ESMO 2025 and in *Nature Medicine* (2025): overall response rate **26 % in 47
  mesothelioma patients** at clinically optimised doses (**32 %** in 22 patients when a
  urine albumin:creatinine threshold is also applied), disease control rate ~86 %, mostly
  grade 1–2 toxicity with reversible proteinuria. **FDA orphan drug and fast-track
  designation**; phase III planned for **H1 2026**.
- **IK-930** (Ikena), another TEAD-palmitoylation inhibitor, ran a phase 1 and was
  **terminated for sponsor strategic reasons** — not, per the reports, for a safety signal.
- ESMO 2025 framed two TEAD inhibitors as the first evidence of efficacy for targeted
  therapy in mesothelioma at all.

**What this means for us, concretely.** The pathway our positive control tests is the
pathway the clinic is now betting on, in the exact genotype (NF2-loss / merlin-loss)
DepMap lets us subset. Two consequences:

1. **The positive control is well-chosen** — it is not a convenient internal marker, it is
   the axis with a phase III behind it.
2. **The shortlist's value moves downstream.** With YAP–TEAD entering registrational
   trials, the useful question is no longer "is Hippo the target" but **"what else does an
   NF2-null cell need, that a TEAD inhibitor will not cover"** — resistance and combination
   partners. That is a selective-dependency question inside a small subgroup, which is
   exactly this library's shape.

⚠️ Trial numbers above come from conference and news reporting. Verify against the *Nature
Medicine* paper before any manuscript use.

---

## 3. The DepMap frontier — and why it makes this problem worse, not better

- **Next-generation 3D models** (*Nature*, 2026): 147 genome-scale CRISPR screens in
  organoids and spheroids across 10 cancer types, expanding DepMap into molecular subtypes
  the 2D panel missed.
- **Pan-cancer biomarker blueprint** (bioRxiv, 2025) and a clinically informed dependency
  map with a target-prioritisation framework (*Cancer Cell*, 2023) — the field's own
  shortlisting machinery.
- Standard practice for biomarker-associated dependency remains: contrast the mutant group
  against the rest, correct genome-wide with FDR.

**The opening this creates.** Every one of these advances *shrinks* the subgroups being
contrasted — a molecular subtype in an organoid panel has fewer lines than a lineage in the
2D panel. The inflation of a top-$k$ statistic grows as $n$ falls. So the frontier is moving
toward the regime where an uncorrected subgroup contrast is **most** wrong, and the field's
standard correction (FDR) addresses the cutoff, not the ordering.

---

## 4. Which approach can advance — ranked by expected value

**1. Own the heterogeneous-$n$ regime — but claim far less than this section originally
did.** ⚠️ **Corrected 2026-08-26 the same day it was written.** The original text here said
this was "a defensible contribution that nobody is currently making. **This is the paper.**"
That was wrong, and the adversarial review found it wrong within hours:

- **Gelman & Price (1999)** state the confound *and* the z-indexed-by-$n$ remedy, and
  describe the confound itself as *"well known"* in 1999.
- **Hartman et al. (2024)**, *Annals of Applied Statistics* 18(1), publish an
  **individualised empirical null indexed by centre size**, then z, then rank — the same
  three-step shape.
- **GSEA (2005)** and **VEGAS (2010)** both build empirical nulls of genuine *selection*
  statistics calibrated to entity size.

What survives is narrow and is set out in
[`deep/selection-bias.md`](deep/selection-bias.md) §5: operator generality, a control-pool
null rather than a model fitted to the analysis data, correcting the null's **mean and sd**
over a grid of $n$ rather than one or the other, and the LLM-leaderboard application. That
is a methods contribution, not a conceptual one, and it must be framed as such.

**2. Fix the dependence problem — the field just published the direction.** Forster et al.
repair empirical Bayes under dependence by density convolution and bagging, and report that
as few as ~20 bootstrap samples stabilise it. Our predicted flaw (`lineage.md` §5, §8a) is
the same problem in a different estimator: rows resampled as if independent. **Adopt their
diagnosis, not their estimator** — fit the null on blocks (gene-shaped, LD-shaped,
lineage-shaped) and bootstrap it. This closes the `−4.09` control anomaly and the missing
intervals in one move.

**3. Target the subgroup-contrast pattern directly.** "Mutant vs rest, FDR-corrected" is
standard practice across DepMap analyses. Our NF2 run measured what it costs: a known-true
axis ranked worse than random on the raw contrast. Generalising that measurement across
many genotype subgroups — not just NF2 — would be an empirical claim about a widely used
method, testable with data already on disk.

**4. Do not compete on effect-size estimation.** Bootstrap and convoluted empirical Bayes
already do that better than a resampled null will. Cede it, cite it, and stay on ranking
and comparability.

---

## Sources

- [The winner's curse under dependence (Biostatistics 2025)](https://academic.oup.com/biostatistics/article-abstract/26/1/kxaf025/8242203) · [preprint](https://www.biorxiv.org/content/10.1101/2023.09.22.558978v3)
- [Review of statistical corrections for winner's curse (PLOS Genetics)](https://journals.plos.org/plosgenetics/article?id=10.1371%2Fjournal.pgen.1010546)
- [YAP/TEAD inhibitor VT3989 phase 1/2 (Nature Medicine 2025)](https://www.nature.com/articles/s41591-025-04029-3) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/41111090/)
- [ESMO 2025 daily reporter — two TEAD inhibitors in mesothelioma](https://dailyreporter.esmo.org/esmo-congress-2025/thoracic-malignancies/data-from-two-novel-tead-inhibitors-provide-the-first-evidence-for-the-efficacy-and-safety-of-targeted-treatments-in-mesothelioma)
- [FDA fast track for VT3989 (OncLive)](https://www.onclive.com/view/fda-grants-fast-track-designation-to-vt3989-for-unresectable-mesothelioma)
- [MD Anderson newsroom — ESMO 2025 VT3989](https://www.mdanderson.org/newsroom/research-newsroom/esmo-2025--vt3989-continues-to-show-promising-early-results-in-p.h00-159780390.html)
- [A dependency map enhanced with next-generation 3D cancer models (Nature 2026)](https://www.nature.com/articles/s41586-026-10843-7)
- [The present and future of the Cancer Dependency Map (Nature Reviews Cancer)](https://www.nature.com/articles/s41568-024-00763-x)
- [Pan-cancer biomarker analysis from DepMap (bioRxiv 2025)](https://www.biorxiv.org/content/10.1101/2025.02.07.637152v2.full)
- [Clinically informed map of dependencies and target prioritisation (Cancer Cell 2023)](https://www.sciencedirect.com/science/article/pii/S1535610823004440)
