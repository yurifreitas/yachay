"""Stage 10 — Design. Choosing what to measure next.

Stages 0-9 answer *"given these measurements, what should I nominate?"*. This one answers
the question that comes before it and is almost never asked: **"given a budget, which
measurements should I buy?"**

It matters because the default is actively bad. Every screening competition, and most
internal pipelines, nominate **the highest-scoring candidates**. That is the right design
for *harvesting* — you want the best few and you are done. It is close to the worst design
for *learning*, for a reason that is structural rather than statistical:

    The top of a ranking is concentrated. In the screen this library came from, the six
    nominated pairs contained just five distinct genes, and one gene (PLAGL1) appeared in
    five of the six. A design like that measures one gene repeatedly and leaves the rest
    of the space untouched, so the resulting data can support almost no inference about
    which genes interact.

The classical name for the fix is **optimal experimental design** (Kiefer & Wolfowitz
1960; Fedorov's exchange algorithm, 1972). It is sixty years old, standard in
pharmacology and industrial statistics, and largely absent from ML screening pipelines.

## The model this stage designs for

The quantity you want to learn is usually an entity-level effect composed additively:

    y[i,j] = a[i] + a[j] + noise

Estimating `a` well means making `XᵀX` well-conditioned, where `X` is the incidence matrix
of the design. Two classical criteria:

* **D-optimality** — maximise `det(XᵀX)`; the volume of the confidence ellipsoid shrinks.
* **A-optimality** — minimise `trace((XᵀX)⁻¹)`; the *average* variance of the estimates.

`A` is the better default here: it optimises the thing you actually report (per-entity
estimates), and it degrades gracefully when the design is briefly singular.

## What this stage does NOT claim

Optimal design maximises information about a model *you have already chosen*. It cannot
tell you that the model is wrong. Pair it with Stage 4 (baseline-first) and Stage 5
(leakage-safe validation), which can. And a pure-information design is not a nomination
list: if the budget must also deliver hits, split it (see :func:`split_budget`) rather
than pretending one set does both jobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "DesignReport",
    "a_optimal_pairs",
    "balanced_pairs",
    "design_report",
    "focused_pairs",
    "suggest_n_entities",
    "split_budget",
    "top_k_pairs",
    "power_for_design",
]


# ---------------------------------------------------------------------------
# Diagnosing a design
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DesignReport:
    """What a set of chosen measurements can and cannot support."""

    n_measurements: int
    n_entities: int
    max_share: float           # largest share of measurements held by one entity
    min_appearances: int       # fewest appearances among entities present
    a_score: float             # mean variance of the per-entity estimates (lower better)
    d_logdet: float            # log det of the information matrix (higher better)
    estimable: int             # entities appearing enough times to be estimated at all

    def summary(self) -> str:
        return (
            f"{self.n_measurements} measurements over {self.n_entities} entities; "
            f"top entity holds {self.max_share:.0%}; {self.estimable} estimable; "
            f"A={self.a_score:.4g} (mean estimate variance), log|XtX|={self.d_logdet:.4g}"
        )


def _incidence(pairs: Sequence[tuple[str, str]]) -> tuple[np.ndarray, list[str]]:
    """Design matrix for y[i,j] = a[i] + a[j]: one row per pair, two ones per row."""
    entities = sorted({e for p in pairs for e in p})
    index = {e: k for k, e in enumerate(entities)}
    X = np.zeros((len(pairs), len(entities)), dtype=float)
    for r, (i, j) in enumerate(pairs):
        X[r, index[i]] += 1.0
        X[r, index[j]] += 1.0      # += so a self-pair (i,i) correctly carries weight 2
    return X, entities


def _a_and_d(X: np.ndarray, ridge: float = 1e-6) -> tuple[float, float]:
    """A-score (mean estimate variance) and D-score (log det) of a design matrix."""
    info = X.T @ X + ridge * np.eye(X.shape[1])
    try:
        a = float(np.trace(np.linalg.inv(info)) / X.shape[1])
    except np.linalg.LinAlgError:
        a = float("inf")
    sign, logdet = np.linalg.slogdet(info)
    return a, float(logdet) if sign > 0 else float("-inf")


def design_report(pairs: Sequence[tuple[str, str]], min_appearances: int = 3) -> DesignReport:
    """Diagnose a proposed set of measurements before spending the budget on it."""
    if not pairs:
        raise ValueError("no pairs given")
    X, entities = _incidence(pairs)
    counts = X.sum(axis=0)
    a, d = _a_and_d(X)
    return DesignReport(
        n_measurements=len(pairs),
        n_entities=len(entities),
        max_share=float(counts.max() / len(pairs)),
        min_appearances=int(counts.min()),
        a_score=a,
        d_logdet=d,
        estimable=int((counts >= min_appearances).sum()),
    )


# ---------------------------------------------------------------------------
# Designs
# ---------------------------------------------------------------------------
def top_k_pairs(candidates: pd.DataFrame, budget: int, *, score: str = "score",
                a: str = "geneA", b: str = "geneB") -> list[tuple[str, str]]:
    """The default design: measure the highest-scoring candidates.

    Included as the BASELINE TO BEAT, not as a recommendation. It is correct when the
    budget's only job is to harvest hits and you will not model the results.
    """
    top = candidates.nlargest(budget, score)
    return [(str(r[a]), str(r[b])) for _, r in top.iterrows()]


def balanced_pairs(candidates: pd.DataFrame, budget: int, *, score: str = "score",
                   a: str = "geneA", b: str = "geneB",
                   cap: int | None = None) -> list[tuple[str, str]]:
    """Greedy: take the best candidate whose entities are not yet over-represented.

    A cheap, explainable middle ground — it keeps a score preference but refuses to spend
    the whole budget on one entity. `cap` defaults to roughly an even split.
    """
    if cap is None:
        cap = max(2, int(np.ceil(2 * budget / max(8, budget // 3))))
    used: dict[str, int] = {}
    chosen: list[tuple[str, str]] = []
    for _, r in candidates.sort_values(score, ascending=False).iterrows():
        i, j = str(r[a]), str(r[b])
        if used.get(i, 0) >= cap or used.get(j, 0) >= cap:
            continue
        chosen.append((i, j))
        used[i] = used.get(i, 0) + 1
        used[j] = used.get(j, 0) + 1
        if len(chosen) >= budget:
            break
    return chosen


def a_optimal_pairs(candidates: pd.DataFrame, budget: int, *, score: str | None = None,
                    a: str = "geneA", b: str = "geneB", seed: int = 0,
                    score_weight: float = 0.0) -> list[tuple[str, str]]:
    """Greedy A-optimal design: each pick is the one that most reduces estimate variance.

    Sequential greedy rather than Fedorov exchange — with thousands of candidates the
    exchange step is not worth its cost, and greedy A-optimality is within a few percent
    in practice.

    `score_weight > 0` blends in a preference for high-scoring candidates, for the common
    real constraint that the budget must also return something useful. 0 is pure
    information; large values approach :func:`top_k_pairs`.
    """
    rng = np.random.default_rng(seed)
    cand = [(str(r[a]), str(r[b])) for _, r in candidates.iterrows()]
    if score_weight and score is not None:
        s = candidates[score].to_numpy(dtype=float)
        s = (s - s.min()) / (np.ptp(s) or 1.0)
    else:
        s = np.zeros(len(cand))

    entities = sorted({e for p in cand for e in p})
    index = {e: k for k, e in enumerate(entities)}
    p = len(entities)

    # Track the information matrix incrementally; a ridge keeps it invertible from step 1.
    info = 1e-3 * np.eye(p)
    inv = np.linalg.inv(info)
    chosen: list[tuple[str, str]] = []
    remaining = set(range(len(cand)))

    for _ in range(min(budget, len(cand))):
        best, best_gain = -1, -np.inf
        # Rows are sparse (two ones), so the A-criterion update is closed-form per
        # candidate: no matrix inverse inside the loop.
        for idx in remaining:
            i, j = cand[idx]
            ii, jj = index[i], index[j]
            u = np.zeros(p)
            u[ii] += 1.0
            u[jj] += 1.0
            v = inv @ u
            denom = 1.0 + float(u @ v)
            gain = float(v @ v) / denom            # reduction in trace(inv)
            if score_weight:
                gain += score_weight * s[idx]
            if gain > best_gain:
                best_gain, best = gain, idx
        if best < 0:
            break
        i, j = cand[best]
        u = np.zeros(p)
        u[index[i]] += 1.0
        u[index[j]] += 1.0
        v = inv @ u
        inv -= np.outer(v, v) / (1.0 + float(u @ v))   # Sherman-Morrison
        chosen.append((i, j))
        remaining.discard(best)
    return chosen


def focused_pairs(candidates: pd.DataFrame, budget: int, *, n_entities: int,
                  score: str = "score", a: str = "geneA", b: str = "geneB",
                  seed: int = 0) -> list[tuple[str, str]]:
    """Restrict to the top `n_entities` by score, then design A-optimally WITHIN them.

    This exists because pure A-optimality has a failure mode that only shows up when you
    score a design by the power of the test you will actually run.

    A-optimality minimises the MEAN variance of the estimates, so it spreads a small
    budget across every entity in the candidate pool. On a real screen that meant 150
    measurements over 117 genes -- about 2.5 each, below the replication the analysis
    needs per entity, so the permutation test had **zero** power despite an excellent
    A-score. The criterion was optimising a quantity nobody was going to report.

    The fix is a decision the criterion cannot make for you: with a small budget you must
    measure FEWER entities WELL rather than all of them badly. Choose the pool, then let
    A-optimality allocate within it. `n_entities` is that choice, and
    :func:`suggest_n_entities` estimates it from the budget.
    """
    keep = (
        pd.concat([candidates[[a, score]].rename(columns={a: "e"}),
                   candidates[[b, score]].rename(columns={b: "e"})])
        .groupby("e")[score].max().nlargest(n_entities).index
    )
    pool = candidates[candidates[a].isin(keep) & candidates[b].isin(keep)]
    if pool.empty:
        raise ValueError("no candidate pairs lie inside the chosen entity pool")
    return a_optimal_pairs(pool, budget, a=a, b=b, seed=seed)


def suggest_n_entities(budget: int, *, appearances_per_entity: int = 8) -> int:
    """How many entities a budget can support at a target replication level.

    Each pair measurement contributes 2 entity-appearances, so
    ``n_entities = 2 * budget / appearances_per_entity``. The default of 8 is a
    pragmatic floor: below roughly 5 appearances an entity-level effect cannot be
    separated from its own noise, and the permutation test loses power sharply.
    """
    return max(4, int(round(2 * budget / max(1, appearances_per_entity))))


def split_budget(candidates: pd.DataFrame, budget: int, *, harvest: float = 0.5,
                 score: str = "score", a: str = "geneA", b: str = "geneB",
                 seed: int = 0) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Split a budget into a harvest half and a learning half, and return both.

    The honest answer when one budget is asked to do two jobs. Returns
    ``(harvest_pairs, learning_pairs)``; the learning half is chosen A-optimally from
    what the harvest half did not already take, so the two are complementary rather than
    redundant.
    """
    n_harvest = int(round(budget * harvest))
    harvest_pairs = top_k_pairs(candidates, n_harvest, score=score, a=a, b=b)
    taken = {tuple(sorted(p)) for p in harvest_pairs}
    rest = candidates[~candidates.apply(
        lambda r: tuple(sorted((str(r[a]), str(r[b])))) in taken, axis=1)]
    learning_pairs = a_optimal_pairs(rest, budget - n_harvest, a=a, b=b, seed=seed)
    return harvest_pairs, learning_pairs


