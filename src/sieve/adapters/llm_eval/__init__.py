"""LLM evaluation adapter — the same bug, outside biology.

## Why this belongs in the same library as a CRISPR screen

A prompt-evaluation workbench runs *variants x inputs x N executions* and ranks the
variants by an accuracy aggregate. That is structurally identical to a perturbation
screen:

| perturbation screen              | prompt / model evaluation                |
|----------------------------------|------------------------------------------|
| entity = gene knockout           | entity = prompt variant, model, config   |
| observation = one cell           | observation = one execution on one input |
| score = top-3 of 12 signatures   | score = pass rate, best-of-N, mean judge score |
| observations vary per entity     | **executions vary per variant**          |
| control = non-targeting guides   | control = a variant known to be at baseline |

And the failure is the same failure. Two forms of it, both extremely common:

**1. Best-of-N selection.** Picking the variant with the highest observed score is a
max-order statistic over the variants. With few runs each, the winner is mostly the
variant that got lucky, and its reported score is biased upward — so the number you
publish will not reproduce. This is the "regression to the mean after you ship the
winning prompt" that everyone has experienced and few instrument.

**2. Unequal run budgets.** Iterating on prompts means promising variants get *more*
runs. That makes observation count correlate with expected quality in one direction and
with score inflation in the other. The leaderboard is then partly a ranking of run
count, and which direction it leans is not knowable without calibrating.

The correction is Stage 1, unchanged: resample real baseline executions, apply the same
aggregate, standardize by observation count.

## What "control" means here

You need executions that carry **no treatment effect**, in the same harness. Options, in
descending order of how much you can trust them:

1. A baseline variant run many times — the direct analogue of a non-targeting control.
2. All executions pooled, with the variant label shuffled — a permutation null. Weaker,
   because a real effect contaminates the pool, but always available.

:func:`baseline_pool` builds the first; :func:`permutation_pool` builds the second and
says so in its return value, so a report cannot quietly claim the stronger one.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = [
    "ExecutionLog",
    "baseline_pool",
    "permutation_pool",
    "best_of_n",
    "pass_rate",
    "score_variants",
]


@dataclass(frozen=True)
class ExecutionLog:
    """Long-form execution records: one row per (variant, input, execution).

    Columns:
        variant  str    what is being compared (prompt hash, model id, config name)
        item     str    the input / test case
        outcome  float  the per-execution measurement (0/1 correctness, judge score, ...)
    """

    frame: pd.DataFrame
    variant: str = "variant"
    item: str = "item"
    outcome: str = "outcome"

    def __post_init__(self) -> None:
        missing = [c for c in (self.variant, self.item, self.outcome)
                   if c not in self.frame.columns]
        if missing:
            raise KeyError(f"execution log is missing columns: {missing}")

    def counts(self) -> pd.Series:
        return self.frame.groupby(self.variant).size()

    def matrix(self, variant: str) -> np.ndarray:
        """(executions x items) outcome matrix for one variant, NaN where not run."""
        sub = self.frame[self.frame[self.variant] == variant]
        wide = sub.pivot_table(index=sub.groupby(self.item).cumcount(),
                               columns=self.item, values=self.outcome)
        return wide.to_numpy(dtype=float)


# ---------------------------------------------------------------------------
# aggregates — the statistics people actually rank on
# ---------------------------------------------------------------------------
def pass_rate(block: np.ndarray) -> np.ndarray:
    """Mean outcome. The one aggregate that is NOT a max-order statistic.

    Included as the contrast case: a plain mean is unbiased, so calibration barely moves
    it. If your leaderboard uses this and observation counts vary, you have a variance
    problem, not a bias problem — and the fix is a confidence interval, not Stage 1.
    """
    return np.asarray(block, dtype=float).mean(axis=-1)


def best_of_n(block: np.ndarray) -> np.ndarray:
    """Max outcome — the pass@k / best-of-N selection rule. Badly biased at small N.

    This is the aggregate that makes an LLM leaderboard behave like a screening metric:
    a variant run 50 times has ~50 chances to produce its best output; one run 5 times
    has 5. Ranking them together ranks the run budget.
    """
    return np.asarray(block, dtype=float).max(axis=-1)


def score_variants(
    log: ExecutionLog,
    statistic,
    *,
    min_executions: int = 1,
) -> pd.DataFrame:
    """One row per variant: the aggregate plus the execution count behind it.

    Satisfies :func:`sieve.contracts.entity_scores`, so every stage consumes it.
    """
    rows = []
    for variant, sub in log.frame.groupby(log.variant):
        vals = sub[log.outcome].to_numpy(dtype=float)
        vals = vals[np.isfinite(vals)]
        if vals.size < min_executions:
            continue
        rows.append({
            "entity": str(variant),
            "score": float(statistic(vals[None, :])[0]),
            "n": int(vals.size),
        })
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# control pools
# ---------------------------------------------------------------------------
def baseline_pool(log: ExecutionLog, baseline_variant: str, *, features: int = 1) -> np.ndarray:
    """Control observations from a baseline variant run many times.

    The strong null: a variant you assert carries no treatment effect, measured in the
    same harness, so it inherits the harness's own noise structure.
    """
    sub = log.frame[log.frame[log.variant] == baseline_variant]
    if sub.empty:
        raise KeyError(
            f"baseline variant {baseline_variant!r} not in the log. Available: "
            f"{sorted(log.frame[log.variant].unique())[:8]}"
        )
    vals = sub[log.outcome].to_numpy(dtype=float)
    vals = vals[np.isfinite(vals)]
    return vals.reshape(-1, features) if features > 1 else vals.reshape(-1, 1)


def permutation_pool(log: ExecutionLog, *, seed: int = 0) -> tuple[np.ndarray, str]:
    """Weak null: all executions pooled, variant labels discarded.

    Returns ``(pool, caveat)``. The caveat is returned rather than logged so that a
    report built on this null has to carry the sentence — the whole point of Stage 8 is
    that a weaker method cannot silently be described as the stronger one.
    """
    rng = np.random.default_rng(seed)
    vals = log.frame[log.outcome].to_numpy(dtype=float)
    vals = vals[np.isfinite(vals)]
    rng.shuffle(vals)
    caveat = (
        "Null estimated by pooling ALL executions and discarding variant labels. Real "
        "effects contaminate this pool, so it is conservative: it overstates the null "
        "and understates every z. Prefer a dedicated baseline variant where one exists."
    )
    return vals.reshape(-1, 1), caveat
