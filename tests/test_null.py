"""Stage 1 tests.

Every test here corresponds to a mistake that was actually made in the screen this
library was distilled from, not to a hypothetical.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import sieve as sv
from sieve.stages.null import _default_grid


def control_pool(n=4000, features=12, rho=0.45, seed=0):
    """Correlated control observations — a screen's signatures are never independent."""
    rng = np.random.default_rng(seed)
    shared = rng.normal(size=(n, 1))
    own = rng.normal(size=(n, features))
    return rho * shared + np.sqrt(1 - rho**2) * own


def test_topk_mean_is_biased_upward_under_pure_noise():
    """The whole premise: a top-k statistic reads above zero with no effect present."""
    null = sv.fit_null(control_pool(), sv.top_k_mean(3), observed_counts=[1, 500], n_draws=800)
    assert null.mean[0] > 0.4, "top-3-of-12 on one observation should be far above zero"
    assert null.mean[-1] < null.mean[0] / 4, "the bias must shrink as n grows"


def test_bias_decays_monotonically_with_observation_count():
    null = sv.fit_null(control_pool(), sv.top_k_mean(3), observed_counts=[1, 1000], n_draws=800)
    d = np.diff(null.mean)
    assert (d <= 1e-3).all(), f"null mean is not decreasing in n: {null.mean}"
    assert (np.diff(null.sd) <= 1e-3).all(), "null sd must also shrink with n"


def test_calibration_removes_the_count_artifact():
    """The finding that reframed an entire project.

    Entities with NO effect but different observation counts get systematically
    different raw scores. Ranking on the raw score therefore ranks observation count.
    Calibrated, that correlation must collapse.
    """
    ctrl = control_pool(n=6000)
    rng = np.random.default_rng(1)
    counts = rng.integers(1, 800, size=400)
    stat = sv.top_k_mean(3)

    raw = np.array([stat(ctrl[rng.integers(0, len(ctrl), size=(1, c))].mean(axis=1))[0]
                    for c in counts])
    df = pd.DataFrame({"entity": [f"e{i}" for i in range(len(counts))],
                       "score": raw, "n": counts})
    sv.entity_scores().validate(df)

    null = sv.fit_null(ctrl, stat, observed_counts=counts, n_draws=1500)
    out = sv.calibrate(df, null, score="score", count="n")

    def spearman(a, b):
        ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
        return float(np.corrcoef(ra, rb)[0, 1])

    before = abs(spearman(out["score"], np.log1p(out["n"])))
    after = abs(spearman(out["z"], np.log1p(out["n"])))
    assert before > 0.35, f"setup failed: raw score should track count, got {before:.3f}"
    assert after < 0.15, f"calibration left a count artifact: {after:.3f} (was {before:.3f})"


def test_grid_must_span_the_observed_counts():
    """The bug that shipped: np.interp CLAMPS, so a short grid silently mis-calibrates.

    A grid ending at 512 calibrated a 1,645-observation entity against the 512 null,
    understating its z by nearly half. Now it is an error, not a silent wrong answer.
    """
    ctrl = control_pool()
    with pytest.raises(ValueError, match="does not span"):
        sv.fit_null(ctrl, sv.top_k_mean(3), observed_counts=[1, 5000],
                    grid=[1, 4, 16, 64, 512], n_draws=200)


def test_grid_spans_endpoints_by_default():
    counts = [3, 17, 940]
    null = sv.fit_null(control_pool(), sv.top_k_mean(3), observed_counts=counts, n_draws=200)
    assert null.counts[0] <= min(counts) and null.counts[-1] >= max(counts)
    assert _default_grid(3, 940)[0] == 3


def test_refuses_a_control_pool_too_small_to_be_honest():
    with pytest.raises(ValueError, match="too few"):
        sv.fit_null(control_pool(n=20), sv.top_k_mean(3), observed_counts=[1, 10])


def test_calibration_is_deterministic_for_a_seed():
    a = sv.fit_null(control_pool(), sv.top_k_mean(3), observed_counts=[1, 100], n_draws=400, seed=7)
    b = sv.fit_null(control_pool(), sv.top_k_mean(3), observed_counts=[1, 100], n_draws=400, seed=7)
    np.testing.assert_allclose(a.mean, b.mean)
    np.testing.assert_allclose(a.sd, b.sd)


def test_a_real_effect_survives_calibration():
    """Calibration must not flatten everything — a genuine large effect stays on top."""
    ctrl = control_pool(n=5000)
    stat = sv.top_k_mean(3)
    counts = np.array([1, 1, 1, 200])
    # three one-observation noise draws, and one real effect measured on 200 observations
    rng = np.random.default_rng(3)
    scores = [stat(ctrl[rng.integers(0, len(ctrl), size=(1, 1))].mean(axis=1))[0] for _ in range(3)]
    scores.append(1.0)  # modest raw score, but on 200 observations
    df = pd.DataFrame({"entity": list("abcd"), "score": scores, "n": counts})
    null = sv.fit_null(ctrl, stat, observed_counts=counts, n_draws=1500)
    out = sv.calibrate(df, null, score="score", count="n")
    assert out.loc[out["z"].idxmax(), "entity"] == "d", (
        "the well-measured real effect must win after calibration:\n" + out.to_string()
    )
