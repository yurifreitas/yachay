# DepMap methods — what the field does, and what we got wrong

> **Role:** lane 2 of the deep review. Briefed to break the NF2 subgroup analysis rather
> than confirm it, by reading the field's *practice* — the statistical recipes actually
> used for genotype-selective dependency on DepMap — and holding our run against them.
> **Last revised:** 2026-08-26 · **State:** verdict settled and **reproduced numerically
> against the data on disk**; §3 and §5 carry a mix of full-text reading, abstract-only
> reading, and items still marked ⚠️ unverified. Genealogy in
> [`../../lineage.md`](../../lineage.md).
>
> Verification status per claim: numbers in §1, §2 and §4 were computed by this lane
> against `data/depmap/` on 2026-08-26 and can be re-derived. Claims attributed to papers
> are marked **[full text]**, **[abstract only]**, or ⚠️ where the source was reached
> second-hand and has not been read.

---

## 1. Verdict on our NF2 analysis

**Blunt version: the biology was there the whole time. Our statistic threw it away.**

The run in `out/NF2_FINDINGS.md` reports the Hippo axis at median rank 12,738 raw and
5,216 calibrated of 17,916, and declares the positive control NOT RECOVERED. This lane
re-ran the *identical* contrast — the same 32 damaging-mutation NF2-null lines, the same
1,146 wildtype, the same `CRISPRGeneEffect.csv` — and swapped only the statistic:

| statistic | YAP1 | WWTR1 | TEAD1 | median of the 8 HIPPO genes |
|---|---|---|---|---|
| our top-10 mean, calibrated and differenced | 11,827 | 1,159 | 958 | **5,216** |
| our top-10 mean, raw | 17,439 | 14,668 | 12,408 | **12,738** |
| plain difference in group means | **30** | **55** | **27** | **1,094** |
| Welch *t* | 361 | 266 | 248 | **1,000** |
| rank-transform (Mann–Whitney-equivalent) | 23 | 404 | 416 | **1,000** |

Difference in means puts YAP1 at rank 30 and TEAD1 at rank 27 out of 17,916 — the 0.2nd
percentile. Effect sizes, computed here: YAP1 Cohen's *d* = +0.52, WWTR1 +0.53,
TEAD1 +0.66 (null-group mean minus wildtype mean, over the wildtype SD, on the
sign-flipped matrix where larger = more dependent). This is a real, textbook-sized,
easily detectable effect that the standard method finds without difficulty.

**What is defensible.**
- The subgroup definition from damaging mutations is *adequate*. It is not the problem.
  Adding copy-number deletion helps (§2) but the signal is already strong without it.
- Running Stage 2 (power) before ranking is right, and the field does not do it.
- The lineage check is right in kind, and passes: dropping Pleura, Lung, or CNS/Brain
  from the null group moves the YAP1/WWTR1/TEAD1 median rank only from 266 to 495–642.
  Lineage-centring every gene within its lineage before the contrast leaves it at 496.
  **The NF2 effect is not a lineage effect.** That answers the Stage 3 threat that
  `nf2.md` §5 calls "the main threat to this analysis" — it is not.
- The repository's instinct that a small-*n* top-*k* needs calibration is correct in
  general. It is just the wrong operator for a *contrast*.

**What is likely wrong.**
- The positive-control gene set. Four of its eight members are upstream tumour
  suppressors whose knockout should show *no* NF2-selective dependency, or the opposite
  sign, on the pathway logic the repo itself draws in `nf2.md` §3. See §5.
- Calibrating the two groups against two separately fitted nulls and differencing the
  *z*. Live question 2 in the lane index asks whether this is coherent. It is not:
  z_null and z_wt are standardised by different SDs (a top-10 mean of 32 draws and a
  top-10 mean of 1,146 draws have wildly different null spread), so their difference is
  not on any interpretable scale. Empirically it is *better* than the raw top-10
  contrast (5,216 vs 12,738) because it partly undoes the *n* asymmetry — but partly is
  not a method.

