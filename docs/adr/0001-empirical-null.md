# 0001 — Fit the null empirically from controls, not parametrically

> **Role:** the decision to fit the null from real controls rather than from a distributional assumption.
> **Last revised:** 2026-08-29 · **State:** accepted, ⚠️ back-filled.

**Status:** accepted · ⚠️ back-filled 2026-08-26 from a decision taken earlier
**Supersedes:** nothing

## Context

A selection operator (max, top-k mean, quantile, best-of-N) applied to noisy estimates is
positively biased, and the bias depends on the number of observations behind the estimate.
The bias can be obtained two ways:

1. **Parametrically** — assume a distribution, use order-statistic theory or a closed-form
   deflation. The deflated Sharpe ratio takes this route.
2. **Empirically** — resample real observations known to carry no effect, apply the same
   statistic, and read the bias off the resulting distribution.

## Decision

Empirically, from the screen's own controls.

## Consequences

**Gained.** The null inherits the screen's real correlation structure, its real heavy
tails, and its real per-entity counts. None of these has to be named or parameterised, and
none can be got wrong by assuming independence that is not there.

**Paid.** The method **requires a control pool** — observations known to carry no effect.
Where there is none, Stage 1 cannot run, and the honest response is to say so rather than
substitute an assumption and keep the name. This is a real limitation and is stated in the
README, the methodology, and the manuscript's limitations section rather than buried.

**Also paid.** The null is only as good as the control definition. If the controls are not
really inert, the bias estimate is contaminated. This is the leading suspect in the
unexplained −4.09 anomaly (`../lineage.md` §8a).