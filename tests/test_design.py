"""Stage 10 tests.

The claims this stage makes are quantitative, so the tests are too: each one asserts a
relationship between designs that was measured on real data, not a code path.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sieve.stages import design as dz


def universe(n_entities: int = 40, seed: int = 0) -> pd.DataFrame:
    """All pairs over n entities, with a score that concentrates on a few of them."""
    rng = np.random.default_rng(seed)
    names = [f"g{i:02d}" for i in range(n_entities)]
    strength = dict(zip(names, rng.exponential(1.0, n_entities)))
    rows = [(a, b, strength[a] + strength[b])
            for i, a in enumerate(names) for b in names[i:]]
    return pd.DataFrame(rows, columns=["geneA", "geneB", "score"])


def test_top_k_touches_many_entities_but_estimates_almost_none():
    """The core diagnosis, and it is sharper than "top-k covers fewer entities".

    Top-k actually TOUCHES more entities than a balanced design -- it reaches deep into
    the tail, one measurement at a time. What it does not do is measure any of them
    enough times to estimate. Coverage is not the metric; estimability is.
    """
    u = universe()
    top = dz.design_report(dz.top_k_pairs(u, 60))
    bal = dz.design_report(dz.balanced_pairs(u, 60))

    assert top.max_share > bal.max_share * 2, (
        f"top-k should be far more concentrated: {top.summary()} vs {bal.summary()}")
    assert top.min_appearances < bal.min_appearances, (
        "top-k leaves entities with too few measurements to estimate")
    assert top.estimable < bal.estimable, (
        f"top-k touches {top.n_entities} entities but estimates only {top.estimable}; "
        f"balanced touches {bal.n_entities} and estimates {bal.estimable}")


def test_a_optimal_beats_top_k_on_estimate_variance():
    """The criterion does what it says: lower mean variance of the per-entity estimates."""
    u = universe()
    a_score = dz.design_report(dz.a_optimal_pairs(u, 60, seed=1)).a_score
    top_score = dz.design_report(dz.top_k_pairs(u, 60)).a_score
    assert a_score < top_score, f"A-optimal {a_score:.4g} should beat top-k {top_score:.4g}"


def test_focused_design_beats_both_on_actual_power():
    """The finding that motivated `focused_pairs`.

    A-optimality minimises MEAN estimate variance, which spreads a small budget across
    every entity -- below the replication the permutation test needs, so power collapses
    even though the A-score is excellent. Sizing the pool first fixes it. Measured on the
    real screen: top-k 4%, pure A-optimal 0%, focused 20%.
    """
    u = universe(n_entities=60, seed=3)
    budget, tau, sigma = 120, 0.3, 1.0
    kw = dict(effect_sd=tau, noise_sd=sigma, n_sim=120, n_perm=120, seed=5)

    p_top = dz.power_for_design(dz.top_k_pairs(u, budget), **kw)
    p_all = dz.power_for_design(dz.a_optimal_pairs(u, budget, seed=5), **kw)
    p_focus = dz.power_for_design(
        dz.focused_pairs(u, budget, n_entities=dz.suggest_n_entities(budget), seed=5), **kw)

    assert p_focus > p_top, f"focused {p_focus:.2f} should beat top-k {p_top:.2f}"
    assert p_focus >= p_all, f"focused {p_focus:.2f} should beat spread-thin {p_all:.2f}"


def test_suggest_n_entities_matches_the_replication_target():
    """Each pair contributes two appearances, so n = 2 * budget / appearances."""
    assert dz.suggest_n_entities(150, appearances_per_entity=8) == 38
    assert dz.suggest_n_entities(600, appearances_per_entity=8) == 150
    assert dz.suggest_n_entities(10, appearances_per_entity=100) == 4   # floored


def test_power_is_zero_when_the_test_cannot_run():
    """A design with too few estimable entities reports 0, not a spurious number."""
    tiny = [("a", "b"), ("c", "d")]
    assert dz.power_for_design(tiny, effect_sd=1.0, noise_sd=0.1, n_sim=10, n_perm=10) == 0.0


def test_split_budget_returns_disjoint_halves():
    """The honest answer when one budget must both harvest and learn."""
    u = universe()
    harvest, learning = dz.split_budget(u, 40, harvest=0.5, seed=2)
    assert len(harvest) == 20 and len(learning) == 20
    overlap = {tuple(sorted(p)) for p in harvest} & {tuple(sorted(p)) for p in learning}
    assert not overlap, f"the two halves must be complementary, got {overlap}"


def test_self_pairs_carry_double_weight():
    """A pair (i, i) is two measurements of i, and the incidence matrix must say so."""
    rep = dz.design_report([("a", "a"), ("a", "b"), ("b", "c"), ("c", "a")])
    assert rep.n_entities == 3
    # 'a' appears twice in the self-pair plus once each in two others = 4 of 8 slots.
    assert rep.max_share == pytest.approx(4 / 4)


def test_design_report_rejects_an_empty_design():
    with pytest.raises(ValueError, match="no pairs"):
        dz.design_report([])