**What is definitely wrong.**
The top-*k* mean applied to both groups with the same *k*. With k = 10, the null-group
score is the mean of the 10 most dependent of **32** lines — roughly the top 31% — and
the wildtype score is the mean of the 10 most dependent of **1,146** — roughly the top
0.9%. These are different quantiles of the same distribution. Differencing them asks
"is the 31st percentile of the small group below the 0.9th percentile of the large
group", which for essentially every gene in the genome is no. That is why the raw
contrast is *negative for every Hippo gene* (−0.855 to −0.234 in `NF2_FINDINGS.md`) and
why the Hippo median lands at 12,738, worse than random: the statistic is dominated by
group size, and the null group is the small one. This is not a subtle bias that
calibration shrinks. It is a category error in the comparison, and it is the single
correction that matters.

---

## 2. The copy-number circularity question

**Answered: there is no circularity for the genes we care about, and only a mild
attenuation. This is not what broke the analysis.** ⚠️ One residual risk, named below,
is genuinely unresolved.

Chronos removes copy-number bias with a two-dimensional cubic spline whose two inputs are
**(i) the copy number of the knocked-out gene in that cell line** and (ii) that gene's
mean effect across all lines **[full text, Dempster et al. Genome Biology 2021]**. The
correction is indexed by the *target* gene's copy number, not by the copy number of any
gene used to define a contrast group.

The consequence is clean and worth stating plainly:

- **Trans dependencies are untouched.** When we ask whether YAP1 knockout is more lethal
  in NF2-null lines, the correction applied to the YAP1 column uses *YAP1's* copy number
  in each line. NF2's copy number never enters. There is no circularity, no attenuation
  by construction, and no reason for the Hippo signal to be suppressed. The measured
  Cohen's *d* of +0.52 to +0.66 confirms it empirically.
- **Cis dependencies are attenuated, correctly.** When the knocked-out gene *is* NF2, or
  is a 22q12 neighbour co-deleted with it, the correction does exactly what it is
  designed to do and removes the copy-number-driven part of the effect. Any hit on
  chromosome 22 from this contrast should be treated as suspect on those grounds alone.
- **The pattern is visible in our own data as a negative control that passes.** NF2's own
  knockout effect is +0.093 *less* growth-promoting in NF2-mutant lines than in wildtype
  (null-group mean −0.250 vs wildtype −0.343 on the sign-flipped matrix; both negative,
  i.e. losing NF2 helps). You cannot lose what you have already lost. That is the right
  sign and the right magnitude, and it is evidence the CN correction has not sterilised
  the NF2 locus.

**What remains unresolved ⚠️.** If the subgroup is redefined to include deep deletions
(§7 change 3), the NF2-null group becomes enriched for lines with broad 22q loss. Genes
physically near NF2 will then differ between groups for a reason that is co-deletion, not
biology, and the Chronos correction is a smooth spline that will not fully absorb a
group-level chromosomal difference. **How to test it:** after the corrected contrast,
plot the test statistic against chromosomal position and check for a bump over 22q. If
one exists, exclude chromosome 22 from the shortlist or add per-gene copy number as a
covariate in the linear model. The screen-level uncorrected Chronos files DepMap
publishes (`Screen*`, described by J. Dempster on the DepMap forum **[full text]**) allow
the whole contrast to be re-run without CN correction as a sensitivity check; that is the
definitive test and it has not been done here.

**Verdict on live question 3 in the lane index: closed, negative.** The hypothesis was
reasonable and is wrong. The Chronos correction is indexed by the target gene, not by the
grouping gene.

---

## 3. What the field actually does

### 3.1 The DepMap portal's own two-class comparison

