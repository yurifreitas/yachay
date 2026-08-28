# 0004 — Fit nulls on blocks, not rows

**Status:** accepted · written 2026-08-26 before the work; **prediction scored correct the same day**
**Supersedes:** nothing. Amends the implementation under 0001.

## Context

`fit_null` resamples control **rows** as if they were independent draws. Three independent
lines of evidence say this is wrong:

1. **Predicted internally.** SNPs in linkage disequilibrium are not independent draws, so
   the planned GWAS adapter will need block resampling (`../lineage.md` §5).
2. **Measured internally.** Nonessential control genes calibrate to a mean z of −4.09
   rather than ~0. Leading hypothesis: pooling control observations across genes models the
   spread of a *draw from the pool*, not of a *gene*, and real genes carry between-gene
   variance the pooled draw does not (`../lineage.md` §8a).
3. **Published externally.** Forster et al. (*Biostatistics* 26(1), 2025) prove that
   Tweedie's formula is biased under strong dependence between estimates and repair it with
   density convolution plus bagging, reporting that ~20 bootstrap samples suffice to
   stabilise the estimate.

Three routes to one correction is the strongest evidence available that the correction is
real.

## Decision (proposed)

1. Add an `n_eff` concept distinct from the raw count `n`.
2. Allow the control pool to carry a **block label** (gene, LD block, lineage, batch) and
   resample blocks rather than rows.
3. Bootstrap the fitted null so every calibrated number can carry an interval — which also
   closes the repository's top standards gap (GUM, `../references/standards.md` §7 item 1).

## Consequences (anticipated)

**Expected to fix.** The −4.09 control offset, if the hypothesis is right. This is a
**prediction**, recorded before the work so it can be scored rather than rationalised: if
block resampling does not move the control mean materially toward zero, the hypothesis is
wrong and this record is superseded rather than quietly amended.

> **Scored 2026-08-26: correct.** A gene-shaped null puts the nonessential controls at
> **mean z = +0.017, sd ≈ 1**, from −4.09. The decomposition reproduces the old number
> exactly (−0.2112 / 0.0517 = −4.08). Evidence in `../references/deep/internal-audit.md`.

**Expected to cost.** Blocks mean fewer effective draws, so the null's own uncertainty
rises. That is not a regression — it is the uncertainty that was always there, previously
hidden by treating correlated rows as independent.

**Open question.** Whether to adopt Forster et al.'s estimator or only their diagnosis. The
current position is diagnosis only: they are better at effect-size estimation and this
library should not compete there (`../references/state-of-the-art.md` §4).