# ---------------------------------------------------------------------------
# What a design buys you, in power
# ---------------------------------------------------------------------------
def power_for_design(
    pairs: Sequence[tuple[str, str]],
    *,
    effect_sd: float,
    noise_sd: float,
    n_sim: int = 300,
    n_perm: int = 300,
    alpha: float = 0.05,
    min_appearances: int = 3,
    seed: int = 0,
) -> float:
    """Simulated power to detect entity-specific effects under this exact design.

    `effect_sd` and `noise_sd` are the entity-level effect sd and the per-measurement
    noise sd — estimate both from a pilot rather than assuming them. The test is the same
    label permutation used elsewhere in the library, so the number is comparable to what
    the analysis will actually report.

    This is the function that makes the stage concrete: it converts "which design?" into
    a number you can put in a budget request.
    """
    rng = np.random.default_rng(seed)
    entities = sorted({e for p in pairs for e in p})
    index = {e: k for k, e in enumerate(entities)}
    ia = np.array([index[i] for i, _ in pairs])
    ib = np.array([index[j] for _, j in pairs])
    memb = {k: (ia == k) | (ib == k) for k in range(len(entities))}
    eligible = [k for k in range(len(entities)) if memb[k].sum() >= min_appearances]
    if len(eligible) < 4:
        return 0.0                      # too few estimable entities for the test to run

    hits = 0
    for _ in range(n_sim):
        eff = rng.normal(0, effect_sd, len(entities))
        y = eff[ia] + eff[ib] + rng.normal(0, noise_sd, len(pairs))
        stat = np.var([y[memb[k]].mean() for k in eligible])
        null = np.empty(n_perm)
        for t in range(n_perm):
            yp = rng.permutation(y)
            null[t] = np.var([yp[memb[k]].mean() for k in eligible])
        if float((null >= stat).mean()) < alpha:
            hits += 1
    return hits / n_sim