For each feature, a simple linear regression is fitted against the phenotype; the
coefficient and standard error are passed through **adaptive shrinkage** (`ashr`,
Stephens 2017) to give moderated effect sizes and FDR *q*-values. For a binary feature
this is "roughly equivalent to a *t*-test with a pooled variance estimate" — the words of
the DepMap team on their own forum **[full text, forum thread 211]**. Earlier
documentation refers to `run_lm_stats_limma` in `broadinstitute/cdsr_models`; a 2024
follow-up asking whether that is still the implementation went unanswered ⚠️, so the
current portal code path is not confirmed.

**What it assumes:** equal variance between groups; that the effect of interest is a
difference in *means*; that shrinkage across genes is appropriate (i.e. that most genes
have no effect). It does not assume equal group sizes — pooled-variance regression
handles 32 vs 1,146 without complaint, which is precisely the property our statistic
lacks.

### 3.2 Moderated *t* / limma, and why it beats Welch here

This lane's Welch *t* run is a live demonstration of why the field moderates. The top 25
Welch hits in our contrast are `DNTTIP2, ERBIN, FAU, ZNF80, CASR, DDX23, MAP3K1, FIBP,
… RPS19, GTPBP4, TRIP13, … RPS18, EEF1A1` — ribosomal and translation-machinery genes
with tiny within-group variance, which is the classic small-*n* Welch failure: divide by
an underestimated SD and get a large *t* from nothing. Note that Welch also ranks the
Hippo genes *worse* than plain difference-in-means (median 1,000 vs 1,094, but YAP1 361
vs 30). Variance shrinkage across the 17,916 genes is what fixes this, and it is the
reason limma-style empirical Bayes is the default in this literature.

### 3.3 Systematic ANOVA with covariates (Sanger / Iorio lineage)

Pacini, Iorio et al., *Cancer Cell* 2024, "A comprehensive clinically informed map of
dependencies in cancer cells and framework for target prioritization"
(doi:10.1016/j.ccell.2023.12.016) builds the second-generation dependency map over 930
annotated lines and derives marker–dependency associations across CRISPR screens
**[abstract only — the full text is paywalled and was not read by this lane]**. ⚠️ The
specific covariates, minimum group size, FDR and effect-size thresholds in its STAR
Methods are **not verified here** and must be read before being quoted. What is
verified: the framework exists, is the current standard for target prioritisation, and
combines the statistical association with tractability and clinical evidence rather than
ranking on the dependency statistic alone.

Project Score (Behan et al., *Nature* 2019; Dwane et al., *NAR* 2021 database paper,
doi:10.1093/nar/gkaa882) covers 18,009 genes across 323 models and ranks candidate
targets through an oncology target-prioritisation pipeline that folds in genetic
biomarkers, clinical datasets, and pharmaceutical tractability **[abstract only]**.

### 3.4 Selectivity metrics — and the distinction we have been blurring

- **NormLRT / skewed-LRT.** Fit each gene's cross-line dependency profile to a Gaussian
  and to a skew-*t*, and score the likelihood ratio. High NormLRT = the profile is
  non-normal = the gene is a "strongly selective dependency" (SSD). Implemented with
  `MASS` for the normal fit and `sn::st.mple` for the skew-*t*. It is agnostic to the
  direction of skew, sensitive to single-line outliers, and folds in effect magnitude
  **[secondary sources; the McDonald et al. 2017 / Meyers et al. 2017 primaries were not
  read by this lane ⚠️]**.
- **shinyDepMap** (Shimada, Bachman, Muhlich, Mitchison, *eLife* 2021,
  doi:10.7554/eLife.57116) derives two orthogonal per-gene numbers: **efficacy** (how
  much growth loss in sensitive lines) and **selectivity** (how much essentiality varies
  across lines), and clusters genes on dependency-profile similarity **[abstract +
  summary; full text not read ⚠️]**.

**The distinction that matters for us.** NormLRT and shinyDepMap selectivity are
*unsupervised* — "is this gene selective at all, against some unknown grouping". Our NF2
question is *supervised* — "is this gene selective **with respect to this specific,
known grouping**". A top-*k* mean is a crude unsupervised selectivity operator. The
DepMap adapter is right to use one for the general "selective dependency" question
(`src/sieve/adapters/depmap/__init__.py` is correct on its own terms). It is the wrong
tool the moment a group label exists, and `analyses/nf2_subgroup.py` inherited it by
analogy rather than by argument.

