"""The non-biology instance: does the same correction fix an LLM leaderboard?

If it does not, `sieve` is a genomics library with pretensions. These tests are the
claim that it is not.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import sieve as sv
from sieve.adapters import llm_eval as le


def make_log(run_budgets: dict[str, int], true_rate: float = 0.5, seed: int = 0):
    """Variants that are ALL EQUALLY GOOD, differing only in how often they were run."""
    rng = np.random.default_rng(seed)
    rows = []
    for variant, n in run_budgets.items():
        for i in range(n):
            rows.append({
                "variant": variant,
                "item": f"item{i % 20}",
                "outcome": float(rng.random() < true_rate),
            })
    return le.ExecutionLog(pd.DataFrame(rows))


def test_best_of_n_leaderboard_ranks_the_run_budget():
    """The bug, demonstrated: identical variants, different budgets, false ranking."""
    budgets = {f"v{i}": n for i, n in enumerate([4, 8, 16, 32, 64, 128, 256])}
    log = make_log(budgets)
    board = le.score_variants(log, le.best_of_n)

    counts = board["n"].to_numpy()
    scores = board["score"].to_numpy()
    # With a 0/1 outcome, best-of-N saturates at 1.0 quickly — the inflation shows as
    # the low-budget variants being the ONLY ones that fail to reach the ceiling.
    worst = board.nsmallest(1, "score").iloc[0]
    assert worst["n"] == min(counts), (
        "the lowest-scoring variant should be the least-run one, since all variants are "
        f"equally good by construction:\n{board}"
    )
    assert scores.max() == 1.0


def test_mean_is_unbiased_so_calibration_barely_moves_it():
    """The contrast case, so the library does not oversell the correction.

    "Unbiased" means no SYSTEMATIC drift with run count. It does not mean a small
    spread: at n=8 with p=0.5 the standard error is 0.18, so low-budget variants scatter
    widely. That scatter is variance, and the fix for variance is a confidence interval,
    not Stage 1. Averaged over seeds, the correlation with run count must vanish.
    """
    budgets = {f"v{i}": n for i, n in enumerate([8, 16, 64, 256, 512])}
    corrs = []
    for seed in range(40):
        board = le.score_variants(make_log(budgets, seed=seed), le.pass_rate)
        corrs.append(float(np.corrcoef(
            pd.Series(board["score"]).rank(), pd.Series(board["n"]).rank())[0, 1]))
    mean_corr = float(np.mean(corrs))
    assert abs(mean_corr) < 0.25, (
        f"a plain mean drifted with run count (mean rho={mean_corr:+.3f} over 40 seeds); "
        "if a MEAN is biased by budget, the test data is wrong, not the library."
    )


def test_calibration_flattens_the_budget_artifact_for_best_of_n():
    """The fix: after Stage 1, equally-good variants stop being ordered by budget."""
    rng = np.random.default_rng(11)
    # Continuous judge scores make the max-order bias visible without saturating at 1.0.
    budgets = {f"v{i}": n for i, n in enumerate([5, 10, 20, 40, 80, 160, 320, 640])}
    rows = []
    for variant, n in budgets.items():
        for i in range(n):
            rows.append({"variant": variant, "item": f"i{i}", "outcome": rng.normal()})
    # a baseline variant, run heavily, carrying no treatment effect
    for i in range(3000):
        rows.append({"variant": "baseline", "item": f"i{i}", "outcome": rng.normal()})
    log = le.ExecutionLog(pd.DataFrame(rows))

    board = le.score_variants(log, le.best_of_n)
    board = board[board["entity"] != "baseline"].reset_index(drop=True)

    def spearman(a, b):
        return float(np.corrcoef(pd.Series(a).rank(), pd.Series(b).rank())[0, 1])

    # 8 variants make Spearman coarse: 7-of-8 concordance is already 0.786, so a 0.8
    # threshold is finer than the statistic's own granularity.
    before = spearman(board["score"], np.log(board["n"]))
    assert before > 0.7, f"setup failed: best-of-N should track run count, got {before:.2f}"

    control = le.baseline_pool(log, "baseline")
    null = sv.fit_null(control, le.best_of_n, observed_counts=board["n"],
                      reduce="raw", n_draws=1200)
    out = sv.calibrate(board, null, score="score", count="n")

    after = abs(spearman(out["z"], np.log(out["n"])))
    assert after < 0.5, (
        f"calibration failed to remove the run-budget artifact: {before:.2f} -> {after:.2f}\n"
        f"{out[['entity', 'score', 'n', 'z']]}"
    )


def test_permutation_pool_returns_its_own_caveat():
    """A weaker null must carry the sentence that says so (Stage 8)."""
    log = make_log({"a": 40, "b": 40})
    pool, caveat = le.permutation_pool(log)
    assert pool.ndim == 2 and len(pool) == 80
    assert "conservative" in caveat and "baseline" in caveat


def test_missing_baseline_names_the_available_variants():
    log = make_log({"a": 10, "b": 10})
    with pytest.raises(KeyError, match="Available"):
        le.baseline_pool(log, "does-not-exist")


def test_variant_scores_satisfy_the_shared_contract():
    """Every adapter must emit the same frame, or the stages are not really shared."""
    log = make_log({"a": 30, "b": 60})
    board = le.score_variants(log, le.pass_rate)
    sv.entity_scores().validate(board)
