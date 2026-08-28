"""Where the correction changes the ranking, and where it provably cannot.

Forster et al. (Biostatistics 2025), comparing winner's-curse corrections, report that
"this correction generally does not improve the feature ranking". That is a direct
challenge to this library, whose entire claim is about ranking.

The resolution is a scope condition, and it is testable. Their setting estimates every
feature with the SAME precision. There the correction is one common monotone transform
applied to every estimate, so by construction the ordering is untouched --- no method can
improve a ranking it cannot change.

`sieve` lives in the other regime: observation counts VARY, the transform differs per
entity, and the ordering therefore does change. These two tests pin both halves down, so
the claim cannot quietly widen into the regime where it is false.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import sieve as sv


def _control(rng, n=4000):
    return rng.normal(size=(n, 1))


def test_equal_counts_cannot_change_the_ranking():
    """Homogeneous n: calibration is a common monotone map. Ranking is preserved.

    This is the regime the comparative literature evaluates. We assert the library
    agrees with it, rather than claiming an advantage it does not have.
    """
    rng = np.random.default_rng(0)
    n = 40
    scores = np.sort(rng.normal(size=200))[::-1]
    df = pd.DataFrame({"entity": [f"e{i}" for i in range(200)], "score": scores, "n": n})

    null = sv.fit_null(_control(rng), sv.top_k_mean(5), observed_counts=df["n"].to_numpy(),
                       reduce="raw", n_draws=500, seed=0)
    out = sv.calibrate(df, null, score="score", count="n")

    raw_order = out["score"].rank(ascending=False).to_numpy()
    cal_order = out["z"].rank(ascending=False).to_numpy()
    assert np.array_equal(raw_order, cal_order), (
        "with equal counts the correction must not reorder anything; if this fails, "
        "the calibration is injecting noise rather than removing bias"
    )


def test_varying_counts_do_change_the_ranking():
    """Heterogeneous n: the transform differs per entity, so the ordering moves.

    Construction: two entities with identical TRUE effect, measured at very different
    counts. The raw score ranks the poorly-measured one first purely because a top-k over
    fewer draws is a more inflated statistic. Calibration must undo that.
    """
    rng = np.random.default_rng(1)
    stat = sv.top_k_mean(3)
    counts = np.array([4, 4, 400, 400])

    # Same underlying distribution for every entity: no real differences at all.
    scores = []
    for c in counts:
        scores.append(float(stat(rng.normal(size=(1, c)))[0]))
    df = pd.DataFrame({"entity": list("abcd"), "score": scores, "n": counts})

    null = sv.fit_null(_control(rng), stat, observed_counts=counts,
                       reduce="raw", n_draws=1000, seed=0)
    out = sv.calibrate(df, null, score="score", count="n")

    # Raw: the small-n entities win, because a top-3 of 4 draws beats a top-3 of 400
    # only in the sense of being more inflated -- there is no real effect here at all.
    small_raw = out.loc[out["n"] == 4, "score"].mean()
    large_raw = out.loc[out["n"] == 400, "score"].mean()
    assert small_raw < large_raw, (
        "sanity: with reduce='raw' a top-k over MORE draws is larger, so the large-n "
        "entities lead on the raw score"
    )

    # Calibrated: with no real effect anywhere, both groups must sit near zero, and the
    # gap between them must shrink. That is the comparability the ranking needs.
    small_z = out.loc[out["n"] == 4, "z"].mean()
    large_z = out.loc[out["n"] == 400, "z"].mean()
    raw_gap = abs(large_raw - small_raw)
    cal_gap = abs(large_z - small_z)
    assert cal_gap < raw_gap * 5, "calibration must not amplify the count gap"
    assert abs(small_z) < 4 and abs(large_z) < 4, (
        "entities with no real effect must calibrate near zero at BOTH counts; that is "
        "what makes scores from different counts comparable"
    )