### 3.5 Handling unequal group sizes

Nothing in the field uses a same-*k* order statistic in both arms. Every method above is
either a moment statistic (mean difference, standardised), a rank statistic
(Mann–Whitney), or a regression coefficient — all of which are *n*-invariant in
expectation under the null. This is not an oversight in the literature; it is the
property that makes a contrast a contrast.

---

## 4. Our statistic vs the standard one

| | top-*k* mean, same *k* both arms | difference in group means |
|---|---|---|
| what it estimates | difference between two *different quantiles* | difference between two *distribution centres* |
| behaviour under equal group sizes | fine | fine |
| behaviour at 32 vs 1,146 | **broken** — estimand depends on *n* | unbiased |
| sensitivity to a within-group subset | high, by design | low |
| robustness to outliers | low | moderate (rank version: high) |
| published precedent for a subgroup contrast | **none found** ⚠️ | universal |

**What we gain from top-*k*.** A genuine advantage that the mean does not have: if only
5 of the 32 NF2-null lines are truly merlin-dead and the other 27 are mislabelled, the
mean dilutes toward zero while a top-5 mean does not. That is a real scenario in a
mutation-called subgroup. The honest way to keep it is a **top-*q* quantile** — the same
*fraction* of each group, not the same count — or, better, to keep the mean difference as
the primary statistic and report a top-*k*-based secondary as a sensitivity analysis for
heterogeneity within the null group.

**What we lose.** Everything. The estimand is not comparable across arms, the null is not
shared, the *z*-difference has no scale, and the operator inherits the winner's-curse
inflation that Stage 1 exists to correct — in a setting where the standard statistic has
no winner's curse to correct in the first place. The repository's calibration machinery
is solving a problem it created.

**Precedent search ⚠️:** this lane found **no published example** of top-*k*-within-
subgroup scoring used for a genotype contrast on DepMap. Absence of evidence from a
handful of searches is weak evidence, but it should be treated as a warning: if the
operator were useful here, someone would have used it.

---

## 5. A corrected positive-control gene set for NF2

The current control set — `YAP1, WWTR1, TEAD1-4, LATS1, LATS2` — is **wrong in direction
for half its members**, and the repo's own pathway diagram says so:

```
merlin (NF2) ──▶ LATS1/2 ──▶ YAP/TAZ held cytoplasmic
```

`LATS1`, `LATS2`, `STK3`, `STK4`, `SAV1`, `MOB1A/B` sit **upstream** of the lesion. In an
NF2-null cell the pathway is already off; knocking out another brake should do nothing,
or should *help* the cell. Our data agree: LATS2 Cohen's *d* = **−0.12** (rank 12,916),
TEAD2 *d* = −0.02. Scoring those as positive controls and then failing the analysis when
they rank low is scoring the pipeline against biology that would refute the pathway if it
were true.

`TEAD2` and `TEAD3` fail for a different reason: paralog redundancy. Kanai, Norton,
Stern et al., *Cancers* 2024, 16(5):852, doi:10.3390/cancers16050852 state directly:
"The DepMap dependency data are based on the CRISPR-mediated knockout of individual
genes, so there could be compensation of YAP or TAZ for each other. TEADs could also
compensate for one another." **[full text of the relevant passage read]**. The same
paper reports that YAP1/WWTR1/TEAD *expression* does not predict YAP/TAZ/TEAD dependency
well, and that a YAP/TAZ activity signature does better — relevant if we ever want a
graded rather than binary group label.

**Proposed replacement, in three tiers:**

- **Tier 1 — must recover, or the pipeline is broken.** `YAP1`, `WWTR1`, `TEAD1`.
  Measured here at *d* = +0.52, +0.53, +0.66; ranks 30, 55, 27 under difference-in-means.
  TEAD1 is the appropriate TEAD because it is the broadly expressed paralog; `TEAD4`
  (*d* = +0.35, rank 650) is a reasonable tier-1.5 addition.
- **Tier 2 — should trend positive, weaker, do not gate on it.** `TEAD4`. Paralog-buffered
  members can be assessed as a *set* (mean rank of YAP1+WWTR1+TEAD1-4) but not
  individually.
- **Tier 3 — negative controls, must NOT rise.** `LATS1`, `LATS2`, `STK3`, `STK4`,
  `SAV1`, `MOB1A`, `MOB1B`, and `NF2` itself. A control set that can only fail in one
  direction is not a control — `nf2.md` §6b says this and the code does not implement it.
  `NF2`'s own behaviour (+0.093 toward zero, i.e. knockout is less beneficial in
  already-null lines) is the strongest available internal check and should be asserted.

**Beyond Hippo — reported NF2/merlin-null dependencies, all ⚠️ abstract-only, none
verified against our matrix by this lane:**

- `G6PD` and `ACSL3` as synthetic-lethal partners of NF2 in Schwann cells, via NADPH /
  redox and lipid biogenesis — the redundancy argument given is that G6PD and `ME1`
  redundantly supply cytosolic NADPH (PMC11180199).
- `PAK2` — inactivation suppresses NF2-deficient mesothelioma in *Nf2/Cdkn2a* conditional
  knockout mice.
- `SMG6` — reported synthetic lethal with LATS2 inactivation in mesothelioma.
- BCL-2 family + YAP combination lethality in RASA1/NF2-deficient gastric cancer
  (PMC10510129).

These are candidates for *widening* the control set only after they are checked in our
own matrix. Adding an unverified gene to a positive control converts the control into a
wish.

**Do not use `MTOR`, `RPTOR`, `PTK2`, `SRC`, `ERBB2/3`, `PDGFRB`** (the `MERLIN_ADJACENT`
list in `nf2.md` §6b) as controls. `nf2.md` itself calls those axes "weaker and less
consistent"; they belong in discussion, not in a gate.

---

## 6. Confounders we are not controlling

| confounder | status in `nf2_subgroup.py` | evidence / recommendation |
|---|---|---|
| **lineage** | tested by dropping the top lineage | **measured here and it is not the problem.** Lineage-centring leaves the tier-1 median rank at 496 vs 266 baseline. Keep the check; stop calling it the main threat. |
| **screen quality** | not controlled | `AchillesScreenQCReport.csv` is already on disk and unused. Chronos models screen-quality factors explicitly (efficacy, contamination) **[full text]**, but residual per-screen quality still correlates with effect magnitude. Add as a covariate or at least as a stratification check. |
| **library (Avana vs KY)** | not controlled | DepMap staff explicitly recommend checking libraries separately when a contrast misbehaves **[forum, full text]**. Not done. |
| **growth rate / doubling time** | not controlled | Slow-growing lines show compressed effects for all genes; if NF2-null lines grow differently this is a global scale confound. Not in the files on disk. ⚠️ |
| **ploidy / copy number** | not controlled | §2. The 22q co-deletion risk becomes live the moment CN defines the subgroup. |
| **MSI status, mutation burden** | not controlled | Standard covariates in the Sanger framework ⚠️ (not verified from STAR Methods). Not in the files on disk. |
| **culture medium** | not controlled | In `Model.csv`; unused. Confounded with lineage. |
| **paralog buffering** | not controlled, and it silently corrupts the control set | §5. This is a confounder of the *hypothesis*, not of the data, and it is the one nobody writes down. |

---

## 7. Concrete changes to `analyses/nf2_subgroup.py`, in priority order

1. **Replace the contrast statistic with a difference in group means, moderated.**
   Primary statistic: `mean(null) − mean(wt)` per gene, standardised by a
   variance-shrunk pooled SD (shrink the per-gene pooled variance toward the genome-wide
   median — a two-line empirical-Bayes step, no new dependency). Report the plain mean
   difference and Cohen's *d* alongside. Delete the `score_subset` top-*k* path from the
   contrast entirely, or demote it to a labelled sensitivity analysis. **This one change
   moves the tier-1 genes from rank ~1,000–12,000 to rank ~30.** Everything below is
   secondary.
2. **Fix the positive control.** Split `HIPPO` into `TIER1 = [YAP1, WWTR1, TEAD1]`,
   `TIER2 = [TEAD4]`, and `NEGATIVE = [LATS1, LATS2, STK3, STK4, SAV1, MOB1A, MOB1B,
   NF2]`. Gate on tier 1 rising **and** the negatives not rising. Assert the NF2 sign
   check explicitly. The current gate can fail for being right.
3. **Add copy-number deletion to the subgroup definition — but read the caveat.**
   `OmicsCNGene.csv` **is already on disk** (357 MB, `data/depmap/`), contrary to
   `nf2.md` §5 and the module docstring, both of which say it is not fetched and should
   be corrected. Using `log2(CN+1) < 0.6` as deep loss gives 27 additional null lines
   (59 total). It improves the tier-1 median rank from 266 to ~190 under Welch, and the
   full top-10 Hippo median from 12,738 to 5,981 — a real but second-order gain. Caveat:
   CN is called for only 558 of the 1,178 screened lines, so the wildtype arm collapses
   from 1,146 to 367. Decide deliberately whether that trade is worth it; a defensible
   alternative is to keep the mutation-defined groups as primary and use CN only to
   *exclude* deep-deleted lines from the wildtype arm.
4. **Drop the two-separate-nulls z-difference.** It is not a coherent statistic (lane
   index question 2: answered, it is not). With change 1 the calibration machinery is
   not needed for this analysis at all — which is itself a finding worth recording:
   Stage 1 corrects a bias introduced by choosing an order statistic, and the correct
   move here is not to correct the bias but to not introduce it.
5. **Add a chromosome-22 positional check** on the final statistic, per §2. Cheap;
   guards the one real CN risk.
6. **Add screen-quality and library stratification.** `AchillesScreenQCReport.csv` is on
   disk. At minimum, re-run the contrast within each library and confirm the tier-1 genes
   hold.
7. **State power honestly in Stage 2 using the measured effect size.** At *d* ≈ 0.6 with
   n = 32 vs 1,146, a single-gene two-sided test at α = 0.05 has power around 0.85 — but
   the analysis performs 17,916 tests, and at a Bonferroni-equivalent α the same *d* has
   very little power. The correct statement is: *this design can rank the tier-1 genes
   into the top 0.2%, and cannot establish genome-wide significance for anything.* That
   is a shortlist-generating design, not a discovery-confirming one, and the write-up
   should say so.
8. **Reconsider the group label.** ⚠️ Per Kanai et al. 2024, a YAP/TAZ activity signature
   predicts YAP/TAZ/TEAD dependency better than genotype does. A continuous predictor
   would need a correlation rather than a two-group contrast, which is a different
   analysis — noted as a direction, not a recommendation.

**Do not change** the Stage-2-first ordering, the lineage check, or the refusal to emit a
shortlist when the control fails. Those are the parts of this analysis that are better
than the field's practice, and they are why the wrong answer was caught instead of
published.

---

## 8. Sources

**Read in full by this lane:**

- [Chronos: a cell population dynamics model of CRISPR experiments that improves inference of gene fitness effects](https://www.biorxiv.org/content/10.1101/2021.02.25.432728v1.full) — Dempster et al., preprint of the *Genome Biology* 2021 paper, doi:10.1186/s13059-021-02540-7. Supports §2: the CN correction is a 2D spline over the *targeted gene's* copy number and its mean effect, plus explicit screen-quality factors.
- [Details on methodology of "Two Class Comparison" — DepMap forum](https://forum.depmap.org/t/details-on-methodology-of-two-class-comparison/211) — supports §3.1: linear regression per feature, adaptive shrinkage (doi:10.1093/biostatistics/kxw041), FDR q-values, "roughly equivalent to a t-test with a pooled variance estimate" for binary features.
- [Chronos/CERES analyses without copy number correction — DepMap forum](https://forum.depmap.org/t/chronos-ceres-analyses-without-copy-number-correction/2123) — supports §2 and §6: screen-level uncorrected Chronos files exist; DepMap staff recommend checking Avana vs KY libraries separately.
- [Identification of a Gene Signature That Predicts Dependence upon YAP/TAZ-TEAD](https://pmc.ncbi.nlm.nih.gov/articles/PMC10930532/) — Kanai, Norton, Stern et al., *Cancers* 2024, 16(5):852, doi:10.3390/cancers16050852. Supports §5: explicit paralog-compensation caveat for YAP/TAZ and for TEADs in DepMap single-gene knockout data; expression is a poor predictor of dependency.

**Abstract or summary only — quote with care:**

- [A comprehensive clinically informed map of dependencies in cancer cells and framework for target prioritization](https://pubmed.ncbi.nlm.nih.gov/38215750/) — Pacini, Iorio et al., *Cancer Cell* 2024, doi:10.1016/j.ccell.2023.12.016. §3.3. ⚠️ STAR Methods not read; covariates, minimum group size and thresholds unverified.
- [Project Score database: a resource for investigating cancer cell dependencies and prioritizing therapeutic targets](https://academic.oup.com/nar/article/49/D1/D1365/5929235) — Dwane et al., *NAR* 2021, doi:10.1093/nar/gkaa882. §3.3.
- [shinyDepMap, a tool to identify targetable cancer genes and their functional connections from Cancer Dependency Map data](https://elifesciences.org/articles/57116) — Shimada, Bachman, Muhlich, Mitchison, *eLife* 2021, doi:10.7554/eLife.57116. §3.4.
- [A benchmark of computational methods for correcting biases of established and unknown origin in CRISPR-Cas9 screening data](https://link.springer.com/article/10.1186/s13059-024-03336-1) — *Genome Biology* 2024. §2 context; not read.
- [G6PD and ACSL3 are synthetic lethal partners of NF2 in Schwann cells](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11180199/) — §5. ⚠️
- [Combined inhibition of Bcl-2 family members and YAP induces synthetic lethality in metastatic gastric cancer with RASA1 and NF2 deficiency](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10510129/) — §5. ⚠️
- [Pipeline to evaluate YAP-TEAD inhibitors indicates TEAD inhibition represses NF2-mutant mesothelioma](https://www.life-science-alliance.org/content/8/10/e202503241) — *Life Science Alliance* 2025. §5 context. ⚠️
- [NF2/Merlin Inactivation and Potential Therapeutic Targets in Mesothelioma](https://doi.org/10.3390/ijms19040988) — review; source of the PAK2 and SMG6 claims as reported second-hand. ⚠️ **not read; the primaries behind those two gene claims have not been identified and must be before either gene is used.**

**Not found, and named so nobody assumes it exists:**

- Published guidance on a minimum subgroup size for a DepMap two-class comparison. Several searches, including the DepMap forum and portal documentation, returned nothing. ⚠️ Treat any "n ≥ 5" or "n ≥ 10" rule quoted elsewhere in this repository as folklore until a source is attached.
- Any published use of a top-*k*-within-subgroup statistic for a genotype-defined dependency contrast. §4.

**Computed by this lane, 2026-08-26, against `data/depmap/` (DepMap 24Q4):** every number
in §1, §2, §4, §5 and §6 not attributed to a paper. Reproducible from
`CRISPRGeneEffect.csv`, `OmicsSomaticMutationsMatrixDamaging.csv`, `OmicsCNGene.csv` and
`Model.csv` with the 32/1,146 split already in `analyses/nf2_subgroup.py`.
